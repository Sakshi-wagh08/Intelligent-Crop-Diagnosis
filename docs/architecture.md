# System Architecture & Technical Specifications

**Project Title:** Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System  
**Academic Reference:** Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution  

---

## Four Architectural Layers

```
+---------------------------------------------------------------------------------------+
| LAYER 1: DATA INGESTION                                                               |
|  - React.js PWA Client: Image Capture & File Upload                                   |
|  - HTML5 Geolocation API: High-Precision GPS Coordinates (Lat, Lon)                  |
|  - Farmer Telemetry: Crop Type & Phenological Growth Stage Selection                  |
|  - FastAPI Gateway: Async Multipart Request Ingestion & Pydantic Validation           |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| LAYER 2: PROCESSING & TELEMETRY                                                       |
|  [Vision Stream - Phase 2]                      [Geospatial Stream - Phase 3]         |
|   - Image Validation & EXIF Orientation Transpose- Async HTTPX Request                |
|   - Resize (224x224) & ImageNet Normalization    - ISRIC SoilGrids 2.0 RESTful API    |
|   - EfficientNet-B0 ONNX Runtime (FP16/FP32)     - Spatial Cache (~500m Grid, TTL)    |
|   - Disease Classification & Softmax Confidence  - Extraction: pH, SOC, N, CEC,       |
|   - Lesion-to-Leaf Segmentation (S_severity)       Sand, Silt, Clay, wv10, wv33, wv1500|
|   - Severity Tier: Low / Moderate / High         - USDA Soil Texture & Hydraulic AWC  |
|                                                  - Regional Benchmark Fallback Matrix |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| LAYER 3: FUSION & RETAIL ENGINE                                                       |
|  [Multimodal Fusion & Dosage Formulation - Phase 4]                                   |
|   - Agronomic Base Dose Lookup: D0 (from Verified University Package of Practices)    |
|   - Severity Factor Computation: Fv = g(S_severity, is_reliable)                      |
|   - Soil Factor Computation: Fs = f(Application_Method, Soil_Status)                  |
|   - Bounded Formulation: D = min(D0 * Fs * Fv, D_label_max)                           |
|   - Multi-Tier Regulatory Safety Gate (Confidence >= 70%, PHI, Incompatibilities)     |
|                                                                                       |
|  [Supply Chain & Spatial Substitution Engine - Phase 5]                               |
|   - PostGIS R-Tree GiST Spatial Query: ST_DWithin(merchant.geom, farmer.geom, d_max)   |
|   - Chemical Equivalence Filtering: active_ingredient_id == target_active_ingredient   |
|   - Concentration Compensation: Qs = Qr * (Cr / Cs)                                   |
|   - Multi-Objective Ranking: Score = w1*(1/Price) + w2*(1/Distance) + w3*Stock        |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| LAYER 4: CLIENT DELIVERY                                                              |
|  - Sub-2.0 Second End-to-End Delivery over Standard Mobile Networks                   |
|  - PWA Responsive Interface (Tailwind CSS)                                            |
|  - Disease Diagnosis & Severity Visualization Badge                                  |
|  - Soil Chemistry Dashboard Cards                                                     |
|  - Prescribed Dosage & Water Volume Dilution Instructions                             |
|  - Ranked Local Merchants with Google Maps Direction Markers                          |
|  - Offline-Capable Caching via Service Workers                                        |
+---------------------------------------------------------------------------------------+
```

---

## Vision Stream Architecture & Specifications (Phase 2)

### 1. Preprocessing Pipeline
- **Validation:** Enforces MIME types (JPEG, PNG, WEBP), max file size (15 MB), and non-empty readable image buffers.
- **Orientation Normalization:** Automatically corrects mobile camera rotation tags (EXIF tag `0x0112`) using `ImageOps.exif_transpose`.
- **Transformation Pipeline:**
  - Spatial resizing: $(224 \times 224)$ via bicubic interpolation.
  - Channel normalization: Mean $\mu = [0.485, 0.456, 0.406]$, Standard Deviation $\sigma = [0.229, 0.224, 0.225]$.
  - Format decoupling: Generates both PyTorch Tensor `(1, 3, 224, 224)` and ONNX `float32` array `(1, 3, 224, 224)`.

