import structlog

from deskflow import conversation
from deskflow.celery import app

log = structlog.get_logger()


@app.task(queue="messages-deskflow", ignore_result=True, time_limit=60)
def process_message(data: dict):
    try:
        conversation.handle_message(data=data)
    except:  # noqa E722
        log.exception("Message error")
    return None


@app.task(queue="messages-deskflow", ignore_result=True, time_limit=60)
def process_ticket_status(data: dict):
    try:
        conversation.handle_ticket_status(data=data)
    except:  # noqa E722
        log.exception("Message error")
    return None
