# Flow Builder - Client Bot

Sistema visual para construção de fluxos de conversação do bot WhatsApp sem necessidade de programação.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Tipos de Nós](#tipos-de-nós)
- [Conexões e Condições](#conexões-e-condições)
- [API Reference](#api-reference)
- [Arquitetura](#arquitetura)

## 🎯 Visão Geral

O Flow Builder permite que você crie e gerencie fluxos de conversação do bot de forma visual, através de uma interface drag-and-drop. Não é mais necessário escrever código Python para modificar o comportamento do bot.

### Características

- ✅ Interface visual drag-and-drop
- ✅ 8 tipos de nós diferentes (mensagem, botões, lista, condição, API, transferência, fim, input)
- ✅ Sistema de versionamento automático
- ✅ Suporte a múltiplos fluxos (apenas um ativo por vez)
- ✅ Compatibilidade com sistema legado de stages
- ✅ Preview visual do fluxo
- ✅ Validação de inputs

## 🚀 Instalação

### 1. Banco de Dados

Aplique a nova migration para criar as tabelas de fluxos:

```bash
psql -U postgres -f deploy/database/02__flows_schema.sql
```

### 2. Backend (Python)

As dependências já estão no `setup.py`. Reinstale o pacote:

```bash
pip install -e .
```

### 3. Frontend (React)

Instale as dependências do frontend:

```bash
cd frontend
npm install
```

### 4. Executar

**Desenvolvimento:**

Terminal 1 - Backend:
```bash
export FLASK_APP=danubio_bot.app
python -m flask run --host=0.0.0.0 --port=5000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Acesse: http://localhost:3000

**Produção:**

```bash
# Build do frontend
cd frontend
npm run build

# O build será colocado em /public e servido pelo Flask
```

## 📖 Como Usar

### 1. Acessar o Flow Builder

Abra http://localhost:3000 no navegador.

### 2. Criar um Novo Fluxo

1. Clique em "Novo Fluxo"
2. Dê um nome e descrição ao fluxo
3. Arraste componentes da barra lateral para o canvas
4. Clique nos nós para editar suas propriedades
5. Conecte os nós arrastando das bordas
6. Salve o fluxo

### 3. Ativar um Fluxo

1. Na lista de fluxos, clique em "Ativar"
2. Apenas um fluxo pode estar ativo por vez
3. O fluxo ativo será usado nas conversas do bot

### 4. Testar o Fluxo

Envie uma mensagem no WhatsApp para o bot. Ele usará o fluxo ativo automaticamente.

## 🧩 Tipos de Nós

### 1. Mensagem de Texto 💬

Envia uma mensagem de texto simples para o usuário.

**Configuração:**
- **Mensagem**: Texto a ser enviado

**Exemplo:**
```
Olá! Bem-vindo à Client.
```

### 2. Botões 🔘

Envia botões interativos (quick replies do WhatsApp).

**Configuração:**
- **Mensagem**: Texto acima dos botões
- **Botões**: Lista de botões (máximo 3)

**Exemplo:**
```
Mensagem: Você já é nosso cliente?
Botões:
  - Sim
  - Não
```

### 3. Lista 📋

Envia uma lista de opções selecionáveis.

**Configuração:**
- **Texto**: Mensagem principal
- **Corpo**: Subtítulo
- **Rodapé**: Texto no rodapé
- **Texto do botão**: Texto do botão que abre a lista
- **Opções**: Array JSON com as opções

**Exemplo de opções:**
```json
[
  {
    "title": "Lojas",
    "rows": [
      {"id": "goiabeiras", "title": "Vitória/Goiabeiras", "description": ""},
      {"id": "laranjeiras", "title": "Serra/Laranjeiras", "description": ""}
    ]
  }
]
```

### 4. Capturar Input ⌨️

Recebe e valida input do usuário.

**Configuração:**
- **Tipo de Input**: text, number, cpf, email
- **Chave no contexto**: Nome da variável onde salvar
- **Mensagem de erro**: Mensagem se validação falhar

**Exemplo:**
```
Tipo: cpf
Chave: cpf_cliente
Mensagem de erro: CPF inválido. Digite novamente.
```

O valor capturado fica disponível no contexto para uso posterior.

### 5. Condição 🔀

Direciona o fluxo baseado em condições.

**Configuração:**
- **Rótulo**: Nome da condição

**Uso:**
1. Conecte este nó a múltiplos destinos
2. Configure condições em cada conexão (edge)

**Tipos de condição:**
- `equals`: Texto exato
- `contains`: Contém texto
- `regex`: Expressão regular
- `context`: Valor no contexto
- `is_positive`: Resposta positiva (sim, ok, etc)
- `is_digit`: É número

### 6. Chamada API 🔌

Faz uma chamada para API externa (Sankhya ERP).

**Configuração:**
- **Tipo de API**:
  - `get_customer`: Busca dados do cliente
  - `get_products`: Busca produtos pendentes
  - `get_services`: Busca serviços pendentes
- **Rótulo**: Nome do nó

**Exemplo:**
```
Tipo: get_customer
```

Os dados retornados são salvos no contexto automaticamente.

### 7. Transferir 👤

Transfere a conversa para atendimento humano.

**Configuração:**
- **ID do Departamento**: ID do departamento no Monitchat
- **Mensagem**: Mensagem ao transferir
- **Rótulo**: Nome do nó

**IDs de departamento:**
- 2287: Goiabeiras
- 2288: Laranjeiras
- 2289: Campo Grande
- 2290: Vila Velha Centro
- 2291: Portal Glória
- 2292: Cachoeiro
- 2134: Assistência Técnica
- 2285: SAC
- 2286: Serviços

### 8. Finalizar 🏁

Finaliza a conversa e reseta o contexto.

**Configuração:**
- **Mensagem de despedida**: Mensagem final
- **Rótulo**: Nome do nó

**Exemplo:**
```
A Client agradece o seu contato!
```

## 🔗 Conexões e Condições

### Conectar Nós

1. Arraste da borda inferior de um nó
2. Solte na borda superior do nó de destino
3. A conexão (edge) é criada

### Configurar Condições

Para nós de condição, você pode configurar condições nas conexões:

```json
{
  "type": "equals",
  "values": ["sim", "yes", "1"]
}
```

**Estrutura da edge no JSON do fluxo:**
```json
{
  "id": "edge_1",
  "source": "node_1",
  "target": "node_2",
  "data": {
    "condition": {
      "type": "equals",
      "values": ["opcao1", "1"]
    }
  }
}
```

## 🔌 API Reference

### GET /api/v1/flows

Lista todos os fluxos.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Fluxo Principal",
      "description": "Fluxo de atendimento padrão",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00",
      "updated_at": "2025-01-01T00:00:00"
    }
  ]
}
```

### GET /api/v1/flows/:id

Retorna um fluxo específico.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Fluxo Principal",
    "description": "Fluxo de atendimento padrão",
    "data": {
      "nodes": [...],
      "edges": [...],
      "metadata": {...}
    },
    "is_active": true,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
}
```

### POST /api/v1/flows

Cria um novo fluxo.

**Request:**
```json
{
  "name": "Novo Fluxo",
  "description": "Descrição",
  "data": {
    "nodes": [],
    "edges": []
  },
  "is_active": false
}
```

### PUT /api/v1/flows/:id

Atualiza um fluxo existente.

**Request:**
```json
{
  "name": "Nome Atualizado",
  "description": "Nova descrição",
  "data": {
    "nodes": [...],
    "edges": [...]
  },
  "is_active": true
}
```

**Nota:** Ao ativar um fluxo (`is_active: true`), todos os outros são desativados automaticamente.

### DELETE /api/v1/flows/:id

Deleta um fluxo.

**Restrições:**
- Não é possível deletar um fluxo ativo

### GET /api/v1/flows/active

Retorna o fluxo ativo.

## 🏗️ Arquitetura

### Backend

```
src/danubio_bot/
├── models/
│   └── flow.py              # Modelo SQLAlchemy para fluxos
├── api/
│   └── flow_api.py          # Endpoints REST
├── flow_interpreter.py      # Interpretador de fluxos
└── conversation.py          # Integração com sistema de conversação
```

### Frontend

```
frontend/
├── src/
│   ├── pages/
│   │   ├── FlowList.jsx     # Lista de fluxos
│   │   └── FlowBuilder.jsx  # Editor visual
│   └── components/
│       ├── Sidebar.jsx      # Barra lateral com nós
│       ├── CustomNode.jsx   # Renderização de nós
│       └── NodeEditorModal.jsx  # Modal de edição
```

### Fluxo de Execução

1. **Mensagem chega** → `conversation.py:handle_message()`
2. **Carrega interpretador** → `get_interpreter_for_msisdn()`
3. **Busca nó atual** → Baseado no `stage` do contexto
4. **Executa nó** → `interpreter.execute_node()`
5. **Determina próximo nó** → Baseado em condições
6. **Atualiza contexto** → Salva novo `stage`
7. **Envia respostas** → Através do WhatsApp client

### State Machine

O sistema funciona como uma máquina de estados:

```
┌─────────────┐
│   Mensagem  │
│   Recebida  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Carrega   │
│   Contexto  │ (stage atual)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Executa Nó │
│    Atual    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Avalia     │
│  Condições  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Atualiza   │
│   Stage     │ (próximo nó)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Envia     │
│  Respostas  │
└─────────────┘
```

### Estrutura do JSON do Fluxo

```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "message",
      "position": { "x": 100, "y": 100 },
      "data": {
        "message": "Olá! Como posso ajudar?"
      }
    },
    {
      "id": "node_2",
      "type": "button",
      "position": { "x": 100, "y": 200 },
      "data": {
        "message": "Escolha uma opção:",
        "buttons": ["Opção 1", "Opção 2"]
      }
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "data": {}
    }
  ],
  "metadata": {
    "version": "1.0.0",
    "created_by": "system"
  }
}
```

## 💡 Dicas e Boas Práticas

### 1. Nomear Nós Claramente

Use rótulos descritivos nos nós para facilitar a manutenção.

### 2. Sempre Ter um Nó de Fim

Todo fluxo deve terminar com um nó de finalização para resetar o contexto.

### 3. Testar Antes de Ativar

Crie e teste o fluxo antes de ativá-lo em produção.

### 4. Usar Condições para Ramificação

Use nós de condição para criar fluxos inteligentes que se adaptam ao input do usuário.

### 5. Salvar Frequentemente

Salve o fluxo regularmente durante a edição.

### 6. Versionamento

Toda alteração em um fluxo cria uma nova versão automaticamente. Você pode reverter se necessário consultando a tabela `flow_versions`.

### 7. IDs de Stage

- O ID do nó é usado como `stage` no contexto
- Use nomes descritivos para os IDs (ex: "ask_cpf", "send_menu")
- O nó inicial deve ter ID "start"
- O nó de fim deve ter ID "end"

## 🐛 Troubleshooting

### Fluxo não está funcionando

1. Verifique se o fluxo está ativo
2. Verifique se há apenas um fluxo ativo
3. Confira os logs do Flask para erros

### Nós não conectam

1. Certifique-se de arrastar da borda inferior para a superior
2. Nós de fim não têm saída

### Frontend não carrega

1. Verifique se o backend está rodando na porta 5000
2. Verifique se há erros no console do navegador
3. Limpe o cache do navegador

### Validação falha sempre

1. Verifique o tipo de input configurado
2. Confira se a mensagem de erro está definida

## 🔄 Migração do Sistema Legado

O sistema é compatível com o código legado. O interpretador de fluxos tem prioridade, mas se não houver fluxo ativo, o sistema usa as classes de stage antigas.

Para migrar um fluxo existente:

1. Crie um novo fluxo no Flow Builder
2. Recrie os stages como nós visuais
3. Configure as transições como conexões
4. Teste o novo fluxo
5. Ative o fluxo quando estiver pronto

## 📝 Exemplos

### Exemplo 1: Fluxo Simples de Boas-Vindas

```
[Start] → [Mensagem: "Olá!"] → [Botões: "É cliente?"]
                                      ├─ Sim → [Input: CPF] → [API: get_customer] → [Menu]
                                      └─ Não → [Menu Não Cliente]
