# 🎯 Guia do Nó Router Inteligente

## 📋 O que é o Router?

O **Router Inteligente** é um nó especial que combina as funcionalidades de:
- ✅ **INPUT**: Captura e salva o input do usuário
- ✅ **CONDITION**: Avalia múltiplas condições
- ✅ **VALIDAÇÃO**: Exibe mensagem de erro quando nenhuma condição for atendida
- ✅ **RETRY**: Mantém o usuário no mesmo nó até digitar algo válido

---

## 🆚 Diferença entre CONDITION e ROUTER

### **Nó CONDITION** (original)
```
Usuário digita "xuxu"
  → Não dá match em nenhuma condição
  → Segue pela edge default (se existir)
  → OU fica travado sem resposta
```

### **Nó ROUTER** ✨ (novo)
```
Usuário digita "xuxu"
  → Não dá match em nenhuma condição
  → Exibe mensagem de erro customizada
  → Mantém usuário no router
  → Usuário tenta novamente até acertar
```

---

## 🚀 Como Usar

### **Passo 1: Adicionar Router ao Canvas**

1. Arraste **"Router Inteligente"** da sidebar (ícone 🎯)
2. Clique no nó para editar

### **Passo 2: Configurar Router**

Campos disponíveis:

#### **Rótulo** (opcional)
Nome descritivo do router
```
Ex: "Menu Principal"
```

#### **Mensagem de Erro** (obrigatório)
Mensagem exibida quando nenhuma condição for atendida
```
Ex: "Opção inválida! Digite 1, 2 ou 3."
```

#### **Salvar input em** (opcional)
Chave para salvar o input do usuário no contexto
```
Ex: "menu_option"
```

### **Passo 3: Conectar Saídas**

1. **Conecte o router a múltiplos nós** (uma conexão para cada opção válida)
2. **Clique em cada conexão** e configure uma condição:
   - 🟢 **Equals**: Para menu numérico (1, 2, 3)
   - 🔵 **Contains**: Para seleção de texto ("goiabeira", "laranjeira")
   - Etc.

---

## 💡 Exemplo Prático: Menu de Opções

### **Cenário:**
Menu com 3 opções. Se usuário digitar algo inválido, mostrar erro e pedir novamente.

### **Estrutura do Fluxo:**

```
[Mensagem: "Digite 1, 2 ou 3"]
           │
           ▼
    [Router: Menu]
           │
           ├─ 🟢 equals "1" → [Opção 1: Produtos]
           ├─ 🟢 equals "2" → [Opção 2: Serviços]
           └─ 🟢 equals "3" → [Opção 3: Crediário]
```

### **Configuração do Router:**

```json
{
  "label": "Menu Principal",
  "error_message": "Opção inválida! Por favor, digite 1, 2 ou 3.",
  "context_key": "menu_option"
}
```

### **Configuração das Conexões:**

**Edge 1 (Produtos):**
```json
{
  "condition": {
    "type": "equals",
    "values": ["1", "um", "produtos"]
  },
  "label": "Opção 1"
}
```

**Edge 2 (Serviços):**
```json
{
  "condition": {
    "type": "equals",
    "values": ["2", "dois", "servicos"]
  },
  "label": "Opção 2"
}
```

**Edge 3 (Crediário):**
```json
{
  "condition": {
    "type": "equals",
    "values": ["3", "tres", "crediario"]
  },
  "label": "Opção 3"
}
```

---

## 📊 Comportamento em Execução

### **Cenário 1: Input Válido**
```
Bot: "Digite 1, 2 ou 3"
User: "1"
  → ✅ Dá match na condição "equals ['1']"
  → Vai para nó "Opção 1: Produtos"
  → Contexto: { "menu_option": "1" }
```

### **Cenário 2: Input Inválido**
```
Bot: "Digite 1, 2 ou 3"
User: "xuxu"
  → ❌ Não dá match em nenhuma condição
  → Exibe: "Opção inválida! Por favor, digite 1, 2 ou 3."
  → Mantém stage no router
  → Aguarda novo input

User: "2"
  → ✅ Dá match na condição "equals ['2']"
  → Vai para nó "Opção 2: Serviços"
  → Contexto: { "menu_option": "2" }
```

### **Cenário 3: Múltiplas Tentativas**
```
Bot: "Digite 1, 2 ou 3"
User: "abc"
  → ❌ Erro: "Opção inválida! Por favor, digite 1, 2 ou 3."

User: "xyz"
  → ❌ Erro: "Opção inválida! Por favor, digite 1, 2 ou 3."

User: "3"
  → ✅ Match! Vai para "Opção 3: Crediário"
```

