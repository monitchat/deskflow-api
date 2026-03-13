from datetime import datetime

from sqlalchemy import (  # create_engine,
    BOOLEAN,
    JSON,
    TIMESTAMP,
    BigInteger,
    Column,
)

# from danubio_bot.config import SQLALCHEMY_DATABASE_URI
from danubio_bot.dbms import Base, Session


class AutomaticMessage(Base):
    __tablename__ = "automatic_messages"

    id = Column("id", BigInteger, primary_key=True)
    regular_period = Column("regular_period", BOOLEAN, nullable=False)
    data = Column("data", JSON(), nullable=False)
    starts_at = Column(
        "starts_at",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
    )

    ends_at = Column(
        "ends_at",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
    )

    def __init__(self, data, starts_at, ends_at, regular_period=False):
        self.data = data
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.regular_period = regular_period


def get_messages_active():
    with Session() as session:
        return (
            session.query(AutomaticMessage)
            .filter(datetime.utcnow() >= AutomaticMessage.starts_at)
            .filter(datetime.utcnow() < AutomaticMessage.ends_at)
            .all()
        )


def add(ctx):
    with Session.begin() as session:
        session.add(ctx)
        return ctx


def delete(id):
    with Session() as session:
        session.query(AutomaticMessage).filter(
            AutomaticMessage.id == id
        ).delete()
        session.commit()
        return True
