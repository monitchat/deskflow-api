from abc import ABC, abstractmethod

from deskflow import context, settings


class BotStage(ABC):
    stage = None
    settings = settings.load()

    def get_last_message(self, replies):
        return replies[-1] if len(replies) > 0 else None

    @abstractmethod
    def handle_input(self):
        raise NotImplementedError

    def set_context(self, msisdn: str, data: dict) -> None:
        context.merge(msisdn=msisdn, data=data)

    def get_context_value(self, msisdn: str, property: str) -> str:
        return context.get_value(msisdn=msisdn, property=property)

    def get_context_values(self, msisdn: str, properties: list) -> list:
        return context.get_values(msisdn=msisdn, properties=properties)
