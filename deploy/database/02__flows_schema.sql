\c danubio_bot

-- Tabela para armazenar fluxos de conversação
CREATE TABLE flows
(
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    data        JSONB        NOT NULL, -- Estrutura JSON com nós e conexões
    is_active   BOOLEAN      NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX flows_is_active_idx ON flows (is_active);
CREATE INDEX flows_data_idx ON flows USING GIN (data);

-- Tabela para versionamento de fluxos
CREATE TABLE flow_versions
(
    id         SERIAL PRIMARY KEY,
    flow_id    INTEGER      NOT NULL REFERENCES flows (id) ON DELETE CASCADE,
    version    INTEGER      NOT NULL,
    data       JSONB        NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX flow_versions_flow_id_idx ON flow_versions (flow_id);
CREATE INDEX flow_versions_version_idx ON flow_versions (flow_id, version);

-- Inserir fluxo default baseado no fluxo atual
INSERT INTO flows (name, description, data, is_active)
VALUES (
    'Fluxo Principal',
    'Fluxo de atendimento padrão do Client Bot',
    '{
        "nodes": [],
        "edges": [],
        "metadata": {
            "created_by": "system",
            "version": "1.0.0"
        }
    }'::jsonb,
    true
);
