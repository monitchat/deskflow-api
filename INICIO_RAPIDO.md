# 🚀 Início Rápido - Flow Builder Client

## ✅ Status da Migração

O fluxo existente foi **migrado com sucesso** para o Flow Builder!

- ✅ Banco de dados configurado
- ✅ Fluxo "Fluxo Client (Migrado)" criado
- ✅ 39 nós convertidos
- ✅ 51 conexões mapeadas
- ⚠️  Fluxo criado como **INATIVO** (para teste)

## 🎯 Próximos Passos

### 1. Iniciar o Sistema

**Terminal 1 - Backend Flask:**
```bash
export FLASK_APP=danubio_bot.app
python -m flask run --host=0.0.0.0 --port=5000
```

**Terminal 2 - Frontend React:**
```bash
cd frontend
npm run dev
```

### 2. Acessar o Flow Builder

Abra no navegador: **http://localhost:3000**

Você verá:
- ✅ "Fluxo Principal" (o primeiro criado pelo sistema)
- ✅ "Fluxo Client (Migrado)" ⭐ **É ESTE QUE VOCÊ QUER!**

### 3. Visualizar o Fluxo Migrado

1. Clique em **"Fluxo Client (Migrado)"**
2. Você verá o fluxo completo com todos os nós e conexões
3. Use o mouse para:
   - **Arrastar**: Mover o canvas
   - **Scroll**: Zoom in/out
   - **Clique no nó**: Editar propriedades

### 4. Testar o Fluxo

Antes de ativar em produção:

1. No Flow Builder, clique em **"Ativar"** no card do fluxo
2. Envie mensagens de teste no WhatsApp
3. Verifique se o comportamento está correto

### 5. Fazer Ajustes (Opcional)

Se precisar modificar algo:

1. Clique no nó que deseja editar
2. Altere as propriedades no modal
3. Clique em **"Salvar"**
4. Não esqueça de salvar o fluxo (botão "Salvar Fluxo" no topo)

## 📊 Estrutura do Fluxo Migrado

### Nós Principais

```
[Início]
  └─ [Buscar Parceiro] (API)
       └─ [É Montador?] (Condição)
            ├─ SIM → [Menu Parceiro]
            │          └─ Opções: AT (1), Lojas (2), SAC (3)
            └─ NÃO → [É Cliente?] (Botão)
                       ├─ SIM → [Pedir CPF] → [Buscar Cliente] → [Menu Principal]
                       │                                             ├─ 1: Nova Compra → [Lojas]
                       │                                             ├─ 2: Produtos Pendentes
                       │                                             ├─ 3: Serviços
                       │                                             ├─ 4: Assistência Técnica
                       │                                             └─ 5: SAC
                       └─ NÃO → [Menu Não Cliente]
                                   ├─ 1: Nova Compra → [Lojas]
                                   └─ 2: SAC
```

### Tipos de Nós Usados

| Tipo | Quantidade | Descrição |
|------|-----------|-----------|
| 💬 Mensagem | 12 | Textos enviados ao usuário |
| 🔘 Botões | 2 | Botões interativos |
| 📋 Lista | 2 | Seleção de lojas |
| ⌨️ Input | 5 | Captura de dados do usuário |
| 🔀 Condição | 8 | Ramificação lógica |
| 🔌 API Call | 8 | Integrações com Sankhya |
| 👤 Transferir | 15 | Roteamento para departamentos |
| 🏁 Fim | 1 | Finalização |

### Departamentos Configurados

- **Lojas**:
  - 2287: Goiabeiras
  - 2288: Laranjeiras
  - 2289: Campo Grande
  - 2290: Vila Velha Centro
  - 2291: Portal Glória
  - 2292: Cachoeiro

- **Setores**:
  - 2134: Assistência Técnica
  - 2285: SAC
  - 2286: Serviços

## 🔄 Sistema Híbrido

O sistema funciona em **modo híbrido**:

- ✅ **Com fluxo ativo**: Usa o Flow Builder
- ✅ **Sem fluxo ativo**: Usa o código legado (`bot_stage.py`)

Isso permite:
- Testar o novo fluxo sem quebrar o atual
- Fazer rollback instantâneo se necessário
- Migração gradual e segura

## 🎨 Usando o Flow Builder

### Criar Novo Fluxo

1. Clique em **"+ Novo Fluxo"**
2. Dê um nome e descrição
3. Arraste componentes da barra lateral
4. Conecte os nós
5. Configure cada nó clicando nele
6. Salve o fluxo

### Editar Fluxo Existente

1. Clique no card do fluxo
2. Edite visualmente
3. Salve as alterações
4. Ative quando estiver pronto

### Componentes Disponíveis

Arraste da barra lateral:

- 💬 **Mensagem** → Texto simples
- 🔘 **Botões** → Quick replies (max 3)
- 📋 **Lista** → Seleção de opções
- ⌨️ **Input** → Captura e valida dados
- 🔀 **Condição** → Ramificação inteligente
- 🔌 **API Call** → Integração com Sankhya
- 👤 **Transferir** → Roteamento
- 🏁 **Fim** → Finalizar conversa

## 📚 Documentação Completa

- **FLOW_BUILDER_README.md**: Guia completo do Flow Builder
- **MIGRACAO_FLUXO.md**: Detalhes da migração
- **frontend/README.md**: Documentação técnica do frontend
- **CLAUDE.md**: Documentação do projeto (atualizada)

## 🐛 Problemas Comuns

### Frontend não carrega

```bash
# Certifique-se que o backend está rodando
curl http://localhost:5000/api/v1/health

# Reinstale dependências do frontend
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Fluxo não aparece

```bash
# Verifique no banco
psql -U postgres -d danubio_bot -c "SELECT id, name, is_active FROM flows;"
```

### Bot não responde

1. Verifique se algum fluxo está ativo
2. Se nenhum estiver ativo, usa o código legado
3. Veja os logs do Flask para erros

## 💡 Dicas de Uso

1. **Organize visualmente**: Arrume os nós para facilitar leitura
2. **Use nomes descritivos**: Facilita manutenção
3. **Teste antes de ativar**: Sempre teste em dev primeiro
4. **Salve frequentemente**: Não há auto-save
5. **Use o minimap**: Para navegar em fluxos grandes
6. **Zoom**: Use o scroll do mouse

## 🎯 Comandos Úteis

```bash
# Ver logs do Flask
tail -f nohup.out

# Verificar fluxos no banco
psql -U postgres -d danubio_bot -c "SELECT * FROM flows;"

# Reexecutar migração (substitui fluxo existente)
python scripts/migrate_flow_to_builder.py

# Build frontend para produção
cd frontend
npm run build
# Arquivos vão para /public
```

## ✨ Próximas Melhorias Possíveis

- [ ] Adicionar mais validações de input
- [ ] Criar templates de fluxos comuns
- [ ] Implementar importar/exportar JSON
- [ ] Adicionar analytics de fluxo
- [ ] Criar simulador de conversa
- [ ] Adicionar comentários nos nós
- [ ] Implementar undo/redo visual

## 📞 Suporte

Dúvidas? Consulte:
1. Esta documentação
2. FLOW_BUILDER_README.md
3. Logs do sistema
4. Console do navegador (F12)

---

**Parabéns! 🎉**

Você agora tem um sistema visual para gerenciar o bot sem precisar programar!

Divirta-se criando fluxos! 🚀
