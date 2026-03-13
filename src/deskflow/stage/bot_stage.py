from string import punctuation
from ast import literal_eval

from structlog import get_logger
from unidecode import unidecode

from deskflow.common import validate_cpf, format_cpf
from deskflow.client import support, vipdesk
from deskflow.config import (
    ID_DEPARTAMENTO_CREDIARIO,
    ID_DEPARTAMENTO_ASSISTENCIA_TECNICA,
)
from deskflow.stage.bot_stage_abstract import BotStage
from deskflow.stage.buttons import ASK_YES_NO_BUTTONS, HOW_CAN_WE_HELP_NON_PARTNER_BUTTONS

import json

log = get_logger()

def safe_get_value(data):
    """
    Safely extracts value from data that could be either a dict or JSON string
    """
    if not data:
        return None
    
    log.info(f"data: {data} {type(data)}")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (ValueError, SyntaxError) as e:
            log.info(f"json.loads: {data} {type(data)} {e}")
            try:
                data = literal_eval(data)
            except json.JSONDecodeError:
                log.info(f"literal_eval: {data} {type(data)} {e}")
                return None
    

    if isinstance(data, list):
        return data


    if not isinstance(data, dict):
        log.info(f"data: {data} {type(data)} não é dict")
        return None
        
    log.info(f"data: {data} {type(data)} é dict")
    return data

class AskStartMenuStage(BotStage):
    stage = "ask_start_menu"
    replies = []

    def handle_input(self, msisdn: str, text: str = None) -> list:
        self.replies = []

        is_logged_in = self.get_context_value(msisdn=msisdn, property="is_logged_in")
        if is_logged_in:
            log.info(f"is_logged_in: {is_logged_in} {msisdn}")
            customer = self.get_context_value(msisdn=msisdn, property="customer")
            codparc = self.get_context_value(msisdn=msisdn, property="codparc")
            if customer and codparc:
                return BotSendMenuOptions().handle_input(msisdn=msisdn)
        

            return BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)

        partner = vipdesk.get_partner(phone=msisdn).get('responseBody', {}).get('records', {}).get('record', None)
        log.info(f"------------------------------------------------------------------------partner: {partner}")
        if partner:
            tipo_parceiro = partner.get('TIPO').get('$')
            codparc = partner.get('CODPARC').get('$')
            nomeparc = partner.get('NOMEPARC').get('$')
            nomectt = partner.get('NOMECTT').get('$')
            self.set_context(msisdn=msisdn, data={"cpf": partner.get('CPF').get('$'),  "tipo_contato": tipo_parceiro, "codparc": codparc, "nomeparc": nomeparc, "nomectt": nomectt})
            if tipo_parceiro and tipo_parceiro == "M":
                return BotSendMenuParceiroOptions().handle_input(msisdn=msisdn)
            
        return BotAskIsCustomer().handle_input(msisdn=msisdn)

class BotAskIsMontador(BotStage):
    stage = "ask_is_montador"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        self.replies = [
            {
                "type": "button",
                "body": "É Montador?",
                "buttons": ASK_YES_NO_BUTTONS,
            },
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveIsMontadorStage.stage,
                "previous_stage": BotAskIsMontador.stage,
            },
        )

        return self.replies
    

class BotReceiveIsMontadorStage(BotStage):
    stage = "receive_is_montador_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []
        
        if text in ["1", "um", unidecode(ASK_YES_NO_BUTTONS[0].strip(punctuation).lower())]:
            partner = vipdesk.get_partner(phone=msisdn).get('responseBody', {}).get('records', {}).get('record', None)
            if partner:
                tipo_parceiro = partner.get('TIPO').get('$')
                codparc = partner.get('CODPARC').get('$')
                nomeparc = partner.get('NOMEPARC').get('$')
                nomectt = partner.get('NOMECTT').get('$')
                self.set_context(msisdn=msisdn, data={"cpf": partner.get('CPF').get('$'),  "tipo_contato": tipo_parceiro, "codparc": codparc, "nomeparc": nomeparc, "nomectt": nomectt})
            self.replies = BotSendMenuParceiroOptions().handle_input(msisdn=msisdn)
        else:
            self.replies = BotAskIsCustomer().handle_input(msisdn=msisdn)

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "previous_stage": BotAskIsMontador.stage,
            },
        )

        return self.replies


class BotAskIsCustomer(BotStage):
    stage = "ask_is_customer"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        self.replies = [
            {
                "type": "button",
                "body": "É um prazer receber o seu contato. Já é nosso Cliente?",
                "buttons": ASK_YES_NO_BUTTONS
            },
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveIsCustomerStage.stage,
                "previous_stage": BotAskIsMontador.stage,
            },
        )

        return self.replies


