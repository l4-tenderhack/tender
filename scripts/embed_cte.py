#!/usr/bin/env python3
"""
Batch-embed CTE names from PostgreSQL via Ollama and store vectors in Qdrant.

Saves progress to a checkpoint file so it can resume after interruption.

Usage:
    pip install asyncpg httpx
    python scripts/embed_cte.py
    python scripts/embed_cte.py --batch-size 500 --ollama-batch 64 --collection cte_name
    python scripts/embed_cte.py --reset  # ignore checkpoint, start from scratch
"""

import asyncio
import argparse
import json
import logging
import time
import uuid
from pathlib import Path

import asyncpg
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DB_DSN = (
    "postgresql://postgres:q8TNMnTqRGzoXkD8oNSyLLyFt2SpAOMY3e4vVcOU77tGzJo1iTEcyTOALFTuuNS9"
    "@larek.tech:34000/postgres"
)
OLLAMA_URL = "http://larek.tech:55300"
QDRANT_URL = "https://qdrant.larek.tech"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"

POINT_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
MAX_RETRIES = 5
RETRY_DELAY = 5
CHECKPOINT_FILE = Path(__file__).parent / ".embed_checkpoint.json"


def load_checkpoint(collection: str) -> dict:
    if CHECKPOINT_FILE.exists():
        data = json.loads(CHECKPOINT_FILE.read_text())
        if data.get("collection") == collection:
            return data
    return {}


def save_checkpoint(collection: str, last_id: str, processed: int, failed_ids: list[str]):
    CHECKPOINT_FILE.write_text(json.dumps({
        "collection": collection,
        "last_id": last_id,
        "processed": processed,
        "failed": len(failed_ids),
        "failed_ids": failed_ids,
    }))


def clear_checkpoint():
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()


OLLAMA_OPTIONS: dict = {}


async def get_embedding_dim(http: httpx.AsyncClient) -> int:
    resp = await http.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": ["test"], "options": OLLAMA_OPTIONS},
        timeout=10,
    )
    resp.raise_for_status()
    return len(resp.json()["embeddings"][0])


