# 🔄 Isolamento de Contexto por Fluxo

## 📋 Problema Resolvido

Antes, quando você trocava o fluxo ativo, o contexto do usuário ainda tinha o `stage` do fluxo antigo, causando erro "Node not found".

**Comportamento antigo (problema):**
```
Fluxo A ativo → Usuário em stage "receive_menu"
Ativa Fluxo B → Contexto ainda tem stage "receive_menu"
Usuário envia msg → ❌ Erro: "receive_menu" não existe no Fluxo B
```

## ✅ Solução Implementada

Agora cada contexto tem um `flow_id` que rastreia qual fluxo o usuário está usando.

**Comportamento novo (solução):**
```
Fluxo A ativo → flow_id=2, stage="receive_menu", cpf="123..."
Ativa Fluxo B → flow_id=3, stage="node_1" (início), cpf="123..." ✅ PRESERVADO
Usuário envia msg → ✅ Executa node_1 do Fluxo B
Volta Fluxo A → flow_id=2, stage="node_inicio", cpf="123..." ✅ PRESERVADO
```

## 🗃️ Estrutura da Tabela `contexts`

```sql
CREATE TABLE contexts (
    msisdn VARCHAR(16) PRIMARY KEY,
    data JSONB NOT NULL,
    flow_id INTEGER,                    -- ✨ NOVO!
    updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,

    FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE SET NULL
);
```

## 📊 Exemplo de Contexto

```json
{
  "msisdn": "5527999999999",
  "flow_id": 3,                         // ✨ Rastreia qual fluxo está ativo
  "data": {
    // Dados do fluxo (resetados ao trocar)
    "stage": "node_1",
    "previous_stage": "ask_start_menu",

    // Dados do usuário (PRESERVADOS ao trocar)
    "cpf": "12345678901",
    "codparc": "54321",
    "nomeparc": "João Silva",
    "customer": { ... },
    "tipo_contato": "M",
    "is_logged_in": true
  }
}
```

## 🔧 Como Funciona

### 1. Detecção de Mudança de Fluxo

Quando uma mensagem chega:
```python
# conversation.py
current_flow_id = context.get_value(msisdn, "flow_id")
active_flow = get_active_flow()

if current_flow_id != active_flow.id:
    # Mudou de fluxo!
    start_node = flow_interpreter.get_start_node()
    context.merge(msisdn, {
        "flow_id": active_flow.id,        # Atualiza flow_id
        "stage": start_node,              # Reseta stage para início
        "previous_stage": old_stage,      # Preserva histórico
        # cpf, customer, etc. NÃO são tocados!
    })
```

### 2. Preservação de Dados

**O que é RESETADO ao trocar de fluxo:**
- ✅ `stage` → Vai para o nó inicial do novo fluxo
- ✅ `previous_stage` → Atualizado para o stage antigo
- ✅ `flow_id` → Atualizado para o ID do novo fluxo

**O que é PRESERVADO ao trocar de fluxo:**
- ✅ `cpf` (CPF do usuário)
- ✅ `codparc` (Código do parceiro)
- ✅ `nomeparc` (Nome do parceiro)
- ✅ `customer` (Dados completos do cliente)
- ✅ `tipo_contato` (M=Montador, C=Cliente)
- ✅ `is_logged_in` (Estado de autenticação)
- ✅ Todos os outros dados do contexto!

### 3. Nó Inicial Automático

O sistema detecta automaticamente qual é o nó inicial:
```python
def get_start_node(self):
    """
    Encontra o nó inicial do fluxo.
    O nó inicial é aquele que não tem nenhuma edge apontando para ele.
    """
    # Se há apenas 1 nó, ele é o inicial
    if len(self.nodes) == 1:
        return list(self.nodes.keys())[0]

    # Encontra nós que são targets de alguma edge
    target_nodes = {edge["target"] for edge in self.edges}

    # O nó inicial é aquele que não é target de nenhuma edge
    start_nodes = [
        node_id for node_id in self.nodes.keys()
        if node_id not in target_nodes
    ]

    return start_nodes[0] if start_nodes else list(self.nodes.keys())[0]
```

## 🎯 Casos de Uso

### Caso 1: Primeiro Acesso ao Fluxo Visual

```
Usuário novo → flow_id=NULL, stage="ask_start_menu"
Envia mensagem → Sistema detecta flow_id=NULL ≠ 3 (ativo)
                → Reseta stage para "node_1" (início do Fluxo 3)
                → flow_id=3
```

### Caso 2: Trocar de Fluxo (Preservando Dados)

```
Fluxo A (id=2) ativo
Usuário: flow_id=2, cpf="123...", stage="menu_montador"

Admin ativa Fluxo B (id=3)

Usuário envia msg:
  → Sistema detecta flow_id=2 ≠ 3 (ativo)
  → Reseta stage="node_1" (início do Fluxo B)
  → flow_id=3
  → cpf="123..." ✅ PRESERVADO!
```

### Caso 3: Voltar ao Fluxo Anterior

```
Admin ativa Fluxo A (id=2) novamente

Usuário envia msg:
  → Sistema detecta flow_id=3 ≠ 2 (ativo)
  → Reseta stage para início do Fluxo A
  → flow_id=2
  → cpf="123..." ✅ AINDA PRESERVADO!
```

## 🚀 Benefícios

1. ✅ **Sem Perda de Dados**: CPF, customer, codparc, etc. são preservados
2. ✅ **Transição Suave**: Ao trocar fluxo, usuário começa do início automaticamente
3. ✅ **Flexibilidade**: Admin pode trocar fluxos sem quebrar conversas ativas
4. ✅ **Segurança**: Foreign key garante integridade (flow_id sempre válido ou NULL)
5. ✅ **Histórico**: previous_stage preserva de onde o usuário veio

## 📝 Arquivos Modificados

### Migration SQL
- `deploy/database/03__add_flow_id_to_contexts.sql` ✨ NOVO
  - Adiciona coluna `flow_id` na tabela `contexts`
  - Adiciona foreign key para `flows`
  - Adiciona índice para performance

### Backend
- `src/danubio_bot/conversation.py` (modificado)
  - Detecta mudança de `flow_id`
  - Reseta `stage` para início do novo fluxo
  - Preserva todos os outros dados do contexto

- `src/danubio_bot/flow_interpreter.py` (modificado)
  - Adiciona método `get_start_node()` para detectar nó inicial
  - Fallback automático quando nó não existe

## 🧪 Como Testar

### 1. Ver contexto atual
```bash
curl http://localhost:5000/api/v1/flows/debug/context/5527999999999
```

### 2. Criar Fluxo B e ativar
```bash
# No Flow Builder, criar novo fluxo e ativar
```

### 3. Enviar mensagem no WhatsApp
```
Usuário: "oi"
```

### 4. Verificar que flow_id mudou e dados foram preservados
```bash
curl http://localhost:5000/api/v1/flows/debug/context/5527999999999
```

Resposta esperada:
```json
{
  "flow_id": 3,              // ✅ Novo flow_id
  "stage": "node_1",         // ✅ Stage resetado
  "cpf": "12345678901",      // ✅ Dados preservados
  "customer": { ... },       // ✅ Dados preservados
  "codparc": "54321"         // ✅ Dados preservados
}
```

## 🔍 Logs para Debug

Quando trocar de fluxo, você verá no log:
```
Flow changed from 2 to 3, resetting stage to start node
Using start node: node_1
```

---

**Agora você pode trocar entre fluxos sem perder dados do cliente!** 🎉