class BotReceiveIsCustomerStage(BotStage):
    stage = "receive_is_customer_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []
        
        if text in ["2", "não", "nao", unidecode(ASK_YES_NO_BUTTONS[1].strip(punctuation).lower())]:
            return BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)


        partner = vipdesk.get_partner(phone=msisdn).get('responseBody', {}).get('records', {}).get('record', None)
        cpf = None
        if partner:
            cpf = partner.get('CPF').get('$',"").strip()
            tipo_parceiro = partner.get('TIPO').get('$')
            codparc = partner.get('CODPARC').get('$')
            nomeparc = partner.get('NOMEPARC').get('$')
            nomectt = partner.get('NOMECTT').get('$')
            self.set_context(msisdn=msisdn, data={"cpf": cpf,  "tipo_contato": tipo_parceiro, "codparc": codparc, "nomeparc": nomeparc, "nomectt": nomectt})

        if cpf:
            self.replies = BotAskCpfClienteStage().handle_input(msisdn=msisdn)
        else:
            self.replies = BotAskCpfNonPartnerStage().handle_input(msisdn=msisdn)


        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "previous_stage": BotAskIsCustomer.stage,
            },
        )

        return self.replies


class BotSendMenuParceiroOptions(BotStage):
    stage = "ask_menu_parceiro_options"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        codparc = self.get_context_value(msisdn=msisdn, property="codparc")
        nomeparc = self.get_context_value(msisdn=msisdn, property="nomeparc")
        nomectt = self.get_context_value(msisdn=msisdn, property="nomectt")

        self.replies = [
            {
                "type": "text",
                "text": f"Parceiro: *{codparc}*, Contato: *{nomectt}*\n\n Certo! Escolha uma das opões abaixo para continuarmos:\n\n1 - Assistência Técnica\n2 - Lojas\n3 - SAC\n\n\nDigite *Sair* Para finalizar o atendimento."
            }
        ]
        
        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveMenuParceiroStage.stage,
                "previous_stage": BotSendMenuParceiroOptions.stage,
            },
        )

        return self.replies


class BotSendMenuOptions(BotStage):
    stage = "ask_menu_options"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        nomeparc = self.get_context_value(msisdn=msisdn, property="nomeparc")
        nomectt = self.get_context_value(msisdn=msisdn, property="nomectt")
        codparc = self.get_context_value(msisdn=msisdn, property="codparc")
        
        self.replies = [
            {
                "type": "text",
                "text": f"Parceiro: *{codparc}*, Contato: *{nomectt}*\n\n*Certo! Escolha uma das opções abaixo para continuarmos:*\n\n1 - Realizar nova compra de produto/serviço\n2 - Minhas compras (Montagem/Entrega)\n3 - Meus serviços de limpeza e outros\n4 - Garantia e Assistência Técnica\n5 - SAC\n\n_Digite *SAIR* para finalizar o atendimento_"
            }
        ]
        
        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveMenuPrincipalStage.stage,
                "previous_stage": BotSendMenuOptions.stage,
            },
        )

        return self.replies

class BotReceiveMenuNonClientStage(BotStage):
    stage = "receive_menu_principal_non_client_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []

        if text.isdigit() is False:
            return [
                {"text": "Informe apenas o *número* correspondente a opção do *menu*", "type": "text"},
                *BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)
            ]
        
        if text in [
            "1",
            "um"
        ]:
            
            return BotSentLojasMenuStage().handle_input(msisdn=msisdn)
        elif text in [
            "2",
            "dois"
        ]:
            return SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=2285)
        else:
            return BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)
    

class BotReceiveMenuParceiroStage(BotStage):
    stage = "receive_menu_parceiro_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []

        if text.isdigit() is False:
            return [
                {"text": "Informe apenas o *número* correspondente a opção do *menu*", "type": "text"},
                *BotSendMenuOptions().handle_input(msisdn=msisdn)
            ]
        
        if text in [
            "2",
            "dois"
        ]:
            
            return BotSentLojasMenuStage().handle_input(msisdn=msisdn)
        elif text in [
            "1",
            "um"
        ]:
            return SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=2134)
        elif text in [
            "3",
            "três",
            "tres",
        ]:
            return SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=2285)
        else:
            return BotSendMenuParceiroOptions().handle_input(msisdn=msisdn)


class BotReceiveMenuPrincipalStage(BotStage):
    stage = "receive_menu_principal_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []

        if text.isdigit() is False:
            return [
                {"text": "Informe apenas o *número* correspondente a opção do *menu*", "type": "text"},
                *BotSendMenuOptions().handle_input(msisdn=msisdn)
            ]
        
        if text in [
            "1",
            "um"
        ]:
            return BotSentLojasMenuStage().handle_input(msisdn=msisdn)
        elif text in [
            "2",
            "dois"
        ]:
            return BotSentProdutosPendenteEntregaStage().handle_input(msisdn=msisdn)
        elif text in [
            "3",
            "tres",
            "três",
            "treis"
        ]:
            return BotSentServicosPendenteStage().handle_input(msisdn=msisdn)
        elif text in [
            "4",
            "quatro"
        ]:
            return BotSentProdutosEntreguesStage().handle_input(msisdn=msisdn)
        elif text in [
            "5",
            "cinco"
        ]:

            nome = self.get_context_value(msisdn=msisdn, property="customer").get("NOMECTT", {}).get("$").split(" ")[0].capitalize()
            self.replies = [
                {
                    "type": "text",
                    "text": f"Olá {nome}. Para agilizar seu atendimento, por favor, me diga em que posso ajudar"
                }
            ]

            return [*SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=2285), *self.replies ]
        else:
            pass

        return self.replies


