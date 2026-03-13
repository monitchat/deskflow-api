from abc import ABC, abstractmethod

from danubio_bot.contracts.abstract_whatsapp import AbstractWhatsapp


class AbstractBroker(ABC):
    @abstractmethod
    def get_whatsapp_client() -> AbstractWhatsapp:
        raise not NotImplementedError