### 2. Model Architecture
- **Backbone:** EfficientNet-B0 (`torchvision.models.efficientnet_b0`).
- **Feature Dimensionality:** 1280 channels from the inverted residual MBConv feature extractor.
- **Classification Head:**
  $$\text{Head} = \text{Dropout}(p=0.2) \to \text{Linear}(1280 \to K)$$
- **Target Classes ($K=7$):**
  - Tomato: `Tomato___Early_Blight`, `Tomato___Late_Blight`, `Tomato___healthy`
  - Potato: `Potato___Late_Blight`, `Potato___healthy`
  - Rice: `Rice___Blast`, `Rice___healthy`

### 3. Disease Severity Formulation ($S_{severity}$)
$$S_{severity} = \frac{\sum_{(x,y) \in \text{Leaf}} \mathbb{I}_{\text{Lesion}}(x, y)}{\sum_{(x,y)} \mathbb{I}_{\text{Leaf}}(x, y)}$$
Where:
- $\mathbb{I}_{\text{Leaf}}(x, y)$ is the binary indicator for foliar canopy pixels segmented in HSV/LAB space.
- $\mathbb{I}_{\text{Lesion}}(x, y)$ is the binary indicator for necrotic brown/black and chlorotic yellow lesion pixels strictly bounded within the leaf canopy.

#### Severity Tiers & Agronomic Canopy Adjustments:
- **None / Trace:** $S_{severity} < 0.01 \implies F_v = 1.00$, baseline carrier water volume ($W_0$)
- **Low:** $0.01 \le S_{severity} \le 0.10 \implies F_v = 1.00$, baseline carrier water volume ($W_0$)
- **Moderate:** $0.10 < S_{severity} \le 0.25 \implies F_v = 1.00$, baseline carrier water volume ($W_0$)
- **High:** $S_{severity} > 0.25 \implies F_v = 1.00$, increased carrier water volume ($W = W_0 \times 1.15$)

> **Regulatory Compliance Note on $F_v$:** Automatic severity-based chemical dosage increases are strictly disabled ($F_v = 1.00$). Official statutory pesticide registrations (CIBRC / DPPQ&S / EPA) mandate fixed active ingredient concentrations and per-hectare limits. Increasing chemical active ingredient dosages based on visual severity violates statutory pesticide label claims, accelerates pathogen resistance, and risks foliar phytotoxicity. Adjustments for severe canopy infection are confined to spray carrier water dilution volume (+15%).

### 4. ONNX Runtime Edge Optimization
- Models are exported using ONNX Opset 17 with dynamic batch dimension: `{"input": {0: "batch_size"}, "output": {0: "batch_size"}}`.
- Cross-runtime numerical consistency is enforced: $\max|\hat{y}_{\text{PyTorch}} - \hat{y}_{\text{ONNX}}| \le 10^{-3}$.

---

## Remote Soil Telemetry Stream Architecture & Specifications (Phase 3)

### 1. Data Ingestion Architecture & Service Protocol
The telemetry module communicates with the official **ISRIC SoilGrids 2.0 RESTful Spatial API** (`https://rest.isric.org/soilgrids/v2.0/properties/query`) via asynchronous HTTPX requests (`httpx.AsyncClient`).

### 2. Supported Soil Properties and Unit Conversions
SoilGrids v2.0 scales physical values by integer factors (`d_factor`) to minimize payload bandwidth. The telemetry engine applies verified mathematical scaling:
- `phh2o`: $d\_factor = 10 \implies \text{pH}$ (dimensionless)
- `soc`: $d\_factor = 10 \implies \text{g/kg}$
- `nitrogen`: $d\_factor = 100 \implies \text{g/kg}$
- `cec`: $d\_factor = 10 \implies \text{cmol}(c)/\text{kg}$
- `sand`, `silt`, `clay`: $d\_factor = 10 \implies \%$
- `wv0010`, `wv0033`, `wv1500`: $d\_factor = 10 \implies \%$ vol
- Available Water Capacity: $\text{AWC} = wv0033 - wv1500$ ($\%$ vol)