class BotAskVerificarPendenciaMenu(BotStage):
    stage = "ask_verificar_pendencia_options"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        self.replies = [
            {"type": "text", "text": "*O que você gostaria de fazer?*\n\n1 - Solicitar Alteração de data\n2 - Dúvidas sobre o item selecionado\n3 - Retornar ao menu anterior\n4 - Encerrar atendimento\n\n_Digite o número da opção correpondente_\n\nDigite *SAIR* para finalizar o atendimento ou *voltar* para retornar ao menu anterior"}
        ]
        
        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveMenuPrincipalStage.stage,
                "previous_stage": BotSendMenuOptions.stage,
            },
        )

        return self.replies


class BotSentProdutosPendenteEntregaStage(BotStage):
    stage = "bot_sent_produtos_pendentes_entrega_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):

        # TODO
        # buscar produtos sanhkya
        codparc = self.get_context_value(msisdn=msisdn, property="codparc")
        log.info(f"codparc: {codparc}") 
        customer_orders = vipdesk.get_products(codigo=codparc).get('responseBody', {}).get('records', {}).get('record', None)
        customer_orders = safe_get_value(customer_orders)
        if not customer_orders:
            self.replies = [*BotSendNoProductsPendenteStage().handle_input(msisdn=msisdn)]
            return self.replies

        
        orders = []
        if isinstance(customer_orders, list):
            for order in customer_orders:
                order_data = safe_get_value(order)
                orders.append({
                    "status": order_data.get('STATUS').get('$'),
                    "sequencia": order_data.get('SEQUENCIA').get('$'),
                    "nota": order_data.get('NUNOTA').get('$'),
                    "dtentrega": order_data.get('DTENTREGA').get('$'),
                    "dhemissao": order_data.get('DHEMISSAO').get('$'),
                    "qtdneg": order_data.get('QTDNEG').get('$'),
                    "codprod": order_data.get('CODPROD').get('$'),
                    "descprod": order_data.get('DESCRPROD').get('$'),
                })
        else:
            orders.append({
                "status": customer_orders.get('STATUS').get('$'),
                "sequencia": customer_orders.get('SEQUENCIA').get('$'),
                "nota": customer_orders.get('NUNOTA').get('$'),
                "dtentrega": customer_orders.get('DTENTREGA').get('$'),
                "dhemissao": customer_orders.get('DHEMISSAO').get('$'),
                "qtdneg": customer_orders.get('QTDNEG').get('$'),
                "codprod": customer_orders.get('CODPROD').get('$'),
                "descprod": customer_orders.get('DESCRPROD').get('$'),
            })

        log.info(f"orders raw: {orders}")
        orders.sort(key=lambda x: (x.get('nota'), x.get('sequencia')))
        log.info(f"orders: {orders}")
        grouped_orders = {}
        for order in orders:
            log.info(f"order: {order}")
            nota = order.get('nota')
            if nota not in grouped_orders:
                grouped_orders[nota] = []
            grouped_orders[nota].append(order)

        if len(grouped_orders) <= 0:
            self.replies = [*BotSendNoProductsPendenteStage().handle_input(msisdn=msisdn)]
        
            return self.replies
        

        self.replies = [
            {
                "type": "text",
                "text": "*Aqui estão os produtos pendentes de entrega:*\n" + "\n".join([
                    f"*Nota {nota}*\n" + "\n".join([
                        f"{item.get('sequencia')}. {item.get('descprod')} ({item.get('qtdneg')} un) \nStatus: {item.get('status')}\n- Entrega: {item.get('dtentrega')[:10]}"
                        for item in items
                    ]) + "\n"
                    for nota, items in grouped_orders.items()
                ])
            },
            *BotAskOqueFazerProdutosPendenteStage().handle_input(msisdn=msisdn)
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "customer_orders": customer_orders,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": ReceiveOqueFazerProdutosPendenteStage.stage,
                "previous_stage": BotSentLojasMenuStage.stage,
            },
        )

        return self.replies
    

