# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Client Bot is a WhatsApp chatbot built with Flask and Celery that handles customer service conversations for Client (furniture retailer). The bot uses a state machine pattern to manage conversation flows, integrates with external APIs (Monitchat for WhatsApp, Sankhya ERP for customer data), and processes messages asynchronously through RabbitMQ.

## Recent Updates (2025)

**Flow Builder Interface Improvements:**
- ✅ Redesign completo da página de login com gradiente moderno
- ✅ Adição da logo do MonitChat no header e login
- ✅ Integração com MonitChat API para buscar departamentos automaticamente
- ✅ Novo nó "Alterar Status" (🎫) para gerenciar status de tickets
- ✅ Busca automática de status com ordenação por progresso
- ✅ Preview detalhado de status (nome, descrição, porcentagem)
- ✅ Melhorias na UX dos dropdowns e seleção de dados
- ✅ Tratamento robusto de erros com fallback para input manual

**Novos Componentes:**
- `set_ticket_status`: Nó para alterar status de tickets via MonitChat API
- Integração completa com endpoints MonitChat (departamentos e status)
- Sistema de autenticação JWT com MonitChat

## Development Commands

### Environment Setup
```bash
# Create and activate virtualenv
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools
pip install -e .
pip install pytest pytest-cov pre-commit flake8 isort black gunicorn

# Install git hooks
pre-commit install
pre-commit autoupdate
```

### Database
```bash
# Start local PostgreSQL
tests/resources/database/run-container.sh
tests/resources/database/seed-database.sh
```

### Testing and Quality
```bash
# Run all tests with coverage
scripts/run-tests.sh

# Run linter only
flake8 src/

# Run tests only
pytest -v --cov=danubio_bot tests/

# Run single test file
pytest tests/test_file.py -v

# Format code (pre-commit hooks will run automatically)
black src/
isort src/
```

### Local Development
```bash
# Start RabbitMQ
docker run -d --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.10-management

# Run with docker-compose
docker-compose up

# SSH tunnel for receiving callbacks (development)
ssh -R 5000:localhost:5000 -i danubio-bot-dev_key.pem ubuntu@danubio-bot-dev.eastus2.cloudapp.azure.com 'sudo killall -9 socat 2>/dev/null ; sudo socat TCP-LISTEN:80,fork,reuseaddr TCP:localhost:5000'
```

## Architecture

### Core Components

**Flask Application** (`app.py`):
- Application factory pattern with health checks
- Structured logging with structlog (JSON output)
- SQLAlchemy database integration with PostgreSQL
- Error handlers for API and validation errors

**Message Processing** (Celery workers):
- `message_worker.py`: Processes incoming WhatsApp messages via `process_message` task
- `sender_worker.py`: Sends outgoing messages via `send_message` task with delayed execution support
- Two RabbitMQ queues: `messages-danubio-bot` and `send-message-danubio-bot`

**API Endpoints** (`service.py`):
- `/api/v1/whatsapp/webhook` (POST): Receives WhatsApp messages, enqueues to Celery
- `/api/v1/ticket/webhook` (POST): Receives ticket status updates
- `/api/v1/whatsapp/conversation` (POST): Sends messages directly
- `/api/v1/health` (GET): Health check endpoint

**Conversation State Machine** (`conversation.py`):
- `Conversation` class manages user interactions by phone number (msisdn)
- State is stored in PostgreSQL via `context.py` (Context model with JSON data column)
- Stages dynamically loaded from `stage/bot_stage.py` via introspection
- Special keywords trigger navigation: restart keywords go to `AskEndStage`, "voltar" goes to previous stage

### Stage System

**BotStage Abstract Base** (`stage/bot_stage_abstract.py`):
- All conversation stages inherit from `BotStage`
- Each stage has a `stage` class attribute (unique identifier)
- Must implement `handle_input(msisdn, text)` returning list of reply dictionaries
- Built-in helpers: `set_context()`, `get_context_value()`, `get_last_message()`

**Stage Flow Pattern**:
1. "Ask" stages: Send messages/questions to user, set next stage to corresponding "Receive" stage
2. "Receive" stages: Process user input, validate, transition to next Ask stage
3. Context updates track `stage`, `previous_stage`, and `last_message_sent`

**Key Stages** (in `stage/bot_stage.py`):
- `AskStartMenuStage`: Entry point, determines if user is customer/montador/non-client
- `SendToDepartmentStage`: Routes conversation to human agents via Monitchat API
- `AskEndStage`: Terminates conversation, resets context

### Reply Types
Replies are dictionaries with `type` field:
- `text`: Simple text message
- `button`: Interactive buttons (WhatsApp quick replies)
- `list`: List picker interface
- `document`/`image`: Media messages
- `end`: Ends chat and resets context
- `exec`: Executes another stage after delay (used by `sender_worker.py`)

