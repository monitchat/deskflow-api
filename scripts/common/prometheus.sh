initialize_prometheus_env() {
  export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-multiproc-dir
  rm -rf ${PROMETHEUS_MULTIPROC_DIR}
  mkdir -p ${PROMETHEUS_MULTIPROC_DIR}
}
