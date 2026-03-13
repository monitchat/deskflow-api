from danubio_bot.client.smarters.whatsapp import Whatsapp
from danubio_bot.contracts.abstract_whatsapp import AbstractWhatsapp


class Smarters:
    def get_whatsapp_client(
        self,
    ) -> AbstractWhatsapp:
        return Whatsapp
