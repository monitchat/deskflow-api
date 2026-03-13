import structlog
from flask import Blueprint, request

from deskflow import activity
from deskflow.client.factory.monitchat import Monitchat
from deskflow.client.whatsapp_client import WhatsappClient
from deskflow.message_worker import process_message, process_ticket_status

log = structlog.get_logger()

# Flask blueprint for handling bot API requests
api = Blueprint("conversation", __name__)
factory = Monitchat()
client = WhatsappClient(factory=factory)


@api.route("/api/v1/whatsapp/webhook", methods=["POST"])
def webhook():
    data = request.json or {}

    # Aceita flow_id via query parameter ou body
    # Query parameter tem prioridade sobre body
    flow_id = request.args.get("flow_id", type=int) or data.get("flow_id")

    if flow_id:
        data["flow_id"] = flow_id
        log.info(f"Webhook received with flow_id: {flow_id}")

    # Se flow_id não for fornecido, o sistema usará o flow ativo
    task = process_message.delay(data)

    return {"id": task.task_id}, 200


@api.route("/api/v1/ticket/webhook", methods=["POST"])
def ticket():
    data = request.json or {}

    # Aceita flow_id via query parameter ou body
    # Query parameter tem prioridade sobre body
    flow_id = request.args.get("flow_id", type=int) or data.get("flow_id")

    if flow_id:
        data["flow_id"] = flow_id
        log.info(f"Ticket webhook received with flow_id: {flow_id}")

    # Se flow_id não for fornecido, o sistema usará o flow ativo
    task = process_ticket_status.delay(data)

    return {"id": task.task_id}, 200


@api.route("/api/v1/whatsapp/conversation", methods=["POST"])
def conversation():
    activity.save(request.json)
    data = request.json
    # req = StartConversationSchema().load(request.json)
    client.send_text_message(
        {"chat_id": data.get("chatId"), "message": data.get("text")}
    )

    return "", 200
