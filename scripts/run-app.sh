#!/usr/bin/env bash

CWD=$(dirname "$0")

# Initialize Prometheus environment vars
source "${CWD}"/common/prometheus.sh
initialize_prometheus_env

# Run workers (Celery with RabbitMQ)
celery --app=deskflow worker --concurrency 8 --queues messages-deskflow,send-message-deskflow --prefetch-multiplier 1 --loglevel INFO &
# Run application
exec gunicorn -c deploy/gunicorn.conf.py --timeout 300 "deskflow.app:create_app()" --reload
