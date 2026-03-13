from danubio_bot.client.omnichat.whatsapp import Whatsapp
from danubio_bot.contracts.abstract_broker import AbstractBroker
from danubio_bot.contracts.abstract_whatsapp import AbstractWhatsapp


class Omnichat(AbstractBroker):
    def get_whatsapp_client(
        self,
    ) -> AbstractWhatsapp:
        return Whatsapp