### 3. Spatial Coordinate Caching (~500m Grid Pooling)
$$\text{Lat}_{\text{grid}} = \text{round}\left(\frac{\text{Lat}}{0.005}\right) \times 0.005, \quad \text{Lon}_{\text{grid}} = \text{round}\left(\frac{\text{Lon}}{0.005}\right) \times 0.005$$

### 4. Regional Agronomic Fallback Matrix
Published ICAR-NBSS&LUP Karnataka agro-climatic benchmarks (Zones 4, 5, 6, 8, 9, 10). Out-of-bounds coordinates return `data_status: "unavailable"`. **No synthetic values are ever fabricated.**

---

## Multimodal Fusion & Bounded Dosage Recommendation Engine (Phase 4)

### 1. Mathematical Dosage Formulation
$$D = \min\left(D_0 \times F_s \times F_v, \; D_{\text{label\_max}}\right)$$

Where:
- **$D_0$ (Base Dosage):** Official baseline dosage per unit area (e.g. $\text{kg/acre}$ or $\text{L/acre}$) derived from accredited university packages-of-practices (ICAR-IIHR, UAS Bengaluru, CPRI, NRRI) for the specific crop, diagnosed disease, and growth stage.
- **$F_s$ (Soil Factor):**
  - For foliar chemical treatments, active uptake occurs exclusively through leaf cuticular pores, independent of the soil matrix. Therefore, $F_s = 1.00$ (neutral / disabled).
  - When soil telemetry is unavailable, $F_s = 1.00$.
- **$F_v$ (Severity Factor):** Strictly maintained at neutral baseline ($F_v = 1.00$).
  - Official CIBRC/EPA/FAO pesticide product labels strictly specify active ingredient dosage rates per unit area.
  - Artificially increasing pesticide chemical dosage (e.g. $\times 1.05$ or $\times 1.15$) based on foliar symptom severity is NOT authorized by certified product labels, risks foliar phytotoxicity, accelerates pathogen resistance, and violates statutory pesticide regulations.
  - Consequently, chemical dosage multiplier $F_v$ is strictly disabled ($F_v = 1.00$).
- **$D_{\text{label\_max}}$ (Statutory Label Maximum):** Registered ceiling from CIBRC product registration. Dosage is never allowed to exceed this threshold under any circumstance ($D \le D_{\text{label\_max}}$).

### 2. Water Spray Dilution Scaling
Under severe foliar infection ($S_{severity} > 0.25$ or High severity tier), extension guidelines recommend increasing carrier water volume (+15%) to ensure thorough canopy penetration without altering chemical active ingredient concentration:
$$W = W_0 \times 1.15 \quad [\text{L/acre}]$$

### 3. Multi-Tier Regulatory Safety Gate

```
[Diagnostic Telemetry Input]
            │
            ▼
[Gate 1: Healthy Plant Evaluation] ──(Healthy)──► [Status: NO_TREATMENT_NEEDED, Dose: 0.0]
            │ (Infected)
            ▼
[Gate 2: Confidence Threshold Check] ──(< 70%)──► [Status: REJECTED_LOW_CONFIDENCE, Dose Withheld]
            │ (>= 70%)
            ▼
[Gate 3: Treatment Verification Status] ──(Demo)──► [Status: REJECTED_UNVERIFIED, Dose Withheld]
            │ (VERIFIED)
            ▼
[Gate 4: Pre-Harvest Interval (PHI)] ──(Harvest < PHI)──► [Status: REJECTED_PHI_VIOLATION, Dose Prohibited]
            │ (Harvest >= PHI)
            ▼
[Gate 5: Tank-Mix Incompatibility] ──(Incompatible)──► [Status: REJECTED_INCOMPATIBILITY, Dose Withheld]
            │ (Compatible)
            ▼
[Gate 6: Bounded Dosage Formulation]
  D_raw = D0 * Fs * Fv
  D_final = min(D_raw, D_label_max)
            │
            ▼
[Output: Approved Prescription with Traceable Citation & PPE Directives]
```

