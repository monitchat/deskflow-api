\c danubio_bot

CREATE TABLE activity
(
    id         SERIAL PRIMARY KEY,
    content    JSONB       NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX activity_content_idx ON activity USING GIN (content);
CREATE INDEX activity_created_at_idx ON public.activity (created_at);

--

CREATE TABLE contexts
(
    msisdn     VARCHAR(16) NOT NULL,
    data       JSONB       NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX contexts_msisdn_idx ON contexts (msisdn);
ALTER TABLE contexts ADD created_at TIMESTAMPTZ null;

--

CREATE TABLE survey
(
    id             SERIAL PRIMARY KEY,
    pre_order_id     VARCHAR(32) NOT NULL,
    msisdn         VARCHAR(16) NOT NULL,
    content        JSONB       NOT NULL,
    status         VARCHAR(16) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX survey_pre_order_id_idx ON survey (pre_order_id);

CREATE TABLE optouts
(
    msisdn     VARCHAR(16) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX optouts_msisdn_idx ON optouts (msisdn);

CREATE TABLE automatic_messages
(
    id         SERIAL PRIMARY KEY,
    regular_period  BOOLEAN NOT NULL,
    data       JSONB       NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ends_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE activity  ADD caller VARCHAR(80) NULL;
CREATE INDEX caller_idx ON activity USING BTREE(caller);

CREATE TABLE settings
(
    id             SERIAL PRIMARY KEY,
    data           JSONB NOT NULL
);

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
