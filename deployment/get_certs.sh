#!/bin/bash

apt update
apt install python3 python3-venv libaugeas0 -y
python3 -m venv /opt/certbot/
/opt/certbot/bin/pip install certbot 
ln -s /opt/certbot/bin/certbot /usr/bin/certbot
echo "0 0,12 * * * root /opt/certbot/bin/python -c 'import random; import time; time.sleep(random.random() * 3600)' && sudo certbot renew -q" | tee -a /etc/crontab > /dev/null
exec certbot certonly --standalone --non-interactive --agree-tos -m ${WM_EMAIL} -d ${HOST_NAME} --cert-name ${HOST_NAME} --http-01-port=8080 -v