```

### Exemplo 2: Fluxo de Atendimento com Condições

```
[Start] → [Mensagem: "Como posso ajudar?"]
            → [Condição]
                ├─ "compra" → [Lojas]
                ├─ "entrega" → [Produtos Pendentes]
                └─ default → [Transferir SAC]
```

## 🎓 Tutorial Passo a Passo

### Criar um Fluxo de Captura de CPF

1. **Criar o fluxo**
   - Clique em "Novo Fluxo"
   - Nome: "Validação de CPF"

2. **Adicionar nó de mensagem**
   - Arraste "Mensagem de Texto"
   - Configure: "Por favor, digite seu CPF"

3. **Adicionar nó de input**
   - Arraste "Capturar Input"
   - Tipo: CPF
   - Chave: "cpf"
   - Erro: "CPF inválido"

4. **Adicionar chamada API**
   - Arraste "Chamada API"
   - Tipo: get_customer

5. **Adicionar condição**
   - Arraste "Condição"
   - Rótulo: "Cliente encontrado?"

6. **Conectar os nós**
   - Mensagem → Input
   - Input → API
   - API → Condição
   - Condição → (conecte a dois destinos diferentes)

7. **Salvar e ativar**

## 📞 Suporte

Para dúvidas ou problemas:
- Consulte este README
- Verifique os logs do sistema
- Revise a estrutura do JSON do fluxo

---

Desenvolvido para Client 🛋️
