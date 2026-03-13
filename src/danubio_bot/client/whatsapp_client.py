from danubio_bot.contracts.abstract_broker import AbstractBroker


class WhatsappClient:
    _client = None

    def __init__(self, factory: AbstractBroker) -> None:
        self._client = factory.get_whatsapp_client()

    def send_text_message(self, data: dict):
        return self._client.send_text_message(data)

    def send_template_message(self, data: dict):
        return self._client.send_text_message(data)

    def send_list_message(self, data: dict):
        return self._client.send_list_message(data)

    def send_media_message(self, data: dict):
        return self._client.send_media_message(data)

    def send_image_message(self, data: dict):
        return self._client.send_image_message(data)

    def send_button_message(self, data: dict):
        return self._client.send_button_message(data)

    def end_chat(self, data: dict):
        return self._client.end_chat(data)
