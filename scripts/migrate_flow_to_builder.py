"""
Script de migração do fluxo legado para o Flow Builder

Este script converte o fluxo existente em bot_stage.py para o formato JSON
do Flow Builder e insere no banco de dados.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from danubio_bot.models import flow as flow_model
from danubio_bot.dbms import Session

# Mapeamento do fluxo atual da Client
DANUBIO_FLOW = {
    "nodes": [
        # ===== NÓ INICIAL =====
        {
            "id": "ask_start_menu",
            "type": "api_call",
            "position": {"x": 250, "y": 50},
            "data": {
                "api_type": "get_partner",
                "label": "Verificar se é parceiro/cliente"
            }
        },

        # ===== RAMIFICAÇÃO INICIAL =====
        {
            "id": "check_partner_type",
            "type": "condition",
            "position": {"x": 250, "y": 150},
            "data": {"label": "É Montador ou Cliente?"}
        },

        # ===== FLUXO MONTADOR =====
        {
            "id": "send_menu_parceiro",
            "type": "message",
            "position": {"x": 50, "y": 250},
            "data": {
                "message": "Parceiro: *{codparc}*, Contato: *{nomectt}*\n\nCerto! Escolha uma das opções abaixo para continuarmos:\n\n1 - Assistência Técnica\n2 - Lojas\n3 - SAC\n\nDigite *Sair* Para finalizar o atendimento."
            }
        },
        {
            "id": "receive_menu_parceiro",
            "type": "input",
            "position": {"x": 50, "y": 350},
            "data": {
                "input_type": "number",
                "context_key": "menu_parceiro_option",
                "label": "Receber opção do menu parceiro"
            }
        },
        {
            "id": "route_parceiro_option",
            "type": "condition",
            "position": {"x": 50, "y": 450},
            "data": {"label": "Rotear opção parceiro"}
        },
        {
            "id": "transfer_assistencia_parceiro",
            "type": "transfer",
            "position": {"x": -100, "y": 550},
            "data": {
                "department_id": 2134,
                "message": "Transferindo para Assistência Técnica...",
                "label": "AT Parceiro"
            }
        },
        {
            "id": "transfer_sac_parceiro",
            "type": "transfer",
            "position": {"x": 200, "y": 550},
            "data": {
                "department_id": 2285,
                "message": "Transferindo para SAC...",
                "label": "SAC Parceiro"
            }
        },

        # ===== PERGUNTAR SE É CLIENTE =====
        {
            "id": "ask_is_customer",
            "type": "button",
            "position": {"x": 450, "y": 250},
            "data": {
                "message": "É um prazer receber o seu contato. Já é nosso Cliente?",
                "buttons": ["Sim", "Não"]
            }
        },
        {
            "id": "receive_is_customer",
            "type": "condition",
            "position": {"x": 450, "y": 350},
            "data": {"label": "É cliente?"}
        },

        # ===== FLUXO NÃO CLIENTE =====
        {
            "id": "send_menu_non_client",
            "type": "message",
            "position": {"x": 650, "y": 450},
            "data": {
                "message": "Por favor, escolha uma das opções abaixo:\n\n1 - Realizar nova compra\n2 - SAC\n\nDigite *Sair* Para finalizar o atendimento."
            }
        },
        {
            "id": "receive_menu_non_client",
            "type": "input",
            "position": {"x": 650, "y": 550},
            "data": {
                "input_type": "number",
                "context_key": "menu_non_client_option",
                "label": "Opção não cliente"
            }
        },
        {
            "id": "route_non_client_option",
            "type": "condition",
            "position": {"x": 650, "y": 650},
            "data": {"label": "Rotear não cliente"}
        },
        {
            "id": "transfer_sac_non_client",
            "type": "transfer",
            "position": {"x": 750, "y": 750},
            "data": {
                "department_id": 2285,
                "message": "Transferindo para SAC...",
                "label": "SAC Não Cliente"
            }
        },

        # ===== FLUXO CLIENTE - PEDIR CPF =====
        {
            "id": "ask_cpf_cliente",
            "type": "message",
            "position": {"x": 250, "y": 450},
            "data": {
                "message": "É um prazer receber seu contato. Por gentileza, informe o número do seu CPF."
            }
        },
        {
            "id": "receive_cpf_cliente",
            "type": "input",
            "position": {"x": 250, "y": 550},
            "data": {
                "input_type": "cpf",
                "context_key": "cpf",
                "validation": {
                    "error_message": "CPF inválido. Por favor, digite novamente."
                },
                "label": "Capturar CPF"
            }
        },
        {
            "id": "get_customer_data",
            "type": "api_call",
            "position": {"x": 250, "y": 650},
            "data": {
                "api_type": "get_customer",
                "label": "Buscar dados do cliente"
            }
        },
        {
            "id": "check_customer_found",
            "type": "condition",
            "position": {"x": 250, "y": 750},
            "data": {"label": "Cliente encontrado?"}
        },

        # ===== MENU PRINCIPAL CLIENTE =====
        {
            "id": "send_menu_principal",
            "type": "message",
            "position": {"x": 250, "y": 850},
            "data": {
                "message": "Parceiro: *{codparc}*, Contato: *{nomectt}*\n\n*Certo! Escolha uma das opções abaixo para continuarmos:*\n\n1 - Realizar nova compra de produto/serviço\n2 - Minhas compras (Montagem/Entrega)\n3 - Meus serviços de limpeza e outros\n4 - Garantia e Assistência Técnica\n5 - SAC\n\n_Digite *SAIR* para finalizar o atendimento_"
            }
        },
        {
            "id": "receive_menu_principal",
            "type": "input",
            "position": {"x": 250, "y": 950},
            "data": {
                "input_type": "number",
                "context_key": "menu_principal_option",
                "label": "Opção menu principal"
            }
        },
        {
            "id": "route_menu_principal",
            "type": "condition",
            "position": {"x": 250, "y": 1050},
            "data": {"label": "Rotear menu principal"}
        },

        # ===== OPÇÃO 1: NOVA COMPRA - LOJAS =====
        {
            "id": "send_lojas_menu",
            "type": "list",
            "position": {"x": -200, "y": 1150},
            "data": {
                "text": "Certo! Para melhor atende-lo, escolha uma das nossas lojas mais próxima da sua localidade.",
                "body": "Escolha uma de nossas lojas",
                "footer": "_Digite sair para encerrar o atendimento_",
                "action": {
                    "button": "Ver Lojas",
                    "sections": [{
                        "title": "Ver Lojas",
                        "rows": [
                            {"id": "Goiabeiras", "title": "Vitória/Goiabeiras", "description": ""},
                            {"id": "Laranjeiras", "title": "Serra/Laranjeiras", "description": ""},
                            {"id": "Campo Grande", "title": "Cariacica/Campo Grande", "description": ""},
                            {"id": "Vila Velha", "title": "Vila Velha/Centro", "description": ""},
                            {"id": "Glória", "title": "Vila Velha/Portal Glória", "description": ""},
                            {"id": "Cachoeiro de Itapemirim", "title": "Cachoeiro de Itapemirim", "description": ""}
                        ]
                    }]
                }
            }
        },
        {
            "id": "receive_loja_menu",
            "type": "input",
            "position": {"x": -200, "y": 1250},
            "data": {
                "input_type": "text",
                "context_key": "loja_selecionada",
                "label": "Loja selecionada"
            }
        },
        {
            "id": "route_loja_transfer",
            "type": "condition",
            "position": {"x": -200, "y": 1350},
            "data": {"label": "Rotear para loja"}
        },
        {
            "id": "transfer_goiabeiras",
            "type": "transfer",
            "position": {"x": -400, "y": 1450},
            "data": {
                "department_id": 2287,
                "message": "Transferindo para Goiabeiras...",
                "label": "Goiabeiras"
            }
        },
        {
            "id": "transfer_laranjeiras",
            "type": "transfer",
            "position": {"x": -250, "y": 1450},
            "data": {
                "department_id": 2288,
                "message": "Transferindo para Laranjeiras...",
                "label": "Laranjeiras"
            }
        },
        {
            "id": "transfer_campo_grande",
            "type": "transfer",
            "position": {"x": -100, "y": 1450},
            "data": {
                "department_id": 2289,
                "message": "Transferindo para Campo Grande...",
                "label": "Campo Grande"
            }
        },
        {
            "id": "transfer_vila_velha",
            "type": "transfer",
            "position": {"x": 50, "y": 1450},
            "data": {
                "department_id": 2290,
                "message": "Transferindo para Vila Velha Centro...",
                "label": "Vila Velha"
            }
        },
        {
            "id": "transfer_gloria",
            "type": "transfer",
            "position": {"x": 200, "y": 1450},
            "data": {
                "department_id": 2291,
                "message": "Transferindo para Portal Glória...",
                "label": "Glória"
            }
        },
        {
            "id": "transfer_cachoeiro",
            "type": "transfer",
            "position": {"x": 350, "y": 1450},
            "data": {
                "department_id": 2292,
                "message": "Transferindo para Cachoeiro...",
                "label": "Cachoeiro"
            }
        },

        # ===== OPÇÃO 2: PRODUTOS PENDENTES =====
        {
            "id": "get_produtos_pendentes",
            "type": "api_call",
            "position": {"x": 100, "y": 1150},
            "data": {
                "api_type": "get_products",
                "label": "Buscar produtos pendentes"
            }
        },
        {
            "id": "show_produtos_pendentes",
            "type": "message",
            "position": {"x": 100, "y": 1250},
            "data": {
                "message": "*Aqui estão os produtos pendentes de entrega:*\n{produtos_list}"
            }
        },
        {
            "id": "ask_oque_fazer_produtos",
            "type": "message",
            "position": {"x": 100, "y": 1350},
            "data": {
                "message": "*Escolha uma opção:*\n\n1 - Solicitar Alteração de data\n2 - Dúvidas sobre o(s) produto(s)\n3 - Falar com atendente\n\nDigite *SAIR* para finalizar o atendimento ou *voltar* para retornar ao menu anterior"
            }
        },

        # ===== OPÇÃO 3: SERVIÇOS PENDENTES =====
        {
            "id": "get_servicos_pendentes",
            "type": "api_call",
            "position": {"x": 400, "y": 1150},
            "data": {
                "api_type": "get_services",
                "label": "Buscar serviços pendentes"
            }
        },
        {
            "id": "show_servicos_pendentes",
            "type": "message",
            "position": {"x": 400, "y": 1250},
            "data": {
                "message": "*Aqui estão os serviços contratados:*\n{servicos_list}"
            }
        },
        {
            "id": "ask_oque_fazer_servicos",
            "type": "message",
            "position": {"x": 400, "y": 1350},
            "data": {
                "message": "*Por favor, escolha uma opção:*\n\n1 - Solicitar Alteração de data\n2 - Dúvidas sobre o(s) serviço(s)\n\nDigite *SAIR* para finalizar ou *voltar* para retornar ao menu anterior"
            }
        },

        # ===== OPÇÃO 4: ASSISTÊNCIA TÉCNICA =====
        {
            "id": "get_produtos_entregues",
            "type": "api_call",
            "position": {"x": 700, "y": 1150},
            "data": {
                "api_type": "get_products",
                "label": "Buscar produtos entregues"
            }
        },
        {
            "id": "transfer_assistencia",
            "type": "transfer",
            "position": {"x": 700, "y": 1250},
            "data": {
                "department_id": 2134,
                "message": "Aguarde, em breve você será atendido.",
                "label": "Assistência Técnica"
            }
        },

        # ===== OPÇÃO 5: SAC =====
        {
            "id": "transfer_sac_cliente",
            "type": "transfer",
            "position": {"x": 1000, "y": 1150},
            "data": {
                "department_id": 2285,
                "message": "Olá. Para agilizar seu atendimento, por favor, me diga em que posso ajudar",
                "label": "SAC Cliente"
            }
        },

        # ===== NÓ DE FIM =====
        {
            "id": "ask_end",
            "type": "end",
            "position": {"x": 250, "y": 1600},
            "data": {
                "message": "A Client agradece o seu contato. Precisando, estamos à disposição!",
                "label": "Finalizar"
            }
        }
    ],

    "edges": [
        # Fluxo inicial
        {"source": "ask_start_menu", "target": "check_partner_type"},

        # Se for montador
        {
            "source": "check_partner_type",
            "target": "send_menu_parceiro",
            "data": {
                "condition": {
                    "type": "context",
                    "key": "tipo_contato",
                    "value": "M"
                }
            }
        },
        {"source": "send_menu_parceiro", "target": "receive_menu_parceiro"},
        {"source": "receive_menu_parceiro", "target": "route_parceiro_option"},
        {
            "source": "route_parceiro_option",
            "target": "transfer_assistencia_parceiro",
            "data": {
                "condition": {"type": "equals", "values": ["1", "um"]}
            }
        },
        {
            "source": "route_parceiro_option",
            "target": "send_lojas_menu",
            "data": {
                "condition": {"type": "equals", "values": ["2", "dois"]}
            }
        },
        {
            "source": "route_parceiro_option",
            "target": "transfer_sac_parceiro",
            "data": {
                "condition": {"type": "equals", "values": ["3", "tres", "três"]}
            }
        },
        {"source": "transfer_assistencia_parceiro", "target": "ask_end"},
        {"source": "transfer_sac_parceiro", "target": "ask_end"},

        # Se não for montador, pergunta se é cliente
        {
            "source": "check_partner_type",
            "target": "ask_is_customer"
        },
        {"source": "ask_is_customer", "target": "receive_is_customer"},

        # Se não for cliente
        {
            "source": "receive_is_customer",
            "target": "send_menu_non_client",
            "data": {
                "condition": {"type": "equals", "values": ["2", "não", "nao"]}
            }
        },
        {"source": "send_menu_non_client", "target": "receive_menu_non_client"},
        {"source": "receive_menu_non_client", "target": "route_non_client_option"},
        {
            "source": "route_non_client_option",
            "target": "send_lojas_menu",
            "data": {
                "condition": {"type": "equals", "values": ["1", "um"]}
            }
        },
        {
            "source": "route_non_client_option",
            "target": "transfer_sac_non_client",
            "data": {
                "condition": {"type": "equals", "values": ["2", "dois"]}
            }
        },
        {"source": "transfer_sac_non_client", "target": "ask_end"},

        # Se for cliente, pede CPF
        {
            "source": "receive_is_customer",
            "target": "ask_cpf_cliente",
            "data": {
                "condition": {"type": "equals", "values": ["1", "sim"]}
            }
        },
        {"source": "ask_cpf_cliente", "target": "receive_cpf_cliente"},
        {"source": "receive_cpf_cliente", "target": "get_customer_data"},
        {"source": "get_customer_data", "target": "check_customer_found"},

        # Se cliente encontrado
        {
            "source": "check_customer_found",
            "target": "send_menu_principal",
            "data": {
                "condition": {"type": "context", "key": "customer", "value": "exists"}
            }
        },
        # Se não encontrado
        {
            "source": "check_customer_found",
            "target": "send_menu_non_client"
        },

        # Menu principal
        {"source": "send_menu_principal", "target": "receive_menu_principal"},
        {"source": "receive_menu_principal", "target": "route_menu_principal"},

        # Opção 1: Nova compra
        {
            "source": "route_menu_principal",
            "target": "send_lojas_menu",
            "data": {
                "condition": {"type": "equals", "values": ["1", "um"]}
            }
        },

        # Opção 2: Produtos pendentes
        {
            "source": "route_menu_principal",
            "target": "get_produtos_pendentes",
            "data": {
                "condition": {"type": "equals", "values": ["2", "dois"]}
            }
        },
        {"source": "get_produtos_pendentes", "target": "show_produtos_pendentes"},
        {"source": "show_produtos_pendentes", "target": "ask_oque_fazer_produtos"},

        # Opção 3: Serviços
        {
            "source": "route_menu_principal",
            "target": "get_servicos_pendentes",
            "data": {
                "condition": {"type": "equals", "values": ["3", "tres", "três"]}
            }
        },
        {"source": "get_servicos_pendentes", "target": "show_servicos_pendentes"},
        {"source": "show_servicos_pendentes", "target": "ask_oque_fazer_servicos"},

        # Opção 4: Assistência
        {
            "source": "route_menu_principal",
            "target": "get_produtos_entregues",
            "data": {
                "condition": {"type": "equals", "values": ["4", "quatro"]}
            }
        },
        {"source": "get_produtos_entregues", "target": "transfer_assistencia"},
        {"source": "transfer_assistencia", "target": "ask_end"},

        # Opção 5: SAC
        {
            "source": "route_menu_principal",
            "target": "transfer_sac_cliente",
            "data": {
                "condition": {"type": "equals", "values": ["5", "cinco"]}
            }
        },
        {"source": "transfer_sac_cliente", "target": "ask_end"},

        # Lojas
        {"source": "send_lojas_menu", "target": "receive_loja_menu"},
        {"source": "receive_loja_menu", "target": "route_loja_transfer"},
        {
            "source": "route_loja_transfer",
            "target": "transfer_goiabeiras",
            "data": {
                "condition": {"type": "contains", "values": ["goiabeira"]}
            }
        },
        {
            "source": "route_loja_transfer",
            "target": "transfer_laranjeiras",
            "data": {
                "condition": {"type": "contains", "values": ["laranjeira"]}
            }
        },
        {
            "source": "route_loja_transfer",
            "target": "transfer_campo_grande",
            "data": {
                "condition": {"type": "contains", "values": ["campo grande"]}
            }
        },
        {
            "source": "route_loja_transfer",
            "target": "transfer_vila_velha",
            "data": {
                "condition": {"type": "contains", "values": ["vila velha"]}
            }
        },
        {
            "source": "route_loja_transfer",
            "target": "transfer_gloria",
            "data": {
                "condition": {"type": "contains", "values": ["gloria", "glória"]}
            }
        },
        {
            "source": "route_loja_transfer",
            "target": "transfer_cachoeiro",
            "data": {
                "condition": {"type": "contains", "values": ["cachoeiro"]}
            }
        },

        # Todas transferências vão para fim
        {"source": "transfer_goiabeiras", "target": "ask_end"},
        {"source": "transfer_laranjeiras", "target": "ask_end"},
        {"source": "transfer_campo_grande", "target": "ask_end"},
        {"source": "transfer_vila_velha", "target": "ask_end"},
        {"source": "transfer_gloria", "target": "ask_end"},
        {"source": "transfer_cachoeiro", "target": "ask_end"},
    ],

    "metadata": {
        "version": "1.0.0",
        "created_by": "migration_script",
        "description": "Fluxo migrado do sistema legado bot_stage.py"
    }
}


def migrate_flow():
    """Migra o fluxo legado para o Flow Builder"""
    print("🔄 Iniciando migração do fluxo Client...")

    try:
        # Verifica se já existe um fluxo com este nome
        with Session() as session:
            from danubio_bot.models.flow import Flow
            existing = session.query(Flow).filter(Flow.name == "Fluxo Client (Migrado)").first()

            if existing:
                print("⚠️  Fluxo 'Fluxo Client (Migrado)' já existe!")
                response = input("Deseja substituir? (s/n): ")
                if response.lower() != 's':
                    print("❌ Migração cancelada")
                    return

                # Atualiza o fluxo existente
                flow_model.update_flow(
                    flow_id=existing.id,
                    name="Fluxo Client (Migrado)",
                    description="Fluxo completo de atendimento da Client - migrado automaticamente do código legado",
                    data=DANUBIO_FLOW,
                    is_active=False
                )
                print(f"✅ Fluxo atualizado com sucesso! ID: {existing.id}")
            else:
                # Cria novo fluxo
                flow = flow_model.create_flow(
                    name="Fluxo Client (Migrado)",
                    description="Fluxo completo de atendimento da Client - migrado automaticamente do código legado",
                    data=DANUBIO_FLOW,
                    is_active=False
                )
                print(f"✅ Fluxo criado com sucesso! ID: {flow.id}")

        print("\n📊 Estatísticas do fluxo:")
        print(f"   - Nós: {len(DANUBIO_FLOW['nodes'])}")
        print(f"   - Conexões: {len(DANUBIO_FLOW['edges'])}")
        print("\n💡 Próximos passos:")
        print("   1. Acesse o Flow Builder em http://localhost:3000")
        print("   2. Abra o fluxo 'Fluxo Client (Migrado)'")
        print("   3. Revise e ajuste conforme necessário")
        print("   4. Ative o fluxo quando estiver pronto")
        print("\n⚠️  IMPORTANTE: O fluxo foi criado INATIVO. Teste antes de ativar!")

    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    migrate_flow()
