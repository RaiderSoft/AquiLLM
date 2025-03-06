#!/bin/bash
set -e

celery -A aquillm worker --loglevel=info &

exec python -m uvicorn aquillm.asgi:application --host 0.0.0.0 --port ${PORT:-8080}
