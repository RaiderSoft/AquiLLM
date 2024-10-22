#!/bin/bash

cd ~chandler/aquillm/
source venv/bin/activate
cd aquillm
python3 -m uvicorn aquillm.asgi:application --host 0.0.0.0 --port 443 --ssl-keyfile=/etc/letsencrypt/live/aquillm.space/privkey.pem --ssl-certfile=/etc/letsencrypt/live/aquillm.space/fullchain.pem
