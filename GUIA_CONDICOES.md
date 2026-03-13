# 🔀 Guia Completo de Condições no Flow Builder

## 📋 Índice

- [Como Funcionam as Condições](#como-funcionam-as-condições)
- [Tipos de Condições](#tipos-de-condições)
- [Variáveis Disponíveis no Contexto](#variáveis-disponíveis-no-contexto)
- [Exemplos Práticos](#exemplos-práticos)
- [Debug e Visualização](#debug-e-visualização)

---

## 🎯 Como Funcionam as Condições

### **Conceito:**

O nó de **Condição** NÃO envia mensagem. Ele é um **roteador invisível** que:

1. Recebe o input do usuário
2. Avalia as condições de cada conexão (edge)
3. Direciona para o próximo nó baseado na condição

### **Estrutura:**

```
[Nó Anterior]
     │
     ▼
[Nó Condição] ← Não envia nada, só avalia
     │
     ├─ Condição A → [Nó Destino A]
     ├─ Condição B → [Nó Destino B]
     └─ Default (sem condição) → [Nó Destino C]
```

### **Configuração:**

As condições são configuradas nas **CONEXÕES (edges)**, não no nó!

**Formato JSON da Edge:**
```json
{
  "source": "node_condition",
  "target": "node_destino",
  "data": {
    "condition": {
      "type": "equals",
      "values": ["sim", "yes", "1"]
    }
  }
}
```

---

## 🔧 Tipos de Condições

### **1. `equals` - Comparação Exata**

Verifica se o texto do usuário é **exatamente** um dos valores.

**Configuração:**
```json
{
  "type": "equals",
  "values": ["sim", "yes", "1", "ok"]
}
```

**Exemplo:**
- Usuário digita: "sim" → ✅ Match
- Usuário digita: "SIM" → ✅ Match (case insensitive)
- Usuário digita: "Sim, quero" → ❌ Não match

---

### **2. `contains` - Contém Texto**

Verifica se o texto do usuário **contém** algum dos valores.

**Configuração:**
```json
{
  "type": "contains",
  "values": ["goiabeira", "gloria", "laranjeira"]
}
```

**Exemplo:**
- Usuário digita: "Vitória/Goiabeiras" → ✅ Match (contém "goiabeira")
- Usuário digita: "quero ir em goiabeiras" → ✅ Match
- Usuário digita: "cachoeiro" → ❌ Não match

---

### **3. `regex` - Expressão Regular**

Usa expressão regular para validação avançada.

**Configuração:**
```json
{
  "type": "regex",
  "pattern": "^\\d{11}$"
}
```

**Exemplos de padrões:**
- `^\\d{11}$` → Exatamente 11 dígitos (celular)
- `^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$` → CPF formatado
- `^[0-9]+$` → Apenas números

---

### **4. `context` - Valor no Contexto**

Verifica valores salvos no contexto (banco de dados).

**Configuração:**
```json
{
  "type": "context",
  "key": "tipo_contato",
  "value": "M"
}
```

**Casos especiais:**
```json
{
  "type": "context",
  "key": "customer",
  "value": "exists"  ← Verifica se existe (não vazio)
}
```

---

### **5. `is_positive` - Resposta Positiva**

Verifica se é uma resposta afirmativa.

**Configuração:**
```json
{
  "type": "is_positive"
}
```

**Match:**
- "sim", "yes", "ok", "okay", "claro", "com certeza", etc.

---

### **6. `is_digit` - É Número**

Verifica se o input é um número.

**Configuração:**
```json
{
  "type": "is_digit"
}
```

**Match:**
- "1", "123", "9999" → ✅
- "1a", "abc", "1.5" → ❌

---

## 📦 Variáveis Disponíveis no Contexto

Após cada **nó de API Call** ou **Input**, variáveis ficam disponíveis no contexto:

### **Após `get_partner` (Buscar Parceiro):**

```javascript
{
  "cpf": "12345678901",
  "tipo_contato": "M",          // "M" = Montador, "C" = Cliente
  "codparc": "12345",
  "nomeparc": "Nome da Empresa",
  "nomectt": "Nome do Contato",
  "partner": { /* dados completos */ }
}
```

**Uso em condição:**
```json
{
  "type": "context",
  "key": "tipo_contato",
  "value": "M"  // É montador?
}
```

---

### **Após `get_customer` (Buscar Cliente):**

```javascript
{
  "customer": {
    "CODPARC": {"$": "12345"},
    "NOMEPARC": {"$": "João Silva"},
    "NOMECTT": {"$": "João"},
    "CPF": {"$": "12345678901"},
    "EMAILCTT": {"$": "joao@email.com"},
    "TELEFONE": {"$": "27999999999"},
    "ENDERECO": {"$": "Rua ABC, 123"}
  },
  "is_logged_in": true,
  "codparc": "12345"
}
```

**Uso em condição:**
```json
{
  "type": "context",
  "key": "customer",
  "value": "exists"  // Cliente foi encontrado?
}
```

---

### **Após `get_products` (Buscar Produtos):**

```javascript
{
  "customer_orders": {
    "responseBody": {
      "records": {
        "record": [
          {
            "NUNOTA": {"$": "123456"},
            "SEQUENCIA": {"$": "1"},
            "STATUS": {"$": "P"},  // P = Pendente, F = Finalizado
            "DTENTREGA": {"$": "2025-01-15"},
            "DESCRPROD": {"$": "Sofá 3 lugares"}
          }
        ]
      }
    }
  }
}
```

---

### **Após `get_services` (Buscar Serviços):**

```javascript
{
  "customer_services": {
    "responseBody": {
      "records": {
        "record": [
          {
            "NUNOTA": {"$": "789"},
            "SERVICO": {"$": "Limpeza de Sofá"},
            "TPSERV": {"$": "L"},  // L = Limpeza, H = Hidratação
            "QTDNEG": {"$": "1"}
          }
        ]
      }
    }
  }
}
```

---

### **Após Nós de Input:**

Quando você configura um nó de **Input** com `context_key`, o valor fica salvo:

**Exemplo: Input de CPF**
```json
// Configuração do nó
{
  "input_type": "cpf",
  "context_key": "cpf"
}

// Depois de validado, fica no contexto:
{
  "cpf": "12345678901"
}
```

**Exemplo: Input de Menu**
```json
// Configuração do nó
{
  "input_type": "number",
  "context_key": "menu_option"
}

// Fica no contexto:
{
  "menu_option": "2"
}
```

---

## 💡 Exemplos Práticos

### **Exemplo 1: Verificar se é Montador**

```
[Buscar Parceiro] (get_partner)
     │
     ▼
[Condição: É Montador?]
     │
     ├─ tipo_contato = "M" → [Menu Montador]
     └─ default → [Perguntar se é Cliente]
```

**Edge 1 (Montador):**
```json
{
  "source": "check_partner_type",
  "target": "menu_montador",
  "data": {
    "condition": {
      "type": "context",
      "key": "tipo_contato",
      "value": "M"
    }
  }
}
```

**Edge 2 (Default):**
```json
{
  "source": "check_partner_type",
  "target": "ask_is_customer"
  // Sem "data" → edge default
}
```

---

### **Exemplo 2: Menu com Números**

```
[Mensagem: "Digite 1, 2 ou 3"]
     │
     ▼
[Input: Captura Número]
     │
     ▼
[Condição: Qual opção?]
     │
     ├─ text = "1" → [Opção 1]
     ├─ text = "2" → [Opção 2]
     ├─ text = "3" → [Opção 3]
     └─ default → [Mensagem de Erro]
```

**Edge Opção 1:**
```json
{
  "source": "route_menu",
  "target": "opcao_1",
  "data": {
    "condition": {
      "type": "equals",
      "values": ["1", "um"]
    }
  }
}
```

---

### **Exemplo 3: Selecionar Loja**

```
[Lista de Lojas]
     │
     ▼
[Input: Loja Selecionada]
     │
     ▼
[Condição: Qual Loja?]
     │
     ├─ contém "goiabeira" → [Transfer: Goiabeiras]
     ├─ contém "laranjeira" → [Transfer: Laranjeiras]
     └─ etc...
```

**Edge Goiabeiras:**
```json
{
  "source": "route_loja",
  "target": "transfer_goiabeiras",
  "data": {
    "condition": {
      "type": "contains",
      "values": ["goiabeira", "goiabeiras"]
    }
  }
}
```

---

## 🔍 Debug e Visualização

### **1. Ver Contexto de um Usuário**

**API:**
```bash
curl http://localhost:5000/api/v1/flows/debug/context/5527999999999
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "msisdn": "5527999999999",
    "context": {
      "stage": "receive_is_customer",
      "previous_stage": "ask_is_customer",
      "cpf": "12345678901",
      "codparc": "12345",
      "nomeparc": "João Silva",
      "is_logged_in": true,
      "customer": { ... }
    },
    "updated_at": "2025-10-26T22:30:00"
  }
}
```

---

### **2. Listar Todas as Conversas Ativas**

**API:**
```bash
curl http://localhost:5000/api/v1/flows/debug/context
```

**Resposta:**
```json
{
  "success": true,
  "data": [
    {
      "msisdn": "5527999999999",
      "stage": "receive_menu_principal",
      "updated_at": "2025-10-26T22:30:00",
      "preview": {
        "cpf": "12345678901",
        "codparc": "12345",
        "nomeparc": "João Silva",
        "is_logged_in": true
      }
    }
  ]
}
```

---

### **3. Via Docker (Direto no Banco)**

```bash
# Ver contexto de um número
docker exec bot-danubio-postgres-1 psql -U postgres -d danubio_bot -c \
  "SELECT msisdn, data FROM contexts WHERE msisdn = '5527999999999';"

# Ver últimas conversas
docker exec bot-danubio-postgres-1 psql -U postgres -d danubio_bot -c \
  "SELECT msisdn, data->>'stage' as stage, updated_at FROM contexts ORDER BY updated_at DESC LIMIT 10;"
```

---

## 🎨 Como Configurar Condições no Flow Builder (Atualmente)

### **IMPORTANTE:**

Atualmente, as condições **NÃO podem ser editadas visualmente** no Flow Builder. Você precisa:

1. **Editar o JSON do fluxo diretamente** (via banco ou API)
2. **OU** usar o script de migração que já tem as condições configuradas

### **Workaround Temporário:**

**Opção 1: Editar via API**

```bash
# Buscar fluxo
curl http://localhost:5000/api/v1/flows/2 > flow.json

# Editar flow.json (adicionar condições nas edges)

# Salvar de volta
curl -X PUT http://localhost:5000/api/v1/flows/2 \
  -H "Content-Type: application/json" \
  -d @flow.json
```

**Opção 2: Editar no Banco**

```bash
# Buscar JSON
docker exec bot-danubio-postgres-1 psql -U postgres -d danubio_bot -c \
  "SELECT data FROM flows WHERE id = 2;" > flow.json

# Editar flow.json

# Atualizar (cuidado!)
docker exec -i bot-danubio-postgres-1 psql -U postgres -d danubio_bot <<EOF
UPDATE flows
SET data = '...'::jsonb
WHERE id = 2;
EOF
```

---

## 📝 Estrutura Completa de uma Edge com Condição

```json
{
  "id": "edge_1",
  "source": "node_condition",
  "target": "node_destino",
  "markerEnd": {
    "type": "ArrowClosed"
  },
  "data": {
    "condition": {
      "type": "equals",           // Tipo de condição
      "values": ["sim", "1"],     // Valores (para equals/contains)
      "pattern": "^\\d+$",        // Padrão (para regex)
      "key": "customer",          // Chave (para context)
      "value": "exists"           // Valor esperado (para context)
    },
    "label": "Se responder Sim"  // Label visual (opcional)
  }
}
```

---

## 🚀 Próximas Melhorias

Para facilitar o uso, posso adicionar:

1. **Editor visual de condições** no modal do nó
2. **Painel de debug** no Flow Builder mostrando variáveis
3. **Simulador** para testar condições
4. **Autocomplete** de variáveis disponíveis
5. **Validador** de condições

Quer que eu implemente alguma dessas features? 🎯

---

## 🎯 Resumo Rápido

| Tipo | Quando Usar | Exemplo |
|------|-------------|---------|
| `equals` | Texto exato | Menu com números |
| `contains` | Texto contém | Seleção de loja |
| `regex` | Validação complexa | Formato de telefone |
| `context` | Verificar variável | É montador? |
| `is_positive` | Sim/Não | Confirmações |
| `is_digit` | Apenas números | Input numérico |

---

**Variáveis Principais no Contexto:**
- `stage` - Nó atual
- `previous_stage` - Nó anterior
- `tipo_contato` - "M" ou "C" (após get_partner)
- `cpf` - CPF do usuário
- `codparc` - Código do parceiro
- `customer` - Dados do cliente
- `customer_orders` - Produtos pendentes
- `customer_services` - Serviços pendentes
- Qualquer `context_key` configurado em nós de Input

---

Agora você pode **visualizar** o contexto e **entender** como configurar condições! 🚀
