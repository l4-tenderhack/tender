#!/usr/bin/env sh
set -eu

PORT="${PORT:-8000}"
DOCS_URL="${DOCS_URL:-/docs}"
REDOC_URL="${REDOC_URL:-/redoc}"
OPENAPI_URL="${OPENAPI_URL:-/openapi.json}"

printf '\nBackend docs:\n'
printf '  Swagger UI: http://localhost:%s%s\n' "$PORT" "$DOCS_URL"
printf '  ReDoc:      http://localhost:%s%s\n' "$PORT" "$REDOC_URL"
printf '  OpenAPI:    http://localhost:%s%s\n\n' "$PORT" "$OPENAPI_URL"

exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
