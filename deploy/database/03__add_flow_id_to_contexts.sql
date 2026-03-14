-- Migration: Add flow_id to contexts table
-- Purpose: Track which flow the user is currently in, allowing flow switching without losing context data

-- Add flow_id column to contexts table
ALTER TABLE contexts ADD COLUMN IF NOT EXISTS flow_id INTEGER;

-- Add foreign key constraint to flows table
ALTER TABLE contexts
ADD CONSTRAINT fk_contexts_flow_id
FOREIGN KEY (flow_id)
REFERENCES flows(id)
ON DELETE SET NULL;

-- Create index for faster lookups by flow_id
CREATE INDEX IF NOT EXISTS idx_contexts_flow_id ON contexts(flow_id);

-- Comment
COMMENT ON COLUMN contexts.flow_id IS 'ID do fluxo ativo que o usuário está executando. NULL = usa sistema legado';

ALTER TABLE flows ADD COLUMN IF NOT EXISTS company_id INTEGER;
ALTER TABLE flows ADD COLUMN IF NOT EXISTS secrets JSONB DEFAULT '{}';