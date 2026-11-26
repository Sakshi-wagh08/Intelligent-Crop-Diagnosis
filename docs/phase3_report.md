# Phase 3: Remote Soil Telemetry — Implementation Report

**Project Title:** Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System  
**Academic Document:** Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution  
**Milestone:** Phase 3 Completion  

---

## 1. SoilGrids Availability & Access Method Investigation

### 1.1 Live REST API Inspection Results
Prior to code implementation, live network probes were conducted against the official ISRIC SoilGrids 2.0 REST API (`https://rest.isric.org/soilgrids/v2.0/properties/query`):

| Probe Target | Lat, Lon Coordinates | Response Status | Observed Behavior & Findings |
| :--- | :--- | :--- | :--- |
| **ISRIC Benchmark** | `51.9851, 5.6637` (Wageningen, NL) | **HTTP 200 OK** | Returned verified properties: `phh2o` mean 54 ($5.4$ pH), `soc` mean 812 ($81.2\,\text{g/kg}$). Query time: $\approx 0.28\,\text{s}$. |
| **Agricultural Field** | `13.0, 77.0` (Tumakuru, Karnataka) | **HTTP 200 OK** | Returned full 10-layer payload: `phh2o` (6.5), `soc` (19.3 g/kg), `nitrogen` (1.47 g/kg), `cec` (16.4 cmol/kg), `sand` (49.4%), `silt` (22.0%), `clay` (28.6%), `wv0010` (38.7%), `wv0033` (30.2%), `wv1500` (12.1%). |
| **Urban / Paved Terrain** | `12.9716, 77.5946` (Bangalore Urban) | **HTTP 200 OK** | SoilGrids masks urban built-up surfaces: values returned `mean: null`. Confirms that **urban/paved areas require fallback handling**. |
| **Ocean Coordinates** | `0.0, 0.0` (Gulf of Guinea) | **HTTP 200 OK** | Masked surface: values returned `mean: null`. Requires explicit unavailable status. |
| **Invalid Coordinates** | `999.0, 77.0` | **HTTP 422 Unprocessable** | Returned Pydantic validation error: `ensure this value is less than or equal to 90.0`. |
| **Invalid Layer Name** | `13.0, 77.0`, `property=invalid_prop` | **HTTP 500 Internal Error** | ISRIC server threw internal error; confirms need for client-side property validation. |

### 1.2 Evaluation of Official Alternative Access Methods

1. **ISRIC SoilGrids 2.0 REST API (Selected Access Method):**
   - *Architecture:* Asynchronous GeoJSON point queries (`httpx.AsyncClient`).
   - *Advantages:* Lightweight JSON payloads, low bandwidth, zero binary geospatial dependencies, returns quantiles (`Q0.05`, `Q0.5`, `Q0.95`, `uncertainty`).
   - *Limitations:* Subject to public internet latency fluctuations (typically 300ms to 2.5s) and rate limits; masked over water bodies and urban surfaces. Mitigated through strict 2.0s timeouts, ~500m spatial caching, and regional agronomic fallback.
2. **OGC Web Coverage Service (WCS 2.0):**
   - *Evaluation:* ISRIC provides WCS endpoints (`https://maps.isric.org/mapserv?map=/map/{property}.map`).
   - *Assessment:* Queries return binary GeoTIFF raster subsets. Fetching raster rasters for single latitude/longitude points imposes substantial network overhead, requires heavy binary libraries (`GDAL` / `rasterio`), and increases end-to-end latency beyond the target sub-2.0s SLA.
3. **WebDAV / Direct Raster Download:**
   - *Evaluation:* Full global GeoTIFF rasters at 250m resolution are available via WebDAV (`https://files.isric.org/soilgrids/latest/data/`).
   - *Assessment:* The global dataset exceeds several hundred gigabytes. While ideal for offline on-premise spatial database hosting in an enterprise deployment, it is unsuitable for real-time mobile API querying without dedicated GIS infrastructure.
4. **Google Earth Engine (GEE):**
   - *Evaluation:* Earth Engine hosts SoilGrids global image collections (`ISRIC/World/SoilGrids/...`).
   - *Assessment:* Requires Google Cloud project enrollment, service account key provisioning, and the `earthengine-api` Python client. Point evaluations via Earth Engine add authorization overhead and cloud billing dependencies.

---

## 2. Implemented Modules and Files

