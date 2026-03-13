import requests
import structlog
from tenacity import retry, stop_after_attempt, wait_fixed

from deskflow.config import OMNICHAT_API_KEY, OMNICHAT_API_SECRET
from deskflow.contracts.abstract_whatsapp import AbstractWhatsapp
from deskflow.schemas.omnichat import (
    SendButtonMessageSchema,
    SendImageMessageSchema,
    SendTemplateMessageSchema,
)

API_BASE_URL = "https://api.omni.chat/v1"
TIMEOUT = 30  # in seconds

log = structlog.get_logger()


class Whatsapp(AbstractWhatsapp):
    """Send a text message to the given chat_id.
    Args:
        data (SendTextMessageSchema) -- Data containing fields.
    """

    def send_text_message(data):
        chat_id = data.get("chat_id")
        message = data.get("message")

        resp = requests.post(
            f"{API_BASE_URL}/messages",
            json={
                "chatId": chat_id,
                "message": message,
                "type": "TEXT",
                "forceSend": True,
            },
            headers={
                "x-api-key": OMNICHAT_API_KEY,
                "x-api-secret": OMNICHAT_API_SECRET,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
    def send_buttons(data):
        """Send a message using a interactive buttons to the given chat_id.

        Args:
            data (SendButtonMessageSchema)
        """

        SendButtonMessageSchema().load(data)

        chat_id = data.get("chat_id")
        header = data.get("header", "")
        body = data.get("body", None)
        footer = data.get("footer", "")
        buttons = data.get("buttons", None)

        data = {
            "type": "INTERACTIVE_BUTTON",
            "chatId": chat_id,
            "button": {
                "header": header,
                "body": body,
                "footer": footer,
                "buttons": buttons,
            },
            "forceSend": True,
        }

        resp = requests.post(
            f"{API_BASE_URL}/messages",
            json=data,
            headers={
                "x-api-key": OMNICHAT_API_KEY,
                "x-api-secret": OMNICHAT_API_SECRET,
            },
            timeout=TIMEOUT,
        )

        resp.raise_for_status()
        print(resp.json())
        return resp.json()

    def send_image_message(data):
        SendImageMessageSchema().load(data)

        chat_id = data.get("chat_id")
        attachment = data.get("attachment")

        data = {
            "type": "IMAGE",
            "chatId": chat_id,
            "forceSend": True,
            "attachment": attachment,
        }

        resp = requests.post(
            f"{API_BASE_URL}/messages",
            json=data,
            headers={
                "x-api-key": OMNICHAT_API_KEY,
                "x-api-secret": OMNICHAT_API_SECRET,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def send_list_message(data):
        return super().send_list_message()

    def send_template_message(data):
        """Send a message using a template to the given MSISDN.
        Args:
            data (SendTemplateMessageSchema)
        """

        SendTemplateMessageSchema().load(data)

        template_id = data.get("template_id")
        msisdn = data.get("msisdn")
        template_tokens = data.get("template_tokens", [])
        attachment_url = data.get("attachment_url", None)
        type = data.get("type", None)

        data = {
            "templateId": template_id,
            "platformId": msisdn,
            "templateTokens": template_tokens,
            "forceSend": True,
        }

        if type is not None:
            data.update(type=type, attachmentUrl=attachment_url)

        # log.info(f"""Template data sent {data}""")
        resp = requests.post(
            f"{API_BASE_URL}/messages",
            json=data,
            headers={
                "x-api-key": OMNICHAT_API_KEY,
                "x-api-secret": OMNICHAT_API_SECRET,
            },
            timeout=TIMEOUT,
        )
        # log.info(f"Send Template Response: {resp.json()}")
        resp.raise_for_status()

        # Retrieve the chatId
        resp2 = requests.get(
            f"{API_BASE_URL}/messages/{resp.json()['objectId']}",
            headers={
                "x-api-key": OMNICHAT_API_KEY,
                "x-api-secret": OMNICHAT_API_SECRET,
            },
            timeout=TIMEOUT,
        )
        # log.info(f"Get chat template response: {resp2.json()}")
        resp2.raise_for_status()
        return resp2.json()