class BotSentServicosPendenteStage(BotStage):
    stage = "bot_sent_servicos_pendentes_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):

        codparc = self.get_context_value(msisdn=msisdn, property="codparc")
        log.info(f"codparc: {codparc}")
        customer_services = vipdesk.get_services(codigo=codparc).get('responseBody', {}).get('records', {}).get('record', None)
        log.info(f"customer_services: {customer_services}")
        if not customer_services:
            self.replies = [*BotSendNoProductsPendenteStage().handle_input(msisdn=msisdn)]
            return self.replies
        
        services = [{
            "codempnegoc": service.get('CODEMPNEGOC').get('$'),
            "fantabrev": service.get('FANTABREV').get('$'),
            "nfse": service.get('NFSE').get('$'),
            "sequencia": service.get('SEQUENCIA').get('$'),
            "nunota": service.get('NUNOTA').get('$'),
            "seqnfs": service.get('SEQNFS').get('$'),
            "codserv": service.get('CODSERV').get('$'),
            "servico": service.get('SERVICO').get('$'),
            "tpserv": service.get('TPSERV').get('$'),
            "codprod": service.get('CODPROD').get('$'),
            "produto": service.get('DESCRPROD').get('$'),
            "qtdneg": service.get('QTDNEG').get('$'),
            "codtipoper": service.get('CODTIPOPER').get('$'),
            "nomeparc": service.get('NOMEPARC').get('$'),
            "ordemcarga": service.get('ORDEMCARGA').get('$'),
        } for service in customer_services]

        services.sort(key=lambda x: (x.get('nunota'), x.get('sequencia')))

        grouped_services = {}
        for service in services:
            nunota = service.get('nunota')
            if nunota not in grouped_services:
                grouped_services[nunota] = []
            grouped_services[nunota].append(service)

        if len(grouped_services) <= 0:
            self.replies = [*BotSendNoProductsPendenteStage().handle_input(msisdn=msisdn)]
        
            return self.replies
        

        tipos_servicos = {
            "H": "Hidratação",
            "I": "Impermeabilização",
            "L": "Higienização",
            "N": "Nenhum",
        }
        log.info(f"grouped_services: {grouped_services}")
        self.replies = [
            {
                "type": "text",
                "text": "*Aqui estão os serviços contratados:*\n" + "\n".join([
                    f"*NF {nunota}*\n" + "\n".join([
                        f"{item.get('sequencia')} - {tipos_servicos.get(item.get('tpserv'), 'Nenhum')} - {item.get('servico')} ({item.get('qtdneg')} un) \n- Produto: {item.get('produto')}"
                        for item in items
                    ]) + "\n"
                    for nunota, items in grouped_services.items()
                ])
            },
            *BotAskOqueFazerServicosStage().handle_input(msisdn=msisdn)
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "customer_services": customer_services,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": ReceiveOqueFazerProdutosPendenteStage.stage,
                "previous_stage": BotSentLojasMenuStage.stage,
            },
        )

        return self.replies


class ReceivePendenciaEntregaMenu(BotStage):
    stage = "receive_pendencia_entrega_menu_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:

        if text.isdigit() is False:
            return [
                {"text": "Informe apenas o *número* correspondente a opção do *menu*", "type": "text"},
                *BotSentProdutosPendenteEntregaStage().handle_input(msisdn=msisdn)
            ]


        if text == "3":
            return BotSendMenuOptions().handle_input(msisdn=msisdn)
        elif text == "4":
            return AskEndStage().handle_input(msisdn=msisdn)
        
        self.replies = BotSentLojasMenuStage().handle_input(msisdn=msisdn)

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": ReceiveLojaPendenciaEntregaMenu.stage,
                "previous_stage": BotSentProdutosPendenteEntregaStage.stage,
            },
        )

        return self.replies
        

class ReceiveLojaPendenciaEntregaMenu(BotStage):
    stage = "receive_loja_pendencia_entrega_menu_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        
        
        self.replies = SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=ID_DEPARTAMENTO_CREDIARIO)

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": AskEndStage.stage,
                "previous_stage": BotSentProdutosPendenteEntregaStage.stage,
            },
        )

        return self.replies


class BotAskCpfStage(BotStage):
    stage = "ask_cpf"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        self.replies = BotAskCpfNonPartnerStage().handle_input(msisdn=msisdn)

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveCpfNonPartnerStage.stage,
                "previous_stage": BotAskCpfStage.stage,
            },
        )

        return self.replies


class ReceiveNonClientMenuStage(BotStage):
    stage = "receive_non_client_menu_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []

        if text in [
            unidecode(HOW_CAN_WE_HELP_NON_PARTNER_BUTTONS[0].strip(punctuation).lower()),
            "1",
            "um"
        ]:
            return BotSentLojasMenuStage().handle_input(msisdn=msisdn)
        elif text in [
            unidecode(HOW_CAN_WE_HELP_NON_PARTNER_BUTTONS[1].strip(punctuation).lower()),
            "2",
            "dois"
        ]:
            return BotAskCpfClienteStage().handle_input(msisdn=msisdn)
        else:
            pass

        return self.replies


class BotAskCpfClienteStage(BotStage):
    stage = "bot_ask_cpf_cliente_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):

        self.replies = [
            {
                "type": "text",
                "text": "É um prazer receber seu contato. Por gentileza, informe o número do seu CPF.",
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveCpfClienteStage.stage,
                "previous_stage": BotAskCpfClienteStage.stage,
            },
        )

        return self.replies
    
