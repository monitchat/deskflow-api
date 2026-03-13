from abc import ABC, abstractmethod


class AbstractWhatsapp(ABC):
    @abstractmethod
    def send_text_message(data: dict):
        raise NotImplementedError

    @abstractmethod
    def send_template_message(data: dict):
        raise NotImplementedError

    @abstractmethod
    def send_list_message(data: dict):
        raise NotImplementedError

    @abstractmethod
    def send_media_message(data: dict):
        raise NotImplementedError

    @abstractmethod
    def send_image_message(data: dict):
        raise NotImplementedError

    @abstractmethod
    def send_button_message(data: dict):
        raise NotImplementedError

    @abstractmethod
    def end_chat(data: dict):
        raise NotImplementedError