### Context Management (`context.py`)

- PostgreSQL table `contexts` with `msisdn` (phone) as primary key
- Stores JSON blob with conversation state, stage history, customer data
- Key functions: `load()`, `merge()` (upsert with retry), `get_value()`, `delete()`
- Thread-safe with SQLAlchemy sessions and tenacity retry logic

### External Integrations

**WhatsApp Client** (`client/whatsapp_client.py`):
- Factory pattern using `AbstractBroker` interface
- Currently uses Monitchat provider (`client/factory/monitchat.py`)
- Methods: `send_text_message`, `send_button_message`, `send_list_message`, `send_media_message`, `end_chat`

**Danubio API** (`client/danubio.py`):
- Integration with Sankhya ERP system
- Fetches customer data: `get_partner()`, `get_client()`, `get_products()`, `get_services()`
- Updates customer preferences: `update_parceiro()`

**Support System** (`client/support.py`):
- Monitchat ticket management
- `get_current_ticket()`, `route_to_department()`

## Configuration

Environment variables in `config.py`:
- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_URL`: RabbitMQ broker URL (default: `amqp://rabbitmq:5672`)
- `MONITCHAT_API_ACCESS_TOKEN`, `MONITCHAT_SENDER`, `MONITCHAT_BASE_URL`: WhatsApp provider credentials
- `DANUBIO_API_BASE_URL`, `DANUBIO_USER`, `DANUBIO_PASSWORD`: ERP integration
- `OPENAI_SECRET_KEY`: OpenAI API key (used in conversation.py)
- Department IDs for routing: `ID_DEPARTAMENTO_GOIABEIRAS`, `ID_DEPARTAMENTO_CREDIARIO`, etc.

Special keyword lists:
- `RESTART_CONVERSATION_KEYWORDS`: Trigger conversation end
- `BACK_KEYWORDS`: Navigate to previous stage
- `POSITIVE_KEYWORDS`: Yes/confirmation responses

## Code Style

- Python 3.9
- Line length: 79 characters (black/isort configured)
- Flake8 ignores: E501 (line too long), W503 (line break before binary operator)
- Pre-commit hooks enforce: trailing-whitespace, end-of-file-fixer, black, isort, flake8

## Flow Builder (NOVO SISTEMA VISUAL)

### Visão Geral

O Flow Builder é uma interface visual para criar e gerenciar fluxos de conversação sem código. Ele substitui a necessidade de editar `bot_stage.py` manualmente.

**Arquivos principais:**
- `src/danubio_bot/models/flow.py`: Modelo de dados para fluxos
- `src/danubio_bot/api/flow_api.py`: API REST para CRUD
- `src/danubio_bot/flow_interpreter.py`: Interpretador de fluxos JSON
- `frontend/`: Interface React com editor visual

**Como funciona:**
1. Crie fluxos visualmente através da interface web
2. Fluxos são salvos como JSON no banco de dados
3. O interpretador executa o JSON como state machine
4. Sistema é compatível com stages legados (fallback automático)

### Uso do Flow Builder

**Acesso:**
```bash
# Desenvolvimento
cd frontend && npm run dev
# Abrir http://localhost:5173

# Build para produção
cd frontend && npm run build
# Arquivos gerados em: ../public/
```

**Frontend Stack:**
- React 18 com Vite
- React Router para navegação
- React Flow para editor visual de fluxos
- Axios para requisições HTTP
- Autenticação via MonitChat API (JWT)
- Interface responsiva com design moderno

**Estrutura do Frontend:**
- `src/pages/`: Páginas principais (Login, FlowBuilder, FlowList)
- `src/components/`: Componentes reutilizáveis (Header, Sidebar, NodeEditorModal, CustomNode)
- `src/config/`: Configurações (axios, api endpoints)
- `public/`: Arquivos estáticos e build de produção

**Componentes disponíveis:**
- 💬 Mensagem: Texto simples
- 🔘 Botões: Quick replies
- 📋 Lista: Seleção de opções
- ⌨️ Input: Captura e valida dados
- 🔀 Condição: Ramificação baseada em regras
- 🎯 Router Inteligente: Roteador com múltiplas saídas e mensagem de erro
- 🔌 API Call: Integração com Sankhya (predefinida)
- 🌐 API Request: Requisição HTTP customizável (GET/POST/PUT/DELETE/PATCH)
- 💾 Salvar no Contexto: Salva valores no contexto da conversa
- ⏱️ Delay: Aguarda X segundos antes de continuar
- 👤 Transferir: Roteamento para departamentos (integrado com MonitChat API)
- 🎫 Alterar Status: Altera o status do ticket/atendimento (integrado com MonitChat API)
- 🏁 Fim: Finalização e reset