class BotReceiveCpfClienteStage(BotStage):
    stage = "receive_cpf_cliente_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []
        
        valid, cpf = validate_cpf(cpf=text)
        try:
            cpf = format_cpf(text)
        except ValueError:
            return [
                {"type": "text", "text": f"Cpf ({text}) inválido"},
                *BotAskCpfClienteStage().handle_input(msisdn=msisdn)
            ]
        if valid is False:
            return [
                {"type": f"Cpf ({cpf}) inválido"},
                *BotAskCpfClienteStage().handle_input(msisdn=msisdn)
            ]
        
        codparc = self.get_context_value(msisdn=msisdn, property="codparc")
        customers = vipdesk.get_client(cpf=cpf, codparc=codparc).get('responseBody', {})
        log.info(f"customers: {customers}")
        customers = customers.get('records', {})
        customers = customers.get('record', None)
        customer = None
        
        if customers and isinstance(customers, dict):
            customer = customers
        elif customers and len(customers) > 0:
            customer = customers[0]

        if customer is None:
            return BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)
        
        self.replies = [
            *BotSendMenuOptions().handle_input(msisdn=msisdn)
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "customer": customer,
                "is_logged_in": True,
                "cpf": cpf,
                "codparc": customer.get('CODPARC').get('$'),
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveMenuPrincipalStage.stage,
                "previous_stage": BotAskCpfClienteStage.stage,
            },
        )

        return self.replies

class BotAskCpfNonPartnerStage(BotStage):
    stage = "bot_ask_cpf_non_partner_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        log.info("Não é cliente")
        self.replies = [
            {
                "type": "text",
                "text": "É um prazer receber seu contato. Por gentileza, informe o número do seu CPF."
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveCpfNonPartnerStage.stage,
                "previous_stage": BotAskCpfNonPartnerStage.stage,
            },
        )

        return self.replies


class BotSendMenuNonClientOptions(BotStage):
    stage = "ask_menu_non_client"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):
        self.replies = [
            {
                "type": "text",
                "text": "*CPF não encontrado em nosso sistema.*\n\nPor favor, escolha uma das opções abaixo:\n\n1 - Realizar nova compra\n2 - SAC\n\n\nDigite *Sair* Para finalizar o atendimento."
            }
        ]
        
        self.set_context(
            msisdn=msisdn,
            data={
                "is_logged_in": True,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveMenuNonClientStage.stage,
                "previous_stage": BotSendMenuOptions.stage,
            },
        )

        return self.replies


class BotReceiveCpfNonPartnerStage(BotStage):
    stage = "receive_cpf_non_partner_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []
        
        valid, cpf = validate_cpf(cpf=text)
        try:
            cpf = format_cpf(text)
        except ValueError:
            return [
                {"type": "text", "text": f"Cpf ({text}) inválido"},
                *BotAskCpfClienteStage().handle_input(msisdn=msisdn)
            ]

        if valid is False:
            return [
                {"type": f"Cpf ({cpf}) inválido"},
                *BotAskCpfStage().handle_input(msisdn=msisdn)
            ]
        
        # cpf = re.sub(r'\D', '', cpf)
        codparc = self.get_context_value(msisdn=msisdn, property="codparc")
        if not codparc:
            self.set_context(
            msisdn=msisdn,
            data={
                    "cpf": cpf,
                    "is_logged_in": True,
                    "last_message_sent": self.get_last_message(
                        replies=self.replies
                    ),
                    "stage": BotReceiveMenuNonClientStage.stage,
                    "previous_stage": BotAskCpfClienteStage.stage,
                },
            )
                
            return [
                {"type": "text", "text": "Cpf não encontrado em nosso sistema"},
                *BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)
            ]
        data = vipdesk.get_client(cpf=cpf, codparc=codparc).get('responseBody', {})
        data = data.get('records', {})
        data = data.get('record', None)
        customer = None
        
        if data and isinstance(data, dict):
            customer = data
        elif data and len(data) > 0:
            customer = data[0]

        if customer is None:
            return BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)
        
        self.replies = [
            *BotSendMenuNonClientOptions().handle_input(msisdn=msisdn)
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "customer": customer,
                "cpf": cpf,
                "is_logged_in": True,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": BotReceiveMenuNonClientStage.stage,
                "previous_stage": BotAskCpfClienteStage.stage,
            },
        )

        return self.replies

class ReceiveLojaMenuStage(BotStage):
    stage = "receive_loja_menu_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        self.replies = []
        
        map_shop_to_department = {
            "vila velha/portal gloria": 2291,
            "vila velha/centro": 2290,
            "serra/laranjeiras": 2288,
            "cariacica/campo grande": 2289,
            "cachoeiro de itapemirim": 2292,
            "vitoria/goiabeiras": 2287
        }

        department_id = map_shop_to_department.get(text)

        if department_id:
            return SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=department_id)
        else:
            return BotSentLojasMenuStage().handle_input(msisdn=msisdn)


