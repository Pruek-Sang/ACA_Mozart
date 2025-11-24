-- ============================================
-- MCP Core v2 - Design Session Schema
-- Runtime state table for design sessions
-- ============================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS mcp;

-- Design Session table
-- Stores runtime state for each MCP design session
CREATE TABLE IF NOT EXISTS mcp.design_session (
    -- Primary identifier
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Project reference
    project_id VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    
    -- Session state
    status VARCHAR(50) NOT NULL DEFAULT 'created',
    -- Possible values: created, running, completed, failed, cancelled
    
    -- Input specification (stored as JSONB)
    input_spec JSONB NOT NULL,
    
    -- Intermediate results (stored as JSONB)
    baseline_context JSONB,
    power_flow_results JSONB,
    
    -- Final result (stored as JSONB)
    result JSONB,
    
    -- Error tracking
    error_message TEXT,
    warnings TEXT[],
    
    -- Metrics
    total_circuits INTEGER,
    compliant_circuits INTEGER,
    total_load_watts NUMERIC(12, 2),
    main_breaker_amps INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Metadata
    created_by VARCHAR(255),
    version VARCHAR(50) DEFAULT '2.0.0',
    metadata JSONB DEFAULT '{}'::JSONB
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_design_session_project_id 
    ON mcp.design_session(project_id);

CREATE INDEX IF NOT EXISTS idx_design_session_status 
    ON mcp.design_session(status);

CREATE INDEX IF NOT EXISTS idx_design_session_created_at 
    ON mcp.design_session(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_design_session_project_status 
    ON mcp.design_session(project_id, status);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION mcp.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_design_session_updated_at
    BEFORE UPDATE ON mcp.design_session
    FOR EACH ROW
    EXECUTE FUNCTION mcp.update_updated_at_column();

-- Comments
COMMENT ON TABLE mcp.design_session IS 
    'Stores runtime state for MCP electrical design sessions';

COMMENT ON COLUMN mcp.design_session.session_id IS 
    'Unique session identifier';

COMMENT ON COLUMN mcp.design_session.project_id IS 
    'Reference to the project being designed';

COMMENT ON COLUMN mcp.design_session.status IS 
    'Current session status: created, running, completed, failed, cancelled';

COMMENT ON COLUMN mcp.design_session.input_spec IS 
    'Original input specification as JSON';

COMMENT ON COLUMN mcp.design_session.baseline_context IS 
    'Resolved baseline context after template resolution';

COMMENT ON COLUMN mcp.design_session.power_flow_results IS 
    'Results from pandapower analysis';

COMMENT ON COLUMN mcp.design_session.result IS 
    'Final McpRunResult as JSON';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON mcp.design_session TO mcp_app;
-- GRANT USAGE ON SCHEMA mcp TO mcp_app;

-- ============================================
-- Sample queries
-- ============================================

-- Get active sessions
-- SELECT * FROM mcp.design_session 
-- WHERE status IN ('created', 'running') 
-- ORDER BY created_at DESC;

-- Get session history for a project
-- SELECT session_id, status, total_circuits, compliant_circuits, created_at, completed_at
-- FROM mcp.design_session
-- WHERE project_id = 'your-project-id'
-- ORDER BY created_at DESC;

-- Get recent completed sessions
-- SELECT * FROM mcp.design_session
-- WHERE status = 'completed'
-- AND completed_at > NOW() - INTERVAL '24 hours'
-- ORDER BY completed_at DESC;
