CREATE TABLE IF NOT EXISTS council_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    risk_score FLOAT,
    recommendation TEXT,
    confidence FLOAT,
    round_number INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id) ON DELETE CASCADE,
    agent VARCHAR(30) NOT NULL,
    confidence FLOAT,
    contribution TEXT,
    key_points JSONB,
    model_used VARCHAR(100),
    provider VARCHAR(30),
    round_number INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS debate_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id) ON DELETE CASCADE,
    round_number INT NOT NULL,
    challenger VARCHAR(30),
    challenged VARCHAR(30),
    challenge_text TEXT,
    response_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS llm_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id) ON DELETE CASCADE,
    agent VARCHAR(30),
    provider VARCHAR(30),
    model VARCHAR(100),
    input_tokens INT,
    output_tokens INT,
    latency_ms INT,
    was_fallback BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON council_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON council_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_outputs_session ON agent_outputs(session_id);
