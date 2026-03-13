# 🎨 Guia Rápido: Editor Visual de Condições

## ✨ Novo! Editor Visual Implementado

Agora você pode **configurar condições clicando**, sem precisar editar JSON! 🎉

---

## 🚀 Como Usar

### **Passo 1: Criar Conexão**

1. Arraste da borda inferior de um nó
2. Solte na borda superior do nó de destino
3. Conexão é criada (cinza = sem condição)

### **Passo 2: Adicionar Condição**

1. **Clique na conexão** (linha entre os nós)
2. Modal abre automaticamente ⚡
3. Configure a condição
4. Clique em "Salvar Condição"
5. Conexão muda de cor! 🎨

---

## 🎨 Cores das Condições

Cada tipo de condição tem uma cor diferente:

| Cor | Tipo | Quando Usar |
|-----|------|-------------|
| 🟢 **Verde** | Equals | Texto exato (menu numérico) |
| 🔵 **Azul** | Contains | Texto parcial (selecionar loja) |
| 🟠 **Laranja** | Context | Verificar variável do contexto |
| 🟣 **Roxo** | Positive | Resposta sim/ok |
| 🔷 **Ciano** | Digit | Apenas números |
| 🔴 **Vermelho** | Regex | Validação complexa |
| ⚪ **Cinza** | Sem condição | Default/fallback |

---

## 📝 Tipos de Condições

### **1. Equals (Igual a) 🟢**

Compara texto exato.

**Quando usar:**
- Menus numéricos (1, 2, 3)
- Opções específicas

**Exemplo:**
```
Valores:
1
um
primeiro
```

**Resultado:**
- Usuário digita "1" → ✅ Match
- Usuário digita "um" → ✅ Match
- Usuário digita "2" → ❌ Não match

---

### **2. Contains (Contém) 🔵**

Verifica se o texto contém algo.

**Quando usar:**
- Seleção de lojas/cidades
- Busca por palavras-chave

**Exemplo:**
```
Valores:
goiabeira
laranjeira
vila velha
```

**Resultado:**
- Usuário digita "Vitória/Goiabeiras" → ✅ Match
- Usuário digita "vou em laranjeiras" → ✅ Match
- Usuário digita "cachoeiro" → ❌ Não match

---

### **3. Context (Contexto) 🟠**

Verifica valor salvo no contexto (banco).

**Quando usar:**
- Verificar se é montador
- Verificar se cliente existe
- Verificar qualquer variável salva

**Variáveis comuns:**
- `tipo_contato` → "M" (montador) ou "C" (cliente)
- `customer` → "exists" (cliente encontrado?)
- `cpf` → CPF do usuário
- `codparc` → Código do parceiro

**Exemplo 1: É montador?**
```
Chave: tipo_contato
Valor: M
```

**Exemplo 2: Cliente existe?**
```
Chave: customer
Valor: exists
```

---

### **4. Positive (Resposta Positiva) 🟣**

Detecta respostas afirmativas automaticamente.

**Quando usar:**
- Confirmações
- Perguntas Sim/Não

**Detecta automaticamente:**
- sim, yes, ok, okay, claro, com certeza, etc.

**Exemplo:**
- Usuário digita "sim" → ✅ Match
- Usuário digita "OK" → ✅ Match
- Usuário digita "não" → ❌ Não match

---

### **5. Digit (É Número) 🔷**

Verifica se é apenas dígitos.

**Quando usar:**
- Validar input numérico
- Menu com números

**Exemplo:**
- Usuário digita "123" → ✅ Match
- Usuário digita "1a" → ❌ Não match

---

### **6. Regex (Expressão Regular) 🔴**

Validação complexa com padrões.

**Quando usar:**
- Validar formato de telefone
- Validar formato de CPF
- Validações customizadas

**Exemplos de padrões:**
```
^\d{11}$           → Exatamente 11 dígitos
^[0-9]+$           → Apenas números
^\d{3}\.\d{3}\.\d{3}-\d{2}$ → CPF formatado
```

---

## 🎯 Exemplo Prático Completo

### **Cenário: Menu com 3 Opções**

```
[Mensagem: "Digite 1, 2 ou 3"]
     │
     ▼
[Condição: Rotear]
     │
     ├─ 🟢 equals "1" → [Opção 1]
     ├─ 🟢 equals "2" → [Opção 2]
     ├─ 🟢 equals "3" → [Opção 3]
     └─ ⚪ default → [Erro: opção inválida]
```

**Como configurar:**

1. **Criar nó Condição** "Rotear"
2. **Conectar** às 4 opções
3. **Clicar** na conexão para Opção 1:
   - Tipo: Equals
   - Valores: `1` e `um`
   - Rótulo: "Opção 1"
4. **Repetir** para Opção 2 e 3
5. **Deixar última conexão sem condição** (default)

---

## 🔍 Ver Variáveis do Contexto

Use as APIs de debug para ver quais variáveis estão disponíveis:

```bash
# Ver todas conversas
curl http://localhost:5000/api/v1/flows/debug/context

# Ver contexto de um número
curl http://localhost:5000/api/v1/flows/debug/context/5527999999999
```

**Resposta mostra:**
```json
{
  "context": {
    "stage": "receive_is_customer",
    "cpf": "12345678901",
    "codparc": "12345",
    "tipo_contato": "M",
    "customer": { ... }
  }
}
```

**Agora você sabe quais variáveis pode usar em condições!**

---

## 💡 Dicas

### ✅ **DO (Faça):**
- Use cores para identificar condições rapidamente
- Sempre tenha uma edge default (sem condição)
- Use rótulos descritivos nas conexões
- Teste cada condição depois de configurar
- Consulte o contexto via API de debug

### ❌ **DON'T (Não Faça):**
- Não deixe nó de condição sem edges
- Não crie condições conflitantes (nunca vão ser alcançadas)
- Não esqueça de salvar o fluxo depois

---

## 🚀 Workflow Completo

1. **Criar nós** (arrastar da sidebar)
2. **Conectar nós** (arrastar das bordas)
3. **Clicar nas conexões** para adicionar condições
4. **Ver preview** no modal
5. **Salvar condição**
6. **Ver cor mudar** ✨
7. **Salvar fluxo** (botão no topo)
8. **Testar** no WhatsApp

---

## 🎨 Preview Visual

Quando você salva uma condição, a conexão mostra:
- **Cor** do tipo de condição
- **Label** com o nome ou tipo
- **Linha mais grossa** (2px vs 1px)

**Exemplo:**
```
[Nó A] ──🟢──✓ equals─→ [Nó B]
          ↑
       Verde, grosso
```

---

## 🔧 Editar Condição Existente

1. **Clique na conexão**
2. Modal abre com valores atuais
3. **Edite** o que quiser
4. **Salvar** → Cor atualiza automaticamente

---

## 🗑️ Remover Condição

**Opção 1:** Mudar para "Sem condição (Default)"
**Opção 2:** Deletar a conexão inteira

---

## 📖 Documentação Completa

- **GUIA_CONDICOES.md** → Detalhes técnicos
- **FLOW_BUILDER_README.md** → Guia completo do Flow Builder
- **INICIO_RAPIDO.md** → Início rápido

---

## 🎉 Pronto!

Agora você pode configurar condições **visualmente**!

**Não precisa mais editar JSON!** 🚀

---

**Dúvidas? Veja:**
- Legenda de cores na sidebar do Flow Builder
- GUIA_CONDICOES.md para casos avançados
- API de debug para ver variáveis disponíveis
