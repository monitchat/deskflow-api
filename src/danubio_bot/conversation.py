from string import punctuation

import structlog
from flask import Blueprint
from unidecode import unidecode

from danubio_bot import activity, context
from danubio_bot import settings as config
from danubio_bot.client.factory.monitchat import Monitchat
from danubio_bot.client.whatsapp_client import WhatsappClient
from danubio_bot.config import BACK_KEYWORDS, RESTART_CONVERSATION_KEYWORDS
from danubio_bot.sender_worker import send_message
from danubio_bot.stage import bot_stage
from danubio_bot.stage.bot_stage import AskEndStage, AskStartMenuStage
from danubio_bot.flow_interpreter import get_interpreter_for_msisdn

log = structlog.get_logger()

# Flask blueprint for handling bot API requests
api = Blueprint("conversation", __name__)

settings = config.load()


def handle_ticket_status(data):
    activity.save(data)
    progress = data.get("current_progress", None)

    if progress:
        progress = float(progress)
        if progress >= 100:
            msisdn = data.get("phone_number")
            # Pega flow_id do data ou usa o ativo
            from danubio_bot.models.flow import get_active_flow
            flow_id = data.get("flow_id")
            if not flow_id:
                active_flow = get_active_flow()
                flow_id = active_flow.id if active_flow else 1

            context.merge(
                msisdn=msisdn,
                flow_id=flow_id,
                data={
                    "stage": AskStartMenuStage.stage,
                },
            )


def handle_message(data):
    activity.save(data)

    try:
        msisdn = data.get("phone_number")

        if msisdn is None:
            return True

        # Determina o flow_id (do payload ou flow ativo)
        flow_id_param = data.get("flow_id")
        if flow_id_param:
            flow_id = flow_id_param
        else:
            # Usa flow ativo se não especificado
            from danubio_bot.models.flow import get_active_flow
            active_flow = get_active_flow()
            flow_id = active_flow.id if active_flow else 1  # Default para 1 se não houver ativo

        ctx = context.load(msisdn=msisdn, flow_id=flow_id)
        text = data.get("message")
        content = data.get("content", None)
        mime_type = data.get("mime_type", None)
        file_name = data.get("file_name", None)
        account_number = data.get("account_number", None)
        flow_id = data.get("flow_id", None)  # Opcional: ID do flow a usar

        data = {
            "text": text,
            "account_number": account_number,
            "content": content,
            "file_name": file_name,
            "mime_type": mime_type,
            "auto_reply": data.get("auto_reply"),
            "type": "text",
            "conversation_id": data.get("conversation_id", None),
            "contact_id": data.get("contact_id", None),
            "extra_field_values": data.get("extra_field_values", []),
            "flow_id": flow_id,  # Adiciona flow_id ao data dict
        }

        if data:
            c = Conversation(msisdn=msisdn, ctx=ctx, data=data)
            c.start()
    except Exception as e:
        log.info(e)


