-- Database initialization script for Barn Lady
CREATE SCHEMA IF NOT EXISTS public;

-- Create a table to track tenant schemas
CREATE TABLE IF NOT EXISTS public.tenant_schemas (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(100) UNIQUE NOT NULL,
    schema_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tenant_schemas_org_id ON public.tenant_schemas(org_id);
CREATE INDEX IF NOT EXISTS idx_tenant_schemas_schema_name ON public.tenant_schemas(schema_name);
