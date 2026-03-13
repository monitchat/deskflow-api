import os

import pytz
from dotenv import load_dotenv

load_dotenv()
# https://flask.palletsprojects.com/en/2.0.x/config/#SECRET_KEY
SECRET_KEY = os.getenv("SECRET_KEY", "dev")

# https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    ("postgresql://deskflow:<SECRET>@172.17.0.1/deskflow"),
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://rabbitmq:5672")

# App env type
APP_ENV = os.getenv("APP_ENV", "development")

ID_DEPARTAMENTO_GOIABEIRAS = os.getenv("ID_DEPARTAMENTO_GOIABEIRAS", "1296")
ID_DEPARTAMENTO_GLORIA = os.getenv("ID_DEPARTAMENTO_GLORIA", "1296")
ID_DEPARTAMENTO_CAMPO_GRANDE = os.getenv("ID_DEPARTAMENTO_CAMPO_GRANDE", "1296")
ID_DEPARTAMENTO_CACHOEIRO = os.getenv("ID_DEPARTAMENTO_CACHOEIRO", "1296")
ID_DEPARTAMENTO_LARANJEIRAS = os.getenv("ID_DEPARTAMENTO_LARANJEIRAS", "1296")
ID_DEPARTAMENTO_VILA_VELHA = os.getenv("ID_DEPARTAMENTO_VILA_VELHA", "1296")
ID_DEPARTAMENTO_CREDIARIO = os.getenv("ID_DEPARTAMENTO_CREDIARIO", "1296")
ID_DEPARTAMENTO_SCUDO = os.getenv("ID_DEPARTAMENTO_SCUDO", "2286")
ID_DEPARTAMENTO_ASSISTENCIA_TECNICA = os.getenv("ID_DEPARTAMENTO_ASSISTENCIA_TECNICA", "1296")
ID_DEPARTAMENTO_SAC = os.getenv("ID_DEPARTAMENTO_SAC", "1296")

# Credentials
OMNICHAT_API_KEY = os.getenv("OMNICHAT_API_KEY", "")
OMNICHAT_API_SECRET = os.getenv("OMNICHAT_API_SECRET", "")

BUILD_TIME = "April 6th 22:08"

MONITCHAT_API_ACCESS_TOKEN = os.getenv(
    "MONITCHAT_API_ACCESS_TOKEN", "e6fc0034-9a45-4038-a3cf-14f9b99f8d02"
)
MONITCHAT_SENDER = os.getenv("MONITCHAT_SENDER", "15550793380")
MONITCHAT_BASE_URL = os.getenv(
    "MONITCHAT_BASE_URL", "https://api-dev2.monitchat.com/api/v1"
)

VIPDESK_BOLETO_BASE_URL = os.getenv(
    "VIPDESK_BOLETO_BASE_URL",
    "https://boletos.vipdesk.net.br/api",
)

VIPDESK_API_BASE_URL = os.getenv(
    "VIPDESK_API_BASE_URL",
    "http://vipdesk-prd.siac.tech/mge/service.sbr",
)

VIPDESK_COMPANY = os.getenv("VIPDESK_COMPANY", "04065234000178")

VIPDESK_PASSWORD = os.getenv("VIPDESK_PASSWORD", "")
VIPDESK_USER = os.getenv("VIPDESK_USER", "")

OPENAI_SECRET_KEY = os.getenv("OPENAI_SECRET_KEY", "")

JWT_SECRET = os.getenv("JWT_SECRET", "")

BRANCH_EXTRA_FIELD_ID = os.getenv("BRANCH_EXTRA_INPUT_ID", 170)

RESTART_CONVERSATION_KEYWORDS = [
    "sair",
    "tchau",
    "exit",
    "bye",
    "para",
    "pare",
    "parar",
    "desistência",
    "desistencia",
    "encerra",
    "encerrar",
    "encerr",
    "encer",
    "encerar",
    "tchau",
    "adeus",
    "sai",
    "desliga",
    "desligar",
    "stop",
    "desisti",
    "desistir",
    "desisto",
    "chega",
    "basta",
    "fechar",
    "pausa",
    "pausar",
    "interromper",
    "encera",
    "tchua",
    "xau",
    "bjs",
    "fui",
    "chega",
    "até logo",
    "ate logo",
]

STOP_KEYWORDS = ["stop", "out"]

POSITIVE_KEYWORDS = [
    "sim",
    "ok",
    "certo",
    "confirma",
    "blz",
    "isso",
    "yes",
    "claro",
    "ctza",
    "sim! isso mesmo",
    "isso ai",
    "oba! claro!",
    "sim, vamos continuar",
]
BACK_KEYWORDS = ["voltar", "corrigir", "back"]
NOTE_KEYWORDS = [str(i + 1) for i in range(0, 5)]

BRT_TIMEZONE = pytz.timezone("America/Sao_Paulo")

INACTIVE_CHAT_MESSAGES = [
    "Olá, está por aí? 🤩",
    "Oi! Quer continuar nossa conversa agora? 🤞",
    "Quando quiser continuar, estou por aqui! 😊",
    "Oi, você ainda está online? 🤗",
]

EMOJI_NUMBERS = {
    "0": "0️⃣",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
}
