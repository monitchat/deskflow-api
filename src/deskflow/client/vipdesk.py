import requests
import structlog
from requests.auth import AuthBase
from requests.exceptions import HTTPError
from datetime import datetime, timedelta
import time

from deskflow.config import VIPDESK_API_BASE_URL, VIPDESK_PASSWORD, VIPDESK_USER

log = structlog.get_logger()


class Authentication(AuthBase):
    cookies = None
    last_session_time = None
    SESSION_TIMEOUT = timedelta(minutes=30)  # Reduzindo para 30 minutos
    MAX_RETRIES = 3

    def __call__(self, r):
        current_time = datetime.now()
        
        # Verifica se os cookies existem e se a sessão não expirou
        if (Authentication.cookies is None or 
            Authentication.last_session_time is None or 
            current_time - Authentication.last_session_time > self.SESSION_TIMEOUT):
            
            log.info("Session expired or not exists, creating new session")
            Authentication.cookies = self._create_session_with_retry()
            Authentication.last_session_time = current_time
        
        log.info(f"Current cookies before request: {Authentication.cookies}")
        log.info(f"Session age: {current_time - Authentication.last_session_time if Authentication.last_session_time else 'New session'}")
        
        # Adiciona os cookies no header
        if Authentication.cookies:
            cookie_string = '; '.join([f'{key}={value}' for key, value in Authentication.cookies.items()])
            r.headers['Cookie'] = cookie_string
        
        log.info(f"Request headers after adding cookies: {dict(r.headers)}")
        
        r.hooks['response'] = [self.handle_unauthorized]
        return r

    def _create_session_with_retry(self):
        """Tenta criar uma sessão com retry em caso de falha"""
        for attempt in range(self.MAX_RETRIES):
            try:
                cookies = create_session()
                if cookies:
                    return cookies
            except Exception as e:
                log.error(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        raise Exception("Failed to create session after multiple attempts")

    def handle_unauthorized(self, response, *args, **kwargs):
        log.info(f"handle_unauthorized response: {response.status_code}")
        log.info(f"handle_unauthorized response text: {response.text}")
        log.info(f"handle_unauthorized response headers: {dict(response.headers)}")
        
        if response.status_code == 401 or (response.status_code == 200 and '"status": "3"' in response.text):
            log.info("Unauthorized response detected, refreshing session")
            try:
                # Força uma nova sessão
                Authentication.cookies = None
                Authentication.last_session_time = None
                
                # Criar nova requisição com os mesmos parâmetros
                session = requests.Session()
                new_response = session.request(
                    method=response.request.method,
                    url=response.request.url,
                    headers={
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    json=response.request.json,
                    auth=self,
                    timeout=30
                )
                
                log.info(f"Retry response status: {new_response.status_code}")
                log.info(f"Retry response headers: {dict(new_response.headers)}")
                log.info(f"Retry response text: {new_response.text}")
                return new_response
                
            except Exception as e:
                log.error(f"Error during session refresh: {str(e)}", exc_info=True)
                raise
        return response


def create_session():
    log.info("Creating new session")
    url = f"{VIPDESK_API_BASE_URL}?serviceName=MobileLoginSP.login&outputType=json"
    
    data = {
        "serviceName": "MobileLoginSP.login",
        "requestBody": {
            "NOMUSU": {"$": VIPDESK_USER},
            "INTERNO": {"$": VIPDESK_PASSWORD},
            "KEEPCONNECTED": {"$": "S"}
        }
    }

    try:
        log.info(f"Sending login request to: {url}")
        resp = requests.post(url=url, json=data, verify=False)
        log.info(f"Login response status: {resp.status_code}")
        log.info(f"Login response headers: {dict(resp.headers)}")
        log.info(f"Login response text: {resp.text}")
        
        resp.raise_for_status()
        cookies = resp.cookies.get_dict()
        log.info(f"Session created successfully with cookies: {cookies}")
        return cookies
    except Exception as e:
        log.error(f"Error creating session: {str(e)}")
        raise



def update_parceiro(codparc: str, alert: str):
    url = f"{VIPDESK_API_BASE_URL}?serviceName=DatasetSP.save&outputType=json"

    data = {
        "serviceName": "DatasetSP.save",
        "requestBody": {
            "entityName": "Parceiro",
            "standAlone": False,
            "fields": [
                "AD_RECALERT"
            ],
            "records": [
                {
                    "pk": {
                        "CODPARC": codparc
                    },
                    "values": {
                        "0": alert
                    }
                }
            ]
        }
    }

    resp = requests.post(url=url, json=data, verify=False, auth=Authentication())
    resp.raise_for_status()
    return resp.cookies.get_dict()


def get_partner(phone: str):
    data = {
        "serviceName": "CRUDServiceProvider.loadView",
        "requestBody": {
            "query": {
                "viewName": "AD_MTCPAR",
                "where": {
                    "$": f"CODPARC = DAM_FNC_BUSCA_PARC_FONE('{phone}') AND ROWNUM = 1"
                },
                "fields": {
                    "field": [
                        {"$": "CODPARC"},
                        {"$": "CODCTT" },
                        {"$": "NOMEPARC"},
                        {"$": "TELEFONE"},
                        {"$": "FAX" },
                        {"$": "CPF"},
                        {"$": "EMAIL" },
                        {"$": "NOMECTT"},
                        {"$": "CPFCTT"},
                        {"$": "TELCTT" },
                        {"$": "FAXCTT" },
                        {"$": "EMAILCTT" },
                        {"$": "TIPO" },
                        {"$": "ENDERECO"}
                    ]
                }
            }
        }
    }
    log.info(f"get_partner data: {data}")
    try:
        resp = requests.get(
            f"{VIPDESK_API_BASE_URL}?serviceName=CRUDServiceProvider.loadView&outputType=json",
            headers={"Content-Type": "application/json"},
            timeout=30,
            json=data,
            auth=Authentication()
        )
        log.info(f"get_partner response status: {resp.status_code}")
        log.info(f"get_partner response headers: {dict(resp.headers)}")
        log.info(f"get_partner response cookies: {dict(resp.cookies)}")
        log.info(f"get_partner response text: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.error(f"Error in get_partner: {str(e)}", exc_info=True)
        raise


def get_client(cpf: str, codparc: str):
    data = {
        "serviceName": "CRUDServiceProvider.loadView",
        "requestBody": {
            "query": {
                "viewName": "AD_MTCPAR",
                "where": {
                    "$": f"""CODPARC = '{codparc}' AND CODCTT = (SELECT CODCTT FROM AD_MTCPAR WHERE DAM_FORMATA_CPF_CNPJ(CPFCTT) = DAM_FORMATA_CPF_CNPJ('{cpf}') AND CODPARC = '{codparc}' AND ROWNUM = 1)"""
                },
                "fields": {
                    "field": [
                        {"$": "CODPARC"},
                        {"$": "CODCTT" },
                        {"$": "NOMEPARC"},
                        {"$": "TELEFONE"},
                        {"$": "FAX" },
                        {"$": "CPF"},
                        {"$": "EMAIL" },
                        {"$": "NOMECTT"},
                        {"$": "CPFCTT"},
                        {"$": "TELCTT" },
                        {"$": "FAXCTT" },
                        {"$": "EMAILCTT" },
                        {"$": "TIPO" },
                        {"$": "ENDERECO"}
                    ]
                }
            }
        }
    }

    log.info(f"get_client data: {data}")
    resp = requests.get(
        f"{VIPDESK_API_BASE_URL}?serviceName=CRUDServiceProvider.loadView&outputType=json",
        headers={"Content-Type": "application/json"},
        timeout=30,
        json=data,
        auth=Authentication()
    )

    log.info(f"get_client response status: {resp.status_code}")
    log.info(f"get_client response headers: {dict(resp.headers)}")
    log.info(f"get_client response cookies: {dict(resp.cookies)}")
    log.info(f"get_client response text: {resp.text}")
    
    resp.raise_for_status()
    return resp.json()


def get_products(codigo: str):

    data = {
        "serviceName": "CRUDServiceProvider.loadView",
        "requestBody": {
            "query": {
                "viewName": "AD_MTCVEN",
                "where": {
                    "$": f"CODPARC = '{codigo}'"
                },
                "fields": {
                    "field": [
                        {"$": "NUNOTA"},
                        {"$": "SEQUENCIA" },
                        {"$": "CODPARC"},
                        {"$": "QTDNEG"},
                        {"$": "DTENTREGA" },
                        {"$": "DHEMISSAO"},
                        {"$": "STATUS" },
                        {"$": "CODPROD" },
                        {"$": "DESCRPROD" }
                    ]
                }
            }
        }
    }

    resp = requests.get(
        f"{VIPDESK_API_BASE_URL}?serviceName=CRUDServiceProvider.loadView&outputType=json",
        headers={"Content-Type": "application/json"},
        timeout=30,
        json=data,
        auth=Authentication()
    )
    log.info(f"get_products resp: {resp.json()}")
    resp.raise_for_status()
    return resp.json()


def get_services(codigo: str):

    data = {
        "serviceName": "CRUDServiceProvider.loadView",
        "requestBody": {
            "query": {
                "viewName": "AD_MTCSRV",
                "where": {
                    "$": f"CODPARC = '{codigo}'"
                },
                "fields": {
                    "field": [
                        {"$": "PREPEDIDO"},
                        {"$": "SEQPROD" },
                        {"$": "CODEMPNEGOC"},
                        {"$": "FANTABREV"},
                        {"$": "NFSE" },
                        {"$": "SEQUENCIA"},
                        {"$": "SEQNFS" },
                        {"$": "CODSERV" },
                        {"$": "SERVICO" },
                        {"$": "TPSERV" },
                        {"$": "CODPROD" },
                        {"$": "DESCRPROD" },
                        {"$": "CODPARC" },
                        {"$": "NUNOTA" },
                        {"$": "QTDNEG" },
                        {"$": "CODTIPOPER" },
                        {"$": "NUMOS" },
                        {"$": "NUNOTA" },
                        {"$": "NOMEPARC" },
                        {"$": "DTENTREGA" },
                        {"$": "ORDEMCARGA" },
                    ]
                }
            }
        }
    }

    resp = requests.get(
        f"{VIPDESK_API_BASE_URL}?serviceName=CRUDServiceProvider.loadView&outputType=json",
        headers={"Content-Type": "application/json"},
        timeout=30,
        json=data,
        auth=Authentication()
    )

    resp.raise_for_status()
    return resp.json()