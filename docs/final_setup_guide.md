# Final Setup, Installation & Execution Guide

**Project Title:** Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System  
**Target Operating System:** Windows 10 / Windows 11 (PowerShell)  
**Academic Context:** Final-Year Capstone Project Deployment  
**Date:** November 2026  

---

## 1. System Requirements & Prerequisites

Before setting up the project, ensure that the following tools are installed on your Windows development environment:

| Requirement | Supported Version | Purpose | Verification Command |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11, 3.12, or 3.13 (64-bit) | Backend API, ML inference, PyTorch & ONNX | `python --version` |
| **Node.js** | v18.0.0 or higher | Frontend React runtime & Vite build engine | `node -v` |
| **npm** | v9.0.0 or higher | Frontend package manager (run as `npm.cmd`) | `npm.cmd -v` |
| **Docker Desktop** *(Optional)* | v4.20+ with Docker Compose | PostgreSQL 16 + PostGIS 3.4 spatial database | `docker compose version` |
| **PowerShell** | 5.1 or PowerShell Core 7+ | Command-line execution shell on Windows | `$PSVersionTable.PSVersion` |

> [!NOTE]
> **Database Requirement:** Running PostgreSQL with PostGIS is **optional** for presentation and demonstration. The system features an automatic, fully functional graceful degradation engine: if PostgreSQL is not running, the application seamlessly utilizes verified agronomic fallback catalogs, client-side geodetic Haversine calculations, and ICAR-NBSS&LUP regional soil benchmarks without crashing.

---

## 2. Step-by-Step Installation Protocol

### Step 2.1: Open PowerShell as Administrator (Execution Policy)
If running PowerShell for the first time, enable script execution for virtual environments:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Step 2.2: Navigate to Project Directory
```powershell
cd c:\Users\admin\OneDrive\Desktop\Intelligent-Crop-Diagnosis
```

### Step 2.3: Python Virtual Environment Setup
Create a clean virtual environment and activate it:
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

Upgrade `pip` and install all production backend dependencies:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.4: Verify Machine Learning Model Weights
Ensure the trained PyTorch checkpoint and optimized ONNX runtime graph are present:
- Checkpoint: `ml_models/weights/efficientnet_b0_best.pth` (~17.5 MB)
- ONNX Graph: `ml_models/weights/efficientnet_b0.onnx` (~16.2 MB)

Verify model files in PowerShell:
```powershell
Get-ChildItem ml_models\weights\
```

If weights need to be exported to ONNX from PyTorch:
```powershell
python ml_models\export_onnx.py
```

### Step 2.5: Install Frontend Dependencies
Navigate into the `frontend` directory and install packages using `npm.cmd`:

> [!IMPORTANT]
> **Windows Command Rule:** On Windows PowerShell, always invoke `npm.cmd` instead of bare `npm` to ensure proper command resolution and path handling.

```powershell
cd frontend
npm.cmd install
cd ..
```

---

## 3. Database Setup (Optional)

### Option A: Running with Full PostgreSQL / PostGIS (Docker)
If you wish to test spatial GiST indexing and persistent database records:
1. Start the PostGIS container:
   ```powershell
   docker compose up -d
   ```
2. Wait 5 seconds for the database to initialize, then run the database migration and seeding script:
   ```powershell
   python -m backend.app.db.init_db
   ```
   This creates tables (`crops`, `diseases`, `chemicals`, `merchants`, `products`, `spatial_cache`) and seeds verified demonstration records.

### Option B: Running in Offline / Graceful Degradation Mode (Default)
No action is required! The backend automatically detects when the database is unreachable and engages:
- The verified agronomic catalog (`Tomato`, `Potato`, `Rice`)
- Standalone substitution calculator ($Q_s = Q_r \times \frac{C_r}{C_s}$)
- Safe `DATABASE_OFFLINE` response for merchant radius queries

---

## 4. Running the Application

To run the complete application for interactive demonstration, open two separate PowerShell windows:

### Terminal 1: Backend API Gateway (FastAPI + Uvicorn)
```powershell
cd c:\Users\admin\OneDrive\Desktop\Intelligent-Crop-Diagnosis
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Backend API Base:** `http://localhost:8000`
- **Interactive Swagger Documentation:** `http://localhost:8000/api/v1/docs`
- **System Health Probe:** `http://localhost:8000/api/v1/health`

