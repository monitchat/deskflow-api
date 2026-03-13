import requests
import structlog

from danubio_bot.config import MONITCHAT_API_ACCESS_TOKEN, MONITCHAT_BASE_URL
from danubio_bot.contracts.abstract_whatsapp import AbstractWhatsapp

log = structlog.get_logger()


class Whatsapp(AbstractWhatsapp):
    def send_text_message(data):
        """Send a text message to the given chat_id.
        Args:
            data (SendTextMessageSchema) -- Data containing fields.
        """
        chat_id = data.get("chat_id")
        message = data.get("message")
        preview_url = data.get("preview_url", False)

        data = {
            "header": {
                "receiver": chat_id,
                "contentType": "text",
                "recipientType": "individual",
                "previewURL": preview_url,
            },
            "content": {"text": message},
        }

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

        data = {
            "header": {
                "receiver": chat_id,
                "contentType": "quickReply",
                "recipientType": "individual",
            },
            "content": {
                "quickReply": {
                    "header": {"text": header} if header else None,
                    "body": {"text": body},
                    "buttons": [{"text": b, "payload": b} for b in buttons],
                    "footer": {"text": footer} if footer else None,
                }
            },
        }

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
