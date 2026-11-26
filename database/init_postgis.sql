-- ==============================================================================
-- DATABASE INITIALIZATION SCRIPT FOR INTELLIGENT CROP DIAGNOSIS SYSTEM
-- PostGIS Spatial & Relational Schema Definition
-- SRID: 4326 (WGS 84 Geodetic Coordinate Reference System)
-- ==============================================================================

-- 1. Enable PostGIS Extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Clean previous tables if resetting (development only)
-- DROP TABLE IF EXISTS chemical_incompatibilities CASCADE;
-- DROP TABLE IF EXISTS products CASCADE;
-- DROP TABLE IF EXISTS merchants CASCADE;
-- DROP TABLE IF EXISTS base_treatments CASCADE;
-- DROP TABLE IF EXISTS active_ingredients CASCADE;
-- DROP TABLE IF EXISTS diseases CASCADE;
-- DROP TABLE IF EXISTS crops CASCADE;

-- 3. Crop cropss Table
CREATE TABLE IF NOT EXISTS (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    scientific_name VARCHAR(150),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Diseases Table (Fungal, Bacterial, Viral, Nutrient Deficiency, Pest)
CREATE TABLE IF NOT EXISTS diseases (
    id SERIAL PRIMARY KEY,
    crop_id INTEGER NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    disease_name VARCHAR(150) NOT NULL,
    scientific_name VARCHAR(200),
    pathogen_type VARCHAR(50) NOT NULL, -- e.g., Fungal, Bacterial, Viral, Deficiency
    symptoms TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_crop_disease UNIQUE (crop_id, disease_name)
);

-- 5. Active Ingredients Table
CREATE TABLE IF NOT EXISTS active_ingredients (
    id SERIAL PRIMARY KEY,
    common_name VARCHAR(150) NOT NULL UNIQUE,
    chemical_family VARCHAR(100),
    standard_concentration_Cr NUMERIC(8, 2) NOT NULL, -- Reference concentration Cr (e.g. 75.0%)
    concentration_unit VARCHAR(20) DEFAULT '%',
    max_legal_dose_cap NUMERIC(8, 2) NOT NULL, -- Absolute label maximum legal dose (D_label_max)
    phi_days INTEGER NOT NULL DEFAULT 0, -- Pre-Harvest Interval in days
    ppe_requirements TEXT,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Base Treatments Table (Agronomic Package-of-Practices Guidelines)
CREATE TABLE IF NOT EXISTS base_treatments (
    id SERIAL PRIMARY KEY,
    disease_id INTEGER NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    active_ingredient_id INTEGER NOT NULL REFERENCES active_ingredients(id) ON DELETE RESTRICT,
    crop_stage VARCHAR(50) NOT NULL, -- e.g., Vegetative, Flowering, Fruiting
    base_dose_D0 NUMERIC(8, 2) NOT NULL, -- Baseline recommended dose D0 per acre
    dose_unit VARCHAR(30) NOT NULL, -- e.g., kg/acre, g/acre, mL/acre, L/acre
    water_dilution_liters_per_acre NUMERIC(8, 2) DEFAULT 200.0,
    application_method VARCHAR(100) DEFAULT 'Foliar Spray',
    application_timing TEXT,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Merchants Table (Agro-dealers with PostGIS Spatial Point)
CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    contact_email VARCHAR(100),
    address TEXT NOT NULL,
    location_geom GEOMETRY(Point, 4326) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Products Table (Commercial agrochemicals with concentration Cs)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    active_ingredient_id INTEGER NOT NULL REFERENCES active_ingredients(id) ON DELETE RESTRICT,
    brand_name VARCHAR(200) NOT NULL,
    concentration_Cs NUMERIC(8, 2) NOT NULL, -- Actual concentration Cs in retail formulation
    formulation_type VARCHAR(50) NOT NULL, -- e.g., WP, EC, SC, SL, WG
    package_size VARCHAR(50) NOT NULL, -- e.g., "500 g", "1 kg", "1 L"
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    registration_number VARCHAR(100) NOT NULL,
    is_legally_registered BOOLEAN NOT NULL DEFAULT TRUE,
    registered_crops VARCHAR(250) DEFAULT 'Tomato, Potato, Rice',
    registered_diseases VARCHAR(250) DEFAULT 'Early Blight, Late Blight, Blast',
    application_method VARCHAR(100) DEFAULT 'Foliar Spray',
    concentration_unit VARCHAR(20) DEFAULT '%',
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Chemical Incompatibilities Table (Tank-mix safety checks)
CREATE TABLE IF NOT EXISTS chemical_incompatibilities (
    id SERIAL PRIMARY KEY,
    ingredient_a_id INTEGER NOT NULL REFERENCES active_ingredients(id) ON DELETE CASCADE,
    ingredient_b_id INTEGER NOT NULL REFERENCES active_ingredients(id) ON DELETE CASCADE,
    warning_message TEXT NOT NULL,
    incompatibility_type VARCHAR(50) DEFAULT 'Tank-mix phytotoxicity hazard',
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_incompatibility_pair UNIQUE (ingredient_a_id, ingredient_b_id)
);

-- 10. Spatial Indexing
-- R-Tree over GiST index for fast spatial radius search (ST_DWithin)
CREATE INDEX IF NOT EXISTS idx_merchants_location_geom ON merchants USING GIST (location_geom);

-- Indexes for relational join performance
CREATE INDEX IF NOT EXISTS idx_diseases_crop_id ON diseases(crop_id);
CREATE INDEX IF NOT EXISTS idx_base_treatments_disease_id ON base_treatments(disease_id);
CREATE INDEX IF NOT EXISTS idx_products_merchant_id ON products(merchant_id);
CREATE INDEX IF NOT EXISTS idx_products_active_ingredient ON products(active_ingredient_id);
