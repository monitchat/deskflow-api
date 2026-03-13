from deskflow.client.monitchat.whatsapp import Whatsapp
from deskflow.contracts.abstract_whatsapp import AbstractWhatsapp


class Monitchat:
    def get_whatsapp_client(
        self,
    ) -> AbstractWhatsapp:
        return Whatsapp
