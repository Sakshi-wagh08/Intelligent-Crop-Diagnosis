# Frontend Client Delivery Layer (React.js PWA)

This directory houses the client delivery layer for the **Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System** (*Academic Reference: Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution*).

---

## 1. Architectural Highlights

- **Framework:** React.js 18.3.1 (Vite 5)
- **Styling & Design System:** Tailwind CSS 3.4.3 with custom agricultural emerald palette, PostCSS, Autoprefixer
- **Routing:** React Router v6.23.1
- **HTTP Client:** Axios v1.7.2 with unified backend error handling and proxying
- **Icons:** Lucide-React v0.378.0
- **Spatial Mapping:** Google Maps JavaScript API with native accessible card/list fallback
- **Testing Engine:** Vitest v1.6.0, React Testing Library v14.3.1, jsdom v24.0.0
- **PWA Capabilities:** W3C Web App Manifest (`manifest.webmanifest`), Service Worker (`sw.js`) with static asset caching

---

## 2. Directory Structure

```
frontend/
├── package.json               # Dependencies and scripts (dev, build, preview, test)
├── vite.config.js             # Vite configuration with /api proxy and Vitest jsdom setup
├── tailwind.config.js         # Custom palette and responsive breakpoints
├── postcss.config.js          # Tailwind and Autoprefixer PostCSS config
├── index.html                 # HTML5 entry with mobile viewport and Inter font
├── .env                       # Environment variables (VITE_API_BASE_URL, VITE_GOOGLE_MAPS_API_KEY)
├── public/
│   ├── manifest.webmanifest   # W3C Web App Manifest
│   ├── sw.js                  # Service Worker with Stale-While-Revalidate caching
│   └── icons/
│       ├── icon-192.svg       # 192x192 SVG icon
│       └── icon-512.svg       # 512x512 SVG icon
└── src/
    ├── index.css              # Tailwind base, utilities, and scrollbar styles
    ├── main.jsx               # React 18 createRoot, BrowserRouter & SW registration
    ├── App.jsx                # Layout with Navbar, Footer, and page routing
    ├── services/
    │   └── api.js             # Axios client wrapping all 11 backend REST endpoints
    ├── components/
    │   ├── Navbar.jsx         # Header with live health probe, PostGIS status, mobile drawer
    │   ├── Footer.jsx         # Academic DT identity, CIBRC/ICAR citations, statutory disclaimers
    │   ├── StatusBadge.jsx    # Unified color-coded status badge component
    │   ├── GoogleMapView.jsx  # Google Maps canvas with markers & radius circle; robust list fallback
    │   ├── SoilCard.jsx       # Soil properties (pH, SOC, Nitrogen, Sand/Silt/Clay, USDA texture, AWC)
    │   ├── DiagnosisCard.jsx  # Leaf upload, OpenCV foliar severity, model pending alert, pathology picker
    │   ├── TreatmentCard.jsx  # Bounded dosage breakdown, PHI gate, PPE, CIBRC source citations
    │   └── SubstitutionCard.jsx# Ranked dealers, Qs = Qr*(Cr/Cs), packs needed, cost, ineligible list
    ├── pages/
    │   ├── HomePage.jsx       # Hero banner, 4-tier interactive walkthrough, system integrity highlights
    │   ├── DiagnosisWizardPage.jsx # 5-step intuitive progressive multimodal diagnostic wizard
    │   ├── MerchantsPage.jsx  # Standalone agro-dealer directory and active ingredient calculator
    │   └── AboutPage.jsx      # Research methodology, governing equations, verified treatments table
    └── __tests__/
        ├── api.test.js        # API service client method definition tests (1 test)
        ├── SoilCard.test.jsx  # Soil property presentation & 250m disclaimer tests (3 tests)
        ├── DiagnosisCard.test.jsx # Model pending, manual test label, & severity tests (3 tests)
        ├── TreatmentCard.test.jsx # Demo banner, backend dosage, verification badge tests (4 tests)
        └── SubstitutionCard.test.jsx # Qs formula, package count, demo badges, ineligible list (2 tests)
```

---

## 3. Getting Started

### Prerequisites
- Node.js (v18+)
- npm (v9+)

### Installation
```bash
npm install
```

### Development Server
```bash
npm run dev
```
Starts the Vite development server on `http://localhost:3000` with automatic `/api` proxy to the FastAPI backend at `http://localhost:8000`.

### Automated Testing (Vitest)
```bash
npm test
```
Executes the 13 automated unit and component integration tests using Vitest and React Testing Library.

### Production Build
```bash
npm run build
```
Generates an optimized, tree-shaken static production bundle in `dist/`.

---

## 4. Progressive Web App (PWA) Capabilities & Offline Boundaries

- **Web App Manifest:** Packaged at `public/manifest.webmanifest`, providing standalone display mode, theme colors, and SVG app icons.
- **Service Worker:** Packaged at `public/sw.js` implementing a Stale-While-Revalidate caching strategy for application assets (HTML, JS, CSS, icons).
- **Explicit Offline Boundaries:**
  - *Offline Functional:* Static UI shell, client-side routing, navigation, and local UI state.
  - *Network Required:* Live ISRIC SoilGrids REST queries, PostGIS geospatial dealer queries, and central multimodal dosage fusion endpoints require network connectivity to the FastAPI backend. Network failures return transparent error alerts rather than stale or fabricated data.

---

## 5. Key Agronomic & System Compliance Features

1. **Zero Fabricated Diagnoses & Model Pending Transparency:**
   When vision model weights are not loaded on the backend (`has_active_model: false`), the UI transparently alerts the user that model training is pending and provides verified pathology selection clearly labeled with `MANUAL TEST INPUT — NOT AN AI DIAGNOSIS`. Any treatment output generated with manual input displays a prominent `DEMONSTRATION & RESEARCH EVALUATION ONLY` banner.

2. **Neutral Geographic Inputs:**
   Coordinate inputs are entirely neutral with manual entry or browser GPS location retrieval (`Use Device GPS`), with no hardcoded or fabricated regional state presets.

3. **Authoritative Dosage Representation:**
   The frontend displays exact authoritative backend values from `dosage_breakdown` without applying client-side scaling. Carrier water scaling claims (+15%) and universal regulatory prohibition claims have been removed in strict adherence to authoritative sources.

4. **ISRIC SoilGrids Disclaimers:**
   Soil telemetry cards clearly label properties as 250m machine-learning derived estimates, explicitly clarifying that total nitrogen is not plant-available mineral nitrogen and Available Water Capacity (AWC) measures volumetric water retention capacity, not instantaneous soil moisture.

5. **Demonstration Data Tagging:**
   All simulated agro-dealers and commercial product inventories are clearly tagged with `[DEMO DATA]` badges to prevent real-world confusion.

6. **Robust Mapping Fallback:**
   The application operates with or without a configured Google Maps API key, providing an interactive, accessible card/list view with direct navigation links when the key is absent.
