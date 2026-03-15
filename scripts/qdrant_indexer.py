#!/usr/bin/env python3
"""
Qdrant indexer for CTE data using OpenRouter embeddings API (qwen/qwen3-embedding-4b).
Uses httpx directly (no qdrant_client) to avoid SSL quirks.

Usage:
    export OPENROUTER_API_KEY=your_key
    python scripts/qdrant_indexer.py \
      --cte search_layer/data/TenderHack_СТЕ.csv \
      --contracts "search_layer/data/TenderHack_Контракты.csv" \
      --qdrant-url https://qdrant.larek.tech \
      --batch-size 64
"""

import argparse
import json
import logging
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

COLLECTION_NAME = "cte_products_qwen"
DEFAULT_BATCH = 64
OPENROUTER_URL = "https://openrouter.ai/api/v1/embeddings"
OPENROUTER_MODEL = "qwen/qwen3-embedding-4b"
EMBEDDING_DIM = 1024


# ---------------------------------------------------------------------------
# OpenRouter
# ---------------------------------------------------------------------------

def _openrouter_headers() -> Dict[str, str]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is required")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def embed_batch(
    http: httpx.Client,
    texts: List[str],
    model: str = OPENROUTER_MODEL,
    dimensions: int = EMBEDDING_DIM,
) -> List[List[float]]:
    if not texts:
        return []
    resp = http.post(
        OPENROUTER_URL,
        headers=_openrouter_headers(),
        json={
            "model": model,
            "input": texts,
            "dimensions": dimensions,
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    data = resp.json()
    items = sorted(data["data"], key=lambda x: x.get("index", 0))
    return [item["embedding"] for item in items]


# ---------------------------------------------------------------------------
# Qdrant REST helpers
# ---------------------------------------------------------------------------

def qdrant_get(http: httpx.Client, base: str, path: str) -> Any:
    resp = http.get(f"{base}{path}", timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def qdrant_put(http: httpx.Client, base: str, path: str, body: Dict) -> Any:
    resp = http.put(f"{base}{path}", json=body, timeout=60.0)
    resp.raise_for_status()
    return resp.json()


def qdrant_post(http: httpx.Client, base: str, path: str, body: Dict) -> Any:
    resp = http.post(f"{base}{path}", json=body, timeout=120.0)
    resp.raise_for_status()
    return resp.json()


def ensure_collection(http: httpx.Client, base: str, collection: str, dim: int):
    existing = {c["name"] for c in qdrant_get(http, base, "/collections")["result"]["collections"]}
    if collection in existing:
        logger.info("Collection '%s' already exists", collection)
        return

    logger.info("Creating collection '%s' (dim=%d)", collection, dim)
    qdrant_put(http, base, f"/collections/{collection}", {
        "vectors": {
            "size": dim,
            "distance": "Cosine",
        },
        "quantization_config": {
            "scalar": {"type": "int8", "always_ram": True}
        },
    })

    for field, schema in [
        ("category", "keyword"),
        ("manufacturer", "keyword"),
        ("price", "float"),
        ("contract_count", "integer"),
    ]:
        qdrant_put(http, base, f"/collections/{collection}/index", {
            "field_name": field,
            "field_schema": schema,
        })

    logger.info("Collection created with indexes")


def upsert_points(http: httpx.Client, base: str, collection: str, points: List[Dict]):
    # wait=false — Qdrant returns immediately, no blocking for write confirmation
    qdrant_put(http, base, f"/collections/{collection}/points?wait=false", {"points": points})


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def parse_characteristics(char_str: str) -> Dict[str, str]:
    if not char_str or pd.isna(char_str):
        return {}
    chars = {}
    for part in re.split(r";(?![^(]*\))", str(char_str)):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            chars[k.strip().lower()] = v.strip()
    return chars


def build_price_map(contracts_path: str) -> Dict[str, Dict]:
    logger.info("Loading contracts from %s", contracts_path)
    df = pd.read_csv(contracts_path)
    logger.info("Contracts rows: %d", len(df))
    price_map = {
        str(k): v
        for k, v in df.groupby("Идентификатор СТЕ по контракту")
        .agg(
            price_avg=("Цена за единицу", "mean"),
            region=("Регион заказчика", lambda x: x.mode()[0] if len(x) else ""),
            contract_count=("Идентификатор контракта", "nunique"),
        )
        .to_dict("index")
        .items()
    }
    logger.info("Price map: %d entries", len(price_map))
    return price_map


def build_embedding_text(doc: Dict) -> str:
    parts = [doc["description"]]
    if doc["category"]:
        parts.append(f"Категория: {doc['category']}")
    if doc["manufacturer"]:
        parts.append(f"Производитель: {doc['manufacturer']}")
    for k, v in list(doc["characteristics"].items())[:10]:
        parts.append(f"{k}: {v}")
    return ". ".join(parts)


def prepare_document(row: Dict, price_map: Optional[Dict]) -> Dict:
    cte_id = str(row.get("Идентификатор СТЕ", ""))
    characteristics = parse_characteristics(row.get("характеристики СТЕ", ""))
    price, region, contract_count = 0.0, "", 0
    if price_map and cte_id in price_map:
        d = price_map[cte_id]
        price = float(d.get("price_avg") or 0)
        region = str(d.get("region") or "")
        contract_count = int(d.get("contract_count") or 0)
    return {
        "cte_id": cte_id,
        "category": str(row.get("Категория", "")),
        "manufacturer": str(row.get("Производитель", "")),
        "description": str(row.get("Наименование СТЕ", "")),
        "characteristics": characteristics,
        "price": price,
        "region": region,
        "contract_count": contract_count,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cte", required=True, help="Path to TenderHack_СТЕ.csv")
    parser.add_argument("--contracts", help="Path to TenderHack_Контракты.csv")
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--collection", default=COLLECTION_NAME)
    parser.add_argument("--openrouter-model", default=OPENROUTER_MODEL,
                        help="OpenRouter embedding model (e.g. qwen/qwen3-embedding-4b)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH,
                        help="Texts per OpenRouter embed request (default 64)")
    parser.add_argument("--workers", type=int, default=1,
                        help="Parallel embed workers for batching")
    args = parser.parse_args()

    headers = {"api-key": args.api_key} if args.api_key else {}
    qdrant_http = httpx.Client(headers=headers, verify=True)
    embed_clients = [httpx.Client() for _ in range(max(1, args.workers))]

    # Detect embedding dimension via probe
    probe = embed_batch(embed_clients[0], ["probe"], model=args.openrouter_model, dimensions=EMBEDDING_DIM)
    dim = len(probe[0])
    logger.info("Embedding dim: %d | batch_size: %d | workers: %d", dim, args.batch_size, args.workers)

    ensure_collection(qdrant_http, args.qdrant_url, args.collection, dim)

    price_map = build_price_map(args.contracts) if args.contracts else None

    logger.info("Reading CTE data from %s", args.cte)
    df = pd.read_csv(args.cte)
    logger.info("CTE rows: %d", len(df))

    docs = [prepare_document(row.to_dict(), price_map) for _, row in df.iterrows()]
    texts = [build_embedding_text(d) for d in docs]

    total = len(docs)
    num_batches = (total + args.batch_size - 1) // args.batch_size
    logger.info("Indexing %d docs in %d batches (batch_size=%d)", total, num_batches, args.batch_size)

    total_embed_ms = 0.0
    total_upsert_ms = 0.0
    docs_done = 0

    def make_points(batch_docs, batch_texts, embeddings, start):
        return [
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, doc["cte_id"] or str(start + j))),
                "vector": embeddings[j],
                "payload": {
                    "cte_id": doc["cte_id"],
                    "category": doc["category"],
                    "manufacturer": doc["manufacturer"],
                    "description": doc["description"],
                    "price": doc["price"],
                    "region": doc["region"],
                    "contract_count": doc["contract_count"],
                    "characteristics_json": json.dumps(doc["characteristics"], ensure_ascii=False),
                    "product_text": batch_texts[j],
                },
            }
            for j, doc in enumerate(batch_docs)
        ]

    bar = tqdm(range(num_batches), desc="Indexing", unit="batch",
               bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {postfix}")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # workers embed threads + 1 upsert thread
    embed_pool = ThreadPoolExecutor(max_workers=args.workers, thread_name_prefix="embed")
    upsert_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="upsert")

    def embed_worker(worker_id: int, batch_texts: List[str]):
        client = embed_clients[worker_id % len(embed_clients)]
        return embed_batch(client, batch_texts, model=args.openrouter_model, dimensions=EMBEDDING_DIM)

    # Split batches across workers when workers>1: each worker gets a sub-batch
    def split_and_embed(batch_texts: List[str], batch_docs: List[Dict], start_idx: int):
        """Embed batch_texts, splitting across workers, return (points, embed_ms)."""
        n = args.workers
        if n == 1:
            t0 = time.perf_counter()
            embs = embed_batch(embed_clients[0], batch_texts, model=args.openrouter_model, dimensions=EMBEDDING_DIM)
            ms = (time.perf_counter() - t0) * 1000
        else:
            chunk = max(1, len(batch_texts) // n)
            futures = {}
            t0 = time.perf_counter()
            for w in range(n):
                sl = slice(w * chunk, (w + 1) * chunk if w < n - 1 else None)
                futures[embed_pool.submit(embed_worker, w, batch_texts[sl])] = sl
            embs = [None] * len(batch_texts)
            for fut in as_completed(futures):
                sl = futures[fut]
                for idx, vec in enumerate(fut.result()):
                    embs[sl.start + idx] = vec
            ms = (time.perf_counter() - t0) * 1000

        pts = make_points(batch_docs, batch_texts, embs, start_idx)
        return pts, ms

    pending_upsert = None
    pending_upsert_t = None

    for i in bar:
        start = i * args.batch_size
        end = min(start + args.batch_size, total)
        batch_texts = texts[start:end]
        batch_docs = docs[start:end]
        bsize = len(batch_docs)

        points, embed_ms = split_and_embed(batch_texts, batch_docs, start)
        total_embed_ms += embed_ms

        # Wait for previous upsert only if still running (should be ~0ms)
        upsert_wait_ms = 0.0
        if pending_upsert is not None:
            t1 = time.perf_counter()
            pending_upsert.result()
            upsert_wait_ms = (time.perf_counter() - t1) * 1000
            total_upsert_ms += (time.perf_counter() - pending_upsert_t) * 1000

        pending_upsert_t = time.perf_counter()
        pending_upsert = upsert_pool.submit(
            upsert_points, qdrant_http, args.qdrant_url, args.collection, points
        )

        docs_done += bsize
        bar.set_postfix({
            "docs": f"{docs_done}/{total}",
            "embed": f"{embed_ms:.0f}ms",
            "wait": f"{upsert_wait_ms:.0f}ms",
            "ms/doc": f"{embed_ms/bsize:.1f}",
        })

    # Flush last upsert
    if pending_upsert is not None:
        pending_upsert.result()

    embed_pool.shutdown(wait=False)
    upsert_pool.shutdown(wait=False)
    bar.close()

    info = qdrant_get(qdrant_http, args.qdrant_url, f"/collections/{args.collection}")
    count = info["result"]["vectors_count"]
    logger.info(
        "Done. '%s' now has %d vectors. "
        "Embed: %.1fs total | Upsert: %.1fs total | Avg %.2fms/doc",
        args.collection, count,
        total_embed_ms / 1000,
        total_upsert_ms / 1000,
        total_embed_ms / total if total else 0,
    )

    for c in embed_clients:
        c.close()
    qdrant_http.close()


if __name__ == "__main__":
    main()