### Telemetry Pipeline (`backend/app/telemetry/`)
- [`exceptions.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/telemetry/exceptions.py): Domain error hierarchy (`SoilTelemetryError`, `SoilGridsAPIError`, `SoilGridsTimeoutError`, `InvalidCoordinatesError`, `SoilDataUnavailableError`).
- [`soilgrids.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/telemetry/soilgrids.py): Asynchronous HTTPX client for SoilGrids 2.0 REST API supporting 10 verified properties, multiple depth horizons (`0-5cm`, `5-15cm`, `15-30cm`), quantiles (`mean`, `Q0.05`, `Q0.5`, `Q0.95`, `uncertainty`), and robust timeout/HTTP error handling.
- [`processing.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/telemetry/processing.py):
  - WGS-84 coordinate validation ($-90 \le \text{lat} \le 90$, $-180 \le \text{lon} \le 180$).
  - Official $d\_factor$ integer scaling for physical properties.
  - USDA Natural Resources Conservation Service (NRCS) soil texture triangle decision classifier (12 textural classes).
  - Hydraulic matrix water retention calculations ($\text{AWC} = wv0033 - wv1500$).
  - Strict advisory disclosures for digital soil mapping estimates, total nitrogen reserves, and matrix hydraulic retention.
- [`cache.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/telemetry/cache.py): Thread-safe in-memory spatial cache implementing $0.005^\circ$ coordinate grid rounding ($\approx 500\,\text{m}$ spatial pooling), configurable TTL expiry (24 hours), and automatic purging.
- [`fallback.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/telemetry/fallback.py): Verified regional agronomic fallback matrix based on published ICAR-NBSS&LUP benchmark soil profiles across 5 agro-climatic zones of Karnataka. **Strict anti-fabrication safeguard:** returns `None` for coordinates outside verified regional zones.
- [`service.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/telemetry/service.py): Multi-tier orchestrator managing Cache $\to$ Live SoilGrids $\to$ Regional Fallback $\to$ Unavailable status.

### Schemas & API Integration
- [`backend/app/schemas/soil.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/schemas/soil.py): Extended Pydantic schemas with `data_status`, `depth`, `units`, `retrieval_timestamp`, `uncertainty_quantiles`, `water_retention`, and backward-compatible parameters.
- [`backend/app/api/v1/endpoints/soil.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/api/v1/endpoints/soil.py): Updated `GET /api/v1/soil/telemetry` endpoint supporting asynchronous execution, depth parameters, and HTTP 422 coordinate validation.

---

## 3. Supported Soil Properties & Unit Conversions

| Layer | Attribute | Raw SoilGrids Scale | Scale Factor ($d\_factor$) | Processed Target Unit | Agronomic Relevance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `phh2o` | Soil Reaction (pH) | $\text{pH} \times 10$ | $10$ | Dimensionless ($-$) | Chemical availability of phosphorus and micronutrients |
| `soc` | Soil Organic Carbon | $\text{dg/kg}$ | $10$ | $\text{g/kg}$ | Soil structural stability and biological activity |
| `nitrogen` | Total Nitrogen | $\text{cg/kg}$ | $100$ | $\text{g/kg}$ | Total nitrogen reserve (NOT immediately available $\text{NO}_3^-$/$\text{NH}_4^+$) |
| `cec` | Cation Exchange Capacity | $\text{mmol}(c)/\text{kg}$ | $10$ | $\text{cmol}(c)/\text{kg}$ | Nutrient retention capacity against chemical leaching |
| `sand` | Sand Fraction | $\text{g/kg}$ | $10$ | $\%$ | Coarse fraction ($0.05 - 2\,\text{mm}$); infiltration rate |
| `silt` | Silt Fraction | $\text{g/kg}$ | $10$ | $\%$ | Medium fraction ($0.002 - 0.05\,\text{mm}$); crusting susceptibility |
| `clay` | Clay Fraction | $\text{g/kg}$ | $10$ | $\%$ | Fine colloidal fraction ($<0.002\,\text{mm}$); chemical fixation |
| `wv0010` | Water content at 10 kPa | $(10^{-2}\,\text{cm}^3/\text{cm}^3) \times 10$ | $10$ | $\%$ vol | Water content when macropores drain |
| `wv0033` | Water content at 33 kPa | $(10^{-2}\,\text{cm}^3/\text{cm}^3) \times 10$ | $10$ | $\%$ vol | Standard agricultural field capacity (FC) |
| `wv1500` | Water content at 1500 kPa | $(10^{-2}\,\text{cm}^3/\text{cm}^3) \times 10$ | $10$ | $\%$ vol | Permanent wilting point (PWP) |

