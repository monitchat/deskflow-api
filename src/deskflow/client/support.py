import requests
import structlog

from deskflow.config import MONITCHAT_API_ACCESS_TOKEN, MONITCHAT_BASE_URL

log = structlog.get_logger()


def get_current_ticket(chat_id: str):
    data = {
        "token": MONITCHAT_API_ACCESS_TOKEN,
    }

    resp = requests.get(
        f"""{MONITCHAT_BASE_URL}/{chat_id}/activeTicket""",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def update_contact(contact_id: str, data: dict):
    data = {"token": MONITCHAT_API_ACCESS_TOKEN, **data}

    resp = requests.put(
        f"""{MONITCHAT_BASE_URL}/bot/contact/{contact_id}""",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    resp.raise_for_status()
    return resp.json()


def upload_base_64_pdf(conversation_id: str, base_64: str):
    data = {"token": MONITCHAT_API_ACCESS_TOKEN, "base64": base_64}

    resp = requests.post(
        f"""{MONITCHAT_BASE_URL}/conversation-file/{conversation_id}""",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    resp.raise_for_status()
    return resp.json()


def route_to_branch(ticket_id: str, branch: str):
    data = {"token": MONITCHAT_API_ACCESS_TOKEN}

    resp = requests.post(
        f"""{MONITCHAT_BASE_URL}/route/ticket/{ticket_id}/branch/{branch}""",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    resp.raise_for_status()
    return resp.json()


def route_to_department(
    ticket_id: str, department_id: str, distribute: bool = False
):
    data = {"token": MONITCHAT_API_ACCESS_TOKEN, "distribute": distribute}

    resp = requests.post(
        f"""{MONITCHAT_BASE_URL}/route/ticket/{ticket_id}/department/{department_id}""",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    resp.raise_for_status()
    return resp.json()