class Conversation:
    def __init__(self, msisdn, ctx, data):
        self.msisdn = msisdn
        self.ctx = ctx
        self.data = data

        factory = Monitchat()
        self.broker = WhatsappClient(factory=factory)

    def merge_context(self, **kwargs):
        flow_id = self.ctx.data.get("flow_id", 1)
        self.ctx = context.merge(self.msisdn, flow_id, kwargs)
        self.reload_context()

    def reload_context(self):
        self.stage = self.ctx.data.get("stage")
        self.name = self.ctx.data.get("name")
        self.msisdn = self.ctx.data.get("msisdn", self.msisdn)

    def load_context(self, msisdn, flow_id):
        return context.load(msisdn, flow_id)

    def update_context(self, ctx):
        return context.update(ctx)

    def reset_context(self, msisdn, flow_id):
        return context.delete(msisdn, flow_id)

    def send_did_not_understand(
        self,
    ) -> None:
        self.broker.send_text_message(
            {
                "chat_id": self.msisdn,
                "message": "Ops! Não entendi o que você escreveu. 😶",
            }
        )

    def start(self):
        # Pega flow_id do data ou do contexto
        flow_id = self.data.get("flow_id") or self.ctx.data.get("flow_id", 1)

        context.merge(
            msisdn=self.msisdn,
            flow_id=flow_id,
            data={
                "account_number": self.data.get("account_number"),
                "content": self.data.get("content"),
                "file_name": self.data.get("file_name"),
                "mime_type": self.data.get("mime_type"),
                "last_message_received": self.data,
                "auto_reply": self.data.get("auto_reply"),
                "conversation_id": self.data.get("conversation_id"),
                "contact_id": self.data.get("contact_id", None),
                "extra_field_values": self.data.get("extra_field_values", []),
                "wait_user": False,
            },
        )
        text = unidecode(self.data.get("text", "").strip(punctuation).lower())

        stage = self.ctx.data.get("stage", "ask_start_menu")

        if stage == "bot_waiting_delay":
            return

        if text is None:
            self.send_did_not_understand()
            return

        # Tenta usar interpretador de fluxos visuais primeiro
        from danubio_bot.models.flow import get_active_flow, get_flow_by_id
        from danubio_bot.flow_interpreter import get_interpreter_for_flow_id

        # Se flow_id foi fornecido no payload, usa ele; senão, usa o ativo
        requested_flow_id = self.data.get("flow_id")

        if requested_flow_id:
            # Flow específico foi solicitado
            target_flow = get_flow_by_id(requested_flow_id)
            flow_interpreter = get_interpreter_for_flow_id(requested_flow_id)
            log.info(f"Using requested flow ID: {requested_flow_id}")
        else:
            # Usa o flow ativo (comportamento padrão)
            target_flow = get_active_flow()
            flow_interpreter = get_interpreter_for_msisdn(self.msisdn)
            if target_flow:
                log.info(f"Using active flow ID: {target_flow.id}")

        if flow_interpreter and target_flow:
            # Usa o sistema de fluxos visuais
            try:
                # Verifica se mudou de fluxo
                current_flow_id = context.get_value(
                    msisdn=self.msisdn, flow_id=flow_id, property="flow_id"
                )

                # Mudou de fluxo OU primeira vez usando fluxo visual
                if current_flow_id != target_flow.id:
                    log.info(
                        f"Flow changed from {current_flow_id} to {target_flow.id}, "
                        f"resetting stage to start node"
                    )
                    start_node = flow_interpreter.get_start_node()
                    context.merge(
                        msisdn=self.msisdn,
                        flow_id=target_flow.id,
                        data={
                            "flow_id": target_flow.id,
                            "stage": start_node,
                            "previous_stage": stage,
                        }
                    )
                    stage = start_node

                # Processa comandos especiais
                if text in RESTART_CONVERSATION_KEYWORDS:
                    stage = "end"
                elif text in ["inicio", "recomecar", "comeco", "menu inicial"]:
                    stage = flow_interpreter.get_start_node()
                    context.merge(
                        msisdn=self.msisdn,
                        flow_id=flow_id,
                        data={"stage": stage}
                    )
                elif text in [t.lower() for t in BACK_KEYWORDS]:
                    stage = context.get_value(
                        msisdn=self.msisdn, flow_id=flow_id, property="previous_stage"
                    )

                auto_reply = self.data.get("auto_reply")
                if not auto_reply:
                    return True

                replies = flow_interpreter.execute_node(
                    stage, self.msisdn, text
                )

                for reply in replies:
                    delay = reply.get("delay", None)
                    if delay:
                        send_message.apply_async(
                            args=[reply], countdown=delay
                        )
                    else:
                        log.info(f"reply: {reply}")
                        self.reply(reply=reply)

                return

            except Exception as e:
                log.error(f"Error executing flow interpreter: {e}")
                # Fallback para sistema antigo se houver erro

        # Sistema antigo (fallback)
        # get all bot stage class
        class_list = [
            getattr(bot_stage, class_name)
            for class_name in dir(bot_stage)
            if isinstance(getattr(bot_stage, class_name), type)
        ]

        map_stage = {}
        # map current stage with corresponding class
        # and instantiate it
        for cls in class_list:
            if hasattr(cls, "stage") and (
                stage_cls := getattr(cls, "stage") is not None
            ):
                stage_cls = getattr(cls, "stage")
                map_stage.update({stage_cls: cls()})

        bot = None

        if text in RESTART_CONVERSATION_KEYWORDS:
            bot = AskEndStage()
        elif text in ["inicio", "recomecar", "comeco", "menu inicial"]:
            bot = AskStartMenuStage()
        elif text in [t.lower() for t in BACK_KEYWORDS]:
            stage = context.get_value(
                msisdn=self.msisdn, flow_id=flow_id, property="previous_stage"
            )
            bot = map_stage.get(stage, None)
        else:
            auto_reply = self.data.get("auto_reply")
            if not auto_reply:
                return True

            bot = map_stage.get(stage, None)
        if not bot:
            self.send_did_not_understand()
            return

        try:
            replies = bot.handle_input(self.msisdn, text) or []
            for reply in replies:
                delay = reply.get("delay", None)
                if delay:
                    send_message.apply_async(args=[reply], countdown=delay)
                else:
                    log.info(f"reply: {reply}")
                    self.reply(reply=reply)

        except Exception as e:
            log.info(e)

    def reply(self, reply: dict):
        account_number = self.data.get("account_number")
        reply.update({"account_number": account_number})
        if reply.get("type") == "text":
            self.broker.send_text_message(
                {"chat_id": self.msisdn, "message": reply.get("text"), **reply}
            )
        elif reply.get("type") == "button":
            self.broker.send_button_message(
                {
                    "chat_id": self.msisdn,
                    "message": reply.get("text"),
                    "buttons": reply.get("buttons"),
                    "body": reply.get("body"),
                    "header": reply.get("header", None),
                    "footer": reply.get("footer", None),
                    "account_number": account_number,
                }
            )
        elif reply.get("type") == "list":
            self.broker.send_list_message(
                {
                    "chat_id": self.msisdn,
                    "action": reply.get("action"),
                    "message": reply.get("text"),
                    "body": reply.get("body"),
                    "header": reply.get("header", None),
                    "footer": reply.get("footer", None),
                    "account_number": account_number,
                }
            )
        elif reply.get("type") == "document":
            self.broker.send_media_message(reply)
        elif reply.get("type") == "image":
            self.broker.send_media_message(reply)
        elif reply.get("type") == "end":
            try:
                self.broker.end_chat(
                    {
                        "conversation_id": self.ctx.data.get(
                            "conversation_id"
                        ),
                    }
                )
            except Exception as e:
                activity.save({"exception": e, "type": "error"})
                self.broker.send_text_message(
                    {
                        "chat_id": self.msisdn,
                        "message": "Obrigado por entrar em contato! Foi um prazer atende-lo(a)",
                        **reply,
                    }
                )