class BotSentLojasMenuStage(BotStage):
    stage = "bot_sent_lojas_menu_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = ""):

        self.replies = [
            {
                "type": "text",
                "text": "Certo! Para melhor atende-lo, escolha uma das nossas lojas mais próxima da sua localidade.",
            },
            {
                    "type": "list",
                    "text": "Escolha uma de nossas lojas",
                    "body": "Escolha uma de nossas lojas",
                    "footer": "_Digite sair para encerrar o atendimento_",
                    "action": {
                        "button": "Ver Lojas",
                        "sections": [
                            {
                                "title": "Ver Lojas",
                                "rows": [
                                    {
                                        "id": "Goiabeiras",
                                        "title": "Vitória/Goiabeiras",
                                        "description": "",
                                    },
                                    {
                                        "id": "Laranjeiras",
                                        "title": "Serra/Laranjeiras",
                                        "description": "",
                                    },
                                    {
                                        "id": "Campo Grande",
                                        "title": "Cariacica/Campo Grande",
                                        "description": "",
                                    },
                                    {
                                        "id": "Vila Velha",
                                        "title": "Vila Velha/Centro",
                                        "description": "",
                                    },
                                    {
                                        "id": "Glória",
                                        "title": "Vila Velha/Portal Glória",
                                        "description": "",
                                    },
                                    {
                                        "id": "Cachoeiro de Itapemirim",
                                        "title": "Cachoeiro de Itapemirim",
                                        "description": "",
                                    }
                                ],
                            }
                        ],
                    },
                }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": ReceiveLojaMenuStage.stage,
                "previous_stage": BotSentLojasMenuStage.stage,
            },
        )

        return self.replies


class SendToDepartmentStage(BotStage):
    stage = "send_to_department"
    replies = []

    def handle_input(self, msisdn: str, department_id: int, text: str = ""):
        resp = support.get_current_ticket(chat_id=msisdn)
        log.info(f"Resp: {resp}")
        ticket = resp.get("ticket", None)

        if ticket:
            self.set_context(msisdn=msisdn, data={**ticket})
            ticket_id = ticket.get("ticket_id")

            support.route_to_department(
                ticket_id=ticket_id,
                department_id=department_id,
                distribute=True,
            )

            self.replies = [
                {
                    "type": "text",
                    "text": "Olá, {contact_name}.\nEstamos transferindo o seu atendimento para um representante.",
                }
            ]

        self.set_context(
            msisdn=msisdn,
            data={
                "is_logged_in": False,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "stage": AskEndStage.stage,
                "previous_stage": AskStartMenuStage.stage,
            },
        )

        return self.replies


class AskEndStage(BotStage):
    stage = "ask_end"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        self.replies = []

        self.replies.append({"type": "end"})
        self.replies.append({
            "type": "text",
            "text": "A Client agradece o seu contato. Precisando, estamos à disposição!"
        })

        self.set_context(
            msisdn=msisdn,
            data={
                "is_logged_in": False,
                "stage": AskStartMenuStage.stage,
                "previous_stage": AskStartMenuStage.stage,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
            },
        )

        return self.replies


class ReceiveNeedMoreHelpStage(BotStage):
    stage = "receive_need_more_help_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = None) -> list:

        self.replies = []

        if text in [
            unidecode(ASK_YES_NO_BUTTONS[0].strip(punctuation).lower()),
            "sim",
            "yes",
            "si",
        ]:
            self.replies = [*AskStartMenuStage().handle_input(msisdn=msisdn)]
        elif text in [
            unidecode(ASK_YES_NO_BUTTONS[1].strip(punctuation).lower()),
            "não",
            "nao",
            "no",
        ]:
            self.replies = [*AskEndStage().handle_input(msisdn=msisdn)]

        return self.replies


class AskNeedMoreHelpStage(BotStage):
    stage = "ask_need_more_help_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        self.replies = []

        self.replies = [
            {
                "type": "button",
                "body": "Ajudo em algo mais?",
                "buttons": ASK_YES_NO_BUTTONS,
            },
            {
                "type": "exec",
                "msisdn": msisdn,
                "wait_stage": AskNeedMoreHelpStage.stage,
                "delay": 60,
                "stage_class_name": AskEndStage.__name__,
            },
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "stage": ReceiveNeedMoreHelpStage.stage,
                "previous_stage": AskNeedMoreHelpStage.stage,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
            },
        )

        return self.replies


class BotSendNoProductsPendenteStage(BotStage):
    stage = "bot_send_no_products_pendente_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        self.replies = [
            {
                "type": "text",
                "text": "*Não foi encontrado nenhum produto/serviço pendente vinculado aos dados informados.*"
            },
            {
                "type": "button",
                "body": "Ajudo em algo mais?",
                "buttons": ASK_YES_NO_BUTTONS,
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "stage": ReceiveNeedMoreHelpStage.stage,
                "previous_stage": BotSendNoProductsPendenteStage.stage,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
            },
        )

        return self.replies


class BotAskOqueFazerProdutosPendenteStage(BotStage):
    stage = "bot_ask_o_que_fazer_produtos_pendente_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        self.replies = [
            {
                "type": "text",
                "text": "*Escolha uma opção:*\n\n1 - Solicitar Alteração de data\n2 - Dúvidas sobre o(s) produto(s)\n3 - Falar com atendente\n\nDigite *SAIR* para finalizar o atendimento ou *voltar* para retornar ao menu anterior"
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "stage": ReceiveOqueFazerProdutosPendenteStage.stage,
                "previous_stage": self.stage,
                "last_message_sent": self.get_last_message(replies=self.replies),
            },
        )

        return self.replies