---

## Localized Merchant Substitution & Spatial Proximity Engine (Phase 5)

### 1. Mathematical Substitution Formulation
When an agro-dealer stocks an alternative commercial product containing the identical active ingredient but at a different concentration $C_s \neq C_r$, the required per-acre product dosage $Q_s$ is adjusted to preserve exact active ingredient rate:
$$Q_s = Q_r \times \left(\frac{C_r}{C_s}\right)$$

Where:
- $Q_r$: Reference recommended dosage per acre (e.g., $0.80\,\text{kg/acre}$)
- $C_r$: Reference formulation active ingredient concentration (e.g., $75.0\%$)
- $C_s$: Substitute retail formulation active ingredient concentration (e.g., $80.0\%$)
- $Q_s$: Adjusted substitute product dosage per acre (e.g., $0.75\,\text{kg/acre}$)

Total product volume required for a given farm area $A$ (acres) and commercial package purchasing requirement:
$$Q_{\text{total}} = Q_s \times A$$
$$\text{Packages Needed} = \left\lceil \frac{Q_{\text{total}}}{\text{Package Capacity}} \right\rceil$$
$$\text{Estimated Purchase Cost} = \text{Packages Needed} \times \text{Unit Retail Price}$$

### 2. Agronomic & Statutory Eligibility Screening Gate
Before chemical substitution is calculated, the candidate product must satisfy 4 mandatory criteria:
1. **Active Ingredient Identity:** Candidate product active ingredient must match the prescribed chemical active ingredient (`product.active_ingredient == prescribed_active_ingredient`).
2. **Statutory Registration:** Candidate product must possess a valid, active CIBRC registration number (`is_legally_registered = True`). Unregistered, expired, or non-certified products are rejected.
3. **Crop & Disease Target Registration:** Candidate product label must be registered for the specific target crop and diagnosed pathology (`registered_crops` contains target crop; `registered_diseases` contains target disease).
4. **Formulation Suitability:** Candidate formulation must be appropriate for the prescribed application method. For foliar sprays, liquid concentrates and wettable powders (`WP`, `WG`, `WDG`, `SC`, `EC`, `SL`, `SP`) are eligible; solid soil granules (`GR`) or dry dusting powders (`DP`) are strictly rejected.

### 3. Geospatial Dealer Search Architecture
- **Primary Geodetic Engine (PostgreSQL / PostGIS):**
  Uses **PostGIS GiST indexing** (Generalized Search Tree implementing R-Tree geometric indexing) over WGS 84 Point geometry (`SRID 4326`). Spatial bounding radius queries execute via geodetic casting:
  ```sql
  SELECT m.id, ROUND((ST_Distance(m.location_geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000.0)::numeric, 3) AS distance_km
  FROM merchants m
  WHERE m.is_active = TRUE
    AND ST_DWithin(m.location_geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :max_meters)
  ORDER BY distance_km ASC;
  ```
- **Fallback Geodetic Engine (SQLite / Testing):**
  When running on non-PostGIS storage, the engine extracts coordinates via GeoAlchemy2 `to_shape` or WKT parsing and evaluates spherical distance using the **Haversine formula** ($R = 6371.0\,\text{km}$).

### 4. Multi-Criteria Normalized Ranking Engine
Eligible merchant-product pairings are evaluated using normalized utilities $[0.0 - 1.0]$:
1. **Price Utility ($U_{\text{price}}$):**
   $$U_{\text{price}} = 1.0 - \frac{P - P_{\min}}{P_{\max} - P_{\min}} \quad (1.0 \text{ if } P_{\max} = P_{\min})$$
2. **Proximity Utility ($U_{\text{distance}}$):**
   $$U_{\text{distance}} = \max\left(0.0, \; 1.0 - \frac{d}{d_{\max}}\right)$$
