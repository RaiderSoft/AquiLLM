#!/bin/bash
# export DJANGO_SETTINGS_MODULE=aquillm.settings
# cd ~chandler/aquillm/
# source venv/bin/activate
# cd aquillm
# python3 -m uvicorn aquillm.asgi:application --host 0.0.0.0 --port 443 --ssl-keyfile=/etc/letsencrypt/live/aquillm.space/privkey.pem --ssl-certfile=/etc/letsencrypt/live/aquillm.space/fullchain.pem
set -e

if [[ -v DJANGO_DEBUG ]]; then
    ./manage.py migrate --noinput
    ./manage.py collectstatic --noinput
    exec ./manage.py runserver 0.0.0.0:${PORT:-8080}
else
    exec python -m uvicorn aquillm.asgi:application --host 0.0.0.0 --port ${PORT:-8080}
fi