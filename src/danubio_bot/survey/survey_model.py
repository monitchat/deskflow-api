from datetime import datetime

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Column, String, or_

from danubio_bot.dbms import Base, Session


class Survey(Base):
    __tablename__ = "survey"

    id = Column("id", BigInteger, primary_key=True)
    msisdn = Column("msisdn", String(32), nullable=False)
    pre_order_id = Column("pre_order_id", String(32), nullable=False)
    content = Column("content", JSON(), nullable=False)
    status = Column("status", String(32), nullable=False)
    updated_at = Column(
        "updated_at",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
    )

    def __init__(self, msisdn, pre_order_id, content):
        self.msisdn = msisdn
        self.pre_order_id = pre_order_id
        self.content = content
        self.status = "idle"

    @classmethod
    def load(self, msisdn, pre_order_id):
        survey = None
        with Session() as session:
            survey = (
                session.query(Survey)
                .filter(Survey.pre_order_id == pre_order_id)
                .first()
            )

        return survey

    @classmethod
    def load_pending(self):
        survey = None
        with Session() as session:
            survey = (
                session.query(Survey).filter(Survey.status == "pending").all()
            )

        return survey

    @classmethod
    def is_there_msisdn_survey(self, msisdn):
        survey = None
        with Session() as session:
            survey = (
                session.query(Survey)
                .filter(Survey.msisdn == msisdn)
                .filter(
                    or_(
                        Survey.status == "pending",
                        Survey.status == "executing",
                    )
                )
                .first()
            )

        return survey

    def update(self, survey):
        with Session.begin() as session:
            srv = (
                session.query(Survey)
                .filter(Survey.pre_order_id == survey.pre_order_id)
                .first()
            )

            if srv:
                srv.content = survey.content
                srv.status = survey.status
                srv.updated_at = datetime.utcnow()
                survey = srv

            session.add(survey)
            return srv
