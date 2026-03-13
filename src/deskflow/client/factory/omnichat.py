from deskflow.client.omnichat.whatsapp import Whatsapp
from deskflow.contracts.abstract_broker import AbstractBroker
from deskflow.contracts.abstract_whatsapp import AbstractWhatsapp


class Omnichat(AbstractBroker):
    def get_whatsapp_client(
        self,
    ) -> AbstractWhatsapp:
        return Whatsapp
