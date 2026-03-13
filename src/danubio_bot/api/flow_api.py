import structlog
import jwt
from flask import Blueprint, jsonify, request

from danubio_bot.models import flow as flow_model
from danubio_bot import config

log = structlog.get_logger()

# Flask blueprint para API de fluxos
api = Blueprint("flow_api", __name__, url_prefix="/api/v1/flows")


def get_user_info_from_token():
    """Extrai informações do usuário do token JWT no header Authorization e verifica assinatura"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            log.warning("Missing or invalid Authorization header")
            return None

        token = auth_header.replace('Bearer ', '')

        # Verifica se JWT_SECRET está configurado
        if not config.JWT_SECRET:
            log.error("JWT_SECRET not configured in environment")
            return None

        # Primeiro decodifica SEM verificar assinatura para pegar o payload
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})

            # Converte sub para string se existir e não for string
            if 'sub' in unverified and not isinstance(unverified['sub'], str):
                unverified['sub'] = str(unverified['sub'])

            log.info(f"Token payload keys: {list(unverified.keys())}")

        except Exception as e:
            log.warning(f"Error decoding unverified token: {e}")
            return None

        # Agora verifica apenas a assinatura
        try:
            unverified_header = jwt.get_unverified_header(token)
            algorithm = unverified_header.get('alg', 'HS256')

            # Verifica a assinatura manualmente
            jwt.decode(
                token,
                config.JWT_SECRET,
                algorithms=[algorithm],
                options={"verify_signature": True, "verify_exp": False}
            )

            log.info("Token signature verified successfully")

            # Valida manualmente a expiração se existir
            if 'exp' in unverified:
                import time
                if unverified['exp'] < time.time():
                    log.warning("Token has expired")
                    return None

        except jwt.InvalidSignatureError:
            log.warning("Invalid token signature")
            return None
        except jwt.DecodeError as e:
            log.warning(f"Token decode error: {e}")
            return None
        except Exception as e:
            log.warning(f"Unexpected token validation error: {e}", exc_info=True)
            return None

        # Usa o payload já decodificado (com sub convertido)
        return {
            'user_id': unverified.get('sub') or unverified.get('user_id') or unverified.get('id'),
            'email': unverified.get('email'),
            'name': unverified.get('name'),
            'company_id': unverified.get('company_id'),
            'role': unverified.get('role'),
            'roles': unverified.get('roles', []),
            'is_admin': unverified.get('is_admin', False),
            'is_manager': unverified.get('is_manager', False),
            'permissions': unverified.get('permissions', []),
        }
    except Exception as e:
        log.error(f"Unexpected error decoding token: {e}", exc_info=True)
        return None


def check_permission(required_permission):
    """Verifica se o usuário tem a permissão necessária"""
    user_info = get_user_info_from_token()

    if not user_info:
        return False, "Unauthorized - Invalid token"

    if not user_info.get('company_id'):
        return False, "Unauthorized - company_id not found in token"

    # Checa se é admin/superadmin por vários campos possíveis
    # Verifica campo 'is_admin' booleano
    if user_info.get('is_admin'):
        return True, user_info

    # Verifica campo 'role' (string)
    role = user_info.get('role')
    if role and isinstance(role, str) and role.lower() in ['admin', 'superadmin', 'owner']:
        return True, user_info

    # Verifica campo 'roles' (array)
    roles = user_info.get('roles', [])
    if isinstance(roles, list):
        roles_lower = [r.lower() if isinstance(r, str) else str(r).lower() for r in roles]
        if any(r in ['admin', 'superadmin', 'owner'] for r in roles_lower):
            return True, user_info

    # Verifica se tem a permissão específica
    permissions = user_info.get('permissions', [])
    if required_permission in permissions:
        return True, user_info

    return False, f"Forbidden - Missing permission: {required_permission}"


@api.route("", methods=["GET"])
def list_flows():
    """Lista todos os fluxos do usuário autenticado"""
    try:
        # Verifica permissão para listar flows
        has_permission, result = check_permission('flows.read')

        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        # Lista apenas flows da empresa do usuário
        flows = flow_model.list_flows(company_id=company_id)

        log.info(f"User {user_info['email']} (role: {user_info.get('role')}) listed {len(flows)} flows from company {company_id}")

        return jsonify(
            {
                "success": True,
                "data": [
                    {
                        "id": flow.id,
                        "name": flow.name,
                        "description": flow.description,
                        "is_active": flow.is_active,
                        "company_id": flow.company_id,
                        "created_at": flow.created_at.isoformat(),
                        "updated_at": flow.updated_at.isoformat(),
                    }
                    for flow in flows
                ],
            }
        ), 200
    except Exception as e:
        log.error(f"Error listing flows: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/<int:flow_id>", methods=["GET"])
def get_flow(flow_id):
    """Retorna um fluxo específico"""
    try:
        # Verifica permissão para ler flows
        has_permission, result = check_permission('flows.read')

        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        flow = flow_model.get_flow_by_id(flow_id)
        if not flow:
            return jsonify(
                {"success": False, "error": "Flow not found"}
            ), 404

        # Verifica se o flow pertence à empresa do usuário
        if flow.company_id != company_id:
            log.warning(f"User {user_info['email']} tried to access flow {flow_id} from another company")
            return jsonify(
                {"success": False, "error": "Forbidden - Flow belongs to another company"}
            ), 403

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": flow.id,
                    "name": flow.name,
                    "description": flow.description,
                    "data": flow.data,
                    "is_active": flow.is_active,
                    "company_id": flow.company_id,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                },
            }
        ), 200
    except Exception as e:
        log.error(f"Error getting flow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("", methods=["POST"])
def create_flow():
    """Cria um novo fluxo"""
    try:
        # Verifica permissão para criar flows
        has_permission, result = check_permission('flows.create')

        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        data = request.get_json()

        if not data.get("name"):
            return jsonify(
                {"success": False, "error": "Name is required"}
            ), 400

        flow_data = data.get("data", {"nodes": [], "edges": []})

        # Ignora company_id do frontend e usa sempre o do token
        flow = flow_model.create_flow(
            name=data["name"],
            description=data.get("description", ""),
            data=flow_data,
            is_active=data.get("is_active", False),
            company_id=company_id,  # Usa company_id do token JWT
        )

        log.info(f"User {user_info['email']} created flow {flow.id} in company {company_id}")

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": flow.id,
                    "name": flow.name,
                    "description": flow.description,
                    "data": flow.data,
                    "is_active": flow.is_active,
                    "company_id": flow.company_id,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                },
            }
        ), 201
    except Exception as e:
        log.error(f"Error creating flow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/<int:flow_id>", methods=["PUT"])
def update_flow(flow_id):
    """Atualiza um fluxo existente"""
    try:
        # Verifica permissão para atualizar flows
        has_permission, result = check_permission('flows.update')

        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        # Verifica se o flow existe e pertence à empresa do usuário
        existing_flow = flow_model.get_flow_by_id(flow_id)
        if not existing_flow:
            return jsonify(
                {"success": False, "error": "Flow not found"}
            ), 404

        if existing_flow.company_id != company_id:
            log.warning(f"User {user_info['email']} tried to update flow {flow_id} from another company")
            return jsonify(
                {"success": False, "error": "Forbidden - Flow belongs to another company"}
            ), 403

        data = request.get_json()

        flow = flow_model.update_flow(
            flow_id=flow_id,
            name=data.get("name"),
            description=data.get("description"),
            data=data.get("data"),
            is_active=data.get("is_active"),
        )

        log.info(f"User {user_info['email']} updated flow {flow_id}")

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": flow.id,
                    "name": flow.name,
                    "description": flow.description,
                    "data": flow.data,
                    "is_active": flow.is_active,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                },
            }
        ), 200
    except Exception as e:
        log.error(f"Error updating flow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/<int:flow_id>", methods=["DELETE"])
def delete_flow(flow_id):
    """Deleta um fluxo"""
    try:
        # Verifica permissão para deletar flows
        has_permission, result = check_permission('flows.delete')

        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        # Verifica se o flow existe e pertence à empresa do usuário
        existing_flow = flow_model.get_flow_by_id(flow_id)
        if not existing_flow:
            return jsonify(
                {"success": False, "error": "Flow not found"}
            ), 404

        if existing_flow.company_id != company_id:
            log.warning(f"User {user_info['email']} tried to delete flow {flow_id} from another company")
            return jsonify(
                {"success": False, "error": "Forbidden - Flow belongs to another company"}
            ), 403

        success = flow_model.delete_flow(flow_id)

        log.info(f"User {user_info['email']} deleted flow {flow_id}")

        return jsonify({"success": True}), 200
    except Exception as e:
        log.error(f"Error deleting flow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/<int:flow_id>/secrets", methods=["GET"])
def get_flow_secrets(flow_id):
    """Retorna os segredos de um fluxo (valores mascarados)"""
    try:
        has_permission, result = check_permission('flows.read')
        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        flow = flow_model.get_flow_by_id(flow_id)
        if not flow:
            return jsonify({"success": False, "error": "Flow not found"}), 404

        if flow.company_id != company_id:
            return jsonify({"success": False, "error": "Forbidden"}), 403

        secrets = flow.secrets or {}
        # Mascara os valores - mostra apenas os primeiros 4 chars
        masked = {}
        for key, value in secrets.items():
            val = str(value)
            if len(val) > 4:
                masked[key] = val[:4] + "*" * (len(val) - 4)
            else:
                masked[key] = "****"

        return jsonify({
            "success": True,
            "data": {
                "secrets": masked,
                "keys": list(secrets.keys()),
            }
        }), 200
    except Exception as e:
        log.error(f"Error getting flow secrets: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/<int:flow_id>/secrets", methods=["PUT"])
def update_flow_secrets(flow_id):
    """
    Atualiza segredos de um fluxo.

    Body: {"secrets": {"SIENGE_AUTH_TOKEN": "Basic xxx", "API_KEY": "abc123"}}
    """
    try:
        has_permission, result = check_permission('flows.update')
        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        flow = flow_model.get_flow_by_id(flow_id)
        if not flow:
            return jsonify({"success": False, "error": "Flow not found"}), 404

        if flow.company_id != company_id:
            return jsonify({"success": False, "error": "Forbidden"}), 403

        data = request.get_json()
        secrets = data.get("secrets", {})

        if not isinstance(secrets, dict):
            return jsonify({"success": False, "error": "secrets must be an object"}), 400

        updated_flow = flow_model.update_flow_secrets(flow_id, secrets)

        log.info(f"User {user_info['email']} updated secrets for flow {flow_id}: {list(secrets.keys())}")

        return jsonify({
            "success": True,
            "data": {"keys": list((updated_flow.secrets or {}).keys())}
        }), 200
    except Exception as e:
        log.error(f"Error updating flow secrets: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/<int:flow_id>/secrets/<key>", methods=["DELETE"])
def delete_flow_secret(flow_id, key):
    """Remove um segredo específico de um fluxo"""
    try:
        has_permission, result = check_permission('flows.update')
        if not has_permission:
            return jsonify({"success": False, "error": result}), 403

        user_info = result
        company_id = user_info['company_id']

        flow = flow_model.get_flow_by_id(flow_id)
        if not flow:
            return jsonify({"success": False, "error": "Flow not found"}), 404

        if flow.company_id != company_id:
            return jsonify({"success": False, "error": "Forbidden"}), 403

        flow_model.delete_flow_secret(flow_id, key)

        log.info(f"User {user_info['email']} deleted secret '{key}' from flow {flow_id}")

        return jsonify({"success": True}), 200
    except Exception as e:
        log.error(f"Error deleting flow secret: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/active", methods=["GET"])
def get_active_flow():
    """Retorna o fluxo ativo"""
    try:
        flow = flow_model.get_active_flow()

        if not flow:
            return jsonify(
                {"success": False, "error": "No active flow found"}
            ), 404

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": flow.id,
                    "name": flow.name,
                    "description": flow.description,
                    "data": flow.data,
                    "is_active": flow.is_active,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                },
            }
        ), 200
    except Exception as e:
        log.error(f"Error getting active flow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/debug/context/<msisdn>", methods=["GET"])
def debug_context(msisdn):
    """Debug: Retorna o contexto de um usuário"""
    try:
        from danubio_bot import context
        from flask import request

        # Flow ID via query parameter ou usa o ativo
        flow_id = request.args.get("flow_id", type=int)
        if not flow_id:
            from danubio_bot.models import flow as flow_model
            active_flow = flow_model.get_active_flow()
            flow_id = active_flow.id if active_flow else 1

        ctx = context.load(msisdn=msisdn, flow_id=flow_id)

        return jsonify(
            {
                "success": True,
                "data": {
                    "msisdn": ctx.msisdn,
                    "context": ctx.data,
                    "updated_at": ctx.updated_at.isoformat() if ctx.updated_at else None,
                },
            }
        ), 200
    except Exception as e:
        log.error(f"Error getting context: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/debug/context", methods=["GET"])
def list_contexts():
    """Debug: Lista todos os contextos ativos"""
    try:
        from danubio_bot import context as context_module
        from danubio_bot.dbms import Session
        from danubio_bot.context import Context

        with Session() as session:
            contexts = session.query(Context).order_by(
                Context.updated_at.desc()
            ).limit(20).all()

            return jsonify(
                {
                    "success": True,
                    "data": [
                        {
                            "msisdn": ctx.msisdn,
                            "stage": ctx.data.get("stage"),
                            "updated_at": ctx.updated_at.isoformat() if ctx.updated_at else None,
                            "preview": {
                                "cpf": ctx.data.get("cpf"),
                                "codparc": ctx.data.get("codparc"),
                                "nomeparc": ctx.data.get("nomeparc"),
                                "is_logged_in": ctx.data.get("is_logged_in"),
                            }
                        }
                        for ctx in contexts
                    ],
                }
            ), 200
    except Exception as e:
        log.error(f"Error listing contexts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def extract_context_fields(data, prefix=""):
    """
    Extrai recursivamente todos os campos de um objeto JSON

    Args:
        data: Dicionário ou valor a ser processado
        prefix: Prefixo do caminho (ex: "customer.")

    Returns:
        Lista de tuplas (caminho_completo, valor_exemplo)
    """
    fields = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}{key}" if prefix else key

            if isinstance(value, (dict, list)):
                # Adiciona o campo complexo
                fields.append((current_path, type(value).__name__))
                # Recursivamente processa subcampos
                fields.extend(extract_context_fields(value, f"{current_path}."))
            else:
                # Campo simples - adiciona com valor de exemplo
                fields.append((current_path, value))

    elif isinstance(data, list) and len(data) > 0:
        # Se for lista, processa o primeiro item como exemplo
        fields.extend(extract_context_fields(data[0], f"{prefix}[0]."))

    return fields


@api.route("/context/fields", methods=["GET"])
def get_context_fields():
    """
    Retorna todos os campos disponíveis no contexto

    Busca um contexto de exemplo (o mais recente) e extrai
    todos os campos disponíveis para uso em ${{campo}}
    """
    try:
        from danubio_bot.dbms import Session
        from danubio_bot.context import Context

        # Busca o contexto mais recente como exemplo
        with Session() as session:
            contexts = session.query(Context).order_by(
                Context.updated_at.desc()
            ).limit(1).all()

            if not contexts:
                return jsonify({
                    "success": True,
                    "data": {
                        "fields": [],
                        "message": "Nenhum contexto encontrado. Inicie uma conversa primeiro."
                    }
                }), 200

            ctx = contexts[0]
            fields = extract_context_fields(ctx.data)

            # Formata para retornar
            formatted_fields = [
                {
                    "path": field[0],
                    "example": str(field[1])[:100] if field[1] is not None else "null",
                    "usage": f"${{{{{field[0]}}}}}"
                }
                for field in fields
                # Permite campos de API (_api*, _raw*) mas ignora outros campos privados
                if not field[0].startswith("_") or field[0].startswith("_api") or field[0].startswith("_raw")
            ]

            return jsonify({
                "success": True,
                "data": {
                    "fields": formatted_fields,
                    "total": len(formatted_fields),
                    "source_msisdn": ctx.msisdn
                }
            }), 200

    except Exception as e:
        log.error(f"Error getting context fields: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/sessions", methods=["GET"])
def get_active_sessions():
    """
    Lista todas as sessões ativas (msisdns com contexto)

    Query params:
    - limit: número máximo de sessões (default: 50)
    """
    try:
        from danubio_bot.dbms import Session
        from danubio_bot.context import Context

        limit = request.args.get('limit', 50, type=int)

        with Session() as session:
            contexts = session.query(Context).order_by(
                Context.updated_at.desc()
            ).limit(limit).all()

            sessions = [
                {
                    "msisdn": ctx.msisdn,
                    "stage": ctx.data.get("stage"),
                    "updated_at": ctx.updated_at.isoformat() if ctx.updated_at else None,
                    "preview": {
                        "nomeparc": ctx.data.get("nomeparc"),
                        "nomectt": ctx.data.get("nomectt"),
                        "cpf": ctx.data.get("cpf"),
                        "codparc": ctx.data.get("codparc"),
                    }
                }
                for ctx in contexts
            ]

            return jsonify({
                "success": True,
                "data": {
                    "sessions": sessions,
                    "total": len(sessions)
                }
            }), 200

    except Exception as e:
        log.error(f"Error getting active sessions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/sessions/<msisdn>/context", methods=["GET"])
def get_session_context(msisdn):
    """
    Retorna o contexto completo de uma sessão específica
    """
    try:
        from danubio_bot import context
        from flask import request

        # Flow ID via query parameter ou usa o ativo
        flow_id = request.args.get("flow_id", type=int)
        if not flow_id:
            from danubio_bot.models import flow as flow_model
            active_flow = flow_model.get_active_flow()
            flow_id = active_flow.id if active_flow else 1

        ctx = context.load(msisdn=msisdn, flow_id=flow_id)

        return jsonify({
            "success": True,
            "data": {
                "msisdn": ctx.msisdn,
                "context": ctx.data,
                "updated_at": ctx.updated_at.isoformat() if ctx.updated_at else None,
                "created_at": ctx.created_at.isoformat() if ctx.created_at else None,
            }
        }), 200

    except Exception as e:
        log.error(f"Error getting session context: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/nodes/<node_id>/last-result", methods=["GET"])
def get_node_last_result(node_id):
    """
    Busca o resultado mais recente de uma execução de um nó API em qualquer sessão

    Útil para mostrar campos disponíveis ao editar um nó set_context
    """
    try:
        from danubio_bot.dbms import Session
        from danubio_bot.context import Context
        from sqlalchemy import text

        result_key = f"_api_result_{node_id}"

        with Session() as session:
            # Busca contextos que tenham esse resultado, ordenado por mais recente
            query = text("""
                SELECT msisdn, data, updated_at
                FROM contexts
                WHERE data::text LIKE :pattern
                ORDER BY updated_at DESC
                LIMIT 1
            """)

            result = session.execute(
                query,
                {"pattern": f"%{result_key}%"}
            ).fetchone()

            if not result:
                return jsonify({
                    "success": False,
                    "error": "No execution result found for this node",
                    "message": "Execute o fluxo ao menos uma vez para ver os campos disponíveis"
                }), 404

            # Carrega o contexto completo
            ctx = session.query(Context).filter_by(msisdn=result[0]).first()

            if not ctx or result_key not in ctx.data:
                return jsonify({
                    "success": False,
                    "error": "Result not found in context"
                }), 404

            node_result = ctx.data[result_key]

            # Extrai os campos recursivamente
            fields = extract_context_fields(node_result)

            # Mostra TODOS os campos, incluindo os que começam com _
            formatted_fields = [
                {
                    "field": field[0],
                    "description": f"Tipo: {type(field[1]).__name__}",
                    "example": str(field[1])[:100] if field[1] is not None else "null"
                }
                for field in fields
            ]

            return jsonify({
                "success": True,
                "data": {
                    "node_id": node_id,
                    "fields": formatted_fields,
                    "total": len(formatted_fields),
                    "executed_at": result[2].isoformat() if result[2] else None,
                    "from_session": result[0],
                    "raw_result": node_result,  # Resultado completo para debug
                    "has_data": len(formatted_fields) > 0
                }
            }), 200

    except Exception as e:
        log.error(f"Error getting node last result: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/test-api-request", methods=["POST"])
def test_api_request():
    """
    Testa uma requisição HTTP sem salvar no contexto

    Body esperado:
    {
        "method": "GET",
        "url": "https://api.exemplo.com/endpoint",
        "query_params": [{"key": "page", "value": "1"}],
        "headers": [{"key": "Authorization", "value": "Bearer token"}],
        "body": "{}",
        "msisdn": "5511999999999"  // opcional, para testar substituição de variáveis
    }
    """
    try:
        import requests
        import json as json_lib
        from danubio_bot.flow_interpreter import replace_context_variables

        data = request.json
        method = data.get("method", "GET").upper()
        url = data.get("url", "")
        query_params = data.get("query_params", [])
        headers_list = data.get("headers", [])
        body = data.get("body", "")
        msisdn = data.get("msisdn")  # Opcional
        test_flow_id = data.get("flow_id")  # Opcional, para resolver secrets

        # Carrega secrets do fluxo se flow_id foi fornecido
        secrets = None
        if test_flow_id:
            secrets = flow_model.get_flow_secrets(test_flow_id)

        # Sanitiza URL removendo prefixos comuns (caso usuário tenha copiado do resultado)
        url = url.strip()
        if url.startswith("URL:"):
            url = url[4:].strip()
        if url.startswith("Final URL:"):
            url = url[10:].strip()

        log.info(f"🧪 TEST API REQUEST - Method: {method}, URL: {url}")

        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400

        # Substitui variáveis do contexto na URL (se msisdn foi fornecido)
        final_url = url
        if msisdn:
            final_url = replace_context_variables(url, msisdn, test_flow_id, secrets)

        log.info(f"🔗 Final URL: {final_url}")

        # Monta query params
        params = {}
        for param in query_params:
            key = param.get("key", "").strip()
            value = param.get("value", "")
            if key:
                if msisdn:
                    value = replace_context_variables(str(value), msisdn, test_flow_id, secrets)
                params[key] = value

        # Monta headers
        request_headers = {}
        for header in headers_list:
            key = header.get("key", "").strip()
            value = header.get("value", "")
            if key:
                if msisdn:
                    value = replace_context_variables(str(value), msisdn, test_flow_id, secrets)
                else:
                    # Mesmo sem msisdn, resolve secrets
                    value = replace_context_variables(str(value), "", test_flow_id, secrets)
                request_headers[key] = value

        # Monta body (se aplicável)
        request_body = None
        if method in ["POST", "PUT", "PATCH"] and body:
            body_with_vars = body
            if msisdn:
                body_with_vars = replace_context_variables(body, msisdn, test_flow_id, secrets)

            try:
                request_body = json_lib.loads(body_with_vars)
            except json_lib.JSONDecodeError:
                request_body = body_with_vars

        # Faz a requisição
        start_time = None
        response = None

        try:
            import time
            start_time = time.time()

            if method == "GET":
                response = requests.get(
                    final_url,
                    params=params,
                    headers=request_headers,
                    timeout=30
                )
            elif method == "POST":
                response = requests.post(
                    final_url,
                    params=params,
                    headers=request_headers,
                    json=request_body if isinstance(request_body, dict) else None,
                    data=request_body if not isinstance(request_body, dict) else None,
                    timeout=30
                )
            elif method == "PUT":
                response = requests.put(
                    final_url,
                    params=params,
                    headers=request_headers,
                    json=request_body if isinstance(request_body, dict) else None,
                    data=request_body if not isinstance(request_body, dict) else None,
                    timeout=30
                )
            elif method == "DELETE":
                response = requests.delete(
                    final_url,
                    params=params,
                    headers=request_headers,
                    timeout=30
                )
            elif method == "PATCH":
                response = requests.patch(
                    final_url,
                    params=params,
                    headers=request_headers,
                    json=request_body if isinstance(request_body, dict) else None,
                    data=request_body if not isinstance(request_body, dict) else None,
                    timeout=30
                )
            else:
                return jsonify({
                    "success": False,
                    "error": f"Unsupported method: {method}"
                }), 400

            elapsed_time = time.time() - start_time if start_time else 0

            # Tenta fazer parse da resposta como JSON
            response_data = None
            try:
                response_data = response.json()
            except:
                response_data = response.text

            log.info(f"✅ Test request completed - Status: {response.status_code}, Time: {elapsed_time:.2f}s")

            return jsonify({
                "success": True,
                "data": {
                    "status_code": response.status_code,
                    "ok": response.ok,
                    "response": response_data,
                    "headers": dict(response.headers),
                    "elapsed_time": round(elapsed_time, 2),
                    "request": {
                        "method": method,
                        "url": final_url,
                        "params": params,
                        "headers": request_headers,
                        "body": request_body
                    }
                }
            }), 200

        except requests.exceptions.Timeout:
            log.error(f"⏱️ Request timeout for URL: {final_url}")
            return jsonify({
                "success": False,
                "error": "Request timeout (30s)",
                "request": {
                    "method": method,
                    "url": final_url,
                    "params": params,
                    "headers": request_headers
                }
            }), 408

        except requests.exceptions.RequestException as e:
            log.error(f"❌ Request error: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "request": {
                    "method": method,
                    "url": final_url,
                    "params": params,
                    "headers": request_headers
                }
            }), 500

    except Exception as e:
        log.error(f"❌ Unexpected error in test API request: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route("/playground/message", methods=["POST"])
def playground_message():
    """
    Processa uma mensagem no playground, executando o fluxo.

    Body: {
        "flow_id": 1,
        "msisdn": "5511999999999",
        "text": "mensagem do usuário",
        "button_id": "btn_1"  // opcional, para cliques em botões
    }
    """
    try:
        from danubio_bot.flow_interpreter import FlowInterpreter
        from danubio_bot import context

        data = request.json
        flow_id = data.get("flow_id")
        msisdn = data.get("msisdn")
        text = data.get("text", "")
        button_id = data.get("button_id")  # Para cliques em botões/listas

        if not flow_id or not msisdn:
            return jsonify({
                "success": False,
                "error": "flow_id and msisdn are required"
            }), 400

        log.info(f"🎮 PLAYGROUND - Flow: {flow_id}, User: {msisdn}, Text: {text}")

        # Busca o fluxo
        flow = flow_model.get_flow_by_id(flow_id)
        if not flow:
            return jsonify({
                "success": False,
                "error": "Flow not found"
            }), 404

        # Se for clique em botão, usar o button_id como texto
        input_text = button_id if button_id else text

        # Cria o interpretador do fluxo
        interpreter = FlowInterpreter(flow.data, flow.id, flow.secrets)

        # Busca contexto atual do usuário
        ctx = context.load(msisdn, flow_id)
        current_stage = ctx.data.get("stage") if ctx else None

        log.info(f"🎮 Current stage from context: {current_stage}")

        # Se não tem stage, começa do início do fluxo
        if not current_stage:
            current_stage = interpreter.get_start_node()
            log.info(f"🎮 Starting from initial node: {current_stage}")

            # Verifica se o nó existe no fluxo
            if not interpreter.get_node(current_stage):
                error_msg = f"Initial node '{current_stage}' not found in flow"
                log.error(f"❌ {error_msg}")
                return jsonify({
                    "success": False,
                    "error": error_msg
                }), 500

        log.info(f"🎮 Executing node: {current_stage}")

        # Executa o nó
        replies = interpreter.execute_node(
            node_id=current_stage,
            msisdn=msisdn,
            text=input_text
        )

        log.info(f"🎮 Replies count: {len(replies)}")

        # Busca contexto atualizado após execução
        ctx = context.load(msisdn, flow_id)
        context_data = ctx.data if ctx else {}

        return jsonify({
            "success": True,
            "data": {
                "replies": replies,
                "context": context_data
            }
        }), 200

    except Exception as e:
        log.error(f"❌ Error in playground message: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route("/playground/session", methods=["POST"])
def create_playground_session():
    """
    Cria uma nova sessão de teste no playground.

    Body: {
        "msisdn": "5511999999999",  // opcional, gera automaticamente se não fornecido
        "flow_id": 1  // opcional, usa flow ativo se não fornecido
    }
    """
    try:
        import random
        from danubio_bot import context

        data = request.json or {}
        msisdn = data.get("msisdn")

        # Determina flow_id (query param > body > flow ativo)
        flow_id = request.args.get("flow_id", type=int) or data.get("flow_id")
        if not flow_id:
            from danubio_bot.models import flow as flow_model
            active_flow = flow_model.get_active_flow()
            flow_id = active_flow.id if active_flow else 1

        # Gera msisdn aleatório se não fornecido
        if not msisdn:
            msisdn = f"55119{random.randint(10000000, 99999999)}"

        # Deleta contexto antigo se existir (limpa qualquer stage legado)
        try:
            context.delete(msisdn, flow_id)
            log.info(f"🎮 Deleted old context for: {msisdn}")
        except:
            pass

        # Cria contexto inicial (sem stage definido - será determinado pelo fluxo)
        context.merge(msisdn=msisdn, flow_id=flow_id, data={
            "playground": True,
            "created_at": __import__('datetime').datetime.now().isoformat()
        })

        log.info(f"🎮 Created playground session: {msisdn} for flow_id: {flow_id} (no stage defined)")

        # Verifica o que foi criado
        ctx = context.load(msisdn, flow_id)
        log.info(f"🎮 Context after creation: {ctx.data if ctx else None}")

        return jsonify({
            "success": True,
            "data": {
                "msisdn": msisdn
            }
        }), 201

    except Exception as e:
        log.error(f"❌ Error creating playground session: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route("/playground/session/<msisdn>", methods=["DELETE"])
def delete_playground_session(msisdn):
    """Deleta uma sessão do playground"""
    try:
        from danubio_bot import context
        from flask import request

        # Flow ID via query parameter ou usa o ativo
        flow_id = request.args.get("flow_id", type=int)
        if not flow_id:
            from danubio_bot.models import flow as flow_model
            active_flow = flow_model.get_active_flow()
            flow_id = active_flow.id if active_flow else 1

        context.delete(msisdn, flow_id)
        log.info(f"🎮 Deleted playground session: {msisdn}")

        return jsonify({
            "success": True,
            "message": "Session deleted"
        }), 200

    except Exception as e:
        log.error(f"❌ Error deleting playground session: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route("/playground/pending/<msisdn>", methods=["GET"])
def get_pending_messages(msisdn):
    """
    Busca mensagens pendentes para o playground.
    Usado para receber mensagens assíncronas (como as de nós com delay).
    """
    try:
        from danubio_bot import context
        from flask import request

        # Flow ID via query parameter ou usa o ativo
        flow_id = request.args.get("flow_id", type=int)
        if not flow_id:
            from danubio_bot.models import flow as flow_model
            active_flow = flow_model.get_active_flow()
            flow_id = active_flow.id if active_flow else 1

        # Busca contexto
        ctx = context.load(msisdn, flow_id)
        pending_messages = ctx.data.get("pending_messages", []) if ctx else []

        # Limpa as mensagens pendentes do contexto
        if pending_messages:
            context.merge(msisdn=msisdn, flow_id=flow_id, data={"pending_messages": []})
            log.info(f"🎮 Retrieved {len(pending_messages)} pending messages for {msisdn}")

        return jsonify({
            "success": True,
            "data": {
                "messages": pending_messages
            }
        }), 200

    except Exception as e:
        log.error(f"❌ Error getting pending messages: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