---

## 4. Rigorous Agronomic Disclosures & Data Integrity Rules

1. **Modeled Estimate Disclaimer:** All SoilGrids predictions are generated by machine learning models trained on global soil profiles at 250m resolution. Outputs are statistical predictions with quantified spatial uncertainty, **not** laboratory analytical measurements.
2. **Total Nitrogen Protection:** In strict compliance with agronomic science, SoilGrids `nitrogen` is labeled as **total elemental nitrogen**. It is explicitly **not** represented as plant-available mineral nitrogen ($\text{NO}_3^-$ / $\text{NH}_4^+$), preventing lethal chemical over-application in Phase 4 fusion calculations.
3. **Hydraulic Matrix vs Dynamic Moisture:** The water retention parameters (`wv0010`, `wv0033`, `wv1500`) are documented as static soil matrix retention capacities (pF curves), **not** dynamic real-time field moisture (which requires field in-situ sensors or meteorological water-balance models).
4. **Prevention of Fabricated Soil Values:** If the external SoilGrids service is unreachable, times out, or returns nulls, and coordinates fall outside verified ICAR-NBSS&LUP regional benchmarks, the system returns `data_status: "unavailable"` and `parameters: None`. **No fake or synthetic soil values are ever fabricated.**

---

## 5. Automated Test Results (51 of 51 Passed)

The complete automated test suite was executed across the repository:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\admin\OneDrive\Desktop\Intelligent-Crop-Diagnosis
plugins: anyio-4.16.0
collected 51 items

