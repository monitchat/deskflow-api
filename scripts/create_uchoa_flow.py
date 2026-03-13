#!/usr/bin/env python3
"""
Script para criar o fluxo Uchôa Empreendimentos via API.

Gera o JSON completo do fluxo de atendimento e envia para o backend.

Uso:
    python scripts/create_uchoa_flow.py --dry-run   # Apenas gera o JSON
    python scripts/create_uchoa_flow.py --post       # Envia para a API
    python scripts/create_uchoa_flow.py --post --api-url http://localhost:5000
"""

import argparse
import json
import sys

# ============================================================
# PLACEHOLDERS - preencher com valores reais antes de ativar
# ============================================================
DEPT_RECEPCAO = "DEPT_RECEPCAO_ID"
DEPT_COMERCIAL = "DEPT_COMERCIAL_ID"
DEPT_FINANCEIRO = "DEPT_FINANCEIRO_ID"
DEPT_ASSISTENCIA = "DEPT_ASSISTENCIA_TECNICA_ID"

SIENGE_BASE = "https://api.sienge.com.br/uchoa/public/api/v1"
# Token real - será salvo nos secrets do fluxo
SIENGE_AUTH_TOKEN_VALUE = "Basic dWNob2EtY2hhdGJvdDo3OTFPcHMweENDbHZuMGVueWUwMFA4VFg3Sm0wYVo1eA=="
# Referência usada no JSON do fluxo (resolvida em runtime)
SIENGE_AUTH_HEADER = "${{secret.SIENGE_AUTH_TOKEN}}"

# URLs de mídia placeholder por empreendimento
EMPREENDIMENTOS = [
    "Club Gênova Residenziale",
    "Edifício Rivage",
    "Martin Sehner",
    "Green Park",
    "Alicante",
]

MEDIA_BOOK = {
    e: f"https://cdn.uchoaempreendimentos.com.br/books/{e.lower().replace(' ', '_')}.pdf"
    for e in EMPREENDIMENTOS
}
MEDIA_FACHADA = {
    e: f"https://cdn.uchoaempreendimentos.com.br/fotos/{e.lower().replace(' ', '_')}_fachada.jpg"
    for e in EMPREENDIMENTOS
}
MEDIA_AREA_COMUM = {
    e: f"https://cdn.uchoaempreendimentos.com.br/fotos/{e.lower().replace(' ', '_')}_area_comum.jpg"
    for e in EMPREENDIMENTOS
}
MEDIA_APTO = {
    e: f"https://cdn.uchoaempreendimentos.com.br/fotos/{e.lower().replace(' ', '_')}_apto.jpg"
    for e in EMPREENDIMENTOS
}
MEDIA_LP = {
    e: f"https://uchoaempreendimentos.com.br/{e.lower().replace(' ', '_')}"
    for e in EMPREENDIMENTOS
}
MEDIA_CARD_CORRETOR = {
    e: f"https://cdn.uchoaempreendimentos.com.br/marketing/{e.lower().replace(' ', '_')}_card.pdf"
    for e in EMPREENDIMENTOS
}

LINK_FORMULARIO_CORRETOR = (
    "https://uchoaempreendimentos.com.br/credenciamento"
)
LINK_PORTAL_CLIENTE = "https://uchoa.cvcrm.com.br/cliente/"
LINK_GARANTIA = (
    "https://uchoaempreendimentos.com.br/regulamentos"
)


# ============================================================
# Helpers
# ============================================================
_x = 0
_y = 0


def pos(x, y):
    """Retorna dict de posição."""
    return {"x": x, "y": y}


def node(id, type, x, y, data):
    """Cria um nó."""
    return {
        "id": id,
        "type": type,
        "position": pos(x, y),
        "data": data,
    }


def edge(source, target, source_handle=None, condition=None, label=None):
    """Cria uma edge."""
    suffix = f"-{source_handle}" if source_handle else ""
    e = {
        "id": f"{source}-{target}{suffix}",
        "source": source,
        "target": target,
        "markerEnd": {"type": "arrowclosed"},
        "data": {},
        "style": {"stroke": "#b1b1b7"},
    }
    if source_handle:
        e["sourceHandle"] = source_handle
    if condition:
        e["data"]["condition"] = condition
    if label:
        e["data"]["label"] = label
    return e


def equals_cond(*values):
    return {"type": "equals", "values": list(values)}


def context_cond(key, value):
    return {"type": "context", "key": key, "value": value}


def positive_cond():
    return {"type": "is_positive"}


def router_option(id, label, cond_type="equals", values=None):
    opt = {"id": id, "label": label, "condition": {"type": cond_type}}
    if values:
        opt["condition"]["values"] = values
    return opt


# ============================================================
# Empreendimentos router helpers
# ============================================================
def empre_options():
    """Gera opções de router para os 5 empreendimentos."""
    opts = []
    for i, name in enumerate(EMPREENDIMENTOS, 1):
        opts.append(
            router_option(
                f"empre_{i}", name, "equals", [str(i), name.lower()]
            )
        )
    return opts


def empre_options_with_humano():
    opts = empre_options()
    opts.append(
        router_option("empre_6", "Atendimento Humano", "equals", ["6"])
    )
    return opts


