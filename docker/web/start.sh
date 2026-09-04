#!/bin/sh

set -e

echo "Collecting static files..."

python manage.py collectstatic \
    --noinput

echo "Starting Gunicorn..."

exec gunicorn \
    config.wsgi:application \
    --config /app/gunicorn.conf.py