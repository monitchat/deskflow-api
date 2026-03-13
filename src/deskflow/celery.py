from celery import Celery

from deskflow.config import RABBITMQ_URL

app = Celery(
    "deskflow",
    broker=RABBITMQ_URL,
    include=["deskflow.message_worker", "deskflow.sender_worker"],
)

app.conf.task_routes = {
    "deskflow.message_worker": {"queue": "messages-deskflow"},
    "deskflow.sender_worker": {"queue": "send-message-deskflow"},
}
