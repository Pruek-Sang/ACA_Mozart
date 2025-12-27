# Mozart Stateful Intelligence Schema
# Version: 1.1.0 | Updated: 2025-12-28
#
# This file documents the Supabase schema for Mozart.
# The actual SQL has been executed in Supabase directly.
#
# Tables:
# - mozart.sessions: Temporary working sessions (auto-expire 24h)
# - mozart.projects: Saved design projects (permanent)
#
# See: https://supabase.com/dashboard/project/YOUR_PROJECT/editor

"""
SQL Reference (already executed):

-- 1. Create isolated schema
CREATE SCHEMA IF NOT EXISTS mozart;

-- 2. Sessions Table
CREATE TABLE mozart.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users NOT NULL DEFAULT auth.uid(),
    stage TEXT DEFAULT 'gathering',
    rooms JSONB DEFAULT '[]',
    loads JSONB DEFAULT '[]',
    site_context JSONB DEFAULT '{}',
    messages JSONB DEFAULT '[]',
    partial_requirements JSONB DEFAULT '{}',
    current_spec JSONB,
    mcp_response JSONB,
    status TEXT DEFAULT 'active',
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Projects Table
CREATE TABLE mozart.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users NOT NULL DEFAULT auth.uid(),
    session_id UUID REFERENCES mozart.sessions(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    rooms JSONB DEFAULT '[]',
    loads JSONB DEFAULT '[]',
    site_context JSONB DEFAULT '{}',
    mcp_response JSONB,
    sld_data JSONB,
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES mozart.projects(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. RLS Policies
ALTER TABLE mozart.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE mozart.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own sessions" ON mozart.sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own projects" ON mozart.projects FOR ALL USING (auth.uid() = user_id);
"""