class ReceiveOqueFazerProdutosPendenteStage(BotStage):
    stage = "receive_o_que_fazer_produtos_pendente_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        if text in ["1", "2"]:
            self.replies = [
                {
                    "type": "text",
                    "text": "Certo. Vamos encaminhar para o atendimento, mas antes, nos conte por favor:"
                },
                {
                    "type": "button",
                    "body": "Você gostaria de receber atualizações sobre a sua entrega?",
                    "buttons": ["Sim", "Não"],
                }
            ]

            self.set_context(
                msisdn=msisdn,
                data={
                    "stage": ReceiveReceberAtualizacoesEntregaStage.stage,
                    "previous_stage": self.stage,
                    "last_message_sent": self.get_last_message(replies=self.replies),
                },
            )

            return self.replies            
        elif text == "3":
            return BotSentLojasEntregaMenuStage().handle_input(msisdn=msisdn)
        elif text == "4":
            return BotSendMenuOptions().handle_input(msisdn=msisdn)
        else:
            return BotAskOqueFazerProdutosPendenteStage().handle_input(msisdn=msisdn)


class ReceiveReceberAtualizacoesEntregaStage(BotStage):
    stage = "receive_receber_atualizacoes_entrega_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        if text.lower() in ["sim", "yes", "si"]:
            codparc = self.get_context_value(msisdn=msisdn, property="codparc")
            resp = vipdesk.update_parceiro(codparc=codparc, alert="S")
            log.info(f"Atualização de parceiro: {resp}")
            self.set_context(msisdn=msisdn, data={"receber_atualizacoes": True})
        else:
            resp = vipdesk.update_parceiro(codparc=codparc, alert="N")
            log.info(f"Atualização de parceiro: {resp}")
            self.set_context(msisdn=msisdn, data={"receber_atualizacoes": False})

            return BotSentLojasEntregaMenuStage().handle_input(msisdn=msisdn)
        
        values = self.get_context_value(msisdn=msisdn, property="customer")

        email = values.get("EMAILCTT", {}).get("$")
        phone = values.get("TELEFONE", {}).get("$")
        name = values.get("NOMECTT", {}).get("$")
        address = values.get("ENDERECO", {}).get("$")

        self.replies = [
            {
                "type": "text",
                "text": "Obrigado pela confirmação! A partir de agora, vocẽ receberá atualizações sobre a sua compra."
            },
            {
                "type": "text",
                "text": f"Confira se seus dados abaixo estão corretos e, caso contrário, gentileza reforçar com seu atendimento a seguir para corrigir no sistema:\n\nNome Completo: {name} \nEndereço Completo: {address} \nE-mail: {email} \nTelefone: {phone}"
            },
            {
                "type": "button",
                "body": "Você confirma seus dados?",
                "buttons": ["Sim", "Não"],
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "stage": ReceiveConfirmarDadosEntregaStage.stage,
                "previous_stage": self.stage,
                "last_message_sent": self.get_last_message(replies=self.replies),
            },
        )

        return self.replies

class ReceiveConfirmarDadosEntregaStage(BotStage):
    stage = "receive_confirmar_dados_entrega_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        return BotSentLojasEntregaMenuStage().handle_input(msisdn=msisdn)

class BotSentLojasEntregaMenuStage(BotStage):
    stage = "bot_sent_lojas_entrega_menu_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        self.replies = [
            {
                "type": "text",
                "text": "Escolha uma loja para ser atendido:",
            },
            {
                "type": "list",
                "text": "Escolha uma de nossas lojas",
                "body": "Escolha uma de nossas lojas",
                "footer": "_Digite sair para encerrar o atendimento_",
                "action": {
                    "button": "Ver Lojas",
                    "sections": [{
                        "title": "Ver Lojas",
                        "rows": [
                            {"id": "Goiabeiras", "title": "Vitória/Goiabeiras"},
                            {"id": "Laranjeiras", "title": "Serra/Laranjeiras"},
                            {"id": "Campo Grande", "title": "Cariacica/Campo Grande"},
                            {"id": "Vila Velha", "title": "Vila Velha/Centro"},
                            {"id": "Glória", "title": "Vila Velha/Portal Glória"},
                            {"id": "Cachoeiro", "title": "Cachoeiro de Itapemirim"}
                        ]
                    }]
                }
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "stage": ReceiveLojaEntregaMenuStage.stage,
                "previous_stage": self.stage,
                "last_message_sent": self.get_last_message(replies=self.replies),
            },
        )

        return self.replies

