-- MCP Core v2 Design Session Schema
-- Schema: amadeus
-- Database: PostgreSQL (Supabase)

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS amadeus;

-- Set search path
SET search_path TO amadeus, public;

-- ============================================
-- Core Catalog Tables
-- ============================================

-- Wire specifications
CREATE TABLE IF NOT EXISTS wires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    size_sqmm DECIMAL(10,2) NOT NULL,
    material VARCHAR(50) DEFAULT 'copper',
    insulation VARCHAR(50) DEFAULT 'PVC',
    max_current_amp DECIMAL(10,2) NOT NULL,
    voltage_rating INTEGER DEFAULT 450,
    temperature_rating INTEGER DEFAULT 70,
    price_per_meter DECIMAL(10,2),
    brand VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(size_sqmm, material, insulation)
);

-- Circuit breaker specifications
CREATE TABLE IF NOT EXISTS breakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rated_current INTEGER NOT NULL,
    poles INTEGER DEFAULT 1 CHECK (poles BETWEEN 1 AND 4),
    breaking_capacity_ka DECIMAL(5,2) DEFAULT 6.0,
    curve_type CHAR(1) DEFAULT 'C' CHECK (curve_type IN ('B', 'C', 'D')),
    brand VARCHAR(100),
    model VARCHAR(100),
    price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conduit specifications
CREATE TABLE IF NOT EXISTS conduits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    internal_diameter_mm DECIMAL(10,2) NOT NULL,
    external_diameter_mm DECIMAL(10,2) NOT NULL,
    material VARCHAR(50) DEFAULT 'PVC',
    color VARCHAR(50) DEFAULT 'white',
    price_per_meter DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Outlet specifications
CREATE TABLE IF NOT EXISTS outlets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outlet_type VARCHAR(50) NOT NULL,
    rated_current INTEGER DEFAULT 16,
    rated_voltage INTEGER DEFAULT 250,
    num_sockets INTEGER DEFAULT 1,
    grounding BOOLEAN DEFAULT TRUE,
    brand VARCHAR(100),
    model VARCHAR(100),
    price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Light fixture specifications
CREATE TABLE IF NOT EXISTS light_fixtures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fixture_type VARCHAR(50) NOT NULL,
    wattage DECIMAL(10,2) NOT NULL,
    lumens DECIMAL(10,2) NOT NULL,
    color_temp_k INTEGER DEFAULT 4000,
    led BOOLEAN DEFAULT TRUE,
    dimmable BOOLEAN DEFAULT FALSE,
    ip_rating VARCHAR(10) DEFAULT 'IP20',
    brand VARCHAR(100),
    model VARCHAR(100),
    price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Room design templates
CREATE TABLE IF NOT EXISTS room_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_type VARCHAR(50) NOT NULL,
    min_area_sqm DECIMAL(10,2) NOT NULL,
    max_area_sqm DECIMAL(10,2) NOT NULL,
    outlet_rules JSONB NOT NULL DEFAULT '{}',
    lighting_rules JSONB NOT NULL DEFAULT '{}',
    circuit_rules JSONB NOT NULL DEFAULT '{}',
    compliance_standard VARCHAR(50) DEFAULT 'EIT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance rules
CREATE TABLE IF NOT EXISTS compliance_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code VARCHAR(50) NOT NULL UNIQUE,
    rule_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    check_function VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'error' CHECK (severity IN ('error', 'warning', 'info')),
    standard VARCHAR(50) DEFAULT 'EIT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Design Session Tables
-- ============================================

-- Design sessions (projects)
CREATE TABLE IF NOT EXISTS design_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(100) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'archived')),
    input_data JSONB NOT NULL,
    output_data JSONB,
    compliance_result JSONB,
    autolisp_script TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Room designs within sessions
CREATE TABLE IF NOT EXISTS room_designs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES design_sessions(id) ON DELETE CASCADE,
    room_id VARCHAR(100) NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    width_m DECIMAL(10,2) NOT NULL,
    length_m DECIMAL(10,2) NOT NULL,
    height_m DECIMAL(10,2) DEFAULT 2.8,
    area_sqm DECIMAL(10,2) GENERATED ALWAYS AS (width_m * length_m) STORED,
    design_data JSONB NOT NULL,
    total_load_watts DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, room_id)
);

-- Circuit designs
CREATE TABLE IF NOT EXISTS circuit_designs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_design_id UUID REFERENCES room_designs(id) ON DELETE CASCADE,
    circuit_id VARCHAR(100) NOT NULL,
    circuit_type VARCHAR(50) NOT NULL,
    breaker_size INTEGER NOT NULL,
    wire_size_sqmm DECIMAL(10,2) NOT NULL,
    conduit_size_mm DECIMAL(10,2) NOT NULL,
    total_load_watts DECIMAL(10,2) NOT NULL,
    connected_devices JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(room_design_id, circuit_id)
);

