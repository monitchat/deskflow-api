import datetime
import json
import re

from pycpfcnpj import cpfcnpj


class APIError(Exception):
    status_code = 500

    def __init__(self, code, message=None, details=None):
        super().__init__()
        self.code = code
        self.message = message
        self.details = details

    def to_dict(self):
        d = {
            "error": {
                "code": self.code,
            }
        }

        if self.message:
            d["error"]["message"] = self.message
        if self.details:
            d["error"]["details"] = self.details

        return d

    def __str__(self):
        return json.dumps(self.to_dict())


class BadRequestError(APIError):
    status_code = 400


class ProductNotFound(APIError):
    status_code = 400


def sanitize_msisdn(msisdn):
    if not msisdn.startswith("+"):
        return "+55" + msisdn
    return msisdn


def extract_firstname(fullname):
    f = fullname.split()[0]
    return f.capitalize()


def format_brl(value):
    return f"R${value:_.2f}".replace(".", ",").replace("_", ".")


def greeting_based_on_time():
    now = datetime.datetime.now().time()
    if now < datetime.time(12, 0):
        return "Bom dia!"
    elif now < datetime.time(18, 0):
        return "Boa tarde!"
    else:
        return "Boa noite!"


def validate_email(email: str):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    if re.match(pattern, email):
        return True
    else:
        return False


def validate_cpf(cpf: str):
    return cpfcnpj.validate(cpf), cpf


def validate_cnpj(cnpj: str):
    if len(cnpj) != 14:
        return validate_cpf(cnpj)

    return cpfcnpj.validate(cnpj), cnpj


def format_cpf(cpf: str) -> str:
    cpf = ''.join(filter(str.isdigit, cpf)) 
    if len(cpf) != 11:
        raise ValueError("CPF must contain exactly 11 digits")
    
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