**Estrutura do JSON:**
```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "message",
      "position": {"x": 100, "y": 100},
      "data": {"message": "Olá!"}
    }
  ],
  "edges": [
    {
      "source": "node_1",
      "target": "node_2",
      "data": {"condition": {...}}
    }
  ]
}
```

**Documentação completa:** Ver `FLOW_BUILDER_README.md`

### Integrações MonitChat API

**Nó de Transferência (👤 Transferir):**
- Busca departamentos automaticamente da API MonitChat
- Endpoint: `GET https://api-v2.monitchat.com/api/v1/department`
- Interface com dropdown para seleção de departamento
- Mostra nome e ID de cada departamento
- Fallback para input manual em caso de erro
- Campos configuráveis:
  - `department_id`: ID do departamento (obrigatório)
  - `message`: Mensagem enviada ao transferir (opcional)
  - `label`: Rótulo customizado do nó (opcional)

**Nó de Alterar Status (🎫 Alterar Status):**
- Busca status de tickets automaticamente da API MonitChat
- Endpoint: `GET https://api-v2.monitchat.com/api/v1/ticket-status`
- Interface com dropdown mostrando:
  - Nome do status
  - Descrição
  - Porcentagem de progresso (0-100%)
- Status ordenados por progresso (menor → maior)
- Preview do status selecionado com detalhes completos
- Fallback para input manual em caso de erro
- Campos configuráveis:
  - `status_id`: ID do status (obrigatório)
  - `label`: Rótulo customizado do nó (opcional)
- API de alteração de status:
  - Endpoint: `POST https://api-v2.monitchat.com/api/v1/ticket/setTicketStatus`
  - Payload: `{"data": ticket_id, "status": status_id}`
  - O `ticket_id` deve estar disponível no contexto da conversa

**Autenticação:**
- Todas as requisições para MonitChat API usam Bearer token
- Token obtido do localStorage após login
- Header: `Authorization: Bearer <token>`
- Renovação automática em caso de 401 (não autorizado)

### Interface Visual (UI/UX)

**Página de Login:**
- Design moderno com gradiente roxo
- Logo do MonitChat centralizada
- Autenticação via MonitChat API (JWT)
- Validação de credenciais
- Armazenamento seguro de token e dados do usuário

**Header da Aplicação:**
- Logo quadrada do MonitChat
- Título "Monitchat Flow"
- Avatar do usuário (com fallback para iniciais)
- Botão de logout
- Design sticky (fixo no topo)

**Editor de Fluxos:**
- Canvas drag-and-drop para criar fluxos visualmente
- Minimap para navegação em fluxos grandes
- Zoom e pan com controles visuais
- Auto-save a cada 2 segundos (com indicador visual)
- Validação de fluxos antes de ativar

**Modal de Edição de Nós:**
- Interface específica para cada tipo de nó
- Dropdowns dinâmicos para seleção (departamentos, status)
- Preview de informações selecionadas
- Autocomplete para variáveis do contexto
- Validação em tempo real
- Estados de loading e erro bem definidos

## Working with Stages (Sistema Legado)

⚠️ **NOTA:** Novos fluxos devem usar o Flow Builder. Use stages apenas para manutenção de código legado.

When adding new conversation stages:

1. Create new class in `stage/bot_stage.py` inheriting from `BotStage`
2. Set unique `stage` class attribute (string identifier)
3. Implement `handle_input(self, msisdn: str, text: str = "") -> list`
4. Update context with `self.set_context()` to set next stage and previous_stage
5. Return list of reply dictionaries
6. Stages are auto-discovered via introspection in `conversation.py:start()`

Example pattern:
```python
class BotAskExampleStage(BotStage):
    stage = "ask_example"

    def handle_input(self, msisdn: str, text: str = ""):
        self.replies = [{"type": "text", "text": "Question here"}]
        self.set_context(
            msisdn=msisdn,
            data={
                "stage": BotReceiveExampleStage.stage,
                "previous_stage": self.stage,
                "last_message_sent": self.get_last_message(self.replies)
            }
        )
        return self.replies
```

## Important Patterns

- Always normalize user input with `unidecode()` and `.strip(punctuation).lower()` before comparison
- Department routing uses `SendToDepartmentStage` which calls `support.route_to_department()`
- Customer lookup flow: check by phone → ask if customer → validate CPF → fetch from ERP
- Delayed messages use Celery's `apply_async(countdown=seconds)`
- Context merging is atomic with retry logic to handle concurrent updates