---

## 🎨 Exemplo Avançado: Seleção de Loja

### **Cenário:**
Usuário seleciona loja digitando parte do nome. Se não encontrar, mostrar erro.

### **Configuração do Router:**

```json
{
  "label": "Seleção de Loja",
  "error_message": "Loja não encontrada! Digite: Goiabeiras, Laranjeiras ou Vila Velha",
  "context_key": "loja_selecionada"
}
```

### **Conexões com CONTAINS:**

**Edge 1:**
```json
{
  "condition": {
    "type": "contains",
    "values": ["goiabeira", "goiabeiras"]
  },
  "label": "Goiabeiras"
}
```

**Edge 2:**
```json
{
  "condition": {
    "type": "contains",
    "values": ["laranjeira", "laranjeiras"]
  },
  "label": "Laranjeiras"
}
```

**Edge 3:**
```json
{
  "condition": {
    "type": "contains",
    "values": ["vila velha", "vv"]
  },
  "label": "Vila Velha"
}
```

### **Teste:**
```
User: "vou em goiabeiras"
  → ✅ Match! (contém "goiabeiras")

User: "quero ir na laranjeira"
  → ✅ Match! (contém "laranjeira")

User: "cachoeiro"
  → ❌ Erro: "Loja não encontrada! Digite: Goiabeiras..."
```

---

## ✅ Vantagens do Router

| Recurso | CONDITION | ROUTER ✨ |
|---------|-----------|-----------|
| Múltiplas saídas | ✅ | ✅ |
| Configuração visual | ✅ | ✅ |
| Salva input no contexto | ❌ | ✅ |
| Mensagem de erro | ❌ | ✅ |
| Retry automático | ❌ | ✅ |
| UX amigável | ❌ | ✅ |

---

## 🔍 Debug e Logs

Quando nenhuma condição for atendida, você verá no log:

```
Router node_5: no condition matched for text='xuxu', showing error message
```

Isso ajuda a identificar quando usuários estão digitando opções inválidas.

---

## 💡 Casos de Uso Comuns

### **1. Menu Numérico**
```
Digite 1, 2, 3 ou 4
  → Router com equals para cada número
  → Erro: "Opção inválida! Digite de 1 a 4."
```

### **2. Seleção de Categoria**
```
Digite: Produtos, Serviços ou Crediário
  → Router com contains para cada categoria
  → Erro: "Categoria inválida! Opções: Produtos, Serviços, Crediário"
```

### **3. Confirmação Sim/Não**
```
Digite SIM ou NÃO
  → Router com is_positive + equals
  → Erro: "Resposta inválida! Digite SIM ou NÃO."
```

### **4. Validação de Formato**
```
Digite apenas números
  → Router com is_digit
  → Erro: "Digite apenas números!"
```

---

## 🚫 O que NÃO Fazer

❌ **Não use router sem mensagem de erro**
- Sempre configure uma mensagem clara

❌ **Não crie condições conflitantes**
- Garanta que apenas uma condição dará match por vez

❌ **Não esqueça de testar todas as opções**
- Teste tanto inputs válidos quanto inválidos

---

## 📝 Estrutura JSON Completa

```json
{
  "id": "node_5",
  "type": "router",
  "data": {
    "label": "Menu Principal",
    "error_message": "Opção inválida! Digite 1, 2 ou 3.",
    "context_key": "menu_option"
  },
  "position": { "x": 400, "y": 300 }
}
```

**Edges:**
```json
[
  {
    "source": "node_5",
    "target": "node_6",
    "data": {
      "condition": {
        "type": "equals",
        "values": ["1"]
      },
      "label": "Opção 1"
    }
  },
  {
    "source": "node_5",
    "target": "node_7",
    "data": {
      "condition": {
        "type": "equals",
        "values": ["2"]
      },
      "label": "Opção 2"
    }
  }
]
```

---

## 🎯 Resumo

O **Router Inteligente** é perfeito para:
- ✅ Menus com validação
- ✅ Seleção de opções com retry
- ✅ Fluxos que exigem input válido
- ✅ UX amigável com feedback claro

**Use quando:** Você quer garantir que o usuário digite algo válido antes de prosseguir.

**Evite quando:** Você quer aceitar qualquer input (use nó INPUT simples).

---

🎉 **Agora você pode criar fluxos inteligentes com validação automática!**
