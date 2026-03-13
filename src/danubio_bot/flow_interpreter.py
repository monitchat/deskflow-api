"""
Interpretador de fluxos visuais.

Este módulo é responsável por executar fluxos de conversação definidos
visualmente através de um JSON com nós e conexões.

Cada nó representa um stage da state machine, e as conexões (edges)
definem as transições entre stages baseadas em condições.
"""

from string import punctuation
import os
import re

import structlog
from unidecode import unidecode

from danubio_bot import context
from danubio_bot.client import danubio, support
from danubio_bot.common import validate_cpf, validate_cnpj, format_cpf
from danubio_bot.config import (
    RESTART_CONVERSATION_KEYWORDS,
    BACK_KEYWORDS,
    POSITIVE_KEYWORDS,
)

log = structlog.get_logger()


def replace_context_variables(text, msisdn, flow_id, secrets=None):
    """
    Substitui variáveis no formato ${{campo}} pelos valores do contexto.

    Suporta três namespaces:
        ${{campo}} → valor do contexto da conversa
        ${{secret.NOME}} → valor dos segredos do fluxo
        ${{env.NOME}} → variável de ambiente

    Args:
        text: Texto com variáveis no formato ${{campo}}
        msisdn: Número do usuário para buscar contexto
        flow_id: ID do fluxo
        secrets: Dict com segredos do fluxo (opcional)

    Returns:
        Texto com variáveis substituídas pelos valores
    """
    if not text or not isinstance(text, str):
        return text

    # Procura por padrões ${{campo}} ou ${{campo.subcampo}}
    pattern = r'\$\{\{([^}]+)\}\}'

    def replace_match(match):
        field_path = match.group(1).strip()
        # Suporte a segredos do fluxo: ${{secret.NOME}}
        if field_path.startswith("secret."):
            secret_name = field_path[7:]
            if secrets and secret_name in secrets:
                return str(secrets[secret_name])
            return match.group(0)
        # Suporte a variáveis de ambiente: ${{env.NOME}}
        if field_path.startswith("env."):
            env_name = field_path[4:]
            value = os.environ.get(env_name, "")
            return value if value else match.group(0)
        # Normaliza path: results.[0].name → results[0].name
        normalized_path = re.sub(r'\.\[(\d+)\]', r'[\1]', field_path)
        value = context.get_value(
            msisdn=msisdn, flow_id=flow_id, property=normalized_path
        )
        return str(value) if value is not None else match.group(0)

    return re.sub(pattern, replace_match, text)


