#!/usr/bin/env python3
"""
Script para atualizar chamadas de context em conversation.py para incluir flow_id
"""

import re

file_path = "/home/luiz-ricardo/projects/bot-danubio/src/danubio_bot/conversation.py"

with open(file_path, "r") as f:
    content = f.read()

original_content = content

# As mudanças necessárias:
# 1. No método start(), já temos acesso a flow_id via self.data.get("flow_id") ou self.ctx.data.get("flow_id")
# 2. Precisamos garantir que flow_id esteja disponível em todos os lugares

# Vamos fazer as substituições manualmente para cada caso específico:

# Linha 36-41: handle_ticket_status - precisa receber flow_id do data
content = content.replace(
    """            context.merge(
                msisdn=msisdn,
                data={
                    "stage": AskStartMenuStage.stage,
                },
            )""",
    """            # Pega flow_id do data ou usa o ativo
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
            )"""
)

# Linha 102: merge_context - adiciona flow_id do ctx
content = content.replace(
    """    def merge_context(self, **kwargs):
        self.ctx = context.merge(self.msisdn, kwargs)
        self.reload_context()""",
    """    def merge_context(self, **kwargs):
        flow_id = self.ctx.data.get("flow_id", 1)
        self.ctx = context.merge(self.msisdn, flow_id, kwargs)
        self.reload_context()"""
)

# Linha 110-111: load_context - adiciona flow_id como parâmetro
content = content.replace(
    """    def load_context(self, msisdn):
        return context.load(msisdn)""",
    """    def load_context(self, msisdn, flow_id):
        return context.load(msisdn, flow_id)"""
)

# Linha 116-117: reset_context - adiciona flow_id como parâmetro
content = content.replace(
    """    def reset_context(self, msisdn):
        return context.delete(msisdn)""",
    """    def reset_context(self, msisdn, flow_id):
        return context.delete(msisdn, flow_id)"""
)

# Linha 130-144: context.merge no início do start() - usa flow_id do data
content = content.replace(
    """    def start(self):
        context.merge(
            msisdn=self.msisdn,
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
        )""",
    """    def start(self):
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
        )"""
)

# Linha 179-181: context.get_value para pegar current_flow_id
content = content.replace(
    """                # Verifica se mudou de fluxo
                current_flow_id = context.get_value(
                    msisdn=self.msisdn, property="flow_id"
                )""",
    """                # Verifica se mudou de fluxo
                current_flow_id = context.get_value(
                    msisdn=self.msisdn, flow_id=flow_id, property="flow_id"
                )"""
)

# Linha 190-198: context.merge quando muda de fluxo
content = content.replace(
    """                    start_node = flow_interpreter.get_start_node()
                    context.merge(
                        msisdn=self.msisdn,
                        data={
                            "flow_id": target_flow.id,
                            "stage": start_node,
                            "previous_stage": stage,
                        }
                    )
                    stage = start_node""",
    """                    start_node = flow_interpreter.get_start_node()
                    context.merge(
                        msisdn=self.msisdn,
                        flow_id=target_flow.id,
                        data={
                            "flow_id": target_flow.id,
                            "stage": start_node,
                            "previous_stage": stage,
                        }
                    )
                    stage = start_node"""
)

# Linha 204-208: context.merge para comandos especiais (inicio)
content = content.replace(
    """                elif text in ["inicio", "recomecar", "comeco", "menu inicial"]:
                    stage = flow_interpreter.get_start_node()
                    context.merge(
                        msisdn=self.msisdn,
                        data={"stage": stage}
                    )""",
    """                elif text in ["inicio", "recomecar", "comeco", "menu inicial"]:
                    stage = flow_interpreter.get_start_node()
                    context.merge(
                        msisdn=self.msisdn,
                        flow_id=flow_id,
                        data={"stage": stage}
                    )"""
)

# Linha 210-212: context.get_value para previous_stage (dentro do flow interpreter)
content = content.replace(
    """                elif text in [t.lower() for t in BACK_KEYWORDS]:
                    stage = context.get_value(
                        msisdn=self.msisdn, property="previous_stage"
                    )""",
    """                elif text in [t.lower() for t in BACK_KEYWORDS]:
                    stage = context.get_value(
                        msisdn=self.msisdn, flow_id=flow_id, property="previous_stage"
                    )"""
)

# Linha 263-265: context.get_value para previous_stage (sistema antigo/fallback)
# Aqui precisamos usar self.ctx.data.get("flow_id") já que estamos no fallback
content = content.replace(
    """        elif text in [t.lower() for t in BACK_KEYWORDS]:
            stage = context.get_value(
                msisdn=self.msisdn, property="previous_stage"
            )
            bot = map_stage.get(stage, None)""",
    """        elif text in [t.lower() for t in BACK_KEYWORDS]:
            stage = context.get_value(
                msisdn=self.msisdn, flow_id=flow_id, property="previous_stage"
            )
            bot = map_stage.get(stage, None)"""
)

if content != original_content:
    with open(file_path, "w") as f:
        f.write(content)
    print("✅ conversation.py atualizado com sucesso!")
    print("Total de mudanças:")
    print("  - handle_ticket_status: adicionada lógica para determinar flow_id")
    print("  - merge_context: usa flow_id do ctx")
    print("  - load_context: adicionado parâmetro flow_id")
    print("  - reset_context: adicionado parâmetro flow_id")
    print("  - start(): pega flow_id do data ou ctx")
    print("  - Todas as chamadas context.merge/get_value agora incluem flow_id")
else:
    print("❌ Nenhuma mudança necessária")