# ============================================================
# Build flow
# ============================================================
def build_flow():
    nodes = []
    edges_list = []

    # ------- Mensagem Inicial -------
    nodes.append(node("welcome", "message", 0, 0, {
        "message": (
            "Olá! Seja bem-vindo ao atendimento da "
            "*Uchôa Empreendimentos* 🏗️\n\n"
            "Como podemos te ajudar hoje?\n"
            "1. Sou Cliente\n"
            "2. Quero Comprar um imóvel\n"
            "3. Sou corretor\n"
            "4. Quero vender um terreno\n"
            "5. Quero trabalhar com vocês"
        ),
    }))

    # ------- Menu Principal (Router) -------
    nodes.append(node("main_router", "router", 0, 250, {
        "label": "Menu Principal",
        "error_message": (
            "Opção inválida! Por favor, digite um número de 1 a 5."
        ),
        "context_key": "menu_principal",
        "options": [
            router_option("op1", "Sou Cliente", "equals",
                          ["1", "cliente", "sou cliente"]),
            router_option("op2", "Quero Comprar", "equals",
                          ["2", "comprar", "quero comprar",
                           "quero comprar um imovel"]),
            router_option("op3", "Sou Corretor", "equals",
                          ["3", "corretor", "sou corretor"]),
            router_option("op4", "Vender Terreno", "equals",
                          ["4", "terreno", "quero vender um terreno",
                           "vender terreno"]),
            router_option("op5", "Trabalhar Conosco", "equals",
                          ["5", "trabalhar", "quero trabalhar",
                           "quero trabalhar com voces"]),
        ],
    }))
    edges_list.append(edge("welcome", "main_router"))

    # ===================== OP 5 - Trabalhar Conosco =====================
    nodes.append(node("op5_msg", "message", 1200, 500, {
        "message": (
            "Que bom saber do seu interesse em trabalhar conosco! 🎉\n\n"
            "Para participar dos nossos processos seletivos, você pode:\n"
            "- Enviar seu currículo para o e-mail: "
            "rh@uchoaempreendimentos.com, "
            "informando no assunto o cargo de interesse; ou\n"
            "- Realizar sua inscrição diretamente pelo nosso site de "
            "recrutamento Pandapé.\n\n"
            "Ficamos à disposição e desejamos boa sorte!"
        ),
    }))
    nodes.append(node("op5_end", "end", 1200, 750, {
        "message": (
            "A Uchôa Empreendimentos agradece o seu contato. "
            "Precisando, estamos à disposição!"
        ),
        "label": "Fim (RH)",
    }))
    edges_list.append(edge("main_router", "op5_msg", "op5"))
    edges_list.append(edge("op5_msg", "op5_end"))

    # ===================== OP 4 - Vender Terreno =====================
    nodes.append(node("op4_msg", "message", 900, 500, {
        "message": (
            "Perfeito! 👍\n\n"
            "Recebemos sua solicitação para venda de terreno. "
            "Seu contato será encaminhado para o nosso setor de "
            "Expansão, que é o responsável por analisar novas áreas. "
            "Em breve, nossa equipe entrará em contato com você."
        ),
    }))
    nodes.append(node("op4_transfer", "transfer", 900, 750, {
        "department_id": DEPT_RECEPCAO,
        "message": "Transferindo para a Recepção...",
        "label": "Transfer Recepção",
    }))
    edges_list.append(edge("main_router", "op4_msg", "op4"))
    edges_list.append(edge("op4_msg", "op4_transfer"))

    # ===================== OP 3 - Sou Corretor =====================
    nodes.append(node("op3_msg", "message", 600, 500, {
        "message": (
            "Bem-vindo(a)! 🤝\n"
            "Este canal é exclusivo para atendimento aos corretores.\n\n"
            "O que você deseja fazer agora?\n"
            "1. Materiais de Marketing\n"
            "2. Credenciamento como corretor parceiro\n"
            "3. Negociação e apoio comercial\n"
            "4. Falar com o comercial"
        ),
    }))
    nodes.append(node("op3_router", "router", 600, 800, {
        "label": "Menu Corretor",
        "error_message": "Opção inválida! Digite um número de 1 a 4.",
        "context_key": "menu_corretor",
        "options": [
            router_option("cor1", "Marketing", "equals",
                          ["1", "marketing", "materiais"]),
            router_option("cor2", "Credenciamento", "equals",
                          ["2", "credenciamento"]),
            router_option("cor3", "Negociação", "equals",
                          ["3", "negociacao", "negociação"]),
            router_option("cor4", "Falar Comercial", "equals",
                          ["4", "comercial"]),
        ],
    }))
    edges_list.append(edge("main_router", "op3_msg", "op3"))
    edges_list.append(edge("op3_msg", "op3_router"))

    # -- Cor 4: Falar comercial direto
    nodes.append(node("cor4_transfer", "transfer", 900, 1100, {
        "department_id": DEPT_COMERCIAL,
        "message": (
            "Entendi! Você está sendo redirecionado para um especialista."
        ),
        "label": "Transfer Comercial (Corretor)",
    }))
    edges_list.append(edge("op3_router", "cor4_transfer", "cor4"))

    # -- Cor 3: Negociação - escolher empreendimento
    nodes.append(node("cor3_msg", "message", 600, 1100, {
        "message": (
            "Antes de te passar para o nosso gerente de vendas, "
            "conta pra gente: qual empreendimento você deseja "
            "atendimento?\n"
            "1. Club Gênova Residenziale\n"
            "2. Edifício Rivage\n"
            "3. Martin Sehner\n"
            "4. Green Park\n"
            "5. Alicante"
        ),
    }))
    nodes.append(node("cor3_router", "router", 600, 1350, {
        "label": "Empreendimento (Negociação)",
        "error_message": "Opção inválida! Digite um número de 1 a 5.",
        "context_key": "empreendimento_negociacao",
        "options": empre_options(),
    }))
    nodes.append(node("cor3_save", "set_context", 600, 1600, {
        "label": "Salvar Empreendimento",
        "mappings": [
            {"key": "empreendimento", "value": "empreendimento_negociacao",
             "source": "context"},
        ],
    }))
    nodes.append(node("cor3_transfer", "transfer", 600, 1800, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Negociação)",
    }))
    edges_list.append(edge("op3_router", "cor3_msg", "cor3"))
    edges_list.append(edge("cor3_msg", "cor3_router"))
    # All empreendimento options go to cor3_save
    for i in range(1, 6):
        edges_list.append(
            edge("cor3_router", "cor3_save", f"empre_{i}")
        )
    edges_list.append(edge("cor3_save", "cor3_transfer"))

    # -- Cor 2: Credenciamento
    nodes.append(node("cor2_msg", "message", 300, 1100, {
        "message": (
            "Que bom ter você com a gente! 🎉\n\n"
            "Para seguir com o cadastro como corretor, "
            "acesse o link abaixo e preencha o formulário:\n\n"
            f"{LINK_FORMULARIO_CORRETOR}"
        ),
    }))
    nodes.append(node("cor2_end", "end", 300, 1350, {
        "message": (
            "A Uchôa Empreendimentos agradece o seu contato!"
        ),
        "label": "Fim (Credenciamento)",
    }))
    edges_list.append(edge("op3_router", "cor2_msg", "cor2"))
    edges_list.append(edge("cor2_msg", "cor2_end"))

    # -- Cor 1: Marketing - escolher empreendimento
    nodes.append(node("cor1_msg", "message", 0, 1100, {
        "message": (
            "Para qual empreendimento deseja receber materiais "
            "de marketing?\n"
            "1. Club Gênova Residenziale\n"
            "2. Edifício Rivage\n"
            "3. Martin Sehner\n"
            "4. Green Park\n"
            "5. Alicante"
        ),
    }))
    nodes.append(node("cor1_router", "router", 0, 1350, {
        "label": "Empreendimento (Marketing)",
        "error_message": "Opção inválida! Digite um número de 1 a 5.",
        "context_key": "empreendimento_mkt",
        "options": empre_options(),
    }))
    # Cada empreendimento envia o card de materiais
    nodes.append(node("cor1_card_msg", "message", 0, 1600, {
        "message": (
            "Ótima escolha! 🎨\n"
            "Acesse o link abaixo para fazer o download dos materiais."
        ),
    }))
    nodes.append(node("cor1_card_media", "media", 0, 1800, {
        "media_type": "document",
        "url": "https://cdn.uchoaempreendimentos.com.br/marketing/card_materiais.pdf",
        "file_name": "Materiais_de_Marketing.pdf",
        "caption": "Card de Materiais de Marketing",
        "label": "PDF Card Materiais",
    }))
    nodes.append(node("cor1_end", "end", 0, 2000, {
        "message": (
            "A Uchôa Empreendimentos agradece o seu contato!"
        ),
        "label": "Fim (Marketing)",
    }))
    edges_list.append(edge("op3_router", "cor1_msg", "cor1"))
    edges_list.append(edge("cor1_msg", "cor1_router"))
    for i in range(1, 6):
        edges_list.append(
            edge("cor1_router", "cor1_card_msg", f"empre_{i}")
        )
    edges_list.append(edge("cor1_card_msg", "cor1_card_media"))
    edges_list.append(edge("cor1_card_media", "cor1_end"))

    # ===================== OP 2 - Quero Comprar =====================
    nodes.append(node("op2_msg", "message", -600, 500, {
        "message": (
            "Excelente escolha! 🏠\n\n"
            "Temos em nosso portfólio empreendimentos cuidadosamente "
            "planejados, com opções de apartamentos e lotes que unem "
            "localização, qualidade e boas condições de compra.\n\n"
            "Posso te mostrar agora os empreendimentos disponíveis ou "
            "te direcionar para um atendimento humano com nosso time "
            "comercial para tirar todas as suas dúvidas.\n\n"
            "O que você prefere fazer agora?\n"
            "1. Ver empreendimentos\n"
            "2. Falar com o comercial"
        ),
    }))
    nodes.append(node("op2_router", "router", -600, 850, {
        "label": "Comprar - Opções",
        "error_message": "Opção inválida! Digite 1 ou 2.",
        "context_key": "comprar_opcao",
        "options": [
            router_option("comp1", "Ver Empreendimentos", "equals",
                          ["1", "ver", "empreendimentos",
                           "ver empreendimentos"]),
            router_option("comp2", "Falar Comercial", "equals",
                          ["2", "comercial", "falar comercial",
                           "falar com o comercial"]),
        ],
    }))
    edges_list.append(edge("main_router", "op2_msg", "op2"))
    edges_list.append(edge("op2_msg", "op2_router"))

    # -- Comp2: Falar com comercial
    nodes.append(node("comp2_transfer", "transfer", -300, 1100, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Comprar)",
    }))
    edges_list.append(edge("op2_router", "comp2_transfer", "comp2"))

    # -- Comp1: Ver empreendimentos
    nodes.append(node("comp1_msg", "message", -600, 1100, {
        "message": (
            "Para qual empreendimento você deseja atendimento?\n"
            "1. Club Gênova Residenziale\n"
            "2. Edifício Rivage\n"
            "3. Martin Sehner\n"
            "4. Green Park\n"
            "5. Alicante\n"
            "6. Atendimento Humano"
        ),
    }))
    nodes.append(node("comp1_router", "router", -600, 1400, {
        "label": "Empreendimento (Comprar)",
        "error_message": "Opção inválida! Digite um número de 1 a 6.",
        "context_key": "empreendimento_comprar",
        "options": empre_options_with_humano(),
    }))
    edges_list.append(edge("op2_router", "comp1_msg", "comp1"))
    edges_list.append(edge("comp1_msg", "comp1_router"))

    # Opção 6 - atendimento humano
    nodes.append(node("comp1_humano_transfer", "transfer", -300, 1650, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Humano)",
    }))
    edges_list.append(
        edge("comp1_router", "comp1_humano_transfer", "empre_6")
    )

    # Opções 1-5: enviar materiais + transferir
    nodes.append(node("comp1_materiais_msg", "message", -600, 1650, {
        "message": (
            "Ótima escolha! 🏗️\n\n"
            "Vou te encaminhar agora para o gerente de vendas, "
            "que vai te orientar de forma personalizada em todo "
            "o processo.\n\n"
            "Enquanto isso, vou te enviar alguns materiais exclusivos "
            "do empreendimento para você já ir se familiarizando com "
            "as opções, plantas e diferenciais.\n\n"
            "Fica tranquilo(a), em instantes alguém do nosso time "
            "fala com você."
        ),
    }))
    for i in range(1, 6):
        edges_list.append(
            edge("comp1_router", "comp1_materiais_msg", f"empre_{i}")
        )

    # Media nodes - book, fachada, area comum, apto, LP
    nodes.append(node("comp1_book", "media", -600, 1900, {
        "media_type": "document",
        "url": "https://cdn.uchoaempreendimentos.com.br/books/book_produto.pdf",
        "file_name": "Book_do_Produto.pdf",
        "caption": "Book do Produto",
        "label": "PDF Book",
    }))
    nodes.append(node("comp1_fachada", "media", -600, 2050, {
        "media_type": "image",
        "url": "https://cdn.uchoaempreendimentos.com.br/fotos/fachada.jpg",
        "caption": "Foto da Fachada",
        "label": "Foto Fachada",
    }))
    nodes.append(node("comp1_area", "media", -600, 2200, {
        "media_type": "image",
        "url": "https://cdn.uchoaempreendimentos.com.br/fotos/area_comum.jpg",
        "caption": "Foto da Área Comum",
        "label": "Foto Área Comum",
    }))
    nodes.append(node("comp1_apto", "media", -600, 2350, {
        "media_type": "image",
        "url": "https://cdn.uchoaempreendimentos.com.br/fotos/apartamento.jpg",
        "caption": "Foto do Apartamento",
        "label": "Foto Apto",
    }))
    nodes.append(node("comp1_lp", "message", -600, 2500, {
        "message": (
            "Link da página do empreendimento:\n"
            "https://uchoaempreendimentos.com.br/empreendimento"
        ),
    }))
    nodes.append(node("comp1_transfer", "transfer", -600, 2700, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Materiais)",
    }))
    edges_list.append(edge("comp1_materiais_msg", "comp1_book"))
    edges_list.append(edge("comp1_book", "comp1_fachada"))
    edges_list.append(edge("comp1_fachada", "comp1_area"))
    edges_list.append(edge("comp1_area", "comp1_apto"))
    edges_list.append(edge("comp1_apto", "comp1_lp"))
    edges_list.append(edge("comp1_lp", "comp1_transfer"))

    # ===================== OP 1 - Sou Cliente =====================
    nodes.append(node("op1_msg", "message", -1800, 500, {
        "message": (
            "Com qual setor você gostaria de falar?\n"
            "1. Falar com o Financeiro\n"
            "2. Falar com a Assistência Técnica\n"
            "3. Falar com o Comercial"
        ),
    }))
    nodes.append(node("op1_router", "router", -1800, 750, {
        "label": "Setor Cliente",
        "error_message": "Opção inválida! Digite 1, 2 ou 3.",
        "context_key": "setor_cliente",
        "options": [
            router_option("setor1", "Financeiro", "equals",
                          ["1", "financeiro"]),
            router_option("setor2", "Assistência Técnica", "equals",
                          ["2", "assistencia", "assistência",
                           "assistencia tecnica"]),
            router_option("setor3", "Comercial", "equals",
                          ["3", "comercial"]),
        ],
    }))
    edges_list.append(edge("main_router", "op1_msg", "op1"))
    edges_list.append(edge("op1_msg", "op1_router"))

    # ---- Setor 3: Comercial (mesmo fluxo Op2) ----
    # Reutiliza o nó op2_msg
    nodes.append(node("setor3_msg", "message", -1200, 1000, {
        "message": (
            "Excelente escolha! 🏠\n\n"
            "Temos em nosso portfólio empreendimentos cuidadosamente "
            "planejados, com opções de apartamentos e lotes que unem "
            "localização, qualidade e boas condições de compra.\n\n"
            "O que você prefere fazer agora?\n"
            "1. Ver empreendimentos\n"
            "2. Falar com o comercial"
        ),
    }))
    nodes.append(node("setor3_router", "router", -1200, 1300, {
        "label": "Comercial (Cliente)",
        "error_message": "Opção inválida! Digite 1 ou 2.",
        "context_key": "cliente_comercial",
        "options": [
            router_option("sc_ver", "Ver Empreendimentos", "equals",
                          ["1", "ver", "empreendimentos"]),
            router_option("sc_falar", "Falar Comercial", "equals",
                          ["2", "comercial", "falar"]),
        ],
    }))
    edges_list.append(edge("op1_router", "setor3_msg", "setor3"))
    edges_list.append(edge("setor3_msg", "setor3_router"))

    nodes.append(node("sc_falar_transfer", "transfer", -1000, 1550, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Cliente)",
    }))
    edges_list.append(
        edge("setor3_router", "sc_falar_transfer", "sc_falar")
    )

    # Ver empreendimentos (mesma lógica)
    nodes.append(node("sc_ver_msg", "message", -1200, 1550, {
        "message": (
            "Para qual empreendimento você deseja atendimento?\n"
            "1. Club Gênova Residenziale\n"
            "2. Edifício Rivage\n"
            "3. Martin Sehner\n"
            "4. Green Park\n"
            "5. Alicante\n"
            "6. Atendimento Humano"
        ),
    }))
    nodes.append(node("sc_ver_router", "router", -1200, 1850, {
        "label": "Empreendimento (Cliente Comercial)",
        "error_message": "Opção inválida! Digite um número de 1 a 6.",
        "context_key": "empreendimento_cliente",
        "options": empre_options_with_humano(),
    }))
    edges_list.append(edge("setor3_router", "sc_ver_msg", "sc_ver"))
    edges_list.append(edge("sc_ver_msg", "sc_ver_router"))

    nodes.append(node("sc_humano_transfer", "transfer", -1000, 2100, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Humano Cliente)",
    }))
    edges_list.append(
        edge("sc_ver_router", "sc_humano_transfer", "empre_6")
    )

    # Materiais + transfer para emp 1-5
    nodes.append(node("sc_materiais_msg", "message", -1200, 2100, {
        "message": (
            "Ótima escolha! 🏗️\n\n"
            "Vou te encaminhar agora para o gerente de vendas.\n\n"
            "Enquanto isso, seguem materiais exclusivos "
            "do empreendimento."
        ),
    }))
    for i in range(1, 6):
        edges_list.append(
            edge("sc_ver_router", "sc_materiais_msg", f"empre_{i}")
        )
    nodes.append(node("sc_book", "media", -1200, 2300, {
        "media_type": "document",
        "url": "https://cdn.uchoaempreendimentos.com.br/books/book_produto.pdf",
        "file_name": "Book_do_Produto.pdf",
        "caption": "Book do Produto",
        "label": "PDF Book (Cliente)",
    }))
    nodes.append(node("sc_fachada", "media", -1200, 2450, {
        "media_type": "image",
        "url": "https://cdn.uchoaempreendimentos.com.br/fotos/fachada.jpg",
        "caption": "Foto da Fachada",
        "label": "Foto Fachada (Cliente)",
    }))
    nodes.append(node("sc_area", "media", -1200, 2600, {
        "media_type": "image",
        "url": "https://cdn.uchoaempreendimentos.com.br/fotos/area_comum.jpg",
        "caption": "Foto da Área Comum",
        "label": "Foto Área (Cliente)",
    }))
    nodes.append(node("sc_apto", "media", -1200, 2750, {
        "media_type": "image",
        "url": "https://cdn.uchoaempreendimentos.com.br/fotos/apartamento.jpg",
        "caption": "Foto do Apartamento",
        "label": "Foto Apto (Cliente)",
    }))
    nodes.append(node("sc_lp", "message", -1200, 2900, {
        "message": (
            "Link da página do empreendimento:\n"
            "https://uchoaempreendimentos.com.br/empreendimento"
        ),
    }))
    nodes.append(node("sc_transfer", "transfer", -1200, 3100, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Materiais Cliente)",
    }))
    edges_list.append(edge("sc_materiais_msg", "sc_book"))
    edges_list.append(edge("sc_book", "sc_fachada"))
    edges_list.append(edge("sc_fachada", "sc_area"))
    edges_list.append(edge("sc_area", "sc_apto"))
    edges_list.append(edge("sc_apto", "sc_lp"))
    edges_list.append(edge("sc_lp", "sc_transfer"))

    # ---- Setor 2: Assistência Técnica ----
    nodes.append(node("setor2_msg", "message", -1800, 1000, {
        "message": (
            "Olá! 🔧\n"
            "Como podemos te ajudar na Assistência Técnica?\n\n"
            "Escolha uma das opções abaixo:\n"
            "1. Dúvidas sobre Garantia\n"
            "2. Abrir um chamado\n"
            "3. Acompanhar um chamado"
        ),
    }))
    nodes.append(node("setor2_router", "router", -1800, 1250, {
        "label": "Menu Assistência",
        "error_message": "Opção inválida! Digite 1, 2 ou 3.",
        "context_key": "menu_assistencia",
        "options": [
            router_option("at1", "Garantia", "equals",
                          ["1", "garantia", "duvidas"]),
            router_option("at2", "Abrir Chamado", "equals",
                          ["2", "abrir", "abrir chamado"]),
            router_option("at3", "Acompanhar Chamado", "equals",
                          ["3", "acompanhar", "acompanhar chamado"]),
        ],
    }))
    edges_list.append(edge("op1_router", "setor2_msg", "setor2"))
    edges_list.append(edge("setor2_msg", "setor2_router"))

    # AT1 - Garantia
    nodes.append(node("at1_msg", "message", -2200, 1500, {
        "message": (
            "Entendi, vou te enviar o link para acessar os nossos "
            "regulamentos.\n\n"
            "Para falar com um especialista tecle *1*"
        ),
    }))
    nodes.append(node("at1_link", "media", -2200, 1700, {
        "media_type": "document",
        "url": LINK_GARANTIA,
        "file_name": "Regulamentos.pdf",
        "caption": "Regulamentos de Garantia",
        "label": "Link Garantia",
    }))
    nodes.append(node("at1_router", "router", -2200, 1900, {
        "label": "Garantia - Ação",
        "error_message": "Digite *1* para falar com especialista "
                         "ou *sair* para encerrar.",
        "context_key": "garantia_acao",
        "options": [
            router_option("at1_esp", "Falar Especialista", "equals",
                          ["1"]),
        ],
    }))
    nodes.append(node("at1_transfer", "transfer", -2200, 2150, {
        "department_id": DEPT_ASSISTENCIA,
        "message": "Transferindo para a Assistência Técnica...",
        "label": "Transfer Assistência (Garantia)",
    }))
    edges_list.append(edge("setor2_router", "at1_msg", "at1"))
    edges_list.append(edge("at1_msg", "at1_link"))
    edges_list.append(edge("at1_link", "at1_router"))
    edges_list.append(edge("at1_router", "at1_transfer", "at1_esp"))

    # AT2 - Abrir Chamado
    nodes.append(node("at2_msg", "message", -1800, 1500, {
        "message": (
            "Para abrir um chamado, siga o passo a passo abaixo "
            "em nosso Portal do Cliente:\n\n"
            f"Acesse o portal pelo link:\n{LINK_PORTAL_CLIENTE}\n\n"
            "Faça login utilizando seu CPF ou CNPJ e sua senha.\n"
            "Na página inicial, clique na opção \"Chamados\".\n"
            "Selecione \"Abrir um chamado\", escolha o contrato "
            "que deseja abrir chamado e descreva o problema e "
            "clique em \"enviar\".\n\n"
            "Pronto! Agora é só aguardar que nossa equipe fará "
            "contato para resolver o seu problema.\n\n"
            "Caso queira atendimento humano digite *1*\n"
            "Ou digite *SAIR* para finalizar o atendimento."
        ),
    }))
    nodes.append(node("at2_router", "router", -1800, 1850, {
        "label": "Chamado - Ação",
        "error_message": "Digite *1* para atendimento humano "
                         "ou *sair* para encerrar.",
        "context_key": "chamado_acao",
        "options": [
            router_option("at2_hum", "Atendimento Humano", "equals",
                          ["1"]),
        ],
    }))
    nodes.append(node("at2_transfer", "transfer", -1800, 2100, {
        "department_id": DEPT_ASSISTENCIA,
        "message": "Transferindo para a Assistência Técnica...",
        "label": "Transfer Assistência (Chamado)",
    }))
    nodes.append(node("at2_end", "end", -1650, 2100, {
        "message": "Atendimento finalizado. Precisando, "
                   "estamos à disposição!",
        "label": "Fim (Chamado)",
    }))
    edges_list.append(edge("setor2_router", "at2_msg", "at2"))
    edges_list.append(edge("at2_msg", "at2_router"))
    edges_list.append(edge("at2_router", "at2_transfer", "at2_hum"))

    # AT3 - Acompanhar Chamado
    nodes.append(node("at3_msg", "message", -1500, 1500, {
        "message": (
            "Para acompanhar seu chamado, siga o passo a passo "
            "abaixo em nosso Portal do Cliente:\n\n"
            f"Acesse o portal pelo link:\n{LINK_PORTAL_CLIENTE}\n\n"
            "Faça login utilizando seu CPF ou CNPJ e sua senha.\n"
            "Na página inicial, clique na opção \"Chamados\".\n"
            "Selecione o chamado que gostaria de acompanhar e "
            "verifique o seu \"status\".\n\n"
            "Caso queira atendimento humano digite *1*\n"
            "Ou digite *SAIR* para finalizar o atendimento."
        ),
    }))
    nodes.append(node("at3_router", "router", -1500, 1850, {
        "label": "Acompanhar - Ação",
        "error_message": "Digite *1* para atendimento humano "
                         "ou *sair* para encerrar.",
        "context_key": "acompanhar_acao",
        "options": [
            router_option("at3_hum", "Atendimento Humano", "equals",
                          ["1"]),
        ],
    }))
    nodes.append(node("at3_transfer", "transfer", -1500, 2100, {
        "department_id": DEPT_ASSISTENCIA,
        "message": "Transferindo para a Assistência Técnica...",
        "label": "Transfer Assistência (Acompanhar)",
    }))
    nodes.append(node("at3_end", "end", -1350, 2100, {
        "message": "Atendimento finalizado. Precisando, "
                   "estamos à disposição!",
        "label": "Fim (Acompanhar)",
    }))
    edges_list.append(edge("setor2_router", "at3_msg", "at3"))
    edges_list.append(edge("at3_msg", "at3_router"))
    edges_list.append(edge("at3_router", "at3_transfer", "at3_hum"))

    # ---- Setor 1: Financeiro ----
    nodes.append(node("setor1_msg", "message", -2600, 1000, {
        "message": (
            "Olá! 💰\n"
            "Como podemos te ajudar?\n\n"
            "Escolha uma das opções abaixo:\n"
            "1. Adquirir uma unidade\n"
            "2. Dúvida sobre contratos"
        ),
    }))
    nodes.append(node("setor1_router", "router", -2600, 1250, {
        "label": "Menu Financeiro",
        "error_message": "Opção inválida! Digite 1 ou 2.",
        "context_key": "menu_financeiro",
        "options": [
            router_option("fin1", "Adquirir Unidade", "equals",
                          ["1", "adquirir"]),
            router_option("fin2", "Dúvida Contratos", "equals",
                          ["2", "duvida", "contratos",
                           "duvida sobre contratos"]),
        ],
    }))
    edges_list.append(edge("op1_router", "setor1_msg", "setor1"))
    edges_list.append(edge("setor1_msg", "setor1_router"))

    # Fin1 - Adquirir (mesmo fluxo Op2)
    nodes.append(node("fin1_transfer", "transfer", -2800, 1500, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Adquirir)",
    }))
    edges_list.append(edge("setor1_router", "fin1_transfer", "fin1"))

    # Fin2 - Dúvida contratos
    nodes.append(node("fin2_msg", "message", -2600, 1500, {
        "message": (
            "Antes de começarmos, preciso saber qual modelo de "
            "contrato você deseja consultar.\n"
            "1. Contrato de financiamento Caixa\n"
            "2. Contrato de financiamento direto com a construtora\n"
            "3. Contrato de financiamento com outros bancos"
        ),
    }))
    nodes.append(node("fin2_router", "router", -2600, 1800, {
        "label": "Tipo Contrato",
        "error_message": "Opção inválida! Digite 1, 2 ou 3.",
        "context_key": "tipo_contrato",
        "options": [
            router_option("ct1", "Caixa", "equals", ["1", "caixa"]),
            router_option("ct2", "Direto Construtora", "equals",
                          ["2", "direto", "construtora"]),
            router_option("ct3", "Outros Bancos", "equals",
                          ["3", "outros", "bancos"]),
        ],
    }))
    nodes.append(node("fin2_input_msg", "message", -2600, 2050, {
        "message": (
            "Certo!\n"
            "Agora, informe o número da reserva ou o seu CPF "
            "para que eu possa localizar o contrato."
        ),
    }))
    nodes.append(node("fin2_input", "input", -2600, 2250, {
        "input_type": "text",
        "context_key": "reserva_cpf",
        "validation": {},
        "label": "Reserva/CPF (Contrato)",
    }))
    nodes.append(node("fin2_transfer", "transfer", -2600, 2450, {
        "department_id": DEPT_COMERCIAL,
        "message": "Transferindo para o Comercial...",
        "label": "Transfer Comercial (Contrato)",
    }))
    edges_list.append(edge("setor1_router", "fin2_msg", "fin2"))
    edges_list.append(edge("fin2_msg", "fin2_router"))
    for ct in ["ct1", "ct2", "ct3"]:
        edges_list.append(
            edge("fin2_router", "fin2_input_msg", ct)
        )
    edges_list.append(edge("fin2_input_msg", "fin2_input"))
    edges_list.append(edge("fin2_input", "fin2_transfer"))

    # ---- Sub-fluxo Financeiro (Boletos / Renegociação / IR) ----
    # Acesso via Menu Financeiro direto do Setor 1
    nodes.append(node("fin_servico_msg", "message", -3200, 1000, {
        "message": (
            "Que tipo de serviço você precisa?\n\n"
            "Escolha uma das opções abaixo:\n"
            "1. 2ª via de boletos\n"
            "2. Renegociar\n"
            "3. Demonstrativo IR"
        ),
    }))

    # Conectar do welcome como alternativa (cliente financeiro direto)
    # Na verdade, este menu é acessado do setor1 como sub-opção.
    # Vamos adicionar uma edge condicional do setor1_msg

    nodes.append(node("fin_servico_router", "router", -3200, 1250, {
        "label": "Tipo Serviço Financeiro",
        "error_message": "Opção inválida! Digite 1, 2 ou 3.",
        "context_key": "servico_financeiro",
        "options": [
            router_option("srv1", "Boletos", "equals",
                          ["1", "boleto", "boletos", "2a via"]),
            router_option("srv2", "Renegociar", "equals",
                          ["2", "renegociar", "renegociacao"]),
            router_option("srv3", "IR", "equals",
                          ["3", "ir", "demonstrativo",
                           "demonstrativo ir"]),
        ],
    }))
    # Nota: este sub-fluxo será linkado manualmente pelo usuário
    # no editor, ou pode ser conectado como sub-opção
    edges_list.append(edge("fin_servico_msg", "fin_servico_router"))

    # --- SRV3: Demonstrativo IR ---
    nodes.append(node("srv3_msg", "message", -2800, 1500, {
        "message": (
            "Para emitir seu extrato de pagamentos (Demonstrativo de IR), "
            "siga o passo a passo abaixo em nosso Portal do Cliente:\n\n"
            f"Acesse o portal pelo link:\n{LINK_PORTAL_CLIENTE}\n\n"
            "Faça login utilizando seu CPF ou CNPJ e sua senha.\n"
            "Na página inicial, clique na opção \"Financeiro\".\n"
            "Selecione \"Demonstrativo IR\", escolha o ano desejado "
            "e clique em \"Emitir\".\n\n"
            "Pronto! Agora é só imprimir ou salvar o documento.\n\n"
            "Se precisar de ajuda, estamos à disposição por aqui!"
        ),
    }))
    nodes.append(node("srv3_end", "end", -2800, 1800, {
        "message": "Atendimento finalizado. Precisando, "
                   "estamos à disposição!",
        "label": "Fim (IR)",
    }))
    edges_list.append(edge("fin_servico_router", "srv3_msg", "srv3"))
    edges_list.append(edge("srv3_msg", "srv3_end"))

    # --- SRV1: Boletos (com API Sienge) ---
    nodes.append(node("srv1_cpf_msg", "message", -3600, 1500, {
        "message": (
            "Para que eu possa gerar um boleto, preciso que me "
            "informe o seu CPF."
        ),
    }))
    nodes.append(node("srv1_cpf_input", "input", -3600, 1700, {
        "input_type": "cpf",
        "context_key": "cpf",
        "validation": {
            "error_message": "CPF inválido. Por favor, digite novamente.",
        },
        "label": "Input CPF (Boleto)",
    }))
    nodes.append(node("srv1_api", "api_request", -3600, 1900, {
        "label": "Buscar Cliente Sienge",
        "method": "GET",
        "url": f"{SIENGE_BASE}/customers?cpf=${{{{cpf}}}}",
        "query_params": [],
        "headers": [
            {"key": "Authorization", "value": SIENGE_AUTH_HEADER},
            {"key": "Content-Type", "value": "application/json"},
        ],
        "body": "",
        "context_key": "sienge_response",
    }))
    nodes.append(node("srv1_cond", "condition", -3600, 2100, {
        "label": "Cliente Existe?",
    }))
    # Existe
    nodes.append(node("srv1_confirma_msg", "message", -3800, 2300, {
        "message": (
            "Localizamos um cadastro com esse CPF em nosso sistema.\n\n"
            "Para seguir com a emissão do seu boleto, "
            "confirme por favor:\n\n"
            "Você é ${{nomeparc}}?\n"
            "1. Sim\n"
            "2. Não"
        ),
    }))
    nodes.append(node("srv1_confirma_router", "router", -3800, 2550, {
        "label": "Confirma Identidade (Boleto)",
        "error_message": "Digite 1 para Sim ou 2 para Não.",
        "context_key": "confirma_identidade",
        "options": [
            router_option("bol_sim", "Sim", "equals",
                          ["1", "sim"]),
            router_option("bol_nao", "Não", "equals",
                          ["2", "nao", "não"]),
        ],
    }))
    # Sim - envia boletos
    nodes.append(node("srv1_boleto_msg", "message", -4000, 2800, {
        "message": (
            "Os boletos vinculados ao seu contrato estão "
            "sendo encaminhados agora neste atendimento.\n\n"
            "Em caso de dúvidas, nosso time permanece à disposição."
        ),
    }))
    nodes.append(node("srv1_boleto_end", "end", -4000, 3000, {
        "message": "Atendimento finalizado. Precisando, "
                   "estamos à disposição!",
        "label": "Fim (Boleto)",
    }))
    # Não - volta
    nodes.append(node("srv1_nao_msg", "message", -3600, 2800, {
        "message": (
            "Ops, parece que houve um erro...\n"
            "Vamos voltar para tentar novamente."
        ),
    }))

    # Não existe
    nodes.append(node("srv1_nao_existe_msg", "message", -3400, 2300, {
        "message": (
            "Ops, não encontrei os dados. 😕\n"
            "Digite novamente seu CPF por favor ou "
            "\"0\" para voltar ao menu."
        ),
    }))
    nodes.append(node("srv1_nao_existe_router", "router", -3400, 2550, {
        "label": "Retry ou Voltar (Boleto)",
        "error_message": "Digite seu CPF ou 0 para voltar.",
        "context_key": "retry_boleto",
        "options": [
            router_option("bol_volta", "Voltar Menu", "equals", ["0"]),
        ],
    }))

    edges_list.append(
        edge("fin_servico_router", "srv1_cpf_msg", "srv1")
    )
    edges_list.append(edge("srv1_cpf_msg", "srv1_cpf_input"))
    edges_list.append(edge("srv1_cpf_input", "srv1_api"))
    edges_list.append(edge("srv1_api", "srv1_cond"))
    edges_list.append(edge(
        "srv1_cond", "srv1_confirma_msg",
        condition=context_cond("sienge_response_success", True),
        label="Existe",
    ))
    edges_list.append(edge(
        "srv1_cond", "srv1_nao_existe_msg",
        condition=context_cond("sienge_response_success", False),
        label="Não existe",
    ))
    edges_list.append(edge("srv1_confirma_msg", "srv1_confirma_router"))
    edges_list.append(
        edge("srv1_confirma_router", "srv1_boleto_msg", "bol_sim")
    )
    edges_list.append(
        edge("srv1_confirma_router", "srv1_nao_msg", "bol_nao")
    )
    edges_list.append(edge("srv1_boleto_msg", "srv1_boleto_end"))
    edges_list.append(edge("srv1_nao_msg", "srv1_cpf_msg"))
    edges_list.append(
        edge("srv1_nao_existe_msg", "srv1_nao_existe_router")
    )
    edges_list.append(
        edge("srv1_nao_existe_router", "fin_servico_msg", "bol_volta")
    )

    # --- SRV2: Renegociar (com API Sienge) ---
    nodes.append(node("srv2_cpf_msg", "message", -3200, 1500, {
        "message": (
            "Para seguir com a renegociação, precisamos localizar "
            "seu contrato em nosso sistema.\n\n"
            "Por favor, informe seu CPF."
        ),
    }))
    nodes.append(node("srv2_cpf_input", "input", -3200, 1700, {
        "input_type": "cpf",
        "context_key": "cpf",
        "validation": {
            "error_message": "CPF inválido. Por favor, digite novamente.",
        },
        "label": "Input CPF (Renegociação)",
    }))
    nodes.append(node("srv2_api", "api_request", -3200, 1900, {
        "label": "Buscar Cliente Sienge (Reneg)",
        "method": "GET",
        "url": f"{SIENGE_BASE}/customers?cpf=${{{{cpf}}}}",
        "query_params": [],
        "headers": [
            {"key": "Authorization", "value": SIENGE_AUTH_HEADER},
            {"key": "Content-Type", "value": "application/json"},
        ],
        "body": "",
        "context_key": "sienge_response",
    }))
    nodes.append(node("srv2_cond", "condition", -3200, 2100, {
        "label": "Cliente Existe? (Reneg)",
    }))
    nodes.append(node("srv2_confirma_msg", "message", -3400, 2300, {
        "message": (
            "Localizamos um cadastro com esse CPF.\n\n"
            "Confirme por favor:\n"
            "Você é ${{nomeparc}}?\n"
            "1. Sim\n"
            "2. Não"
        ),
    }))
    nodes.append(node("srv2_confirma_router", "router", -3400, 2550, {
        "label": "Confirma Identidade (Reneg)",
        "error_message": "Digite 1 para Sim ou 2 para Não.",
        "context_key": "confirma_reneg",
        "options": [
            router_option("ren_sim", "Sim", "equals",
                          ["1", "sim"]),
            router_option("ren_nao", "Não", "equals",
                          ["2", "nao", "não"]),
        ],
    }))
    nodes.append(node("srv2_sim_msg", "message", -3600, 2800, {
        "message": (
            "Obrigado, seu contato está sendo encaminhado para "
            "o responsável que fará a negociação."
        ),
    }))
    nodes.append(node("srv2_transfer", "transfer", -3600, 3000, {
        "department_id": DEPT_FINANCEIRO,
        "message": "Transferindo para o Financeiro...",
        "label": "Transfer Financeiro (Reneg)",
    }))
    nodes.append(node("srv2_nao_msg", "message", -3200, 2800, {
        "message": (
            "Ops, parece que houve um erro...\n"
            "Vamos voltar para tentar novamente."
        ),
    }))
    nodes.append(node("srv2_nao_existe_msg", "message", -3000, 2300, {
        "message": (
            "Ops, não encontrei os dados. 😕\n"
            "Digite novamente seu CPF por favor ou "
            "\"0\" para voltar ao menu."
        ),
    }))
    nodes.append(node("srv2_nao_existe_router", "router", -3000, 2550, {
        "label": "Retry ou Voltar (Reneg)",
        "error_message": "Digite seu CPF ou 0 para voltar.",
        "context_key": "retry_reneg",
        "options": [
            router_option("ren_volta", "Voltar Menu", "equals", ["0"]),
        ],
    }))

    edges_list.append(
        edge("fin_servico_router", "srv2_cpf_msg", "srv2")
    )
    edges_list.append(edge("srv2_cpf_msg", "srv2_cpf_input"))
    edges_list.append(edge("srv2_cpf_input", "srv2_api"))
    edges_list.append(edge("srv2_api", "srv2_cond"))
    edges_list.append(edge(
        "srv2_cond", "srv2_confirma_msg",
        condition=context_cond("sienge_response_success", True),
        label="Existe",
    ))
    edges_list.append(edge(
        "srv2_cond", "srv2_nao_existe_msg",
        condition=context_cond("sienge_response_success", False),
        label="Não existe",
    ))
    edges_list.append(edge("srv2_confirma_msg", "srv2_confirma_router"))
    edges_list.append(
        edge("srv2_confirma_router", "srv2_sim_msg", "ren_sim")
    )
    edges_list.append(
        edge("srv2_confirma_router", "srv2_nao_msg", "ren_nao")
    )
    edges_list.append(edge("srv2_sim_msg", "srv2_transfer"))
    edges_list.append(edge("srv2_nao_msg", "srv2_cpf_msg"))
    edges_list.append(
        edge("srv2_nao_existe_msg", "srv2_nao_existe_router")
    )
    edges_list.append(
        edge("srv2_nao_existe_router", "fin_servico_msg", "ren_volta")
    )

    return {"nodes": nodes, "edges": edges_list}


