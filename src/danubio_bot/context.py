from datetime import datetime, timedelta

from sqlalchemy import JSON, TIMESTAMP, Column, Integer, String, text
from tenacity import retry, stop_after_attempt

from danubio_bot.dbms import Base, Session


class Context(Base):
    __tablename__ = "contexts"

    msisdn = Column("msisdn", String(16), primary_key=True, nullable=False)
    flow_id = Column("flow_id", Integer, primary_key=True, nullable=False)
    data = Column("data", JSON(), nullable=False)
    updated_at = Column(
        "updated_at",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
    )
    created_at = Column(
        "created_at",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow(),
    )

    def __init__(self, msisdn, flow_id, data):
        self.msisdn = msisdn
        self.flow_id = flow_id
        self.data = data


def load(msisdn, flow_id) -> Context:
    with Session.begin() as session:
        ctx = session.query(Context).filter(
            Context.msisdn == msisdn,
            Context.flow_id == flow_id
        ).first()

        if not ctx:
            ctx = Context(
                msisdn,
                flow_id,
                {
                    "stage": None,
                    "previous_stage": None,
                    "version": "1",
                },
            )
            session.add(ctx)
        return ctx


def get_inactive() -> list[Context]:
    with Session.begin() as session:
        ctx = (
            session.query(Context)
            .filter(
                text(
                    "data->>'request_suggestion_sent' = 'false' or data->>'request_suggestion_sent' is null"
                )
            )
            .filter(text("data->>'stage' = 'receive_what_next'"))
            .filter(
                Context.updated_at < datetime.utcnow() - timedelta(minutes=2)
            )
            .all()
        )

        return ctx


def delete(msisdn, flow_id):
    with Session() as session:
        session.query(Context).filter(
            Context.msisdn == msisdn,
            Context.flow_id == flow_id
        ).delete()
        session.commit()
        return True


def update(ctx) -> Context:
    with Session.begin() as session:
        curr_ctx = (
            session.query(Context).filter(
                Context.msisdn == ctx.msisdn,
                Context.flow_id == ctx.flow_id
            ).first()
        )
        if curr_ctx:
            curr_ctx.data = ctx.data
            curr_ctx.updated_at = datetime.utcnow()
            ctx = curr_ctx
        session.add(ctx)
        return ctx


@retry(stop=stop_after_attempt(3))
def merge(msisdn, flow_id, data) -> Context:
    ctx = load(msisdn, flow_id)
    ctx.data.update(data)
    with Session.begin() as session:
        curr_ctx = (
            session.query(Context).filter(
                Context.msisdn == ctx.msisdn,
                Context.flow_id == ctx.flow_id
            ).first()
        )
        if curr_ctx:
            curr_ctx.data = ctx.data
            curr_ctx.updated_at = datetime.utcnow()
            ctx = curr_ctx
        session.add(ctx)
        return ctx


def get_value(msisdn: str, flow_id: int, property: str):
    """
    Busca um valor no contexto.
    Suporta campos aninhados usando ponto (.), arrays com índice [N], e wildcards *

    Exemplos:
        - 'cpf' → busca ctx.data['cpf']
        - 'customer.NOMEPARC.$' → busca ctx.data['customer']['NOMEPARC']['$']
        - 'tags[0].label' → busca ctx.data['tags'][0]['label']
        - 'tags.*.label' → busca todos os labels em tags (retorna array)
        - 'customer.responseBody.records.record[0].CODPARC.$' → navega em estruturas complexas

    Args:
        msisdn: Número do telefone
        flow_id: ID do fluxo
        property: Chave ou path aninhado (separado por ponto)

    Returns:
        Valor encontrado ou None (ou array se usar wildcard *)
    """
    import re

    ctx = load(msisdn=msisdn, flow_id=flow_id)

    # Se não tem ponto nem colchetes, é uma chave simples
    if '.' not in property and '[' not in property:
        return ctx.data.get(property, None)

    # Substitui notação de array [N] por .N temporariamente para facilitar parsing
    # Exemplo: tags[0].label → tags.0.label
    property_normalized = re.sub(r'\[(\d+)\]', r'.\1', property)

    # Divide em partes
    keys = property_normalized.split('.')
    current = ctx.data

    for i, key in enumerate(keys):
        if current is None:
            return None

        # Verifica se é wildcard (*)
        if key == '*':
            # Se current não é lista, retorna None
            if not isinstance(current, list):
                return None

            # Pega o resto do caminho
            remaining_path = '.'.join(keys[i+1:])

            if not remaining_path:
                # Se não tem mais caminho, retorna a lista toda
                return current

            # Aplica o resto do caminho em cada item da lista
            results = []
            for item in current:
                if isinstance(item, dict):
                    # Navega recursivamente
                    temp = item
                    for subkey in remaining_path.split('.'):
                        if isinstance(temp, dict):
                            temp = temp.get(subkey)
                        elif isinstance(temp, list):
                            # Se encontrar lista no meio do caminho, tenta acessar por índice
                            try:
                                idx = int(subkey)
                                temp = temp[idx] if 0 <= idx < len(temp) else None
                            except (ValueError, TypeError):
                                temp = None
                        else:
                            temp = None
                            break
                    if temp is not None:
                        results.append(temp)

            return results if results else None

        # Tenta converter para índice de array
        try:
            index = int(key)
            if isinstance(current, list) and 0 <= index < len(current):
                current = current[index]
            else:
                return None
        except ValueError:
            # Não é número, trata como chave de dicionário
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None

    return current


def get_values(msisdn: str, flow_id: int, properties: list) -> dict:
    ctx = load(msisdn=msisdn, flow_id=flow_id)
    values = {}

    for property in properties:
        values[property] = ctx.data.get(property, None)

    return values