class ReceiveLojaEntregaMenuStage(BotStage):
    stage = "receive_loja_entrega_menu_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        map_shop_to_department = {
            "vitoria/goiabeiras": 2293,
            "serra/laranjeiras": 2294,
            "cariacica/campo grande": 2295,
            "vila velha/centro": 2296,
            "vila velha/portal gloria": 2297,
            "cachoeiro de itapemirim": 2298
        }

        department_id = map_shop_to_department.get(text.lower())
        if department_id:
            return [
                {
                    "type": "text",
                    "text": "Aguarde, em breve você será atendido."
                },
                *SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=department_id),
                {
                    "type": "text",
                    "msisdn": msisdn,
                    "account_number": self.get_context_value(msisdn=msisdn, property="account_number"),
                    "delay": 5,
                    "wait_stage": AskEndStage.stage,
                    "text": "Olá, {contact_name}. Eu sou {my_name}. Para agilizar seu atendimento, por favor me informe, como posso te ajudar hoje?"
                }
            ]
        else:
            return [*BotSentLojasEntregaMenuStage().handle_input(msisdn=msisdn)]

class BotSentProdutosEntreguesStage(BotStage):
    stage = "bot_sent_produtos_entregues_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        codparc = self.get_context_value(msisdn=msisdn, property="codparc")
        customer_orders = vipdesk.get_products(codigo=codparc).get('responseBody', {}).get('records', {}).get('record', None)
        
        if not customer_orders:
            self.replies = [*BotSendNoProductsPendenteStage().handle_input(msisdn=msisdn)]
            return self.replies
        
        orders = [{
            "status": order.get('STATUS').get('$'),
            "sequencia": order.get('SEQUENCIA').get('$'),
            "nota": order.get('NUNOTA').get('$'),
            "dtentrega": order.get('DTENTREGA').get('$'),
            "dhemissao": order.get('DHEMISSAO').get('$'),
            "qtdneg": order.get('QTDNEG').get('$'),
            "codprod": order.get('CODPROD').get('$'),
            "descprod": order.get('DESCRPROD').get('$'),
        } for order in customer_orders if order.get('STATUS').get('$') == 'F']

        grouped_orders = {}
        for order in orders:
            nota = order.get('nota')
            if nota not in grouped_orders:
                grouped_orders[nota] = []
            grouped_orders[nota].append(order)

        if len(grouped_orders) <= 0:
            self.replies = [*BotSendNoProductsPendenteStage().handle_input(msisdn=msisdn)]
        
            return self.replies
        

        self.replies = [
            {
                "type": "text",
                "text": "*Aqui estão os produtos encontrados:*\n" + "\n".join([
                    f"*Nota {nota}*\n" + "\n".join([
                        f"{item.get('sequencia')}. {item.get('descprod')} ({item.get('qtdneg')} un) \n- Entrega: {item.get('dtentrega')[:10]}"
                        for item in items
                    ]) + "\n"
                    for nota, items in grouped_orders.items()
                ])
            },
            *SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=2134)
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "customer_orders": customer_orders,
                "last_message_sent": self.get_last_message(
                    replies=self.replies
                ),
                "previous_stage": BotSentProdutosEntreguesStage.stage,
            },
        )

        return self.replies
class BotAskOqueFazerProdutosEntreguesStage(BotStage):
    stage = "bot_ask_o_que_fazer_produtos_entregues_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        nome = self.get_context_value(msisdn=msisdn, property="customer").get("NOMECTT", {}).get("$").split(" ")[0].capitalize()
        self.replies = [
            {
                "type": "text",
                "text": f"Olá {nome}. Para agilizar seu atendimento, por favor escreva sobre qual item você gostaria de falar."
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "stage": ReceiveOqueFazerProdutosEntreguesStage.stage,
                "previous_stage": self.stage,
                "last_message_sent": self.get_last_message(replies=self.replies),
            },
        )

        return self.replies
        
class ReceiveOqueFazerProdutosEntreguesStage(BotStage):
    stage = "receive_o_que_fazer_produtos_entregues_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        return [
            {
                "type": "text",
                "text": f"Aguarde, em breve você será atendido."
            },
            *SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=ID_DEPARTAMENTO_ASSISTENCIA_TECNICA)
            ]
        
class BotAskOqueFazerServicosStage(BotStage):
    stage = "bot_ask_o_que_fazer_servicos_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str = "") -> list:
        self.replies = [
            {
                "type": "text",
                "text": "*Por favor, escolha uma opção:*\n\n1 - Solicitar Alteração de data\n2 - Dúvidas sobre o(s) serviço(s)\n\nDigite *SAIR* para finalizar ou *voltar* para retornar ao menu anterior"
            }
        ]

        self.set_context(
            msisdn=msisdn,
            data={
                "stage": ReceiveOqueFazerServicosStage.stage,
                "previous_stage": self.stage,
                "last_message_sent": self.get_last_message(replies=self.replies),
            },
        )

        return self.replies
        
class ReceiveOqueFazerServicosStage(BotStage):
    stage = "receive_o_que_fazer_servicos_stage"
    replies = []

    def handle_input(self, msisdn: str, text: str) -> list:
        if text in ["1", "2"]:
            return SendToDepartmentStage().handle_input(msisdn=msisdn, department_id=2286)
        elif text in ["0", "voltar", "Voltar", "menu anterior", "Menu anterior", "zero", "Zero"]:
            return BotSendMenuOptions().handle_input(msisdn=msisdn)
        else:
            return AskEndStage().handle_input(msisdn=msisdn)
        
        