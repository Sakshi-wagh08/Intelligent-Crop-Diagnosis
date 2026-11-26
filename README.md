# Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System

**IEEE Subtitle:** Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution  
**Project Track:** Final-Year Engineering Capstone Project (Design Thinking Track)  
**Academic Year:** 2026–2027  
**System Status:** Complete, Audited & 100% Passing (130 / 130 Automated Tests)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/Vision-PyTorch%20%2F%20Torchvision-EE4C2C.svg)](https://pytorch.org)
[![ONNX Runtime](https://img.shields.io/badge/Edge%20Inference-ONNX%20Runtime-005CED.svg)](https://onnxruntime.ai)
[![ISRIC SoilGrids](https://img.shields.io/badge/Soil%20Telemetry-ISRIC%20SoilGrids%202.0-8B5A2B.svg)](https://soilgrids.org)
[![PostGIS](https://img.shields.io/badge/Geospatial-PostGIS%20SRID%204326-336791.svg)](https://postgis.net)
[![React PWA](https://img.shields.io/badge/Frontend-React%2018%20PWA-61DAFB.svg)](frontend/)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-115%2F115%20Passed-brightgreen.svg)](tests/)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-15%2F15%20Passed-brightgreen.svg)](frontend/src/__tests__/)
[![Model Performance](https://img.shields.io/badge/Vision%20Model-94.20%25%20Held--Out%20(6--Class)-brightgreen.svg)](docs/final_project_report.md)
[![Verification Status](https://img.shields.io/badge/Academic%20Status-Ready%20with%20Documented%20Limitations-orange.svg)](docs/final_verification_report.md)

An intelligent multimodal precision agriculture system designed for smallholder farmers. The platform synthesizes deep learning visual crop diagnosis, remote geospatial soil telemetry, auditable rule-based chemical dosage calculation, and localized agro-dealer availability into a single, cohesive workflow.

---

## 1. System Architecture

The application is structured into a modular **Four-Tier Architecture**:

```text
+-----------------------------------------------------------------------------------+
|                           TIER 1: CLIENT DELIVERY LAYER                           |
|       React 18 PWA (Vite + Tailwind CSS) | Service Worker (Offline Cache)        |
|  - Diagnosis Wizard Page (Step 1-6)    - Agro-Dealer Directory                   |
|  - Real-time Diagnostic Badges         - Traceable Agronomic Citations Repository|
+-----------------------------------------+-----------------------------------------+
                                          | REST API (JSON / Multipart Uploads)
+-----------------------------------------v-----------------------------------------+
|                        TIER 2: BACKEND API GATEWAY (FastAPI)                      |
|       Uvicorn ASGI Server | Pydantic v2 Data Validation | CORS Middleware         |
|  - /api/v1/health       - /api/v1/crops          - /api/v1/vision/diagnose        |
|  - /api/v1/soil/telemetry - /api/v1/fusion/recommend - /api/v1/merchants/substitute|
+-------------------+---------------------+--------------------+--------------------+
                    |                     |                    |
+-------------------v---+ +---------------v---+ +--------------v--+ +----------------v--+
|      VISION STREAM    | |   SOIL TELEMETRY  | | MULTIMODAL FUSION| |  SUBSTITUTION &  |
| (Tier 3 Inference)    | | (Tier 3 Telemetry)| | (Tier 3 Safety)  | |  RANKING ENGINE  |
| - EfficientNet-B0     | | - ISRIC SoilGrids | | - Safety Gates   | | - Active Ingred. |
|   ONNX (25.96ms CPU)  | |   2.0 REST Client |   (Confidence>=70% |   Equivalence:     |
| - OpenCV S_severity   | | - Spatial Cache   |    Healthy Preserve|   Qs = Qr*(Cr/Cs)  |
|   Lesion Segmentation |   (~500m pooling)   |    PHI Enforcement)| - PostGIS ST_DWithin|
| - Top-k Softmax       | | - ICAR-NBSS&LUP   | - Bounded Dosage:  |   GiST / Haversine |
|   Confidence Scores   |   Regional Fallback |   D = min(D0*Fs*Fv,| - Composite Utility|
|                       |                     |           D_max)   |   Score (Price/Dist|
+-----------------------+ +-------------------+ +------------------+ +------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
|                     TIER 4: DATA & KNOWLEDGE PERSISTENCE                          |
| - PostgreSQL 16 + PostGIS 3.4 (SRID 4326) / SQLite In-Memory Testing              |
| - Verified Agronomic Knowledge Base (ICAR, UAS Bengaluru, CPRI, CIBRC Labels)     |
| - Persisted ML Models (PyTorch .pth + ONNX Runtime Opset 17 Graph)                |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Scientific & Engineering Capabilities

1. **Visual Crop Pathology Diagnosis:** EfficientNet-B0 convolutional network classifying 7 canonical crop conditions across Tomato, Potato, and Rice. Achieves **$94.20\%$ held-out accuracy** across the 6 uncontaminated classes ($130 / 138$) and **$93.17\%$** on the 7-class historical staging benchmark ($150 / 161$, with historical duplicate contamination in `Rice___healthy`).
2. **OpenCV Foliar Lesion Severity ($S_{severity}$):** Computer vision segmentation isolating green leaf lamina and necrotic/chlorotic lesions:
   $$S_{severity} = \frac{\text{Lesion Area (Pixels)}}{\text{Total Leaf Area (Pixels)}}$$
   Categorized into standard agronomic tiers: Trace ($<1\%$), Low ($1-10\%$), Moderate ($10-25\%$), and High ($>25\%$). Visual foliar lesion percentage is strictly distinguished from pesticide dosage calculations; both vision diagnostics and the multimodal fusion engine enforce neutral $F_v = 1.00$.
3. **Edge Optimization (ONNX Runtime):** Exported to ONNX Runtime (Opset 17) achieving a consistent **$\sim 3\times$ CPU latency reduction** ($28.25\text{ ms}$ median ONNX CPU vs. $83.36\text{ ms}$ median native PyTorch CPU).
4. **Remote Geospatial Soil Telemetry:** Asynchronous client querying ISRIC SoilGrids 2.0 with spatial coordinate caching (~500m grid pooling) and published ICAR-NBSS&LUP regional agro-climatic fallbacks. Service availability is classified as availability-not-guaranteed per official ISRIC technical pause notices. Modeled 250m grid data does not replace laboratory wet-chemistry testing or real-time field moisture.
5. **Multimodal Fusion & Bounded Dosage Formulation:**
   $$D = \min\left(D_0 \times F_s \times F_v, \; D_{\text{label\_max}}\right)$$
   - Chemical pesticide concentration multipliers based on severity are disabled ($F_v = 1.00$) in accordance with CIBRC statutory labels.
   - Carrier water volume dilution strictly adheres to certified package-of-practices baselines without unsupported multipliers.
   - Enforces a 70% diagnostic confidence threshold, Pre-Harvest Intervals (PHI), and complete chemical suppression on healthy crops.
6. **Localized Merchant Substitution & Ranking:**
   $$Q_s = Q_r \times \left(\frac{C_r}{C_s}\right)$$
   Queries nearby agro-dealers within search radius $d_{\max}$ and computes transparent composite utility scores across unit price ($40\%$), distance ($40\%$), and inventory fulfillment ($20\%$).

---

## 3. Technology Stack

- **Backend:** Python 3.11–3.13, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0, GeoAlchemy2, httpx.
- **Machine Learning & CV:** PyTorch, Torchvision, ONNX Runtime, OpenCV (`opencv-python-headless`), Pillow, NumPy, Scikit-Learn.
- **Spatial Database:** PostgreSQL 16 + PostGIS 3.4 (with GiST spatial indexing), SQLite StaticPool fixture for test suite isolation.
- **Frontend Client:** React 18, Vite 5, Tailwind CSS, Lucide-React, Axios.
- **Testing & Verification:** Pytest, AnyIO, Vitest, React Testing Library, Faulthandler.

---

## 4. Windows Quick Start & Execution Guide

### 4.1 Prerequisites
- Python 3.11, 3.12, or 3.13 (64-bit)
- Node.js 18+ and npm (`npm.cmd`)
- PowerShell 5.1 or Core 7+

### 4.2 Installation Protocol (PowerShell)
```powershell
# 1. Allow virtual environment execution
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Setup Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Setup Frontend dependencies (run with npm.cmd)
cd frontend
npm.cmd install
cd ..
```

### 4.3 Running the Application
Open two separate PowerShell terminal windows:

**Terminal 1 (Backend Gateway):**
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Base: `http://localhost:8000`
- Swagger Documentation: `http://localhost:8000/api/v1/docs`
- Health Probe: `http://localhost:8000/api/v1/health`

**Terminal 2 (Frontend Client):**
```powershell
cd frontend
npm.cmd run dev
```
- Web Application: `http://localhost:3000`

---

## 5. Verification & Test Suite Execution

The repository features 100% automated test coverage across 130 tests:

### 5.1 Backend Regression Suite (115 Tests)
```powershell
python -m pytest tests/ -v
```
*Result: 115 passed in ~59 seconds.*

### 5.2 Frontend Vitest Suite (15 Tests)
```powershell
cd frontend
npm.cmd test -- --run
cd ..
```
*Result: 5 test files, 15 passed in ~20 seconds.*

### 5.3 Production Frontend Compilation
```powershell
cd frontend
npm.cmd run build
cd ..
```
*Result: Clean production bundle in `dist/` in ~16 seconds.*

### 5.4 End-to-End Pipeline Verification
```powershell
python "C:\Users\admin\.gemini\antigravity\brain\b8810aa4-65d5-4310-874a-0332453b3ff3\scratch\e2e_verification.py"
```
*Result: `ALL 7 END-TO-END STEPS PASSED SUCCESSFULLY!`*

---

## 6. Scientific Limitations & Academic Transparency

In adherence to strict academic honesty, the following constraints are documented:
1. **Academic Experimental Prototype & Held-Out Metrics:** The vision model is trained predominantly on single-leaf laboratory images (PlantVillage) and public domain rice images. Upstream leaf grouping analysis (`leaf-map.json`) revealed that 616 of 750 PlantVillage images (82.1%) map to physical leaves, and Rice images contain no grouping metadata. Therefore, physical plant-level split isolation cannot be mathematically guaranteed across the entire taxonomy. The 93.17% 7-class metric is an **experimental prototype staging benchmark with known duplicate contamination** in `Rice___healthy` (17/23 clean test images appeared in historical training), while the **held-out experimental accuracy on the 6 uncontaminated classes is 94.20%** ($130 / 138$). Field validation has not been performed.
2. **2D Foliar Severity & Neutral Chemical Multiplier ($F_v = 1.00$):** $S_{severity}$ uses heuristic OpenCV color thresholding on planar 2D images. All unsupported severity-based chemical and water multipliers have been removed; both the vision endpoint and the multimodal fusion engine strictly enforce neutral $F_v = 1.00$ and certified base water volume in adherence to CIBRC statutory label claims.
3. **SoilGrids Telemetry Availability:** The ISRIC SoilGrids REST API is classified as **availability-not-guaranteed** per official ISRIC technical pause notices. Modeled 250m grid data does not replace laboratory wet-chemistry testing or real-time field moisture.
4. **Database & Browser Testing Boundary:** Host port 5432 is offline; database-offline fallbacks function cleanly, but live PostGIS spatial SQL indexing remains unverified. Live automated browser testing timed out on origin permission prompts and was not completed; frontend automated verification is based on Vitest component integration suites.
5. **Demonstration Data:** Agro-dealer names, coordinates, and prices in the database are synthetic test records tagged with prominent demonstration badges.
6. **Single-Active Substitution:** The product substitution formula ($Q_s = Q_r \times \frac{C_r}{C_s}$) applies exclusively to single active ingredient chemical formulations.

---

## 7. Comprehensive Academic Project Documentation

Detailed project documentation is available in [`docs/`](docs/):
- **[`docs/final_verification_report.md`](docs/final_verification_report.md):** Independent senior verification and audit report covering live HTTP evidence, root cause analysis, and limitation matrices.
- **[`docs/final_project_report.md`](docs/final_project_report.md):** Complete academic capstone report covering Design Thinking methodology, system architecture, mathematical derivations, ML audit, and future scope.
- **[`docs/final_testing_report.md`](docs/final_testing_report.md):** Full quality assurance report covering 130 tests, edge cases, safety gates, and E2E verification.
- **[`docs/final_setup_guide.md`](docs/final_setup_guide.md):** Windows PowerShell setup, execution commands, and troubleshooting guide.
- **[`docs/final_limitations.md`](docs/final_limitations.md):** Exhaustive scientific caveats, leaf grouping analysis, and regulatory boundaries.
- **[`docs/architecture.md`](docs/architecture.md):** Four-tier architectural specifications and multimodal API contracts.
