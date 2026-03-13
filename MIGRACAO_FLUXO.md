# Guia de Migração do Fluxo Client para o Flow Builder

Este guia explica como migrar o fluxo existente do código Python para o Flow Builder visual.

## 📋 Pré-requisitos

1. Banco de dados PostgreSQL configurado
2. Migration `02__flows_schema.sql` aplicada
3. Dependências Python instaladas

## 🚀 Executar Migração

### Passo 1: Aplicar Migration do Banco

```bash
# Se ainda não aplicou
psql -U postgres -d deskflow -f deploy/database/02__flows_schema.sql
```

### Passo 2: Executar Script de Migração

```bash
cd /home/luiz-ricardo/projects/deskflow
python scripts/migrate_flow_to_builder.py
```

O script irá:
- ✅ Criar o fluxo "Fluxo Client (Migrado)" no banco de dados
- ✅ Converter todos os stages para nós visuais
- ✅ Mapear todas as transições para conexões
- ✅ Criar o fluxo como INATIVO (para você testar primeiro)

### Passo 3: Visualizar no Flow Builder

```bash
# Terminal 1 - Backend
export FLASK_APP=deskflow.app
python -m flask run --host=0.0.0.0 --port=5000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Acesse: **http://localhost:3000**

### Passo 4: Revisar o Fluxo

1. Na lista de fluxos, clique em **"Fluxo Client (Migrado)"**
2. Revise os nós e conexões
3. Ajuste conforme necessário
4. **Salve** as alterações

### Passo 5: Testar o Fluxo

Antes de ativar em produção, teste o fluxo:

1. **Ative** o fluxo no Flow Builder
2. Envie mensagens de teste no WhatsApp
3. Verifique se o comportamento está correto
4. Se houver problemas, **desative** e ajuste

### Passo 6: Ativar em Produção

Quando estiver satisfeito com os testes:

1. No Flow Builder, clique em **"Ativar"** no fluxo
2. O sistema automaticamente desativa o fluxo legado
3. O bot passa a usar o novo fluxo visual

## 📊 Estrutura do Fluxo Migrado

O fluxo migrado contém **46 nós** distribuídos em:

### Fluxo Principal

```
[Início]
  → [Buscar Parceiro por Telefone]
    → [É Montador?]
      ├─ Sim → [Menu Parceiro] → [Opções Parceiro]
      └─ Não → [É Cliente?]
          ├─ Sim → [Pedir CPF] → [Menu Cliente]
          └─ Não → [Menu Não Cliente]
```

### Tipos de Nós Utilizados

- **8 nós de API Call**: Buscas no Sankhya
- **15 nós de Transfer**: Roteamento para departamentos
- **12 nós de Message**: Mensagens ao usuário
- **8 nós de Condition**: Lógica de ramificação
- **2 nós de Button**: Botões interativos
- **2 nós de List**: Seleção de lojas
- **5 nós de Input**: Captura de dados
- **1 nó de End**: Finalização

### Departamentos Configurados

- **2287**: Goiabeiras
- **2288**: Laranjeiras
- **2289**: Campo Grande
- **2290**: Vila Velha Centro
- **2291**: Portal Glória
- **2292**: Cachoeiro
- **2134**: Assistência Técnica
- **2285**: SAC
- **2286**: Serviços

## 🔧 Ajustes Comuns

### 1. Mensagens com Variáveis

Algumas mensagens usam placeholders como `{codparc}` e `{nomectt}`. O sistema substitui automaticamente com dados do contexto.

**Exemplo:**
```
Parceiro: *{codparc}*, Contato: *{nomectt}*
```

### 2. Condições Complexas

As condições suportam:
- `equals`: Comparação exata
- `contains`: Contém texto
- `context`: Verifica contexto
- `is_positive`: Resposta positiva (sim, ok)
- `is_digit`: É número

### 3. Validação de CPF

O nó de input já está configurado para validar CPF automaticamente.

## ⚠️ Importante

### Sistema Híbrido

O sistema funciona em modo híbrido:

- **Se houver fluxo ativo**: Usa o Flow Builder
- **Se não houver fluxo ativo**: Usa o código legado (`bot_stage.py`)

Isso permite testar o novo fluxo sem quebrar o sistema atual.

### Rollback

Se precisar voltar ao sistema antigo:

1. No Flow Builder, **desative** o fluxo migrado
2. O sistema volta automaticamente para o código legado
3. Nenhuma alteração no código é necessária

## 🐛 Troubleshooting

### Erro: "No module named deskflow.models"

```bash
# Reinstale o pacote
pip install -e .
```

### Erro: "relation 'flows' does not exist"

```bash
# Aplique a migration
psql -U postgres -d deskflow -f deploy/database/02__flows_schema.sql
```

### Fluxo não aparece no Flow Builder

1. Verifique se o script de migração executou sem erros
2. Consulte o banco de dados:
```sql
SELECT id, name, is_active FROM flows;
```

### Bot não usa o fluxo migrado

1. Verifique se o fluxo está **ativo**
2. Reinicie o servidor Flask
3. Verifique os logs para erros

## 📝 Próximos Passos

Após a migração:

1. **Documente** as mudanças feitas no fluxo
2. **Treine** a equipe no uso do Flow Builder
3. **Monitore** o comportamento do bot
4. **Itere** e melhore o fluxo conforme necessário

## 🎓 Aprendendo o Flow Builder

Para aprender a usar o Flow Builder, consulte:

- **FLOW_BUILDER_README.md**: Documentação completa
- **frontend/README.md**: Documentação técnica do frontend

## 💡 Dicas

1. **Salve frequentemente**: O Flow Builder não tem auto-save
2. **Use nomes descritivos**: Facilita a manutenção
3. **Teste cada alteração**: Antes de ativar em produção
4. **Use versionamento**: O sistema salva versões automaticamente
5. **Organize visualmente**: Arrume os nós para melhor legibilidade

## 📞 Suporte

Dúvidas ou problemas? Consulte:
- FLOW_BUILDER_README.md
- Logs do Flask
- Console do navegador (F12)

---

Boa migração! 🚀
