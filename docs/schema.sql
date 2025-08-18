-- ===============================
-- SCHEMA OLGA_AI
-- ===============================

-- CLIENTES
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- APÓLICES
CREATE TABLE IF NOT EXISTS policies (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    policy_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','INACTIVE','CANCELLED')),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- FILA DE ATENDIMENTO
CREATE TABLE IF NOT EXISTS atendimento_queue (
    id BIGSERIAL PRIMARY KEY,
    phone TEXT NOT NULL,
    message TEXT NOT NULL,
    priority INT NOT NULL DEFAULT 5, -- menor número = mais prioridade
    status TEXT NOT NULL DEFAULT 'AGUARDANDO'
        CHECK (status IN ('AGUARDANDO','PROCESSANDO','CONCLUIDO','ERRO')),
    retry_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_queue_status_priority
    ON atendimento_queue(status, priority, created_at);

CREATE INDEX IF NOT EXISTS idx_queue_phone
    ON atendimento_queue(phone);

-- SINISTROS (mock para fluxo LangGraph)
CREATE TABLE IF NOT EXISTS sinistros (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    protocol TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN','IN_REVIEW','CLOSED','REJECTED')),
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SESSÕES DE USUÁRIO (para simular contexto de conversa)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    phone TEXT NOT NULL,
    session_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
