from datetime import datetime
from inspect import stack

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Column, String

from danubio_bot.dbms import Base, Session


class Activity(Base):
    __tablename__ = "activity"

    id = Column("id", BigInteger, primary_key=True)
    caller = Column("caller", String(32), nullable=True)
    content = Column("content", JSON(), nullable=False)
    created_at = Column(
        "created_at",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
    )

    def __init__(self, content, caller=None):
        self.content = content
        self.caller = caller


def save(content):
    caller = stack()[1].function
    with Session.begin() as session:
        session.add(Activity(content, caller))