async def embed_batch(http: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    for attempt in range(MAX_RETRIES):
        try:
            resp = await http.post(
                f"{OLLAMA_URL}/api/embed",
                json={"model": EMBEDDING_MODEL, "input": texts, "options": OLLAMA_OPTIONS},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()["embeddings"]
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning(f"Embed retry {attempt + 1}/{MAX_RETRIES} (wait {wait}s): {e}")
                await asyncio.sleep(wait)
            else:
                raise


async def detect_name_column(conn: asyncpg.Connection) -> str:
    cols = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'cte_main' ORDER BY ordinal_position"
    )
    names = [r["column_name"] for r in cols]
    logger.info(f"cte_main columns: {names}")
    for candidate in ("cte_position_name", "description", "cte_name"):
        if candidate in names:
            return candidate
    raise ValueError(f"No suitable name column found among: {names}")


def make_point_id(cte_id: str) -> str:
    return str(uuid.uuid5(POINT_NAMESPACE, cte_id))


async def qdrant_upsert(http: httpx.AsyncClient, collection: str, points: list[dict]):
    resp = await http.put(
        f"{QDRANT_URL}/collections/{collection}/points",
        json={"points": points},
        timeout=120,
    )
    resp.raise_for_status()


async def main(batch_size: int, collection: str, ollama_batch: int, reset: bool, num_thread: int):
    global OLLAMA_OPTIONS
    if num_thread > 0:
        OLLAMA_OPTIONS = {"num_thread": num_thread}
        logger.info(f"Ollama num_thread: {num_thread}")

    if reset:
        clear_checkpoint()
        logger.info("Checkpoint cleared, starting from scratch")

    checkpoint = load_checkpoint(collection)
    last_id = checkpoint.get("last_id", "")
    processed = checkpoint.get("processed", 0)
    failed_ids: list[str] = checkpoint.get("failed_ids", [])

    if last_id:
        logger.info(f"Resuming from checkpoint: last_id={last_id}, processed={processed:,}, failed={len(failed_ids)}")

    logger.info("Connecting to PostgreSQL...")
    conn = await asyncpg.connect(DB_DSN)

    try:
        name_col = await detect_name_column(conn)
        logger.info(f"Name column: {name_col}")

        total = await conn.fetchval("SELECT COUNT(*) FROM cte_main")
        logger.info(f"Total CTE records: {total:,}")

        async with httpx.AsyncClient() as http:
            dim = await get_embedding_dim(http)
        logger.info(f"Embedding dimension: {dim}")

        async with httpx.AsyncClient() as http:
            resp = await http.get(f"{QDRANT_URL}/collections/{collection}", timeout=30)
            if resp.status_code == 200:
                info = resp.json()
                pts = info.get("result", {}).get("points_count", 0)
                logger.info(f"Qdrant collection '{collection}' exists ({pts} points)")
            else:
                logger.info(f"Creating Qdrant collection '{collection}' (dim={dim})...")
                resp = await http.put(
                    f"{QDRANT_URL}/collections/{collection}",
                    json={"vectors": {"size": dim, "distance": "Cosine"}},
                    timeout=30,
                )
                resp.raise_for_status()
                logger.info(f"Created collection '{collection}'")

        start = time.time()

        async with httpx.AsyncClient() as http:
            while True:
                rows = await conn.fetch(
                    f"SELECT cte_id, {name_col} FROM cte_main "
                    f"WHERE cte_id > $1 ORDER BY cte_id LIMIT $2",
                    last_id,
                    batch_size,
                )
                if not rows:
                    break

                last_id = rows[-1]["cte_id"]

                ids = [str(r["cte_id"]) for r in rows]
                names_original = [str(r[name_col] or "") for r in rows]
                texts_lower = [n.lower() for n in names_original]

                all_embeddings: list[list[float] | None] = []
                for i in range(0, len(texts_lower), ollama_batch):
                    chunk = texts_lower[i : i + ollama_batch]
                    chunk_ids = ids[i : i + ollama_batch]
                    try:
                        embs = await embed_batch(http, chunk)
                        all_embeddings.extend(embs)
                    except Exception as e:
                        logger.error(f"Embedding failed at batch offset {i}: {e}")
                        all_embeddings.extend([None] * len(chunk))
                        failed_ids.extend(chunk_ids)

                points = []
                for cte_id, name, emb in zip(ids, names_original, all_embeddings):
                    if emb is None:
                        continue
                    points.append({
                        "id": make_point_id(cte_id),
                        "vector": emb,
                        "payload": {"cte_id": cte_id, "name": name},
                    })

                for i in range(0, len(points), 500):
                    await qdrant_upsert(http, collection, points[i : i + 500])

                processed += len(rows)
                save_checkpoint(collection, last_id, processed, failed_ids)

                elapsed = time.time() - start
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = total - processed
                eta_min = remaining / rate / 60 if rate > 0 else 0
                logger.info(
                    f"{processed:,}/{total:,} ({100 * processed / total:.1f}%) "
                    f"| {rate:.0f}/s | ETA {eta_min:.1f}m | failed={len(failed_ids)}"
                )

        elapsed = time.time() - start
        logger.info(
            f"Done: {processed:,} records in {elapsed / 60:.1f} min, {len(failed_ids)} failed"
        )
        if failed_ids:
            logger.info(f"Failed IDs: {failed_ids}")
        clear_checkpoint()

    finally:
        await conn.close()


async def run_with_restart(
    batch_size: int,
    collection: str,
    ollama_batch: int,
    reset: bool,
    num_thread: int,
    max_restarts: int = 50,
    restart_delay: int = 10,
):
    for attempt in range(1, max_restarts + 1):
        try:
            await main(batch_size, collection, ollama_batch, reset, num_thread)
            return
        except Exception as e:
            logger.error(f"Crash #{attempt}/{max_restarts}: {e}")
            if attempt >= max_restarts:
                logger.critical("Max restarts reached, giving up")
                raise
            logger.info(f"Restarting in {restart_delay}s (will resume from checkpoint)...")
            await asyncio.sleep(restart_delay)
            reset = False


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Embed CTE names → Qdrant")
    p.add_argument("--batch-size", type=int, default=1000, help="Rows per DB fetch")
    p.add_argument("--ollama-batch", type=int, default=128, help="Texts per Ollama call")
    p.add_argument("--collection", default="cte_name", help="Qdrant collection")
    p.add_argument("--num-thread", type=int, default=10, help="Ollama CPU threads (0 = default)")
    p.add_argument("--reset", action="store_true", help="Ignore checkpoint, start fresh")
    p.add_argument("--max-restarts", type=int, default=50, help="Max auto-restarts on crash")
    p.add_argument("--restart-delay", type=int, default=10, help="Seconds to wait before restart")
    args = p.parse_args()

    asyncio.run(run_with_restart(
        args.batch_size, args.collection, args.ollama_batch,
        args.reset, args.num_thread, args.max_restarts, args.restart_delay,
    ))
