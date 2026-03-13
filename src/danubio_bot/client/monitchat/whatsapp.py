import requests
import structlog

from danubio_bot.config import MONITCHAT_API_ACCESS_TOKEN, MONITCHAT_BASE_URL
from danubio_bot.contracts.abstract_whatsapp import AbstractWhatsapp

log = structlog.get_logger()


class Whatsapp(AbstractWhatsapp):
    def send_text_message(data):
        chat_id = data.get("chat_id")
        message = data.get("message")
        account_number = data.get("account_number")
        data = {
            "token": MONITCHAT_API_ACCESS_TOKEN,
            "message": message,
            "phone_number": chat_id,
            "sent_by_bot": True,
            "account_number": account_number,
            "preview_url": data.get("preview", None),
        }

        resp = requests.post(
            f"""{MONITCHAT_BASE_URL}/message""",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        resp.raise_for_status()
        return resp.json()

    def send_media_message(data):
        chat_id = data.get("chat_id")
        type = data.get("type")
        url = data.get("url")
        file_name = data.get("file_name", None)
        message = data.get("message")
        account_number = data.get("account_number")
        data = {
            "type": type,
            "token": MONITCHAT_API_ACCESS_TOKEN,
            "phone_number": chat_id,
            "account_number": account_number,
            "message": message,
            "sent_by_bot": True,
            "file_name": file_name,
            "url": url,
        }

        resp = requests.post(
            f"""{MONITCHAT_BASE_URL}/media/send""",
            json=data,
            headers={
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def send_button_message(data):
        """Send button message to the given chat_id.
        Args:
            data (SendButtonMessageSchema) -- Data containing fields.
        """
        chat_id = data.get("chat_id")
        header = data.get("header", None)
        buttons = data.get("buttons", [])
        footer = data.get("footer", None)
        body = data.get("body")
        account_number = data.get("account_number")
        data = {
            "type": "buttons",
            "token": MONITCHAT_API_ACCESS_TOKEN,
            "phone_number": chat_id,
            "account_number": account_number,
            "message": body,
            "sent_by_bot": True,
            "footer_text": footer,
            "buttons": buttons,
            "header_text": header,
        }

        resp = requests.post(
            f"""{MONITCHAT_BASE_URL}/message""",
            json=data,
            headers={
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        resp.raise_for_status()
        return resp.json()

    def send_list_message(data):
        """Send list message to the given chat_id.
        Args:
            data (SendButtonMessageSchema) -- Data containing fields.
        """
        chat_id = data.get("chat_id")
        header = data.get("header", None)
        action = data.get("action", None)
        footer = data.get("footer", None)
        body = data.get("body")
        account_number = data.get("account_number")
        data = {
            "type": "list",
            "token": MONITCHAT_API_ACCESS_TOKEN,
            "phone_number": chat_id,
            "account_number": account_number,
            "message": body,
            "sent_by_bot": True,
            "footer_text": footer,
            "action": action,
            "header_text": header,
        }

        resp = requests.post(
            f"""{MONITCHAT_BASE_URL}/message""",
            json=data,
            headers={
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def send_template_message(data):
        """Send a message using a template to the given MSISDN.
        Args:
            dto (WhatsappDto)
        """

        template_id = data.get("template_id")
        chat_id = data.get("chat_id")
        template_values = data.get("template_values", [])

        data = {
            "header": {"receiver": chat_id, "contentType": "notification"},
            "content": {
                "notification": {"name": template_id, "locale": "pt_BR"}
            },
        }

        if len(template_values):
            data.get("content").get("notification").update(
                {
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": value}
                                for value in template_values
                            ],
                        }
                    ]
                }
            )

        resp = requests.post(
            f"""{MONITCHAT_BASE_URL}/send""",
            json=data,
            headers={
                "Authorization": f"""{MONITCHAT_API_ACCESS_TOKEN}""",
                "Content-Type": "application/json",
                "recipientType": "individual",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def end_chat(data):
        conversation_id = data.get("conversation_id")

        data = {
            "token": MONITCHAT_API_ACCESS_TOKEN,
            "conversation_id": conversation_id,
        }

        resp = requests.post(
            f"""{MONITCHAT_BASE_URL}/conversation/{conversation_id}/end-chat""",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
