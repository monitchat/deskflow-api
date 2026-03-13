from sqlalchemy import JSON, BigInteger, Column
from tenacity import retry, stop_after_attempt

from danubio_bot.dbms import Base, Session


class Setting(Base):
    __tablename__ = "settings"

    id = Column("id", BigInteger, primary_key=True)
    data = Column("data", JSON(), nullable=False)

    def __init__(self, data):
        self.data = data


def load() -> Setting:
    with Session.begin() as session:
        setting = session.query(Setting).first()

        if not setting:
            setting = Setting({"stages": []})
            session.add(setting)
        return setting


def update(setting) -> Setting:
    with Session.begin() as session:
        curr_setting = session.query(Setting).first()
        if curr_setting:
            curr_setting.data = setting.data
        session.add(setting)
        return setting


@retry(stop=stop_after_attempt(3))
def merge(data) -> Setting:
    setting = load()
    setting.data.update(data)
    with Session.begin() as session:
        curr_setting = session.query(Setting).first()
        if curr_setting:
            curr_setting.data = setting.data
            setting = curr_setting
        session.add(setting)
        return setting


def get_value(string_path: str):
    setting = load()
    value = setting.data
    path = string_path.split(".")

    for object in path:
        if object.isdigit():
            indice = int(object)
            value = value[indice]
        else:
            value = value.get(object, {})

        if value is None:
            return None

    return value


def get_values(properties: list) -> list:
    setting = load()
    values = {}

    for property in properties:
        values[property] = setting.data.get(property, None)

    return values


def get_stage(stage: str) -> dict:
    return get_value(f"""stages.{stage}""")