### Terminal 2: Frontend Progressive Web App (React + Vite)
```powershell
cd c:\Users\admin\OneDrive\Desktop\Intelligent-Crop-Diagnosis\frontend
npm.cmd run dev
```
- **Client Application:** `http://localhost:3000`
- The Vite development server automatically proxies API requests from `/api/v1` to `http://localhost:8000`.

---

## 5. Verification & Testing Instructions

### 5.1 Run Full Backend Test Suite (115 Tests)
```powershell
python -m pytest tests/ -v
```
Expected output: `115 passed in ~58s`

### 5.2 Run Frontend Vitest Suite (15 Tests)
```powershell
cd frontend
npm.cmd test -- --run
cd ..
```
Expected output: `5 passed (5 files), 15 passed (15 tests)`

### 5.3 Run Production Frontend Build
Verify that the React PWA compiles for production without warnings:
```powershell
cd frontend
npm.cmd run build
cd ..
```
Expected output: `✓ built in ~15s` (`dist/index.html`, `dist/assets/`)

### 5.4 Run End-to-End Pipeline Verification Script
Run the automated end-to-end integration test exercising all 7 pipeline stages:
```powershell
python "C:\Users\admin\.gemini\antigravity\brain\b8810aa4-65d5-4310-874a-0332453b3ff3\scratch\e2e_verification.py"
```
Expected output:
```text
>>> ALL 7 END-TO-END STEPS PASSED SUCCESSFULLY! <<<
```

---

## 6. Demonstration Walkthrough Guide

Follow these steps to demonstrate the application to evaluators:

1. **Open the Web Browser:** Navigate to `http://localhost:3000`.
2. **Explore the Home Dashboard:**
   - Review the project title: *"Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System"*.
   - View the active system architecture (Four-Tier Architecture, AI Diagnostic Engine, Multimodal Fusion).
3. **Launch the Diagnosis Wizard:** Click **"Start Diagnosis Wizard"**.
   - **Step 1 (Crop & Context):** Select **Tomato** or **Potato**, growth stage **Vegetative**, and enter field coordinates (or leave the default Bangalore coordinates).
   - **Step 2 (Leaf Image Upload):** Upload a genuine leaf sample from `data/clean/Tomato___Early_Blight/` or `data/clean/Potato___healthy/`.
   - **Step 3 (AI Diagnosis & Lesion Analysis):** Observe the live EfficientNet-B0 pathology prediction, Softmax confidence bar, and OpenCV foliar lesion severity ($S_{severity}$ ratio and tier).
   - **Step 4 (Soil Telemetry):** Inspect soil parameters (pH, SOC, texture) fetched via ISRIC SoilGrids or regional fallback with uncertainty notices.
   - **Step 5 (Treatment & Bounded Dosage):** Review the calculated chemical recommendation ($D = \min(D_0 \cdot F_s \cdot F_v, D_{\max})$), Pre-Harvest Interval (PHI), and Personal Protective Equipment (PPE) requirements.
   - **Step 6 (Merchant Substitution & Ranking):** Explore alternative products from nearby agro-dealers ranked by price, distance, and stock with clear mathematical equivalent quantities ($Q_s$).
4. **Demonstrate Safety Gate (Healthy Crop):**
   - Upload a healthy leaf from `data/clean/Potato___healthy/`.
   - Observe that the Safety Gate **suppresses all chemical pesticides**, prevents toxic misapplication, and displays a *"Healthy Crop Preservation"* advisory.

---

## 7. Troubleshooting Common Issues

### Issue 1: `npm : The term 'npm' is not recognized...`
- **Cause:** PowerShell environment variable PATH does not include npm execution wrappers.
- **Solution:** Always run `npm.cmd` instead of `npm`:
  ```powershell
  npm.cmd run dev
  ```

### Issue 2: `EPERM: operation not permitted` on Windows
- **Cause:** Transient Windows file locking by antivirus or indexing service during package installation.
- **Solution:** Re-run the command once more; Windows transient file locks release after ~1 second.

### Issue 3: Port 8000 or 3000 Already in Use
- **Cause:** A previous Python or Node process is still bound to the port.
- **Solution:** Identify and terminate the lingering process:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
  Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
  ```

### Issue 4: Database Connection Warning on Startup
- **Log Message:** `Database server is currently offline or unreachable: ...`
- **Explanation:** This is standard, documented behavior when Docker is not running. The application does not require PostgreSQL to function and automatically utilizes verified fallback catalogs and client-side calculations.
