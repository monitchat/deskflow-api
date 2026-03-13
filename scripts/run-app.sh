#!/usr/bin/env bash

CWD=$(dirname "$0")

# Initialize Prometheus environment vars
source "${CWD}"/common/prometheus.sh
initialize_prometheus_env

# Run workers (Celery with RabbitMQ)
celery --app=danubio_bot worker --concurrency 8 --queues messages-danubio-bot,send-message-danubio-bot --prefetch-multiplier 1 --loglevel INFO &
# Run application
exec gunicorn -c deploy/gunicorn.conf.py --timeout 300 "danubio_bot.app:create_app()" --reload
