# TASKS - Danúbio Bot

## Melhorias de Segurança (Futuro)

### 1. JWT - Validação Adicional
- [ ] Adicionar validação de `aud` (audience) no JWT se o servidor de autenticação suportar
- [ ] Adicionar validação de `iss` (issuer) no JWT se o servidor de autenticação suportar
- [ ] Documentar os claims esperados no JWT para facilitar integração

### 2. Rate Limiting
- [ ] Implementar rate limiting nos endpoints de API para prevenir brute force
- [ ] Considerar usar bibliotecas como `Flask-Limiter`
- [ ] Definir limites apropriados por endpoint (ex: 100 requests/minuto por IP)

### 3. Logging de Segurança
- [ ] Adicionar logging detalhado de tentativas de acesso não autorizadas
- [ ] Implementar alertas para padrões suspeitos (múltiplas falhas de auth do mesmo IP)
- [ ] Criar dashboard/relatório de eventos de segurança

### 4. Monitoramento
- [ ] Adicionar métricas de autenticação (sucesso/falha) no Prometheus
- [ ] Criar alertas para picos de falhas de autenticação
- [ ] Monitorar uso de tokens expirados ou inválidos

## Notas
- Sistema atual já possui proteção criptográfica contra modificação de JWT (verificação de assinatura)
- JWT_SECRET deve ser mantido secreto e rotacionado periodicamente
- Tokens não podem ser modificados sem conhecimento da chave secreta
