CREATE TABLE IF NOT EXISTS mcp_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    agent VARCHAR(30) NOT NULL,
    tool VARCHAR(50) NOT NULL,
    params JSONB,
    result_summary TEXT,
    latency_ms INT,
    was_cached BOOLEAN DEFAULT false,
    sandbox_violations TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    source_ip VARCHAR(45),
    api_key_prefix VARCHAR(8),
    endpoint VARCHAR(200),
    details JSONB,
    severity VARCHAR(10) DEFAULT 'info',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mcp_audit_agent ON mcp_audit_log(agent);
CREATE INDEX IF NOT EXISTS idx_security_audit_type ON security_audit_log(event_type);
