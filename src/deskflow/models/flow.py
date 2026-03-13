from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    TIMESTAMP,
    Text,
)
from sqlalchemy.orm import relationship

from deskflow.dbms import Base, Session


class Flow(Base):
    """Modelo para fluxos de conversação visual"""

    __tablename__ = "flows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    data = Column(JSON(), nullable=False)
    secrets = Column(JSON(), nullable=True, default=dict)
    is_active = Column(Boolean, nullable=False, default=False)
    company_id = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    versions = relationship(
        "FlowVersion", back_populates="flow", cascade="all, delete-orphan"
    )

    def __init__(self, name, description, data, is_active=False, company_id=None, secrets=None):
        self.name = name
        self.description = description
        self.data = data
        self.secrets = secrets or {}
        self.is_active = is_active
        self.company_id = company_id


class FlowVersion(Base):
    """Modelo para versionamento de fluxos"""

    __tablename__ = "flow_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flow_id = Column(Integer, ForeignKey("flows.id"), nullable=False)
    version = Column(Integer, nullable=False)
    data = Column(JSON(), nullable=False)
    created_by = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    flow = relationship("Flow", back_populates="versions")

    def __init__(self, flow_id, version, data, created_by=None):
        self.flow_id = flow_id
        self.version = version
        self.data = data
        self.created_by = created_by


def get_active_flow():
    """Retorna o fluxo ativo"""
    with Session() as session:
        flow = session.query(Flow).filter(Flow.is_active == True).first()  # noqa: E712
        return flow


def get_flow_by_id(flow_id):
    """Retorna um fluxo pelo ID"""
    with Session() as session:
        flow = session.query(Flow).filter(Flow.id == flow_id).first()
        if flow:
            # Força reload dos dados do banco para pegar alterações recentes
            session.refresh(flow)
        return flow


def list_flows(company_id=None):
    """Lista todos os fluxos, opcionalmente filtrados por company_id"""
    with Session() as session:
        query = session.query(Flow)

        if company_id is not None:
            query = query.filter(Flow.company_id == company_id)

        flows = query.order_by(Flow.created_at.desc()).all()
        return flows


def create_flow(name, description, data, is_active=False, company_id=None, secrets=None):
    """Cria um novo fluxo"""
    with Session.begin() as session:
        flow = Flow(
            name=name, description=description, data=data,
            is_active=is_active, company_id=company_id,
            secrets=secrets,
        )
        session.add(flow)
        session.flush()

        # Cria versão inicial
        version = FlowVersion(
            flow_id=flow.id, version=1, data=data, created_by="system"
        )
        session.add(version)
        return flow


def update_flow(flow_id, name=None, description=None, data=None, is_active=None):
    """Atualiza um fluxo existente"""
    with Session.begin() as session:
        flow = session.query(Flow).filter(Flow.id == flow_id).first()

        if not flow:
            return None

        if name is not None:
            flow.name = name
        if description is not None:
            flow.description = description
        if data is not None:
            flow.data = data

            # Cria nova versão
            last_version = (
                session.query(FlowVersion)
                .filter(FlowVersion.flow_id == flow_id)
                .order_by(FlowVersion.version.desc())
                .first()
            )

            new_version_number = (
                last_version.version + 1 if last_version else 1
            )
            version = FlowVersion(
                flow_id=flow.id,
                version=new_version_number,
                data=data,
                created_by="system",
            )
            session.add(version)

        if is_active is not None:
            # Se ativando este fluxo, desativa todos os outros
            if is_active:
                session.query(Flow).filter(Flow.id != flow_id).update(
                    {"is_active": False}
                )
            flow.is_active = is_active

        flow.updated_at = datetime.utcnow()
        return flow


def get_flow_secrets(flow_id):
    """Retorna os segredos de um fluxo"""
    with Session() as session:
        flow = session.query(Flow).filter(Flow.id == flow_id).first()
        if flow:
            return flow.secrets or {}
        return {}


def update_flow_secrets(flow_id, secrets):
    """Atualiza os segredos de um fluxo (merge com existentes)"""
    with Session.begin() as session:
        flow = session.query(Flow).filter(Flow.id == flow_id).first()
        if not flow:
            return None
        current = flow.secrets or {}
        current.update(secrets)
        flow.secrets = current
        flow.updated_at = datetime.utcnow()
        return flow


def delete_flow_secret(flow_id, key):
    """Remove um segredo específico de um fluxo"""
    with Session.begin() as session:
        flow = session.query(Flow).filter(Flow.id == flow_id).first()
        if not flow:
            return None
        current = flow.secrets or {}
        current.pop(key, None)
        flow.secrets = current
        flow.updated_at = datetime.utcnow()
        return flow


def delete_flow(flow_id):
    """Deleta um fluxo"""
    with Session.begin() as session:
        flow = session.query(Flow).filter(Flow.id == flow_id).first()
        if flow:
            session.delete(flow)
            return True
        return False