tests/test_crops_api.py::test_get_crops_returns_seeded_crops PASSED              [  1%]
tests/test_database_models.py::test_crops_and_diseases_relationship PASSED         [  3%]
tests/test_database_models.py::test_base_treatments_and_active_ingredients PASSED [  5%]
tests/test_database_models.py::test_merchant_product_relationships PASSED         [  7%]
tests/test_database_models.py::test_chemical_incompatibilities PASSED            [  9%]
tests/test_health.py::test_root_endpoint PASSED                                  [ 11%]
tests/test_health.py::test_health_endpoint PASSED                                [ 13%]
tests/test_merchants_api.py::test_get_nearby_merchants_within_radius PASSED        [ 15%]
tests/test_merchants_api.py::test_get_nearby_merchants_filtered_by_active_ingredient PASSED [ 17%]
tests/test_soil_api.py::test_soil_telemetry_endpoint PASSED                      [ 19%]
tests/test_soil_telemetry.py::test_coordinate_validation_valid_ranges PASSED      [ 21%]
tests/test_soil_telemetry.py::test_coordinate_validation_invalid_bounds PASSED    [ 23%]
tests/test_soil_telemetry.py::test_usda_texture_classification PASSED            [ 25%]
tests/test_soil_telemetry.py::test_usda_texture_missing_or_invalid PASSED        [ 27%]
tests/test_soil_telemetry.py::test_process_soilgrids_layers_unit_conversion PASSED [ 29%]
tests/test_soil_telemetry.py::test_process_soilgrids_masked_all_nulls PASSED     [ 31%]
tests/test_soil_telemetry.py::test_spatial_grid_rounding PASSED                  [ 33%]
tests/test_soil_telemetry.py::test_spatial_cache_set_get_and_expiration PASSED    [ 35%]
tests/test_soil_telemetry.py::test_regional_fallback_identification PASSED        [ 37%]
tests/test_soil_telemetry.py::test_prevention_of_fabricated_soil_values PASSED    [ 39%]
tests/test_soil_telemetry.py::test_soil_service_live_fetch_success[asyncio] PASSED [ 41%]
tests/test_soil_telemetry.py::test_soil_service_cache_hit[asyncio] PASSED        [ 43%]
tests/test_soil_telemetry.py::test_soil_service_timeout_triggers_regional_fallback[asyncio] PASSED [ 45%]
tests/test_soil_telemetry.py::test_soil_service_503_triggers_unavailable_outside_fallback[asyncio] PASSED [ 47%]
tests/test_soil_telemetry.py::test_api_soil_telemetry_live_endpoint PASSED       [ 49%]
tests/test_soil_telemetry.py::test_api_soil_telemetry_invalid_coordinates_http_422 PASSED [ 50%]
tests/test_vision_api.py::test_get_vision_status_endpoint PASSED                 [ 52%]
tests/test_vision_api.py::test_diagnose_leaf_image_endpoint_valid_image PASSED [ 54%]
tests/test_vision_api.py::test_diagnose_leaf_image_invalid_empty_file PASSED   [ 56%]
tests/test_vision_api.py::test_diagnose_leaf_image_corrupt_file PASSED          [ 58%]
tests/test_vision_model_and_inference.py::test_build_efficientnet_b0_architecture PASSED [ 60%]
tests/test_vision_model_and_inference.py::test_load_model_checkpoint_missing_raises_error PASSED [ 62%]
tests/test_vision_model_and_inference.py::test_disease_classifier_unloaded_predict_raises_error PASSED [ 64%]
tests/test_vision_model_and_inference.py::test_disease_classifier_inference_with_trained_checkpoint PASSED [ 66%]
tests/test_vision_onnx_and_export.py::test_export_pytorch_to_onnx_and_inference PASSED [ 68%]
tests/test_vision_onnx_and_export.py::test_compare_pytorch_and_onnx_numerical_consistency PASSED [ 70%]
tests/test_vision_onnx_and_export.py::test_onnx_missing_file_raises_error PASSED [ 72%]
tests/test_vision_preprocessing.py::test_valid_image_loading_and_conversion PASSED [ 74%]
tests/test_vision_preprocessing.py::test_empty_image_raises_invalid_image_error PASSED [ 76%]
tests/test_vision_preprocessing.py::test_oversized_image_raises_image_too_large_error PASSED [ 78%]
tests/test_vision_preprocessing.py::test_corrupt_bytes_raises_corrupt_image_error PASSED [ 80%]
tests/test_vision_preprocessing.py::test_preprocessing_pytorch_tensor_output PASSED [ 82%]
tests/test_vision_preprocessing.py::test_preprocessing_onnx_numpy_output PASSED  [ 84%]
tests/test_vision_preprocessing.py::test_to_cv2_bgr_conversion PASSED             [ 86%]
tests/test_vision_severity.py::test_clean_healthy_leaf_severity PASSED           [ 88%]
tests/test_vision_severity.py::test_moderate_disease_leaf_severity PASSED         [ 90%]
tests/test_vision_severity.py::test_high_disease_leaf_severity PASSED            [ 92%]
tests/test_vision_severity.py::test_non_foliar_image_undetected PASSED            [ 94%]
tests/test_vision_severity.py::test_pil_image_input_compatibility PASSED          [ 96%]
tests/test_vision_training_pipeline.py::test_data_transforms_specifications PASSED [ 98%]
tests/test_vision_training_pipeline.py::test_load_datasets_and_micro_training_step PASSED [100%]

================== 51 passed, 5 warnings in 68.21s (0:01:08) ==================
```

---

## 6. Execution Instructions

### Querying the Soil Telemetry Endpoint
1. Start the FastAPI development server:
   ```powershell
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Query live telemetry (e.g. agricultural coordinates in Karnataka):
   ```powershell
   curl "http://localhost:8000/api/v1/soil/telemetry?latitude=13.0&longitude=77.0&depth=0-5cm"
   ```
3. Query regional fallback (e.g. urban Bangalore coordinate where SoilGrids masks with nulls):
   ```powershell
   curl "http://localhost:8000/api/v1/soil/telemetry?latitude=12.9716&longitude=77.5946&depth=0-5cm"
   ```
4. Query out-of-bounds / ocean coordinates to verify anti-fabrication protection:
   ```powershell
   curl "http://localhost:8000/api/v1/soil/telemetry?latitude=0.0&longitude=0.0"
   ```

---

## 7. Readiness for Phase 4

- **Phase 3 Status:** 100% complete and fully verified.
- **Architectural Boundary:** As instructed, soil telemetry parameters have **not** yet been connected to chemical dosage formulations.
- **Phase 4 (Next Milestone):** Multimodal Fusion & Bounded Dosage Formulation ($D = D_0 \times F_s \times F_v$, bounded by $D \le D_{\text{label\_max}}$, with phenological stage adjustment and chemical incompatibility checks).