-- ============================================
-- Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_wires_size ON wires(size_sqmm);
CREATE INDEX IF NOT EXISTS idx_wires_current ON wires(max_current_amp);
CREATE INDEX IF NOT EXISTS idx_breakers_current ON breakers(rated_current);
CREATE INDEX IF NOT EXISTS idx_room_templates_type ON room_templates(room_type);
CREATE INDEX IF NOT EXISTS idx_room_templates_area ON room_templates(min_area_sqm, max_area_sqm);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_type ON compliance_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_design_sessions_project ON design_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_design_sessions_status ON design_sessions(status);
CREATE INDEX IF NOT EXISTS idx_room_designs_session ON room_designs(session_id);

-- ============================================
-- Seed Data - Standard Wire Sizes
-- ============================================

INSERT INTO wires (size_sqmm, material, insulation, max_current_amp, voltage_rating) VALUES
    (1.0, 'copper', 'PVC', 11, 450),
    (1.5, 'copper', 'PVC', 14, 450),
    (2.5, 'copper', 'PVC', 18, 450),
    (4.0, 'copper', 'PVC', 24, 450),
    (6.0, 'copper', 'PVC', 31, 450),
    (10.0, 'copper', 'PVC', 42, 450),
    (16.0, 'copper', 'PVC', 56, 450),
    (25.0, 'copper', 'PVC', 73, 450),
    (35.0, 'copper', 'PVC', 89, 450),
    (50.0, 'copper', 'PVC', 108, 450),
    (70.0, 'copper', 'PVC', 136, 450),
    (95.0, 'copper', 'PVC', 164, 450),
    (120.0, 'copper', 'PVC', 188, 450)
ON CONFLICT (size_sqmm, material, insulation) DO NOTHING;

-- ============================================
-- Seed Data - Standard Breaker Sizes
-- ============================================

INSERT INTO breakers (rated_current, poles, breaking_capacity_ka, curve_type) VALUES
    (6, 1, 6.0, 'C'),
    (10, 1, 6.0, 'C'),
    (16, 1, 6.0, 'C'),
    (20, 1, 6.0, 'C'),
    (25, 1, 6.0, 'C'),
    (32, 1, 6.0, 'C'),
    (40, 1, 6.0, 'C'),
    (50, 1, 6.0, 'C'),
    (63, 1, 6.0, 'C'),
    (80, 1, 10.0, 'C'),
    (100, 1, 10.0, 'C'),
    (125, 1, 10.0, 'C')
ON CONFLICT DO NOTHING;

-- ============================================
-- Seed Data - Standard Conduit Sizes
-- ============================================

INSERT INTO conduits (internal_diameter_mm, external_diameter_mm, material) VALUES
    (16, 20, 'PVC'),
    (20, 25, 'PVC'),
    (25, 32, 'PVC'),
    (32, 40, 'PVC'),
    (40, 50, 'PVC'),
    (50, 63, 'PVC'),
    (63, 75, 'PVC')
ON CONFLICT DO NOTHING;

-- ============================================
-- Seed Data - Compliance Rules
-- ============================================

INSERT INTO compliance_rules (rule_code, rule_type, description, check_function, parameters, severity) VALUES
    ('EIT-4.2.1', 'outlet_spacing', 'Maximum outlet spacing is 4.5m', 'check_outlet_spacing', '{"max_spacing_m": 4.5}', 'error'),
    ('EIT-4.3.1', 'wire_sizing', 'Wire must be rated for 125% of circuit load', 'check_wire_rating', '{"safety_factor": 1.25}', 'error'),
    ('EIT-4.4.1', 'breaker_coordination', 'Breaker must be rated <= wire ampacity', 'check_breaker_coordination', '{}', 'error'),
    ('EIT-5.1.1', 'lighting_level', 'Minimum lighting levels per room type', 'check_lighting_level', '{}', 'warning'),
    ('EIT-6.1.1', 'voltage_drop', 'Maximum voltage drop is 3%', 'check_voltage_drop', '{"max_drop_percent": 3.0}', 'error'),
    ('EIT-7.1.1', 'conduit_fill', 'Maximum conduit fill per conductor count', 'check_conduit_fill', '{}', 'warning')
ON CONFLICT (rule_code) DO NOTHING;

-- ============================================
-- Row Level Security (RLS)
-- ============================================

-- Enable RLS on design_sessions
ALTER TABLE design_sessions ENABLE ROW LEVEL SECURITY;

-- Policy for authenticated users to see their own sessions
CREATE POLICY IF NOT EXISTS "Users can view own sessions"
    ON design_sessions FOR SELECT
    USING (auth.uid()::text = created_by OR created_by IS NULL);

CREATE POLICY IF NOT EXISTS "Users can insert own sessions"
    ON design_sessions FOR INSERT
    WITH CHECK (auth.uid()::text = created_by OR created_by IS NULL);

CREATE POLICY IF NOT EXISTS "Users can update own sessions"
    ON design_sessions FOR UPDATE
    USING (auth.uid()::text = created_by OR created_by IS NULL);

-- ============================================
-- Functions
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables
DROP TRIGGER IF EXISTS update_wires_updated_at ON wires;
CREATE TRIGGER update_wires_updated_at
    BEFORE UPDATE ON wires
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_design_sessions_updated_at ON design_sessions;
CREATE TRIGGER update_design_sessions_updated_at
    BEFORE UPDATE ON design_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_room_designs_updated_at ON room_designs;
CREATE TRIGGER update_room_designs_updated_at
    BEFORE UPDATE ON room_designs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
