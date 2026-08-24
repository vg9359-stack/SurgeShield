-- Enable PostGIS spatial extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Drop existing tables to prevent partial schema conflicts
DROP TABLE IF EXISTS simulations CASCADE;
DROP TABLE IF EXISTS settlements CASCADE;
DROP TABLE IF EXISTS dams CASCADE;

-- 1. Dams Table
CREATE TABLE dams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    height_m NUMERIC(5, 2) NOT NULL,
    storage_volume_mcm NUMERIC(8, 2) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL
);

-- 2. Downstream Settlements Table
CREATE TABLE settlements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    population INT DEFAULT 0,
    elevation_m NUMERIC(6, 2),
    location GEOMETRY(Point, 4326) NOT NULL
);

-- 3. Simulation History Table
CREATE TABLE simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dam_id INT REFERENCES dams(id) ON DELETE CASCADE,
    failure_type VARCHAR(50),
    peak_discharge_m3s NUMERIC(10, 2),
    formation_time_min NUMERIC(6, 2),
    breach_width_m NUMERIC(6, 2),
    run_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);