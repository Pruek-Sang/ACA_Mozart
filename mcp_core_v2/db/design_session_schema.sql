-- Design Session Schema for MCP Core v2
-- Database: PostgreSQL / Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Design Sessions Table
CREATE TABLE IF NOT EXISTS design_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    project_number VARCHAR(100),
    service_voltage VARCHAR(50) NOT NULL,
    utility_service_size INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB
);

-- Electrical Loads Table
CREATE TABLE IF NOT EXISTS electrical_loads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES design_sessions(id) ON DELETE CASCADE,
    load_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    load_type VARCHAR(50) NOT NULL,
    voltage VARCHAR(50) NOT NULL,
    power_watts NUMERIC(10, 2) NOT NULL,
    quantity INTEGER DEFAULT 1,
    power_factor NUMERIC(4, 3),
    location JSONB NOT NULL,
    is_continuous BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, load_id)
);

-- Panel Specifications Table
CREATE TABLE IF NOT EXISTS panel_specifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES design_sessions(id) ON DELETE CASCADE,
    panel_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    voltage VARCHAR(50) NOT NULL,
    main_breaker_rating INTEGER NOT NULL,
    number_of_circuits INTEGER NOT NULL,
    location JSONB NOT NULL,
    feeds JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, panel_id)
);

-- Design Results Table
CREATE TABLE IF NOT EXISTS design_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES design_sessions(id) ON DELETE CASCADE,
    calculations JSONB,
    wire_sizing JSONB,
    breaker_selections JSONB,
    conduit_sizing JSONB,
    compliance_report JSONB,
    autolisp_code TEXT,
    errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id)
);

-- Catalog Breakers Table
CREATE TABLE IF NOT EXISTS catalog_breakers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer VARCHAR(255) NOT NULL,
    model_number VARCHAR(255) NOT NULL,
    breaker_type VARCHAR(50) NOT NULL,
    poles VARCHAR(10) NOT NULL,
    ampere_rating INTEGER NOT NULL,
    voltage_rating INTEGER NOT NULL,
    interrupt_rating INTEGER NOT NULL,
    price NUMERIC(10, 2),
    availability BOOLEAN DEFAULT TRUE,
    catalog_page VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Catalog Wires Table
CREATE TABLE IF NOT EXISTS catalog_wires (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer VARCHAR(255) NOT NULL,
    awg_size VARCHAR(20) NOT NULL,
    material VARCHAR(50) NOT NULL,
    insulation_type VARCHAR(50) NOT NULL,
    voltage_rating INTEGER NOT NULL,
    temperature_rating INTEGER NOT NULL,
    stranding VARCHAR(50),
    price_per_foot NUMERIC(8, 4),
    availability BOOLEAN DEFAULT TRUE,
    color_available JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Catalog Conduits Table
CREATE TABLE IF NOT EXISTS catalog_conduits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer VARCHAR(255) NOT NULL,
    material VARCHAR(50) NOT NULL,
    trade_size VARCHAR(20) NOT NULL,
    length_feet INTEGER DEFAULT 10,
    price_per_length NUMERIC(10, 2),
    availability BOOLEAN DEFAULT TRUE,
    indoor_rated BOOLEAN DEFAULT TRUE,
    outdoor_rated BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Catalog Panels Table
CREATE TABLE IF NOT EXISTS catalog_panels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer VARCHAR(255) NOT NULL,
    model_number VARCHAR(255) NOT NULL,
    panel_type VARCHAR(50) NOT NULL,
    main_breaker_rating INTEGER NOT NULL,
    bus_rating INTEGER NOT NULL,
    voltage INTEGER NOT NULL,
    phases INTEGER NOT NULL,
    number_of_spaces INTEGER NOT NULL,
    max_circuits INTEGER NOT NULL,
    enclosure_type VARCHAR(50),
    price NUMERIC(10, 2),
    availability BOOLEAN DEFAULT TRUE,
    dimensions JSONB,
    weight_lbs NUMERIC(8, 2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_design_sessions_session_id ON design_sessions(session_id);
CREATE INDEX idx_design_sessions_status ON design_sessions(status);
CREATE INDEX idx_design_sessions_created_at ON design_sessions(created_at);

CREATE INDEX idx_electrical_loads_session_id ON electrical_loads(session_id);
CREATE INDEX idx_electrical_loads_load_type ON electrical_loads(load_type);

CREATE INDEX idx_panel_specs_session_id ON panel_specifications(session_id);

CREATE INDEX idx_design_results_session_id ON design_results(session_id);

CREATE INDEX idx_catalog_breakers_rating ON catalog_breakers(ampere_rating);
CREATE INDEX idx_catalog_breakers_type ON catalog_breakers(breaker_type);

CREATE INDEX idx_catalog_wires_size ON catalog_wires(awg_size);
CREATE INDEX idx_catalog_wires_material ON catalog_wires(material);

CREATE INDEX idx_catalog_conduits_size ON catalog_conduits(trade_size);
CREATE INDEX idx_catalog_conduits_material ON catalog_conduits(material);

CREATE INDEX idx_catalog_panels_rating ON catalog_panels(main_breaker_rating);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_design_sessions_updated_at
    BEFORE UPDATE ON design_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_catalog_breakers_updated_at
    BEFORE UPDATE ON catalog_breakers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_catalog_wires_updated_at
    BEFORE UPDATE ON catalog_wires
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_catalog_conduits_updated_at
    BEFORE UPDATE ON catalog_conduits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_catalog_panels_updated_at
    BEFORE UPDATE ON catalog_panels
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE design_sessions IS 'Stores electrical design session information';
COMMENT ON TABLE electrical_loads IS 'Stores individual electrical loads for each design session';
COMMENT ON TABLE panel_specifications IS 'Stores electrical panel specifications';
COMMENT ON TABLE design_results IS 'Stores complete design calculation results';
COMMENT ON TABLE catalog_breakers IS 'Product catalog for circuit breakers';
COMMENT ON TABLE catalog_wires IS 'Product catalog for electrical wires/conductors';
COMMENT ON TABLE catalog_conduits IS 'Product catalog for electrical conduits';
COMMENT ON TABLE catalog_panels IS 'Product catalog for electrical panels';