def main():
    parser = argparse.ArgumentParser(
        description="Cria o fluxo Uchôa Empreendimentos"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas gera o JSON e imprime no stdout",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Envia o fluxo para a API",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:5000",
        help="URL base da API (default: http://localhost:5000)",
    )
    parser.add_argument(
        "--company-id",
        type=int,
        default=None,
        help="ID da empresa (opcional)",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.post:
        parser.print_help()
        sys.exit(1)

    flow_data = build_flow()

    payload = {
        "name": "Uchôa Empreendimentos",
        "description": (
            "Fluxo de atendimento completo da Uchôa Empreendimentos. "
            "Inclui: Cliente (Financeiro, Assistência, Comercial), "
            "Comprar imóvel, Corretor, Vender terreno, RH."
        ),
        "data": flow_data,
        "is_active": False,
    }

    if args.company_id:
        payload["company_id"] = args.company_id

    total_nodes = len(flow_data["nodes"])
    total_edges = len(flow_data["edges"])

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print(
            f"\n--- Resumo: {total_nodes} nós, {total_edges} edges ---",
            file=sys.stderr,
        )
        return

    if args.post:
        import requests

        url = f"{args.api_url}/api/v1/flows"
        print(f"Enviando fluxo para {url}...")
        print(f"  Nós: {total_nodes}")
        print(f"  Edges: {total_edges}")

        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if resp.status_code in (200, 201):
                result = resp.json()
                flow_id = result.get("data", {}).get("id", "?")
                print(f"Fluxo criado com sucesso! ID: {flow_id}")

                # Salva as credenciais nos secrets do fluxo
                if flow_id != "?":
                    secrets_url = f"{args.api_url}/api/v1/flows/{flow_id}/secrets"
                    secrets_payload = {
                        "secrets": {
                            "SIENGE_AUTH_TOKEN": SIENGE_AUTH_TOKEN_VALUE,
                        }
                    }
                    secrets_resp = requests.put(
                        secrets_url,
                        json=secrets_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30,
                    )
                    if secrets_resp.status_code == 200:
                        print("Credenciais salvas com sucesso!")
                    else:
                        print(f"Aviso: Erro ao salvar credenciais: {secrets_resp.text}")
            else:
                print(f"Erro {resp.status_code}: {resp.text}")
                sys.exit(1)
        except Exception as e:
            print(
                f"Erro: {e}\n"
                f"Verifique se o servidor está rodando em {args.api_url}."
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
