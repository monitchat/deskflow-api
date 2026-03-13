from deskflow.client.smarters.whatsapp import Whatsapp
from deskflow.contracts.abstract_whatsapp import AbstractWhatsapp


class Smarters:
    def get_whatsapp_client(
        self,
    ) -> AbstractWhatsapp:
        return Whatsapp
