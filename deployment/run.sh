#!/bin/bash
set -e

exec python -m uvicorn aquillm.asgi:application --host 0.0.0.0 --port ${PORT:-8080}
