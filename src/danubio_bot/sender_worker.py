import structlog

from danubio_bot import context
from danubio_bot.celery import app
from danubio_bot.client.factory.monitchat import Monitchat
from danubio_bot.client.whatsapp_client import WhatsappClient
from danubio_bot.stage import bot_stage as stage_class

log = structlog.get_logger()

factory = Monitchat()
broker = WhatsappClient(factory=factory)


@app.task(queue="send-message-danubio-bot", ignore_result=True, time_limit=60)
def execute_delayed_node(msisdn, flow_id, node_id, execute_children=True):
    """
    Executa um nó após um delay.
    Usado pelo componente de delay para agendar a execução de próximos nós.
    """
    try:
        from danubio_bot.models.flow import get_flow_by_id
        from danubio_bot.flow_interpreter import FlowInterpreter

        log.info(f"⏱️ Executing delayed node {node_id} for {msisdn} on flow {flow_id}")

        # Carrega o fluxo
        flow = get_flow_by_id(flow_id)
        if not flow:
            log.error(f"Flow {flow_id} not found")
            return

        # Cria interpretador
        interpreter = FlowInterpreter(flow.data, flow.id, flow.secrets)

        # Executa o nó
        replies = interpreter.execute_node(node_id, msisdn, text="", execute_children=execute_children)

        # Envia as respostas
        log.info(f"⏱️ Processing {len(replies)} replies from delayed node")

        # Armazena mensagens pendentes no contexto para o playground buscar
        ctx = context.load(msisdn=msisdn, flow_id=flow_id)
        pending_messages = ctx.data.get("pending_messages", [])

        # Verifica se é sessão de playground
        # Considera playground se:
        # 1. Tem flag "playground": true no contexto OU
        # 2. msisdn começa com 55119 (padrão gerado pelo playground)
        is_playground_flag = ctx.data.get("playground", False) if ctx else False
        is_playground_msisdn = msisdn.startswith("55119") if msisdn else False
        is_playground = is_playground_flag or is_playground_msisdn

        log.info(f"⏱️ Is playground session: {is_playground} (flag={is_playground_flag}, msisdn_pattern={is_playground_msisdn})")

        # Busca account_number do contexto (número do WhatsApp Business)
        account_number = ctx.data.get("account_number") if ctx else None
        log.info(f"⏱️ Using account_number from context: {account_number}")

        for reply in replies:
            log.info(f"⏱️ Reply: {reply}")
            delay = reply.get("delay", None)
            # Adiciona msisdn, flow_id e account_number ao reply
            reply["msisdn"] = msisdn
            reply["flow_id"] = flow_id
            reply["account_number"] = account_number

            # Adiciona timestamp para o playground saber quando chegou
            import time
            reply["timestamp"] = time.time()

            # Adiciona às mensagens pendentes (para playground)
            pending_messages.append(reply)

            # Se for playground, NÃO envia via WhatsApp
            if is_playground:
                log.info(f"⏱️ Playground session - message stored in pending_messages only, not sending via WhatsApp")
                continue

            # Envia via WhatsApp apenas se NÃO for playground
            if delay:
                log.info(f"⏱️ Scheduling reply with delay {delay}s")
                # Se há outro delay, agenda recursivamente
                send_message.apply_async(args=[reply], countdown=delay)
            else:
                log.info(f"⏱️ Sending reply immediately via send_message task")
                # Envia imediatamente via task para garantir processamento correto
                send_message.apply_async(args=[reply])

        # Salva mensagens pendentes no contexto
        context.merge(msisdn=msisdn, flow_id=flow_id, data={"pending_messages": pending_messages})
        log.info(f"⏱️ Stored {len(replies)} pending messages in context")

        log.info(f"⏱️ Delayed node {node_id} executed successfully, sent {len(replies)} replies")

    except Exception as e:
        log.error(f"⏱️ Error executing delayed node {node_id}: {e}", exc_info=True)


@app.task(queue="send-message-danubio-bot", ignore_result=True, time_limit=60)
def send_message(reply: dict):
    log.info(f"📨 send_message called with reply: {reply}")

    msisdn = reply.get("msisdn")
    log.info(f"📨 msisdn: {msisdn}")

    # Determina flow_id do reply ou usa o flow ativo
    flow_id = reply.get("flow_id")
    if not flow_id:
        from danubio_bot.models.flow import get_active_flow
        active_flow = get_active_flow()
        flow_id = active_flow.id if active_flow else 1

    log.info(f"📨 flow_id: {flow_id}")

    # Tenta carregar contexto, mas se falhar (por transação em andamento), usa valores do reply
    ctx = None
    try:
        ctx = context.load(msisdn=msisdn, flow_id=flow_id)
    except Exception as e:
        log.warning(f"📨 Could not load context (may be transaction conflict): {e}")
        log.info(f"📨 Using values from reply instead")

    stage = reply.get("stage", None)
    wait_stage = reply.get("wait_stage", "")
    bot_stage = ctx.data.get("stage") if ctx else None
    wait_message = reply.get("wait_message", False)

    log.info(f"📨 wait_message: {wait_message}, wait_stage: {wait_stage}, bot_stage: {bot_stage}")

    if wait_message and wait_stage != bot_stage:
        log.info(f"📨 Skipping message - wait condition not met")
        return

    replies = [reply]

    if reply.get("type") == "exec":
        args = reply.get("args", {})
        replies = [
            *getattr(
                stage_class, reply.get("stage_class_name")
            )().handle_input(msisdn=msisdn, **args)
        ]

    if stage:
        context.merge(msisdn=msisdn, flow_id=flow_id, data={"stage": stage})

    log.info(f"📨 Processing {len(replies)} replies")

    for reply in replies:
        reply_type = reply.get("type")
        log.info(f"📨 Processing reply type: {reply_type}")

        if reply_type == "text":
            log.info(f"📨 Sending text message to {msisdn}")
            broker.send_text_message(
                {"chat_id": msisdn, "message": reply.get("text"), **reply}
            )
        elif reply_type == "button":
            log.info(f"📨 Sending button message to {msisdn}")
            button_data = {
                "chat_id": msisdn,
                "message": reply.get("text"),
                "buttons": reply.get("buttons"),
                "body": reply.get("body"),
                "header": reply.get("header", None),
                "footer": reply.get("footer", None),
                "account_number": reply.get("account_number"),
            }
            log.info(f"📨 Button data being sent to broker: {button_data}")
            try:
                response = broker.send_button_message(button_data)
                log.info(f"📨 Monitchat response: {response}")
            except Exception as e:
                log.error(f"📨 Error sending button message: {e}", exc_info=True)
        elif reply.get("type") == "list":
            broker.send_list_message(
                {
                    "chat_id": msisdn,
                    "action": reply.get("action"),
                    "message": reply.get("text"),
                    "body": reply.get("body"),
                    "header": reply.get("header", None),
                    "footer": reply.get("footer", None),
                }
            )
        elif reply.get("type") == "document":
            broker.send_media_message(reply)
        elif reply.get("type") == "image":
            broker.send_media_message(reply)
        elif reply.get("type") == "end":
            try:
                broker.end_chat(
                    {
                        "conversation_id": ctx.data.get("conversation_id"),
                    }
                )

                context.merge(msisdn=msisdn, flow_id=flow_id, data={"wait_user": False})
            except Exception as e:
                print(e)
                broker.send_text_message(
                    {
                        "chat_id": msisdn,
                        "message": "O atendimento {ticket_number} foi finalizado.\nAgradecemos pelo seu contato!",
                        **reply,
                    }
                )
