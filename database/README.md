# Database Architecture & PostGIS Spatial Foundation

This directory contains the database setup and SQL schemas for the **Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System**.

## Schema Overview
- **Spatial Reference System (SRID):** `4326` (WGS 84 GPS Lat/Lon)
- **Spatial Indexing:** R-Tree over GiST spatial indexing (`idx_merchants_location_geom`) for sub-15ms radius filtering (`ST_DWithin`).
- **ORM:** SQLAlchemy 2.0 with GeoAlchemy2 integration.

## Database Entities
1. `crops`: Supported crop varieties (e.g., Tomato, Potato, Rice).
2. `diseases`: Known crop pathologies with pathogen taxonomy (Fungal, Bacterial, Viral, Deficiency).
3. `active_ingredients`: Registered agrochemical chemical entities with standard reference concentration $C_r$, regulatory label dosage caps $D_{\text{label\_max}}$, Pre-Harvest Interval (PHI) constraints, and PPE requirements.
4. `base_treatments`: Agronomic package-of-practices base dosages $D_0$, dilution ratios, and application stages.
5. `merchants`: Local agro-input dealers with GPS `POINT(SRID 4326)` coordinates.
6. `products`: Commercial brand retail offerings with specific concentrations $C_s$, packaging, pricing, inventory stock, and official regulatory registration status.
7. `chemical_incompatibilities`: Prohibited co-application matrix preventing phytotoxicity and negative tank interactions.

## Launching PostgreSQL + PostGIS with Docker
If Docker is installed on your workstation:
```bash
docker compose up -d
```
The database will be initialized with the PostGIS extension and all schema tables automatically from `init_postgis.sql`.
