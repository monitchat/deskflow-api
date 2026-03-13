from celery import Celery

from danubio_bot.config import RABBITMQ_URL

app = Celery(
    "danubio_bot",
    broker=RABBITMQ_URL,
    include=["danubio_bot.message_worker", "danubio_bot.sender_worker"],
)

app.conf.task_routes = {
    "danubio_bot.message_worker": {"queue": "messages-danubio-bot"},
    "danubio_bot.sender_worker": {"queue": "send-message-danubio-bot"},
}
