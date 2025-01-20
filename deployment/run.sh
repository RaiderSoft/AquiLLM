#!/bin/bash
set -e

if [[ -v DJANGO_DEBUG ]]; then
    ./manage.py migrate --noinput
    ./manage.py collectstatic --noinput
    exec ./manage.py runserver 0.0.0.0:${PORT:-8080}
else
    exec python -m uvicorn aquillm.asgi:application --host 0.0.0.0 --port ${PORT:-8080}
fi