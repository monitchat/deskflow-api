from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, String
from sqlalchemy.exc import IntegrityError

from danubio_bot.dbms import Base, Session


class Optout(Base):
    __tablename__ = "optouts"

    msisdn = Column("msisdn", String(16), primary_key=True, nullable=False)
    created_at = Column(
        "created_at",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
    )

    def __init__(self, msisdn, created_at=None):
        self.msisdn = msisdn
        self.created_at = created_at


OPTOUT_TEXTS = [
    "sair",
    "nao",
    "não",
    "não quero",
    "pare",
    "para",
    "parar",
    "stop",
    "cancelar",
    "cancela",
]


def matches(text):
    return text.strip().lower() in OPTOUT_TEXTS


def contains(msisdn):
    with Session() as session:
        return (
            session.query(Optout).filter(Optout.msisdn == msisdn).first()
            is not None
        )


def insert(msisdn):
    try:
        with Session.begin() as session:
            session.add(Optout(msisdn))
    except IntegrityError:
        pass


def delete(msisdn):
    with Session.begin() as session:
        session.query(Optout).filter(Optout.msisdn == msisdn).delete()
