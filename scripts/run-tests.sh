#!/usr/bin/env bash

# Exit when any command fails
set -e

CWD=$(dirname "$0")

# Initialize Prometheus environment vars
source "${CWD}"/common/prometheus.sh
initialize_prometheus_env

# Run linter
flake8 "${CWD}/../src/"

# Run tests
exec pytest -v --cov=danubio_bot "${CWD}/../tests/"
