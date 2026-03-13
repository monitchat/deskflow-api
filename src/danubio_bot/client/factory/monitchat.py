from danubio_bot.client.monitchat.whatsapp import Whatsapp
from danubio_bot.contracts.abstract_whatsapp import AbstractWhatsapp


class Monitchat:
    def get_whatsapp_client(
        self,
    ) -> AbstractWhatsapp:
        return Whatsapp