3. **Stock Fulfillment Utility ($U_{\text{stock}}$):**
   $$U_{\text{stock}} = \begin{cases} 1.0 & \text{if } S \ge R \\ \frac{S}{R} & \text{if } 0 < S < R \\ 0.0 & \text{if } S \le 0 \end{cases}$$
   *(Note: Out-of-stock products are segregated into ineligible candidates and never recommended as active purchase options).*

**Composite Weighted Score:**
$$\text{Score} = \frac{w_{\text{price}} \cdot U_{\text{price}} + w_{\text{distance}} \cdot U_{\text{distance}} + w_{\text{stock}} \cdot U_{\text{stock}}}{w_{\text{price}} + w_{\text{distance}} + w_{\text{stock}}}$$
*(Default weights: $w_{\text{price}} = 0.40$, $w_{\text{distance}} = 0.35$, $w_{\text{stock}} = 0.25$; fully configurable).*

### 5. Explainable Recommendation & Demonstration Integrity
- Every recommendation returns a transparent `ranking_explanation` and `score_breakdown` detailing the contributing utility metrics.
- Ineligible candidates (out of stock, crop mismatch, incompatible formulation) are explicitly listed with human-readable rejection reasons.
- All demonstration agro-dealer entries and test products carry prominent demonstration disclaimer notices (`is_demo = True`).

---

## Layer 4: Client Delivery Layer Architecture (Phase 6)

### 1. Progressive Web Application (PWA) Interface
- **Framework:** React.js 18.3.1 with Vite build bundling.
- **Styling:** Mobile-first, responsive design system using Tailwind CSS with agricultural emerald branding.
- **Component Hierarchy:**
  - `Navbar`: Displays backend API health probe, PostGIS spatial support badge, and responsive drawer navigation.
  - `Footer`: Outlines academic Design Thinking project details, statutory CIBRC/ICAR agronomic citations, and scientific disclaimers.
  - `StatusBadge`: Unified status pill component with color-coding and icons (Live, Cached, Regional Benchmark, Pending, Ineligible, Demo).
  - `DiagnosisCard`: Leaf upload, OpenCV foliar severity segmentation ($S_{\text{severity}}$), educational model training pending notices, and verified pathology selection.
  - `SoilCard`: Geospatial soil telemetry presentation (pH, SOC, Nitrogen, Sand/Silt/Clay, USDA texture, AWC) with educational disclaimers.
  - `TreatmentCard`: Bounded dosage formula ($D = \min(D_0 \times F_s \times F_v, D_{\text{label\_max}})$), carrier volume ($W$), 4 regulatory safety gates, PPE requirements, and CIBRC citations.
  - `SubstitutionCard`: Ranked dealer offerings, $Q_s = Q_r \times \frac{C_r}{C_s}$, package counts, total cost, 3-factor ranking utility score, explainability, and ineligible candidates audit.
  - `GoogleMapView`: Google Maps JavaScript API with markers and search radius circle, with seamless fallback to accessible responsive List View when API key is missing.

### 2. Multi-Step Diagnostic & Sourcing Wizard
The client application unifies the end-to-end user workflow across 5 progressive steps:
1. **Crop & Field Specification:** Crop selection, phenological growth stage, field area in acres, days to harvest (for PHI safety verification), and optional tank-mix co-applied chemicals.
2. **Vision Stream & Foliar Diagnosis:** Drag-and-drop or mobile camera image upload (`capture="environment"`), client-side validation ($\le 15\,\text{MB}$, JPEG/PNG/WEBP), OpenCV foliar lesion segmentation ($S_{\text{severity}}$), and verified pathology selection from knowledge base.
3. **Geospatial Location & Soil Telemetry:** Geolocation via browser GPS or coordinate presets (e.g. Mandya, Bangalore, Dharwad), horizon depth picker, and ISRIC SoilGrids 2.0 query.
4. **Multimodal Fusion & Bounded Dosage Formulation:** Execution of central fusion service, rendering statutory dosage ceiling checks, water dilution rates, PHI compliance, and PPE.
5. **Localized Agro-Dealer Substitution & Sourcing:** Geodesic radius search slider (5–50 km), spatial map/list visualization, active ingredient equivalence calculation, multi-criteria ranking, and printable diagnostic report export.