class FlowInterpreter:
    """Interpretador de fluxos de conversação"""

    def __init__(self, flow_data, flow_id, secrets=None):
        """
        Inicializa o interpretador com os dados do fluxo

        Args:
            flow_data: Dict com a estrutura do fluxo (nodes, edges)
            flow_id: ID do fluxo
            secrets: Dict com segredos do fluxo (opcional)
        """
        self.nodes = {node["id"]: node for node in flow_data.get("nodes", [])}
        self.edges = flow_data.get("edges", [])
        self.flow_id = flow_id
        self.secrets = secrets or {}

    def get_node(self, node_id):
        """Retorna um nó pelo ID"""
        return self.nodes.get(node_id)

    def get_node_edges(self, node_id):
        """Retorna todas as conexões que saem de um nó"""
        return [edge for edge in self.edges if edge["source"] == node_id]

    def get_start_node(self):
        """
        Encontra o nó inicial do fluxo.
        O nó inicial é aquele que não tem nenhuma edge apontando para ele.

        Returns:
            ID do nó inicial ou None se não encontrar
        """
        if not self.nodes:
            return None

        # Se há apenas 1 nó, ele é o inicial
        if len(self.nodes) == 1:
            return list(self.nodes.keys())[0]

        # Encontra nós que são targets de alguma edge
        target_nodes = {edge["target"] for edge in self.edges}

        # O nó inicial é aquele que não é target de nenhuma edge
        start_nodes = [
            node_id for node_id in self.nodes.keys()
            if node_id not in target_nodes
        ]

        # Retorna o primeiro nó inicial encontrado
        return start_nodes[0] if start_nodes else list(self.nodes.keys())[0]

    def execute_node(self, node_id, msisdn, text="", execute_children=True):
        """
        Executa um nó da state machine

        Args:
            node_id: ID do nó a ser executado
            msisdn: Número do usuário
            text: Texto enviado pelo usuário
            execute_children: Se True, executa os nós filhos; se False, apenas executa este nó

        Returns:
            Lista de respostas a serem enviadas
        """
        # Normaliza o texto para comparação com keywords
        normalized_text = unidecode(text.strip(punctuation).lower()) if text else ""

        # Verifica palavras-chave especiais ANTES de executar qualquer nó
        if normalized_text in ["inicio", "recomecar", "comeco", "menu inicial"]:
            print(f"🔄 Keyword detected: '{text}' - restarting flow")
            log.info(f"Keyword '{text}' detected - restarting flow")
            start_node_id = self.get_start_node()
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={"stage": start_node_id, "previous_stage": node_id}
            )
            # Retorna apenas mensagem de confirmação, NÃO executa o nó
            # O nó será executado na próxima mensagem do usuário
            return [{
                "type": "text",
                "text": "Voltando ao início. Digite uma opção para continuar."
            }]

        # Normaliza as keywords de restart também
        normalized_restart_keywords = [
            unidecode(k.strip(punctuation).lower())
            for k in RESTART_CONVERSATION_KEYWORDS
        ]
        if normalized_text in normalized_restart_keywords:
            print(f"🛑 Exit keyword detected: '{text}' - ending conversation")
            log.info(f"Exit keyword '{text}' detected - ending conversation")
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={"stage": None, "previous_stage": node_id}
            )
            return [{
                "type": "text",
                "text": "Conversa encerrada. Digite qualquer coisa para recomeçar."
            }]

        if normalized_text in [t.lower() for t in BACK_KEYWORDS]:
            print(f"⬅️ Back keyword detected: '{text}' - going to previous stage")
            log.info(f"Back keyword '{text}' detected")
            previous_stage = context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="previous_stage")
            if previous_stage:
                context.merge(msisdn=msisdn, flow_id=self.flow_id,
                    data={"stage": previous_stage}
                )
                # Retorna apenas mensagem, NÃO executa o nó
                return [{
                    "type": "text",
                    "text": "Voltando à etapa anterior. Digite uma opção para continuar."
                }]
            else:
                return [{
                    "type": "text",
                    "text": "Não há etapa anterior para voltar."
                }]

        node = self.get_node(node_id)

        # Se o nó não existe, tenta usar o nó inicial do fluxo
        if not node:
            log.warning(f"Node not found: {node_id}, trying to use start node")
            start_node_id = self.get_start_node()

            if start_node_id:
                log.info(f"Using start node: {start_node_id}")
                # Atualiza o contexto para o nó inicial
                context.merge(msisdn=msisdn, flow_id=self.flow_id,
                    data={"stage": start_node_id, "previous_stage": node_id}
                )
                node = self.get_node(start_node_id)
                node_id = start_node_id
            else:
                log.error("No start node found in flow")
                return [{"type": "text", "text": "Erro: fluxo sem nó inicial"}]

        node_type = node.get("type")

        # Mapeia o tipo de nó para o método executor correspondente
        executors = {
            "message": self._execute_message_node,
            "button": self._execute_button_node,
            "list": self._execute_list_node,
            "condition": self._execute_condition_node,
            "router": self._execute_router_node,
            "ai_router": self._execute_ai_router_node,
            "api_call": self._execute_api_call_node,
            "api_request": self._execute_api_request_node,
            "set_context": self._execute_set_context_node,
            "delay": self._execute_delay_node,
            "transfer": self._execute_transfer_node,
            "jump_to": self._execute_jump_to_node,
            "set_ticket_status": self._execute_set_ticket_status_node,
            "media": self._execute_media_node,
            "end": self._execute_end_node,
            "input": self._execute_input_node,
            "ai_agent": self._execute_ai_agent_node,
        }

        executor = executors.get(node_type)

        if not executor:
            log.error(f"Unknown node type: {node_type}")
            return [{"type": "text", "text": "Tipo de nó desconhecido"}]

        return executor(node, msisdn, text, execute_children)

    def _execute_message_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó de mensagem simples"""
        # Se não deve executar filhos, retorna apenas a mensagem
        if not execute_children:
            message = replace_context_variables(node["data"]["message"], msisdn, self.flow_id, self.secrets)
            return [{"type": "text", "text": message}]

        # Verifica se há edges COM condições saindo deste nó
        edges = self.get_node_edges(node["id"])
        has_conditional_edges = any(e.get("data", {}).get("condition") for e in edges)

        # Se há edges com condições, comporta-se como MENU INTERATIVO
        if has_conditional_edges:
            # Se o usuário JÁ digitou algo (não é primeira vez), avalia condições
            if text and text.strip():
                log.info(f"Message node {node['id']} has conditional edges and user provided input - evaluating")
                next_nodes = self._get_next_node(node["id"], msisdn, text)

                if next_nodes:
                    # Atualiza stage para o primeiro nó da lista
                    context.merge(msisdn=msisdn, flow_id=self.flow_id,
                        data={
                            "stage": next_nodes[0],
                            "previous_stage": node["id"],
                            "last_message_sent": node["data"]["message"],
                        },
                    )

                    # NÃO mostra a mensagem novamente, apenas executa os próximos nós
                    # O text já foi consumido pela avaliação das condições, passa text="" para os filhos
                    replies = []
                    if len(next_nodes) > 1:
                        for next_node_id in next_nodes:
                            next_replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                            replies.extend(next_replies)
                    elif len(next_nodes) == 1:
                        next_replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                        replies.extend(next_replies)
                    return replies
                else:
                    # Nenhuma condição atendida - mostra mensagem de erro ou a mensagem original
                    message = replace_context_variables(node["data"]["message"], msisdn, self.flow_id, self.secrets)
                    return [{"type": "text", "text": message}]
            else:
                # Primeira vez - mostra a mensagem e PARA (espera input do usuário)
                log.info(f"Message node {node['id']} has conditional edges - showing message and waiting for input")
                message = replace_context_variables(node["data"]["message"], msisdn, self.flow_id, self.secrets)
                replies = [{"type": "text", "text": message}]

                # Atualiza o stage para este mesmo nó (para processar a resposta depois)
                context.merge(msisdn=msisdn, flow_id=self.flow_id,
                    data={
                        "stage": node["id"],
                        "previous_stage": context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="stage"),
                        "last_message_sent": node["data"]["message"],
                    },
                )
                return replies
        else:
            # Se NÃO há edges com condições, executa RECURSIVAMENTE
            log.info(f"Message node {node['id']} has NO conditional edges - executing recursively")
            message = replace_context_variables(node["data"]["message"], msisdn, self.flow_id, self.secrets)
            replies = [{"type": "text", "text": message}]

            next_nodes = self._get_next_node(node["id"], msisdn, text)

            if next_nodes:
                # Atualiza stage para o primeiro nó da lista
                context.merge(msisdn=msisdn, flow_id=self.flow_id,
                    data={
                        "stage": next_nodes[0],
                        "previous_stage": node["id"],
                        "last_message_sent": node["data"]["message"],
                    },
                )

                # Executa RECURSIVAMENTE os próximos nós SEM passar o text (text="")
                # Nós sem condições são apenas sequenciais, não processam o input anterior
                if len(next_nodes) > 1:
                    # Múltiplos filhos sem condição - executa todos mas SEM seus filhos
                    for next_node_id in next_nodes:
                        next_replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                        replies.extend(next_replies)
                elif len(next_nodes) == 1:
                    # Apenas 1 filho - executa COM seus filhos (recursivo) mas SEM o text
                    next_replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                    replies.extend(next_replies)

            return replies

    def _execute_button_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó de botões"""
        data = node["data"]

        # Converte botões para o formato esperado pelo WhatsApp/Playground
        # Se os botões são strings, converte para objetos com id e title
        raw_buttons = data.get("buttons", [])
        formatted_buttons = []
        for idx, button in enumerate(raw_buttons):
            if isinstance(button, str):
                # Botão simples (string) - converte para objeto
                formatted_buttons.append({
                    "id": str(idx),
                    "title": button
                })
            elif isinstance(button, dict):
                # Botão já é um objeto - mantém como está
                formatted_buttons.append(button)

        # Monta a resposta do botão com suporte a header e footer
        button_reply = {
            "type": "button",
            "body": replace_context_variables(data.get("message", ""), msisdn, self.flow_id, self.secrets),
            "buttons": formatted_buttons,
        }

        # Adiciona header se existir
        if data.get("header"):
            button_reply["header"] = replace_context_variables(data.get("header"), msisdn, self.flow_id, self.secrets)

        # Adiciona footer se existir
        if data.get("footer"):
            button_reply["footer"] = replace_context_variables(data.get("footer"), msisdn, self.flow_id, self.secrets)

        replies = [button_reply]

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            # Atualiza stage para o primeiro nó da lista
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": next_nodes[0],
                    "previous_stage": node["id"],
                    "last_message_sent": data.get("message", ""),
                },
            )

            # Button node PARA aqui - não executa próximos nós
            # Os próximos nós serão executados quando o usuário clicar em um botão

        return replies

    def _execute_list_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó de lista"""
        data = node["data"]
        replies = [
            {
                "type": "list",
                "text": data.get("text", ""),
                "body": data.get("body", ""),
                "footer": data.get("footer", ""),
                "action": data.get("action", {}),
            }
        ]

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            # Atualiza stage para o primeiro nó da lista
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": next_nodes[0],
                    "previous_stage": node["id"],
                    "last_message_sent": data.get("body", ""),
                },
            )

            # List node PARA aqui - não executa próximos nós
            # Os próximos nós serão executados quando o usuário escolher uma opção

        return replies

    def _execute_condition_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó de condição (roteamento baseado em input)"""
        # Este nó não gera resposta, apenas direciona o fluxo

        # Se não deve executar filhos, retorna vazio
        if not execute_children:
            return []

        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            all_replies = []
            # CONDITION processa/avalia o text, então os filhos recebem text=""
            # Se há múltiplos próximos nós (sem condição), executa todos mas SEM seus filhos
            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                    all_replies.extend(replies)
            # Se há apenas 1 próximo nó, executa normalmente (COM seus filhos)
            elif len(next_nodes) == 1:
                replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                all_replies.extend(replies)
            return all_replies

        return []

    def _execute_router_node(self, node, msisdn, text, execute_children=True):
        """
        Executa um nó router inteligente com mensagem de erro.

        Router tem múltiplos handles (saídas), cada um representando uma opção.
        Quando uma opção der match, segue pela edge conectada àquele handle.
        """
        data = node["data"]
        context_key = data.get("context_key", "user_input")
        error_message = data.get(
            "error_message",
            "Opção inválida! Por favor, digite uma das opções válidas."
        )
        options = data.get("options") or []

        # Se não há texto (primeira vez ou chamado recursivamente), apenas PARA e espera
        if not text or not text.strip():
            log.info(f"Router {node['id']}: no text provided - waiting for user input")
            # Atualiza stage para este mesmo nó (para processar resposta depois)
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": node["id"],
                    "previous_stage": context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="stage"),
                },
            )
            return []  # Retorna vazio - não mostra nada, apenas espera

        # Normaliza o texto para comparação
        normalized_text = unidecode(text.strip(punctuation).lower())

        # Salva o input no contexto (opcional)
        if context_key:
            context.merge(msisdn=msisdn, flow_id=self.flow_id, data={context_key: text})

        print(f"\n=== ROUTER DEBUG ===")
        print(f"Router {node['id']}: evaluating {len(options)} options for text='{normalized_text}'")
        log.info(
            f"Router {node['id']}: evaluating {len(options)} options "
            f"for text='{normalized_text}'"
        )

        # Verifica cada opção configurada no router
        for idx, option in enumerate(options):
            condition = option.get("condition", {})
            option_id = option.get("id")
            option_label = option.get("label", "")

            print(f"  Option {idx+1}: label='{option_label}', condition={condition}")

            # Avalia a condição da opção
            match_result = self._evaluate_condition(condition, normalized_text, msisdn)
            print(f"    → Match result: {match_result}")

            if match_result:
                log.info(
                    f"Router {node['id']}: option '{option_label}' matched! "
                    f"Looking for edge with sourceHandle='{option_id}'"
                )

                # Encontra a edge conectada a este handle específico
                matching_edge = next(
                    (
                        edge
                        for edge in self.edges
                        if edge["source"] == node["id"]
                        and edge.get("sourceHandle") == option_id
                    ),
                    None,
                )

                if matching_edge:
                    next_node = matching_edge["target"]
                    log.info(
                        f"Router {node['id']}: following edge to {next_node}"
                    )

                    context.merge(msisdn=msisdn, flow_id=self.flow_id,
                        data={"stage": next_node, "previous_stage": node["id"]},
                    )
                    # ROUTER já avaliou/consumiu o text, passa text="" para os filhos
                    return self.execute_node(next_node, msisdn, text="")
                else:
                    log.warning(
                        f"Router {node['id']}: option matched but no edge "
                        f"connected to handle '{option_id}'"
                    )

        # Nenhuma opção deu match, verificar se tem edge de erro
        error_edge = next(
            (
                edge
                for edge in self.edges
                if edge["source"] == node["id"]
                and edge.get("sourceHandle") == "error"
            ),
            None,
        )

        if error_edge:
            # Tem edge de erro configurada, seguir por ela
            log.info(
                f"Router {node['id']}: no option matched, "
                f"following error edge to {error_edge['target']}"
            )
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": error_edge["target"],
                    "previous_stage": node["id"]
                },
            )
            # ROUTER já avaliou o text, passa text="" para os filhos
            return self.execute_node(error_edge["target"], msisdn, text="")
        else:
            # Sem edge de erro, exibir mensagem e manter no router
            log.warning(
                f"Router {node['id']}: no option matched and no error edge, "
                f"showing error message"
            )
            # NÃO atualiza o stage - usuário permanece no router
            return [{"type": "text", "text": error_message}]

    def _execute_ai_router_node(self, node, msisdn, text, execute_children=True):
        """
        Executa um nó AI Router que usa IA para classificar intenções.

        O AI Router usa um modelo de IA (OpenAI ou Gemini) para analisar
        o input do usuário e identificar qual intenção foi detectada,
        roteando para a saída correspondente.
        """
        import requests as requests_lib
        import json as json_lib

        data = node["data"]
        provider = data.get("ai_provider", "openai")
        api_key = data.get("api_key", "")
        model = data.get("model", "")
        prompt = data.get("prompt", "")
        intents = data.get("intents") or []
        context_key = data.get("context_key", "ai_intent")
        enable_response = data.get("enable_response", False)
        response_prompt = data.get("response_prompt", "")
        error_message = data.get(
            "error_message",
            "Desculpe, não entendi sua mensagem. Pode reformular?"
        )

        # Se não há texto (primeira vez ou chamado recursivamente), apenas PARA e espera
        if not text or not text.strip():
            log.info(f"AI Router {node['id']}: no text provided - waiting for user input")
            # Atualiza stage para este mesmo nó (para processar resposta depois)
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": node["id"],
                    "previous_stage": context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="stage"),
                },
            )
            return []  # Retorna vazio - não mostra nada, apenas espera

        # Validação de configuração
        if not api_key:
            log.error(f"AI Router {node['id']}: API key not configured")
            return [{"type": "text", "text": "Erro: API key não configurada"}]

        # Valida que há intenções OU enable_response ativo
        if (not intents or len(intents) == 0) and not enable_response:
            log.error(f"AI Router {node['id']}: no intents configured and enable_response is False")
            return [{"type": "text", "text": "Erro: Configure intenções ou ative 'Permitir resposta da IA'"}]

        log.info(
            f"AI Router {node['id']}: using {provider} with model {model} "
            f"to analyze text='{text}'"
        )

        # Se não há intenções e enable_response está ativo, pula direto para resposta
        if (not intents or len(intents) == 0) and enable_response:
            log.info(f"AI Router {node['id']}: no intents configured, generating direct response")
            detected_intent = "none"  # Força "none" para ir direto para resposta
        else:
            # Monta o prompt do sistema com as intenções disponíveis
            intents_list = "\n".join([
                f"- {intent['id']}: {intent.get('label', intent['id'])} - {intent.get('description', '')}"
                for intent in intents
            ])

            system_prompt = f"""{prompt}

Intenções disponíveis:
{intents_list}

Analise a mensagem do usuário e identifique APENAS UMA intenção.
Retorne APENAS o ID da intenção no formato JSON: {{"intent": "id_da_intencao"}}
Se nenhuma intenção se aplicar, retorne: {{"intent": "none"}}"""

            try:
                detected_intent = None

                # Chama API do provedor
                if provider == "openai":
                    detected_intent = self._call_openai(
                        api_key, model or "gpt-4o-mini", system_prompt, text
                    )
                elif provider == "gemini":
                    detected_intent = self._call_gemini(
                        api_key, model or "gemini-2.0-flash-exp", system_prompt, text
                    )
                else:
                    log.error(f"AI Router {node['id']}: unsupported provider {provider}")
                    return [{"type": "text", "text": f"Erro: Provedor {provider} não suportado"}]

                log.info(
                    f"AI Router {node['id']}: detected intent = '{detected_intent}'"
                )

                # Salva o intent no contexto (opcional)
                if context_key:
                    context.merge(msisdn=msisdn, flow_id=self.flow_id, data={context_key: detected_intent})
            except Exception as e:
                log.error(f"AI Router {node['id']}: error calling AI API - {str(e)}")
                # Se deu erro na classificação mas tem enable_response, tenta resposta
                if enable_response:
                    detected_intent = "none"
                else:
                    return [{"type": "text", "text": f"Erro ao processar com IA: {str(e)}"}]

        # Se não detectou intenção ou detectou "none", trata como erro OU resposta padrão
        if not detected_intent or detected_intent == "none":
            log.warning(f"AI Router {node['id']}: no intent detected")

            # Se enable_response está ativo, gera uma resposta direta
            if enable_response:
                log.info(f"AI Router {node['id']}: generating default AI response")

                # Usa prompt específico para resposta ou o prompt principal
                ai_response_prompt = response_prompt if response_prompt else prompt

                try:
                    # Gera resposta usando a IA
                    ai_response = None
                    if provider == "openai":
                        ai_response = self._generate_openai_response(
                            api_key, model or "gpt-4o-mini", ai_response_prompt, text
                        )
                    elif provider == "gemini":
                        ai_response = self._generate_gemini_response(
                            api_key, model or "gemini-2.0-flash-exp", ai_response_prompt, text
                        )

                    if ai_response:
                        log.info(f"AI Router {node['id']}: generated response")
                        # Procura edge conectada ao handle 'default'
                        default_edge = next(
                            (
                                edge
                                for edge in self.edges
                                if edge["source"] == node["id"]
                                and edge.get("sourceHandle") == "default"
                            ),
                            None,
                        )

                        # Salva a resposta no contexto
                        context.merge(msisdn=msisdn, flow_id=self.flow_id, data={"ai_response": ai_response})

                        # Envia a resposta e continua no fluxo
                        if default_edge:
                            # Tem próximo nó conectado
                            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                                data={"stage": default_edge["target"], "previous_stage": node["id"]},
                            )
                            # Retorna mensagem da IA e executa próximo nó
                            result = [{"type": "text", "text": ai_response}]
                            result.extend(self.execute_node(default_edge["target"], msisdn, text=""))
                            return result
                        else:
                            # Não tem próximo nó, só retorna a resposta e fica parado
                            return [{"type": "text", "text": ai_response}]
                    else:
                        log.error(f"AI Router {node['id']}: failed to generate response")
                        return [{"type": "text", "text": error_message}]
                except Exception as e:
                    log.error(f"AI Router {node['id']}: error generating response - {str(e)}")
                    return [{"type": "text", "text": error_message}]

            # Se não tem enable_response, segue lógica de erro normal
            # Verifica se tem edge de erro configurada
            error_edge = next(
                (
                    edge
                    for edge in self.edges
                    if edge["source"] == node["id"]
                    and edge.get("sourceHandle") == "error"
                ),
                None,
            )

            if error_edge:
                log.info(
                    f"AI Router {node['id']}: following error edge to {error_edge['target']}"
                )
                context.merge(msisdn=msisdn, flow_id=self.flow_id,
                    data={
                        "stage": error_edge["target"],
                        "previous_stage": node["id"]
                    },
                )
                return self.execute_node(error_edge["target"], msisdn, text="")
            else:
                # Sem edge de erro, exibir mensagem e manter no AI router
                return [{"type": "text", "text": error_message}]

        # Se detectou uma intenção válida, segue para o handle correspondente
        # Encontra a edge conectada ao handle da intenção detectada
        matching_edge = next(
            (
                edge
                for edge in self.edges
                if edge["source"] == node["id"]
                and edge.get("sourceHandle") == detected_intent
            ),
            None,
        )

        if matching_edge:
            next_node = matching_edge["target"]
            log.info(
                f"AI Router {node['id']}: intent '{detected_intent}' matched, "
                f"following edge to {next_node}"
            )

            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={"stage": next_node, "previous_stage": node["id"]},
            )
            return self.execute_node(next_node, msisdn, text="")
        else:
            log.warning(
                f"AI Router {node['id']}: intent '{detected_intent}' detected "
                f"but no edge connected to handle '{detected_intent}'"
            )
            # Trata como erro se não encontrar edge
            return [{"type": "text", "text": error_message}]

    def _call_openai(self, api_key, model, system_prompt, user_message):
        """Chama a API da OpenAI para classificar intenção"""
        import requests as requests_lib
        import json as json_lib

        response = requests_lib.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 50,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse do JSON retornado
        try:
            parsed = json_lib.loads(content)
            return parsed.get("intent")
        except json_lib.JSONDecodeError:
            log.error(f"Failed to parse OpenAI response: {content}")
            return None

    def _call_gemini(self, api_key, model, system_prompt, user_message):
        """Chama a API do Gemini para classificar intenção"""
        import requests as requests_lib
        import json as json_lib

        response = requests_lib.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "contents": [{
                    "parts": [
                        {"text": f"{system_prompt}\n\nMensagem do usuário: {user_message}"}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 50,
                    "responseMimeType": "application/json"
                }
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

        result = response.json()

        # Extrai o texto da resposta do Gemini
        try:
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json_lib.loads(content)
            return parsed.get("intent")
        except (KeyError, IndexError, json_lib.JSONDecodeError) as e:
            log.error(f"Failed to parse Gemini response: {result}")
            return None

    def _generate_openai_response(self, api_key, model, system_prompt, user_message):
        """Gera uma resposta conversacional usando OpenAI"""
        import requests as requests_lib

        response = requests_lib.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _generate_gemini_response(self, api_key, model, system_prompt, user_message):
        """Gera uma resposta conversacional usando Gemini"""
        import requests as requests_lib

        response = requests_lib.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "contents": [{
                    "parts": [
                        {"text": f"{system_prompt}\n\nMensagem do usuário: {user_message}"}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500,
                }
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]

    def _execute_ai_agent_node(self, node, msisdn, text, execute_children=True):
        """
        Executa um nó AI Agent - agente conversacional com suporte a tools.

        O AI Agent usa litellm para suportar múltiplos provedores (OpenAI, Google, Azure)
        e executa tools definidas no fluxo em um loop até gerar uma resposta final.

        Data fields:
            ai_provider: "openai" | "gemini" | "azure"
            api_key: API key do provedor
            azure_api_base: Base URL para Azure (opcional)
            azure_api_version: API version para Azure (opcional)
            model: Nome do modelo
            prompt: System prompt com instruções do agente
            tools: Lista de tools disponíveis para o agente
            max_iterations: Máximo de iterações do loop de tools (default: 10)
            temperature: Temperatura do modelo (default: 0.7)
            max_tokens: Máximo de tokens na resposta (default: 1000)
            context_key: Chave para salvar resposta no contexto
            error_message: Mensagem de fallback em caso de erro
        """
        import json as json_lib

        data = node["data"]
        provider = data.get("ai_provider", "openai")
        api_key = data.get("api_key", "")
        model_name = data.get("model", "")
        prompt = data.get("prompt", "")
        tools_config = data.get("tools") or []

        # Descobre tools conectadas via nós ai_tool
        connected_tools = self._get_connected_tools(node["id"])
        if connected_tools:
            tools_config = tools_config + connected_tools
            log.info(f"AI Agent {node['id']}: found {len(connected_tools)} connected tool nodes")

        max_iterations = int(data.get("max_iterations", 10))
        temperature = float(data.get("temperature", 0.7))
        max_tokens = int(data.get("max_tokens", 1000))
        context_key = data.get("context_key", "ai_agent_response")
        error_message = data.get(
            "error_message",
            "Desculpe, ocorreu um erro ao processar sua mensagem."
        )

        # Substitui variáveis de contexto no prompt
        prompt = replace_context_variables(prompt, msisdn, self.flow_id, self.secrets)

        # Se não há texto, espera input do usuário
        if not text or not text.strip():
            log.info(f"AI Agent {node['id']}: no text - waiting for user input")
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": node["id"],
                    "previous_stage": context.get_value(
                        msisdn=msisdn, flow_id=self.flow_id, property="stage"
                    ),
                },
            )
            return []

        # Validação
        if not api_key:
            log.error(f"AI Agent {node['id']}: API key not configured")
            return [{"type": "text", "text": "Erro: API key não configurada no agente"}]

        log.info(
            f"AI Agent {node['id']}: provider={provider} model={model_name} "
            f"tools={len(tools_config)} text='{text[:50]}'"
        )

        try:
            import litellm

            # Configura o provedor
            litellm_model = self._get_litellm_model(provider, model_name)
            litellm_kwargs = {"api_key": api_key}

            if provider == "azure":
                litellm_kwargs["api_base"] = data.get("azure_api_base", "")
                litellm_kwargs["api_version"] = data.get("azure_api_version", "2024-02-01")

            # Carrega histórico de conversação do contexto
            conversation_history = self._load_agent_history(msisdn)

            # Monta mensagens
            messages = []
            if prompt:
                # Enriquece o prompt com dados do contexto disponíveis
                ctx = context.load(msisdn, self.flow_id)
                if ctx and ctx.data:
                    # Filtra chaves internas
                    ctx_data = {
                        k: v for k, v in ctx.data.items()
                        if not k.startswith("_") and k not in (
                            "stage", "previous_stage", "last_message_sent",
                            "version", "created_at", "playground"
                        ) and v is not None
                    }
                    if ctx_data:
                        import json as json_lib2
                        prompt += (
                            f"\n\nDados disponíveis no contexto da conversa:\n"
                            f"{json_lib2.dumps(ctx_data, ensure_ascii=False, indent=2)}"
                        )
                messages.append({"role": "system", "content": prompt})

            # Adiciona histórico
            messages.extend(conversation_history)

            # Adiciona mensagem atual do usuário
            messages.append({"role": "user", "content": text})

            # Converte tools do flow para formato OpenAI
            openai_tools = self._convert_tools_to_openai_format(tools_config)

            # Loop de execução do agente (tool calling loop)
            for iteration in range(max_iterations):
                log.info(f"AI Agent {node['id']}: iteration {iteration + 1}/{max_iterations}")

                completion_kwargs = {
                    "model": litellm_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **litellm_kwargs,
                }

                if openai_tools:
                    completion_kwargs["tools"] = openai_tools

                response = litellm.completion(**completion_kwargs)
                response_message = response.choices[0].message

                # Adiciona resposta do assistente ao histórico
                messages.append(response_message.model_dump())

                # Se não há tool calls, temos a resposta final
                if not response_message.tool_calls:
                    final_response = response_message.content or ""
                    log.info(f"AI Agent {node['id']}: final response generated")
                    break
                else:
                    # Executa cada tool call
                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json_lib.loads(tool_call.function.arguments)
                        except json_lib.JSONDecodeError:
                            tool_args = {}

                        log.info(
                            f"AI Agent {node['id']}: calling tool '{tool_name}' "
                            f"with args {tool_args}"
                        )

                        # Executa a tool
                        tool_result = self._execute_agent_tool(
                            tool_name, tool_args, tools_config, msisdn
                        )

                        # Adiciona resultado da tool ao histórico
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json_lib.dumps(tool_result, ensure_ascii=False),
                        })
            else:
                # Atingiu máximo de iterações
                log.warning(f"AI Agent {node['id']}: max iterations reached")
                final_response = response_message.content or error_message

            # Salva histórico de conversação atualizado no contexto
            # Mantém apenas as mensagens de user e assistant (sem system)
            history_to_save = [
                m for m in messages
                if (isinstance(m, dict) and m.get("role") in ("user", "assistant"))
                or (hasattr(m, "role") and m.role in ("user", "assistant"))
            ]
            # Limita histórico para não estourar o contexto do banco
            history_to_save = history_to_save[-20:]  # últimas 20 mensagens
            serializable_history = []
            for m in history_to_save:
                if isinstance(m, dict):
                    serializable_history.append({"role": m["role"], "content": m.get("content") or ""})
                else:
                    serializable_history.append({"role": m.role, "content": m.content or ""})

            # Salva no contexto
            context_data = {
                "stage": node["id"],
                "previous_stage": node["id"],
                context_key: final_response,
                "_agent_history": serializable_history,
            }
            context.merge(msisdn=msisdn, flow_id=self.flow_id, data=context_data)

            # Verifica se há edge de saída (quando o agente deve passar para outro nó)
            # Por padrão, o agente fica em loop conversacional no mesmo nó
            # A saída "done" é usada quando o agente decidir encerrar

            return [{"type": "text", "text": final_response}]

        except Exception as e:
            log.error(f"AI Agent {node['id']}: error - {str(e)}", exc_info=True)
            return [{"type": "text", "text": f"{error_message}\n\nDetalhes: {str(e)}"}]

    def _get_litellm_model(self, provider, model_name):
        """Retorna o model string no formato do litellm."""
        defaults = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-2.0-flash",
            "azure": "gpt-4o-mini",
        }
        model = model_name or defaults.get(provider, "gpt-4o-mini")

        if provider == "gemini":
            if not model.startswith("gemini/"):
                return f"gemini/{model}"
        elif provider == "azure":
            if not model.startswith("azure/"):
                return f"azure/{model}"

        return model

    def _load_agent_history(self, msisdn):
        """Carrega histórico de conversação do agente do contexto."""
        history = context.get_value(
            msisdn=msisdn, flow_id=self.flow_id, property="_agent_history"
        )
        if history and isinstance(history, list):
            return history
        return []

    def _convert_tools_to_openai_format(self, tools_config):
        """Converte a configuração de tools do flow para formato OpenAI."""
        if not tools_config:
            return None

        openai_tools = []
        for tool in tools_config:
            tool_type = tool.get("type", "function")

            if tool_type == "http_request":
                # Tool que faz requisição HTTP
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", "http_request"),
                        "description": tool.get("description", "Faz uma requisição HTTP"),
                        "parameters": tool.get("parameters", {
                            "type": "object",
                            "properties": {},
                        }),
                    },
                })
            elif tool_type == "context_lookup":
                # Tool que busca dados do contexto da conversa
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", "get_context"),
                        "description": tool.get(
                            "description",
                            "Busca informações do contexto da conversa"
                        ),
                        "parameters": tool.get("parameters", {
                            "type": "object",
                            "properties": {
                                "key": {
                                    "type": "string",
                                    "description": "A chave do contexto a buscar",
                                }
                            },
                            "required": ["key"],
                        }),
                    },
                })
            elif tool_type == "function":
                # Tool genérica (o schema já vem pronto)
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", "custom_function"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {
                            "type": "object",
                            "properties": {},
                        }),
                    },
                })

        return openai_tools if openai_tools else None

    def _execute_agent_tool(self, tool_name, tool_args, tools_config, msisdn):
        """
        Executa uma tool chamada pelo agente.

        Retorna o resultado como dict/string para ser enviado de volta ao modelo.
        """
        import requests as requests_lib
        import json as json_lib

        # Encontra a configuração da tool
        tool_config = next(
            (t for t in tools_config if t.get("name") == tool_name),
            None,
        )

        if not tool_config:
            return {"error": f"Tool '{tool_name}' not found"}

        tool_type = tool_config.get("type", "function")

        try:
            if tool_type == "http_request":
                # Executa requisição HTTP
                method = tool_config.get("method", "GET").upper()
                url = tool_config.get("url", "")
                headers = tool_config.get("headers", {})

                # Substitui placeholders {param} com args do LLM na URL
                if tool_args and isinstance(tool_args, dict):
                    for param_key, param_value in tool_args.items():
                        url = url.replace(f"{{{param_key}}}", str(param_value))

                # Substitui variáveis de contexto ${{campo}} na URL e headers
                url = replace_context_variables(url, msisdn, self.flow_id, self.secrets)
                for key, value in headers.items():
                    headers[key] = replace_context_variables(
                        value, msisdn, self.flow_id, self.secrets
                    )

                # Mescla args da chamada do LLM com config estática
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "timeout": 30,
                }

                # Remove da query string args que já foram usados na URL
                remaining_args = {
                    k: v for k, v in (tool_args or {}).items()
                    if f"{{{k}}}" not in tool_config.get("url", "")
                }

                if method in ("POST", "PUT", "PATCH"):
                    body = remaining_args or tool_config.get("body", {})
                    request_kwargs["json"] = body
                elif remaining_args:
                    request_kwargs["params"] = remaining_args

                response = requests_lib.request(**request_kwargs)

                try:
                    return response.json()
                except Exception:
                    return {"status_code": response.status_code, "body": response.text[:500]}

            elif tool_type == "context_lookup":
                # Busca valor do contexto
                key = tool_args.get("key", "")
                value = context.get_value(
                    msisdn=msisdn, flow_id=self.flow_id, property=key
                )
                return {"key": key, "value": value}

            elif tool_type == "function":
                # Para tools do tipo function, retorna os args de volta
                # (o comportamento real depende da implementação futura)
                log.info(f"Custom function tool '{tool_name}' called with: {tool_args}")
                return {"status": "executed", "args": tool_args}

            else:
                return {"error": f"Unknown tool type: {tool_type}"}

        except Exception as e:
            log.error(f"Error executing tool '{tool_name}': {str(e)}")
            return {"error": str(e)}

    def _get_connected_tools(self, agent_node_id):
        """
        Descobre nós ai_tool conectados ao agente via edges.
        Retorna lista de configurações de tools no mesmo formato das inline tools.
        """
        connected_tools = []

        # Busca edges que CHEGAM neste agente
        incoming_edges = [
            edge for edge in self.edges
            if edge["target"] == agent_node_id
        ]

        for edge in incoming_edges:
            source_node = self.get_node(edge["source"])
            if source_node and source_node.get("type") == "ai_tool":
                tool_data = source_node.get("data", {})
                tool_config = {
                    "name": tool_data.get("name", f"tool_{source_node['id']}"),
                    "type": tool_data.get("tool_type", "http_request"),
                    "description": tool_data.get("description", ""),
                    "method": tool_data.get("method", "GET"),
                    "url": tool_data.get("url", ""),
                    "headers": tool_data.get("headers", {}),
                    "body": tool_data.get("body", {}),
                    "parameters": tool_data.get("parameters", {
                        "type": "object",
                        "properties": {},
                    }),
                }
                connected_tools.append(tool_config)
                log.info(
                    f"AI Agent: discovered connected tool '{tool_config['name']}' "
                    f"from node {source_node['id']}"
                )

        return connected_tools

    def _execute_input_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que processa input do usuário"""
        data = node["data"]
        input_type = data.get("input_type", "text")
        validation = data.get("validation", {})

        # Se não há texto (primeira vez ou chamado recursivamente), apenas PARA e espera
        if not text or not text.strip():
            log.info(f"Input node {node['id']}: no text provided - waiting for user input")
            # Atualiza stage para este mesmo nó (para processar resposta depois)
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": node["id"],
                    "previous_stage": context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="stage"),
                },
            )
            return []  # Retorna vazio - não mostra nada, apenas espera

        # Valida o input
        is_valid, error_message = self._validate_input(
            text, input_type, validation
        )

        if not is_valid:
            # Retorna mensagem de erro e mantém no mesmo nó
            return [{"type": "text", "text": error_message}]

        # Salva o input no contexto
        context_key = data.get("context_key", "last_input")
        context.merge(msisdn=msisdn, flow_id=self.flow_id, data={context_key: text})

        # Se não deve executar filhos, retorna vazio
        if not execute_children:
            return []

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={"stage": next_nodes[0], "previous_stage": node["id"]},
            )
            all_replies = []
            # Se há múltiplos próximos nós (sem condição), executa todos mas SEM seus filhos
            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                    all_replies.extend(replies)
            # Se há apenas 1 próximo nó, executa normalmente (COM seus filhos)
            elif len(next_nodes) == 1:
                # Repassa o texto original para o próximo nó (útil para ai_agent)
                next_node = self.get_node(next_nodes[0])
                next_text = text if next_node and next_node.get("type") == "ai_agent" else ""
                replies = self.execute_node(next_nodes[0], msisdn, text=next_text, execute_children=True)
                all_replies.extend(replies)
            return all_replies

        return []

    def _execute_api_call_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que faz chamada a API externa"""
        data = node["data"]
        api_type = data.get("api_type")
        label = data.get("label", api_type)
        node_id = node["id"]

        replies = []
        context_data = {}

        log.info(f"🔌 API CALL NODE [{label}] - Type: {api_type}")

        # Executa a chamada de API baseada no tipo
        if api_type == "get_partner":
            # Busca parceiro pelo telefone
            log.info(f"📞 Buscando parceiro por telefone: {msisdn}")
            api_response = danubio.get_partner(phone=msisdn)
            log.info(f"✅ API Response (get_partner): {api_response}")

            partner = api_response.get('responseBody', {}).get('records', {}).get('record', None)

            if partner:
                tipo_parceiro = partner.get('TIPO', {}).get('$')
                codparc = partner.get('CODPARC', {}).get('$')
                nomeparc = partner.get('NOMEPARC', {}).get('$')
                nomectt = partner.get('NOMECTT', {}).get('$')
                cpf = partner.get('CPF', {}).get('$', '')

                log.info(f"👤 Partner found - CODPARC: {codparc}, NOME: {nomeparc}, TIPO: {tipo_parceiro}")

                context_data = {
                    "cpf": cpf,
                    "tipo_contato": tipo_parceiro,
                    "codparc": codparc,
                    "nomeparc": nomeparc,
                    "nomectt": nomectt,
                    "partner": partner,
                    "_raw_api_response": api_response  # Salva resposta completa
                }
            else:
                log.warning(f"⚠️ Partner not found for phone: {msisdn}")
                # Salva resultado mesmo quando não encontra (para debug e schema)
                context_data = {
                    "_raw_api_response": api_response,
                    "_api_status": "not_found"
                }

        elif api_type == "get_customer":
            cpf = context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="cpf")
            codparc = context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="codparc")

            log.info(f"🔍 Buscando cliente - CPF: {cpf}, CODPARC: {codparc}")
            customer_data = danubio.get_client(cpf=cpf, codparc=codparc)
            log.info(f"✅ API Response (get_customer): {customer_data}")

            # Salva no contexto (sempre salva, mesmo se vazio)
            context_data = {
                "customer": customer_data,
                "_raw_api_response": customer_data
            }

        elif api_type == "get_products":
            codparc = context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="codparc")

            log.info(f"📦 Buscando produtos - CODPARC: {codparc}")
            products = danubio.get_products(codigo=codparc)
            log.info(f"✅ API Response (get_products): {products}")

            # Conta quantos produtos foram retornados
            records = products.get('responseBody', {}).get('records', {}).get('record', [])
            product_count = len(records) if isinstance(records, list) else (1 if records else 0)
            log.info(f"📊 Total de produtos encontrados: {product_count}")

            context_data = {
                "customer_orders": products,
                "_raw_api_response": products
            }

        elif api_type == "get_services":
            codparc = context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="codparc")

            log.info(f"🛠️ Buscando serviços - CODPARC: {codparc}")
            services = danubio.get_services(codigo=codparc)
            log.info(f"✅ API Response (get_services): {services}")

            # Conta quantos serviços foram retornados
            records = services.get('responseBody', {}).get('records', {}).get('record', [])
            service_count = len(records) if isinstance(records, list) else (1 if records else 0)
            log.info(f"📊 Total de serviços encontrados: {service_count}")

            context_data = {
                "customer_services": services,
                "_raw_api_response": services
            }

        # Salva os dados no contexto + guarda resultado específico do nó
        if context_data:
            # Salva dados normalmente
            context.merge(msisdn=msisdn, flow_id=self.flow_id, data=context_data)

            # Também salva o resultado específico deste nó para referência futura
            node_result_key = f"_api_result_{node_id}"
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={node_result_key: context_data}
            )
            log.info(f"💾 Saved API result to context key: {node_result_key}")

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={"stage": next_nodes[0], "previous_stage": node["id"]},
            )
            # Executa todos os próximos nós e combina as respostas
            # Se há múltiplos próximos nós (sem condição), executa todos mas SEM seus filhos
            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    next_replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                    if next_replies:
                        replies.extend(next_replies)
            # Se há apenas 1 próximo nó, executa normalmente (COM seus filhos)
            elif len(next_nodes) == 1:
                next_replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                if next_replies:
                    replies.extend(next_replies)

        return replies

    def _execute_api_request_node(self, node, msisdn, text, execute_children=True):
        import json as json_lib
        import requests

        data = node["data"]
        node_id = node["id"]
        label = data.get("label", "API Request")
        method = data.get("method", "GET").upper()
        url = data.get("url", "")
        query_params = data.get("query_params", [])
        headers = data.get("headers", [])
        body = data.get("body", "")
        context_key = data.get("context_key", "api_response")

        log.info(
            f"🌐 API REQUEST NODE [{label}] - Method: {method}, URL: {url}"
        )

        replies = []
        context_data = {}

        try:
            # Substitui variáveis do contexto na URL
            final_url = replace_context_variables(url, msisdn, self.flow_id, self.secrets)
            log.info(f"🔗 URL after variable replacement: {final_url}")

            # Monta query params
            params = {}
            for param in query_params:
                key = param.get("key", "").strip()
                value = param.get("value", "")
                if key:
                    # Substitui variáveis no valor
                    final_value = replace_context_variables(str(value), msisdn, self.flow_id, self.secrets)
                    params[key] = final_value

            if params:
                log.info(f"🔗 Query params: {params}")

            # Monta headers
            request_headers = {}
            for header in headers:
                key = header.get("key", "").strip()
                value = header.get("value", "")
                if key:
                    # Substitui variáveis no valor
                    final_value = replace_context_variables(str(value), msisdn, self.flow_id, self.secrets)
                    request_headers[key] = final_value

            if request_headers:
                log.info(f"📋 Headers: {request_headers}")

            # Monta body (se aplicável)
            request_body = None
            if method in ["POST", "PUT", "PATCH"] and body:
                # Substitui variáveis no body
                body_with_vars = replace_context_variables(body, msisdn, self.flow_id, self.secrets)

                # Tenta fazer parse do JSON
                try:
                    request_body = json_lib.loads(body_with_vars)
                    log.info(f"📦 Body (parsed as JSON): {request_body}")
                except json_lib.JSONDecodeError:
                    # Se não for JSON válido, envia como texto
                    request_body = body_with_vars
                    log.info(f"📦 Body (as text): {request_body}")

            # Faz a requisição
            log.info(
                f"🚀 Making {method} request to: {final_url}"
            )

            response = None
            if method == "GET":
                response = requests.get(
                    final_url,
                    params=params,
                    headers=request_headers,
                    timeout=30
                )
            elif method == "POST":
                response = requests.post(
                    final_url,
                    params=params,
                    headers=request_headers,
                    json=request_body if isinstance(request_body, dict) else None,
                    data=request_body if not isinstance(request_body, dict) else None,
                    timeout=30
                )
            elif method == "PUT":
                response = requests.put(
                    final_url,
                    params=params,
                    headers=request_headers,
                    json=request_body if isinstance(request_body, dict) else None,
                    data=request_body if not isinstance(request_body, dict) else None,
                    timeout=30
                )
            elif method == "DELETE":
                response = requests.delete(
                    final_url,
                    params=params,
                    headers=request_headers,
                    timeout=30
                )
            elif method == "PATCH":
                response = requests.patch(
                    final_url,
                    params=params,
                    headers=request_headers,
                    json=request_body if isinstance(request_body, dict) else None,
                    data=request_body if not isinstance(request_body, dict) else None,
                    timeout=30
                )

            if response:
                log.info(
                    f"✅ API Response - Status: {response.status_code}"
                )

                # Tenta fazer parse da resposta como JSON
                try:
                    response_data = response.json()
                except:
                    # Se não for JSON, salva como texto
                    response_data = {
                        "status_code": response.status_code,
                        "text": response.text,
                        "headers": dict(response.headers)
                    }

                # Salva a resposta no contexto
                context_data = {
                    context_key: response_data,
                    f"{context_key}_status": response.status_code,
                    f"{context_key}_success": 200 <= response.status_code < 300,
                }

                # Salva também resultado específico do nó
                node_result_key = f"_api_result_{node_id}"
                context_data[node_result_key] = {
                    "response": response_data,
                    "status_code": response.status_code,
                    "url": final_url,
                    "method": method,
                }

                log.info(
                    f"💾 Saved API response to context key: {context_key}"
                )

        except requests.exceptions.Timeout:
            log.error(f"⏱️ Request timeout for URL: {final_url}")
            context_data = {
                context_key: {"error": "Request timeout"},
                f"{context_key}_status": 408,
                f"{context_key}_success": False,
            }
        except requests.exceptions.RequestException as e:
            log.error(f"❌ Request error: {str(e)}")
            context_data = {
                context_key: {"error": str(e)},
                f"{context_key}_status": 0,
                f"{context_key}_success": False,
            }
        except Exception as e:
            log.error(f"❌ Unexpected error in API request: {str(e)}")
            context_data = {
                context_key: {"error": str(e)},
                f"{context_key}_status": 0,
                f"{context_key}_success": False,
            }

        # Salva os dados no contexto
        if context_data:
            context.merge(msisdn=msisdn, flow_id=self.flow_id, data=context_data)

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={"stage": next_nodes[0], "previous_stage": node["id"]},
            )
            # Executa todos os próximos nós e combina as respostas
            # Se há múltiplos próximos nós (sem condição), executa todos mas SEM seus filhos
            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    next_replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                    if next_replies:
                        replies.extend(next_replies)
            # Se há apenas 1 próximo nó, executa normalmente (COM seus filhos)
            elif len(next_nodes) == 1:
                next_replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                if next_replies:
                    replies.extend(next_replies)

        return replies

    def _execute_set_context_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que salva valores no contexto"""
        data = node["data"]
        mappings = data.get("mappings", [])
        label = data.get("label", "Set Context")

        log.info(f"💾 SET CONTEXT NODE [{label}] - Mappings: {len(mappings)}")

        context_updates = {}

        for mapping in mappings:
            key = mapping.get("key")
            value = mapping.get("value")
            source = mapping.get("source", "static")

            if not key:
                continue

            # Determina o valor baseado na fonte
            if source == "static":
                # Valor fixo
                final_value = value
            elif source == "context":
                # Busca do contexto
                final_value = context.get_value(msisdn=msisdn, flow_id=self.flow_id, property=value)
            elif source == "input":
                # Último input do usuário
                final_value = context.get_value(msisdn=msisdn, flow_id=self.flow_id, property="last_input")
            else:
                final_value = value

            context_updates[key] = final_value
            log.info(f"  📝 {key} = {final_value} (source: {source})")

        # Salva todos os valores no contexto
        if context_updates:
            context.merge(msisdn=msisdn, flow_id=self.flow_id, data=context_updates)
            log.info(f"✅ Context updated with {len(context_updates)} field(s)")

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={"stage": next_nodes[0], "previous_stage": node["id"]},
            )
            # Executa todos os próximos nós e combina as respostas
            all_replies = []
            # Se há múltiplos próximos nós (sem condição), executa todos mas SEM seus filhos
            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                    all_replies.extend(replies)
            # Se há apenas 1 próximo nó, executa normalmente (COM seus filhos)
            elif len(next_nodes) == 1:
                replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                all_replies.extend(replies)
            return all_replies

        return []

    def _execute_delay_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó de delay - aguarda X segundos antes de continuar"""
        from danubio_bot.sender_worker import execute_delayed_node

        data = node.get("data", {})
        seconds = data.get("seconds", 1)

        # Garante que o delay está entre 1 e 300 segundos
        seconds = max(1, min(300, int(seconds)))

        log.info(f"⏱️ Delay node: waiting {seconds} seconds before continuing")

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            # Atualiza stage para o primeiro nó da lista (para garantir consistência)
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": next_nodes[0],
                    "previous_stage": node["id"],
                },
            )

            # Agenda a execução do próximo nó após o delay
            # IMPORTANTE: Delay SEMPRE agenda, independente de execute_children
            # porque o delay é a função principal do nó, não um efeito colateral
            execute_delayed_node.apply_async(
                kwargs={
                    "msisdn": msisdn,
                    "flow_id": self.flow_id,
                    "node_id": next_nodes[0],
                    "execute_children": True
                },
                countdown=seconds
            )

            log.info(f"⏱️ Scheduled execution of node {next_nodes[0]} in {seconds}s for {msisdn}")

        return []

    def _execute_jump_to_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que pula para outro nó do fluxo"""
        if not execute_children:
            return []

        data = node.get("data", {})
        target_node_id = data.get("target_node_id")

        if not target_node_id:
            log.warning(f"JumpTo node {node['id']} has no target")
            return []

        target_node = self.get_node(target_node_id)
        if not target_node:
            log.error(
                f"JumpTo target node not found: {target_node_id}"
            )
            return [{
                "type": "text",
                "text": "Erro: nó de destino não encontrado",
            }]

        log.info(
            f"JumpTo: {node['id']} → {target_node_id}"
        )

        # Atualiza contexto para o nó de destino
        context.merge(
            msisdn=msisdn,
            flow_id=self.flow_id,
            data={
                "stage": target_node_id,
                "previous_stage": node["id"],
            },
        )

        # Executa o nó de destino
        return self.execute_node(
            target_node_id, msisdn, text="", execute_children=True
        )

    def _execute_transfer_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que transfere para atendimento humano"""
        from danubio_bot.client import support

        # Se não deve executar filhos, retorna vazio
        if not execute_children:
            return []

        data = node.get("data", {})
        department_id = data.get("department_id")

        replies = []
        transfer_success = False
        error_detail = None

        try:
            resp = support.get_current_ticket(chat_id=msisdn)
            ticket = resp.get("ticket", None)

            if not ticket:
                raise Exception("Ticket não encontrado para este atendimento")

            context.merge(msisdn=msisdn, flow_id=self.flow_id, data={**ticket})
            ticket_id = ticket.get("ticket_id")

            support.route_to_department(
                ticket_id=ticket_id,
                department_id=department_id,
                distribute=True,
            )

            transfer_success = True

            message = replace_context_variables(
                data.get(
                    "message",
                    "Estamos transferindo o seu atendimento para um representante.",
                ),
                msisdn,
                self.flow_id,
                self.secrets
            )
            replies.append({"type": "text", "text": message})
            replies.append({
                "type": "transfer_success",
                "node_id": node.get("id"),
                "department_id": department_id,
            })

            log.info(
                f"Transfer successful for {msisdn} to department {department_id}"
            )

        except Exception as e:
            # Extrai detalhes do response da API se disponível
            error_detail = str(e)
            api_response = None
            status_code = None
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    api_response = e.response.json()
                except Exception:
                    api_response = e.response.text

            log.error(
                f"Transfer failed for {msisdn} to department "
                f"{department_id}: {error_detail}",
                status_code=status_code,
                api_response=api_response,
            )
            transfer_success = False

            error_message = replace_context_variables(
                data.get(
                    "error_message",
                    "Não foi possível transferir o atendimento. "
                    "Tente novamente mais tarde.",
                ),
                msisdn,
                self.flow_id,
                self.secrets
            )
            replies.append({"type": "text", "text": error_message})

            # Adiciona detalhes do erro para debug (visível no Playground)
            replies.append({
                "type": "debug",
                "title": "Erro na transferência",
                "error": error_detail,
                "status_code": status_code,
                "api_response": api_response,
                "node_id": node.get("id"),
                "department_id": department_id,
            })

        # Salva resultado da transferência no contexto
        context.merge(
            msisdn=msisdn,
            flow_id=self.flow_id,
            data={
                "transfer_success": transfer_success,
                "transfer_error": error_detail if not transfer_success else None,
                "previous_stage": node["id"],
            },
        )

        # Busca edge pelo sourceHandle (success ou error)
        result_handle = "success" if transfer_success else "error"
        matching_edge = next(
            (
                edge
                for edge in self.edges
                if edge["source"] == node["id"]
                and edge.get("sourceHandle") == result_handle
            ),
            None,
        )

        if matching_edge:
            next_node_id = matching_edge["target"]
            context.merge(
                msisdn=msisdn,
                flow_id=self.flow_id,
                data={"stage": next_node_id},
            )
            node_replies = self.execute_node(
                next_node_id, msisdn, text="", execute_children=True
            )
            replies.extend(node_replies)
        else:
            # Fallback: tenta edges sem sourceHandle (compatibilidade)
            next_nodes = self._get_next_node(node["id"], msisdn, text)
            if next_nodes:
                context.merge(
                    msisdn=msisdn,
                    flow_id=self.flow_id,
                    data={"stage": next_nodes[0]},
                )
                for next_node_id in next_nodes:
                    node_replies = self.execute_node(
                        next_node_id, msisdn, text="", execute_children=True
                    )
                    replies.extend(node_replies)

        return replies

    def _execute_set_ticket_status_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que altera o status do ticket"""
        from danubio_bot.client import support
        import requests
        import os

        # Se não deve executar filhos, retorna vazio
        if not execute_children:
            return []

        data = node.get("data", {})
        status_id = data.get("status_id")

        # Busca o ticket atual
        resp = support.get_current_ticket(chat_id=msisdn)
        ticket = resp.get("ticket", None)

        replies = []

        if ticket and status_id:
            ticket_id = ticket.get("ticket_id")

            # Chama API do MonitChat para alterar status
            try:
                token = os.getenv("MONITCHAT_API_ACCESS_TOKEN")
                monitchat_base_url = os.getenv("MONITCHAT_BASE_URL", "https://api-v2.monitchat.com")

                response = requests.post(
                    f"{monitchat_base_url}/api/v1/ticket/setTicketStatus",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "data": ticket_id,
                        "status": status_id
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    log.info(f"Ticket {ticket_id} status changed to {status_id}")
                else:
                    log.error(f"Error changing ticket status: {response.status_code} - {response.text}")
            except Exception as e:
                log.error(f"Error calling MonitChat API to change status: {str(e)}")

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": next_nodes[0],
                    "previous_stage": node["id"],
                },
            )

            # Executa todos os próximos nós e combina as respostas
            all_replies = []
            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    node_replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                    all_replies.extend(node_replies)
            elif len(next_nodes) == 1:
                node_replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                all_replies.extend(node_replies)

            replies.extend(all_replies)

        return replies

    def _execute_media_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que envia mídia (documento ou imagem)"""
        data = node.get("data", {})
        media_type = data.get("media_type", "document")
        url = replace_context_variables(
            data.get("url", ""), msisdn, self.flow_id, self.secrets
        )
        file_name = replace_context_variables(
            data.get("file_name", ""), msisdn, self.flow_id, self.secrets
        )
        caption = replace_context_variables(
            data.get("caption", ""), msisdn, self.flow_id, self.secrets
        )

        log.info(
            f"📎 MEDIA NODE [{data.get('label', 'Media')}] "
            f"- Type: {media_type}, URL: {url}"
        )

        reply = {"type": media_type, "url": url}
        if file_name:
            reply["file_name"] = file_name
        if caption:
            reply["message"] = caption

        replies = [reply]

        if not execute_children:
            return replies

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)

        if next_nodes:
            context.merge(
                msisdn=msisdn,
                flow_id=self.flow_id,
                data={
                    "stage": next_nodes[0],
                    "previous_stage": node["id"],
                },
            )

            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    next_replies = self.execute_node(
                        next_node_id, msisdn, text="",
                        execute_children=False
                    )
                    replies.extend(next_replies)
            elif len(next_nodes) == 1:
                next_replies = self.execute_node(
                    next_nodes[0], msisdn, text="",
                    execute_children=True
                )
                replies.extend(next_replies)

        return replies

    def _execute_set_context_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó que salva valores no contexto da conversa"""
        # Se não deve executar filhos, retorna vazio
        if not execute_children:
            return []

        data = node.get("data", {})
        context_data = data.get("context_data", {})

        # Salva os valores no contexto
        if context_data:
            # Processa variáveis nos valores antes de salvar
            processed_data = {}
            for key, value in context_data.items():
                if isinstance(value, str):
                    processed_data[key] = replace_context_variables(value, msisdn, self.flow_id, self.secrets)
                else:
                    processed_data[key] = value

            context.merge(msisdn=msisdn, flow_id=self.flow_id, data=processed_data)
            log.info(f"Context updated with data: {processed_data}")

        # Determina os próximos nós
        next_nodes = self._get_next_node(node["id"], msisdn, text)
        replies = []

        if next_nodes:
            context.merge(msisdn=msisdn, flow_id=self.flow_id,
                data={
                    "stage": next_nodes[0],
                    "previous_stage": node["id"],
                },
            )

            # Executa todos os próximos nós e combina as respostas
            all_replies = []
            # Se há múltiplos próximos nós (sem condição), executa todos mas SEM seus filhos
            if len(next_nodes) > 1:
                for next_node_id in next_nodes:
                    node_replies = self.execute_node(next_node_id, msisdn, text="", execute_children=False)
                    all_replies.extend(node_replies)
            # Se há apenas 1 próximo nó, executa normalmente (COM seus filhos)
            elif len(next_nodes) == 1:
                node_replies = self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)
                all_replies.extend(node_replies)

            replies.extend(all_replies)

        return replies

    def _execute_end_node(self, node, msisdn, text, execute_children=True):
        """Executa um nó de finalização"""
        data = node["data"]
        message = data.get("message", "").strip()

        replies = []
        if message:
            replies.append({"type": "text", "text": message})
        replies.append({"type": "end"})

        # Reseta o contexto para o início
        context.merge(msisdn=msisdn, flow_id=self.flow_id,
            data={
                "is_logged_in": False,
                "stage": None,
                "previous_stage": None,
                "last_message_sent": message if message else None,
            },
        )

        return replies

    def _get_next_node(self, current_node_id, msisdn, text):
        """
        Args:
            current_node_id: ID do nó atual
            msisdn: Número do usuário
            text: Texto do usuário

        Returns:
            Lista de IDs dos próximos nós (pode ser vazia, ter 1 ou múltiplos)
        """
        edges = self.get_node_edges(current_node_id)

        if not edges:
            return []

        # Normaliza o texto para comparação
        normalized_text = unidecode(text.strip(punctuation).lower())

        log.info(
            f"_get_next_node: original_text='{text}' | "
            f"normalized_text='{normalized_text}' | "
            f"num_edges={len(edges)}"
        )

        # Separa edges com e sem condição
        conditional_edges = [e for e in edges if e.get("data", {}).get("condition")]
        unconditional_edges = [e for e in edges if not e.get("data", {}).get("condition")]

        # Se há edges com condição, avalia-as primeiro
        if conditional_edges:
            for i, edge in enumerate(edges):
                condition = edge.get("data", {}).get("condition")

                log.info(
                    f"Evaluating edge {i}: {edge['source']} → {edge['target']} | "
                    f"has_condition={condition is not None}"
                )

                if not condition:
                    # Edge sem condição - pula por enquanto
                    continue

                if self._evaluate_condition(
                    condition, normalized_text, msisdn
                ):
                    log.info(f"✅ Edge {i} matched! Going to {edge['target']}")
                    return [edge["target"]]  # Retorna lista com 1 elemento
                else:
                    log.info(f"❌ Edge {i} did not match")

        # Se nenhuma condição foi satisfeita (ou não há condições), usa TODAS as edges sem condição
        if unconditional_edges:
            targets = [e["target"] for e in unconditional_edges]
            log.info(f"🔀 No condition matched or no conditions - executing ALL unconditional edges: {targets}")
            return targets

        return []

    def _evaluate_condition(self, condition, text, msisdn):
        """
        Avalia uma condição

        Args:
            condition: Dict com a condição
            text: Texto normalizado do usuário
            msisdn: Número do usuário

        Returns:
            True se a condição for satisfeita, False caso contrário
        """
        condition_type = condition.get("type")

        if condition_type == "equals":
            # Compara texto exato
            values = condition.get("values", [])
            normalized_values = [
                unidecode(v.strip(punctuation).lower()) for v in values
            ]
            result = text in normalized_values
            print(f"      EQUALS check: text='{text}' | normalized_values={normalized_values} | result={result}")
            log.info(
                f"Condition EQUALS: text='{text}' | "
                f"original_values={values} | "
                f"normalized_values={normalized_values} | "
                f"result={result}"
            )
            return result

        elif condition_type == "contains":
            # Verifica se contém
            values = condition.get("values", [])
            return any(
                unidecode(v.strip(punctuation).lower()) in text
                for v in values
            )

        elif condition_type == "regex":
            # Usa expressão regular
            pattern = condition.get("pattern")
            return bool(re.match(pattern, text))

        elif condition_type == "context":
            # Verifica valor no contexto
            key = condition.get("key")
            expected_value = condition.get("value")
            operator = condition.get("operator", "eq")

            # Se a chave usa sintaxe ${{...}}, resolve a variável
            if key and key.startswith("${{") and key.endswith("}}"):
                resolved = replace_context_variables(
                    key, msisdn, self.flow_id, self.secrets
                )
                actual_value = resolved
                # Se não resolveu (ficou igual), tenta sem ${{}}
                if actual_value == key:
                    actual_value = None
            else:
                actual_value = context.get_value(
                    msisdn=msisdn, flow_id=self.flow_id, property=key
                )

            # Se o valor esperado usa sintaxe ${{...}}, resolve
            if (expected_value and isinstance(expected_value, str)
                    and "${{" in expected_value):
                expected_value = replace_context_variables(
                    expected_value, msisdn, self.flow_id, self.secrets
                )

            log.info(
                f"Condition CONTEXT: key='{key}' | "
                f"operator='{operator}' | "
                f"actual={actual_value} (type={type(actual_value).__name__}) | "
                f"expected={expected_value} (type={type(expected_value).__name__})"
            )

            # Operador "exists": verifica se existe e não é vazio
            if operator == "exists" or expected_value == "exists":
                return actual_value is not None and actual_value != ""

            # Operadores de comparação
            if operator in ("gt", "gte", "lt", "lte"):
                try:
                    actual_num = float(actual_value)
                    expected_num = float(expected_value)
                except (TypeError, ValueError):
                    log.warning(
                        f"Cannot compare non-numeric values: "
                        f"actual={actual_value}, expected={expected_value}"
                    )
                    return False

                if operator == "gt":
                    return actual_num > expected_num
                elif operator == "gte":
                    return actual_num >= expected_num
                elif operator == "lt":
                    return actual_num < expected_num
                elif operator == "lte":
                    return actual_num <= expected_num

            # Operador "neq": diferente
            if operator == "neq":
                if actual_value != expected_value:
                    return str(actual_value) != str(expected_value)
                return False

            # Operador "eq" (padrão): igual com conversão de tipos
            if actual_value == expected_value:
                return True
            return str(actual_value) == str(expected_value)

        elif condition_type == "is_positive":
            # Verifica se é resposta positiva
            return text in [
                unidecode(k.strip(punctuation).lower())
                for k in POSITIVE_KEYWORDS
            ]

        elif condition_type == "is_digit":
            # Verifica se é número
            return text.isdigit()

        return False

    def _validate_input(self, text, input_type, validation):
        """
        Valida o input do usuário

        Args:
            text: Texto do usuário
            input_type: Tipo de input esperado
            validation: Configuração de validação

        Returns:
            Tupla (is_valid, error_message)
        """
        if input_type == "cpf":
            valid, cpf = validate_cpf(cpf=text)
            if not valid:
                return (
                    False,
                    validation.get("error_message", f"CPF ({text}) inválido"),
                )
            return True, None

        elif input_type == "cnpj":
            valid, cnpj = validate_cnpj(cnpj=text)
            if not valid:
                return (
                    False,
                    validation.get("error_message", f"CNPJ ({text}) inválido"),
                )
            return True, None

        elif input_type == "cpf_cnpj":
            # Tenta validar como CPF primeiro (11 dígitos)
            if len(text.replace(".", "").replace("-", "").replace("/", "")) == 11:
                valid, doc = validate_cpf(cpf=text)
                if valid:
                    return True, None
                return (
                    False,
                    validation.get("error_message", f"CPF ({text}) inválido"),
                )
            # Senão, tenta validar como CNPJ (14 dígitos)
            else:
                valid, doc = validate_cnpj(cnpj=text)
                if valid:
                    return True, None
                return (
                    False,
                    validation.get("error_message", f"CNPJ ({text}) inválido"),
                )

        elif input_type == "number":
            if not text.isdigit():
                return (
                    False,
                    validation.get(
                        "error_message", "Por favor, digite apenas números"
                    ),
                )
            return True, None

        elif input_type == "email":
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, text):
                return (
                    False,
                    validation.get(
                        "error_message", "Por favor, digite um email válido"
                    ),
                )
            return True, None

        elif input_type == "regex":
            # Validação customizada usando regex
            pattern = validation.get("pattern", "")
            if not pattern:
                log.warning("Regex validation without pattern - accepting any input")
                return True, None

            try:
                if not re.match(pattern, text):
                    return (
                        False,
                        validation.get(
                            "error_message",
                            f"Formato inválido. O texto deve corresponder ao padrão: {pattern}"
                        ),
                    )
                return True, None
            except re.error as e:
                log.error(f"Invalid regex pattern: {pattern} - Error: {e}")
                return (
                    False,
                    validation.get(
                        "error_message",
                        "Erro na validação. Por favor, tente novamente."
                    ),
                )

        # Tipo text ou outros não validam
        return True, None


def get_interpreter_for_msisdn(msisdn):
    """
    Retorna um interpretador configurado com o fluxo ativo

    Args:
        msisdn: Número do usuário

    Returns:
        FlowInterpreter configurado ou None se não houver fluxo ativo
    """
    from danubio_bot.models import flow as flow_model

    active_flow = flow_model.get_active_flow()

    if not active_flow:
        log.warning("No active flow found")
        return None

    return FlowInterpreter(active_flow.data, active_flow.id, active_flow.secrets)


def get_interpreter_for_flow_id(flow_id):
    """
    Retorna um interpretador configurado com um fluxo específico

    Args:
        flow_id: ID do fluxo

    Returns:
        FlowInterpreter configurado ou None se o fluxo não existir
    """
    from danubio_bot.models import flow as flow_model

    flow = flow_model.get_flow_by_id(flow_id)

    if not flow:
        log.warning(f"Flow with ID {flow_id} not found")
        return None

    return FlowInterpreter(flow.data, flow.id, flow.secrets)
