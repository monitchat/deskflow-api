# import multiprocessing

import gunicorn
from prometheus_flask_exporter.multiprocess import (
    GunicornInternalPrometheusMetrics,
)

# https://stackoverflow.com/questions/16010565/how-to-prevent-gunicorn-from-returning-a-server-http-header
gunicorn.SERVER = ""

# https://docs.gunicorn.org/en/stable/configure.html#configuration-file
bind = "0.0.0.0:5000"
workers = 2


def when_ready(server):
    # Enable mailing loading
    from danubio_bot import conversation_timer

    conversation_timer.start()
    pass


def child_exit(_server, worker):
    GunicornInternalPrometheusMetrics.mark_process_dead_on_child_exit(
        worker.pid
    )
