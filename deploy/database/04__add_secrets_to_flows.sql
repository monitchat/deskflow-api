\c danubio_bot

-- Adiciona coluna secrets para armazenar credenciais por fluxo
-- Cada fluxo pode ter suas próprias API keys, tokens, senhas, etc.
-- No JSON do fluxo, use ${{secret.NOME_DA_CHAVE}} para referenciar
ALTER TABLE flows ADD COLUMN IF NOT EXISTS secrets JSONB DEFAULT '{}';
