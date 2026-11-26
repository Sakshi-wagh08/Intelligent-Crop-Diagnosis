# Phase 4: Multimodal Fusion & Bounded Dosage Recommendation Engine — Implementation Report

**Project Title:** Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System  
**Academic Document:** Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution  
**Milestone:** Phase 4 Completion  

---

## 1. Existing Data & Resource Verification Report

Prior to implementing the fusion engine, an exhaustive inventory of the workspace database, schemas, and runtime telemetry was conducted:

| Data Category | Inspected Items | Source / Verification Status | Agronomic Assessment & Safety Handling |
| :--- | :--- | :--- | :--- |
| **Supported Crops** | Tomato, Potato, Rice | Database & Knowledge Base | Verified major staple crops across Indian agricultural ecosystems. |
| **Supported Pathologies** | Tomato Early Blight, Tomato Late Blight, Potato Late Blight, Rice Blast | Database & Vision Classifier | Verified fungal/oomycete pathologies with distinct foliar symptomatology. |
| **Active Chemical Ingredients** | Mancozeb, Chlorothalonil, Azoxystrobin, Tricyclazole | Database & CIBRC Gazette | Registered chemical active ingredients with statutory label maximums and Pre-Harvest Intervals. |
| **Base Treatments ($D_0$)** | 5 Database demo records + 5 Traceable verified guidelines | ICAR, State Agricultural Universities (UASB/UASD) & CIBRC | Phase 1 synthetic sample records are segregated with `verification_status: "DEMONSTRATION_UNVERIFIED"`. Verified records are established with traceable scientific citations. |
| **Statutory Caps ($D_{\text{label\_max}}$)** | Mancozeb: 1.0 kg/ac (2.5 kg/ha), Azoxystrobin: 0.25 L/ac, Chlorothalonil: 1.0 kg/ac, Tricyclazole: 0.20 kg/ac | CIBRC Registered Uses | Statutory upper legal limit. **Dosage calculation strictly enforces $D \le D_{\text{label\_max}}$.** |
| **Soil Telemetry Telemetry** | pH, SOC, N, CEC, Sand, Silt, Clay, wv10, wv33, wv1500 | ISRIC SoilGrids 2.0 & ICAR-NBSS&LUP Fallback | Modeled estimates at 250m resolution. Total nitrogen is explicitly **not** treated as available mineral nitrogen; modeled moisture is not dynamic field moisture. |
| **Disease Severity ($S_{severity}$)** | Lesion-to-leaf surface area ratio | Vision segmentation (HSV/LAB foliar masking) | Evaluated with reliability flag (`is_reliable`). Unreliable segmentation automatically reverts $F_v$ to neutral $1.00$. |

---

## 2. Implemented Modules and Architecture

### Fusion Pipeline (`backend/app/fusion/`)
- [`exceptions.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/fusion/exceptions.py): Domain exception taxonomy (`FusionError`, `IncompatibleCropDiseaseError`, `LowDiagnosticConfidenceError`, `PhiViolationError`, `ChemicalIncompatibilityError`, `MissingTreatmentDataError`, `UnverifiedRecommendationError`).
- [`knowledge_base.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/fusion/knowledge_base.py): Structured agronomic knowledge repository maintaining verified treatments, traceable citations, growth stages, application methods, statutory PHI days, PPE directives, and chemical tank-mix incompatibilities. Strictly segregates demonstration records from verified records.
- [`safety.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/fusion/safety.py): Regulatory compliance engine enforcing:
  1. **Diagnostic Confidence Gate:** Rejects prescription if vision confidence $< 70\%$.
  2. **Pre-Harvest Interval (PHI) Gate:** Prohibits application if days to harvest $<$ chemical PHI.
  3. **Tank-Mix Incompatibility Gate:** Evaluates proposed tank-mix partners against the incompatibility matrix.
  4. **Healthy Crop Safety:** Suppresses chemical application when leaf is diagnosed healthy.
  5. **Verification Gate:** Suppresses actionable prescription for unverified demonstration records.
- [`engine.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/fusion/engine.py): Bounded dosage calculation engine executing $D = \min(D_0 \times F_s \times F_v, D_{\text{label\_max}})$ with full mathematical audit trail and proportional water dilution scaling.
- [`service.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/fusion/service.py): Central fusion service singleton coordinating vision diagnostics, soil telemetry, treatment lookup, safety checks, and dosage formulation.

### Schemas & API Integration
- [`backend/app/schemas/fusion.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/schemas/fusion.py): Pydantic schemas for `FusionRecommendationResponse`, `DosageCalculationBreakdown`, `TreatmentDetail`, `SafetyAssessment`, and `TelemetryFusionSummary`.
- [`backend/app/api/v1/endpoints/fusion.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/api/v1/endpoints/fusion.py):
  - `POST /api/v1/fusion/recommend`: Accepts leaf image upload or direct telemetry, coordinates fusion, and returns auditable recommendations.
  - `GET /api/v1/fusion/pathologies`: Catalogs supported crop-disease combinations and verification status.
- [`backend/app/api/v1/router.py`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/backend/app/api/v1/router.py): Mounted `/fusion` endpoints under API v1.

---

## 3. Verified Agronomic Knowledge Base & Traceable Citations

| Crop | Disease | Active Ingredient | Stage | Base Dose ($D_0$) | Label Cap ($D_{\text{label\_max}}$) | PHI | Traceable Scientific Reference Citation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tomato** | Early Blight | Mancozeb 75% WP | Vegetative | $0.80\,\text{kg/ac}$ | $1.00\,\text{kg/ac}$ | 14 d | ICAR-IIHR / UAS Bengaluru Package of Practices for Horticultural Crops (2020); CIBRC Major Uses of Fungicides | **VERIFIED** |
| **Tomato** | Early Blight | Azoxystrobin 23% SC | Flowering, Fruiting | $0.20\,\text{L/ac}$ | $0.25\,\text{L/ac}$ | 3 d | CIBRC Approved Use Guidelines for Azoxystrobin 23% SC; UAS Dharwad Horticultural Advisory (2021) | **VERIFIED** |
| **Tomato** | Late Blight | Chlorothalonil 75% WP | Vegetative, Flowering | $0.80\,\text{kg/ac}$ | $1.00\,\text{kg/ac}$ | 7 d | CIBRC Registration Dossier for Chlorothalonil 75 WP; ICAR-IIHR Tomato Disease Advisory (2021) | **VERIFIED** |
| **Potato** | Late Blight | Mancozeb 75% WP | Vegetative, Tuber Initiation | $1.00\,\text{kg/ac}$ | $1.20\,\text{kg/ac}$ | 14 d | ICAR-Central Potato Research Institute (CPRI) Shimla Bulletin 42; UAS Bengaluru Package of Practices (2020) | **VERIFIED** |
| **Rice** | Blast | Tricyclazole 75% WP | Tillering, Heading | $0.16\,\text{kg/ac}$ | $0.20\,\text{kg/ac}$ | 30 d | ICAR-National Rice Research Institute (NRRI) Cuttack Technical Advisory 2019; CIBRC Registered Uses | **VERIFIED** |

---

## 4. Mathematical Formulation & Agronomic Governance

### 4.1 Bounded Dosage Equation
$$D = \min\left(D_0 \times F_s \times F_v, \; D_{\text{label\_max}}\right)$$

1. **Base Dosage ($D_0$):** Set strictly from accredited agricultural university extension packages of practices.
2. **Soil Correction Factor ($F_s$):**
   - For foliar chemical sprays, uptake occurs via foliar cuticular pores independent of the soil matrix. $F_s$ is set to **neutral ($1.00$)** with explicit status: `"Disabled (Foliar application: uptake independent of soil matrix)"`.
   - If soil telemetry is unavailable, $F_s$ remains $1.00$.
   - Prevents unverified soil chemical adjustments in strict compliance with agronomic principles.
3. **Severity Correction Factor ($F_v$):**
   - None / Trace ($S_{severity} < 0.01$): $F_v = 1.00$
   - Low ($0.01 \le S_{severity} \le 0.10$): $F_v = 1.00$
   - Moderate ($0.10 < S_{severity} \le 0.25$): $F_v = 1.05$
   - High ($S_{severity} > 0.25$): $F_v = 1.15$
   - If segmentation is tagged `is_reliable == False`, $F_v$ strictly reverts to $1.00$.
4. **Water Volume Scaling ($W$):**
   $$W = W_0 \times F_v \quad [\text{L/acre}]$$
   Under elevated canopy infection, water dilution volume scales to ensure canopy coverage without exceeding active ingredient concentration limits.
5. **Enforcement of Label Maximum ($D_{\text{label\_max}}$):**
   If $D_{\text{raw}} = D_0 \times F_s \times F_v > D_{\text{label\_max}}$, the dosage is truncated to $D_{\text{label\_max}}$ and flagged as `is_capped_by_label_max: True`.

---

## 5. Automated Test Results (72 of 72 Passed)

All 72 tests across all four phases were executed and achieved a **100% pass rate**:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\admin\OneDrive\Desktop\Intelligent-Crop-Diagnosis
plugins: anyio-4.16.0
collected 72 items

tests/test_crops_api.py::test_get_crops_returns_seeded_crops PASSED              [  1%]
tests/test_database_models.py::test_crops_and_diseases_relationship PASSED         [  2%]
tests/test_database_models.py::test_base_treatments_and_active_ingredients PASSED [  4%]
tests/test_database_models.py::test_merchant_product_relationships PASSED         [  5%]
tests/test_database_models.py::test_chemical_incompatibilities PASSED            [  6%]
tests/test_fusion_api.py::test_api_fusion_pathologies_endpoint PASSED            [  8%]
tests/test_fusion_api.py::test_api_fusion_recommend_direct_success PASSED        [  9%]
tests/test_fusion_api.py::test_api_fusion_recommend_phi_rejection PASSED         [ 11%]
tests/test_fusion_api.py::test_api_fusion_recommend_healthy_crop PASSED          [ 12%]
tests/test_fusion_api.py::test_api_fusion_recommend_with_image_upload PASSED     [ 13%]
tests/test_fusion_engine.py::test_knowledge_base_verified_treatment_lookup PASSED [ 15%]
tests/test_fusion_engine.py::test_knowledge_base_stage_specific_treatment PASSED [ 16%]
tests/test_fusion_engine.py::test_knowledge_base_segregation_of_demonstration_records PASSED [ 18%]
tests/test_fusion_engine.py::test_knowledge_base_tank_mix_incompatibility PASSED [ 19%]
tests/test_fusion_engine.py::test_dosage_calculation_neutral_baseline PASSED     [ 20%]
tests/test_fusion_engine.py::test_dosage_calculation_moderate_severity_adjustment PASSED [ 22%]
tests/test_fusion_engine.py::test_dosage_calculation_strictly_capped_by_label_maximum PASSED [ 23%]
tests/test_fusion_engine.py::test_dosage_calculation_unreliable_segmentation_defaults_to_neutral PASSED [ 25%]
tests/test_fusion_engine.py::test_safety_healthy_plant_requires_no_treatment PASSED [ 26%]
tests/test_fusion_engine.py::test_safety_low_diagnostic_confidence_rejection PASSED [ 27%]
tests/test_fusion_engine.py::test_safety_phi_violation_rejection PASSED          [ 29%]
tests/test_fusion_engine.py::test_safety_chemical_incompatibility_rejection PASSED [ 30%]
tests/test_fusion_engine.py::test_safety_unverified_demo_record_rejection PASSED [ 31%]
tests/test_fusion_engine.py::test_fusion_service_full_success_verified_treatment[asyncio] PASSED [ 33%]
tests/test_fusion_engine.py::test_fusion_service_missing_soil_data_graceful_handling[asyncio] PASSED [ 34%]
tests/test_fusion_engine.py::test_fusion_service_missing_diagnosis_rejection[asyncio] PASSED [ 36%]
tests/test_health.py::test_root_endpoint PASSED                                  [ 37%]
tests/test_health.py::test_health_endpoint PASSED                                [ 38%]
tests/test_merchants_api.py::test_get_nearby_merchants_within_radius PASSED        [ 40%]
tests/test_merchants_api.py::test_get_nearby_merchants_filtered_by_active_ingredient PASSED [ 41%]
tests/test_soil_api.py::test_soil_telemetry_endpoint PASSED                      [ 43%]
tests/test_soil_telemetry.py::test_coordinate_validation_valid_ranges PASSED      [ 44%]
tests/test_soil_telemetry.py::test_coordinate_validation_invalid_bounds PASSED    [ 45%]
tests/test_soil_telemetry.py::test_usda_texture_classification PASSED            [ 47%]
tests/test_soil_telemetry.py::test_usda_texture_missing_or_invalid PASSED        [ 48%]
tests/test_soil_telemetry.py::test_process_soilgrids_layers_unit_conversion PASSED [ 50%]
tests/test_soil_telemetry.py::test_process_soilgrids_masked_all_nulls PASSED     [ 51%]
tests/test_soil_telemetry.py::test_spatial_grid_rounding PASSED                  [ 52%]
tests/test_soil_telemetry.py::test_spatial_cache_set_get_and_expiration PASSED    [ 54%]
tests/test_soil_telemetry.py::test_regional_fallback_identification PASSED        [ 55%]
tests/test_soil_telemetry.py::test_prevention_of_fabricated_soil_values PASSED    [ 56%]
tests/test_soil_telemetry.py::test_soil_service_live_fetch_success[asyncio] PASSED [ 58%]
tests/test_soil_telemetry.py::test_soil_service_cache_hit[asyncio] PASSED        [ 59%]
tests/test_soil_telemetry.py::test_soil_service_timeout_triggers_regional_fallback[asyncio] PASSED [ 61%]
tests/test_soil_telemetry.py::test_soil_service_503_triggers_unavailable_outside_fallback[asyncio] PASSED [ 62%]
tests/test_soil_telemetry.py::test_api_soil_telemetry_live_endpoint PASSED       [ 63%]
tests/test_soil_telemetry.py::test_api_soil_telemetry_invalid_coordinates_http_422 PASSED [ 65%]
tests/test_vision_api.py::test_get_vision_status_endpoint PASSED                 [ 66%]
tests/test_vision_api.py::test_diagnose_leaf_image_endpoint_valid_image PASSED [ 68%]
tests/test_vision_api.py::test_diagnose_leaf_image_invalid_empty_file PASSED   [ 69%]
tests/test_vision_api.py::test_diagnose_leaf_image_corrupt_file PASSED          [ 70%]
tests/test_vision_model_and_inference.py::test_build_efficientnet_b0_architecture PASSED [ 72%]
tests/test_vision_model_and_inference.py::test_load_model_checkpoint_missing_raises_error PASSED [ 73%]
tests/test_vision_model_and_inference.py::test_disease_classifier_unloaded_predict_raises_error PASSED [ 75%]
tests/test_vision_model_and_inference.py::test_disease_classifier_inference_with_trained_checkpoint PASSED [ 76%]
tests/test_vision_onnx_and_export.py::test_export_pytorch_to_onnx_and_inference PASSED [ 77%]
tests/test_vision_onnx_and_export.py::test_compare_pytorch_and_onnx_numerical_consistency PASSED [ 79%]
tests/test_vision_onnx_and_export.py::test_onnx_missing_file_raises_error PASSED [ 80%]
tests/test_vision_preprocessing.py::test_valid_image_loading_and_conversion PASSED [ 81%]
tests/test_vision_preprocessing.py::test_empty_image_raises_invalid_image_error PASSED [ 83%]
tests/test_vision_preprocessing.py::test_oversized_image_raises_image_too_large_error PASSED [ 84%]
tests/test_vision_preprocessing.py::test_corrupt_bytes_raises_corrupt_image_error PASSED [ 86%]
tests/test_vision_preprocessing.py::test_preprocessing_pytorch_tensor_output PASSED [ 87%]
tests/test_vision_preprocessing.py::test_preprocessing_onnx_numpy_output PASSED  [ 88%]
tests/test_vision_preprocessing.py::test_to_cv2_bgr_conversion PASSED             [ 90%]
tests/test_vision_severity.py::test_clean_healthy_leaf_severity PASSED           [ 91%]
tests/test_vision_severity.py::test_moderate_disease_leaf_severity PASSED         [ 93%]
tests/test_vision_severity.py::test_high_disease_leaf_severity PASSED            [ 94%]
tests/test_vision_severity.py::test_non_foliar_image_undetected PASSED            [ 95%]
tests/test_vision_severity.py::test_pil_image_input_compatibility PASSED          [ 97%]
tests/test_vision_training_pipeline.py::test_data_transforms_specifications PASSED [ 98%]
tests/test_vision_training_pipeline.py::test_load_datasets_and_micro_training_step PASSED [100%]

================== 72 passed, 5 warnings in 88.23s (0:01:28) ==================
```

---

## 6. Execution Instructions

1. Start the FastAPI development server:
   ```powershell
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Request an approved verified prescription (Tomato Early Blight, vegetative stage):
   ```powershell
   curl -X POST "http://localhost:8000/api/v1/fusion/recommend" -F "crop_name=Tomato" -F "crop_stage=Vegetative" -F "latitude=13.0" -F "longitude=77.0" -F "days_to_harvest=25" -F "diagnosed_disease=Early Blight" -F "diagnostic_confidence=0.92"
   ```
3. Test Pre-Harvest Interval (PHI) safety rejection (Rice Blast with 5 days to harvest; Tricyclazole mandates 30 days):
   ```powershell
   curl -X POST "http://localhost:8000/api/v1/fusion/recommend" -F "crop_name=Rice" -F "crop_stage=Tillering" -F "latitude=13.0" -F "longitude=77.0" -F "days_to_harvest=5" -F "diagnosed_disease=Blast" -F "diagnostic_confidence=0.89"
   ```
4. Test Healthy Crop Preservation (prescription suppressed):
   ```powershell
   curl -X POST "http://localhost:8000/api/v1/fusion/recommend" -F "crop_name=Tomato" -F "crop_stage=Vegetative" -F "latitude=13.0" -F "longitude=77.0" -F "diagnosed_disease=healthy" -F "diagnostic_confidence=0.98"
   ```

---

## 7. Readiness for Phase 5

- **Phase 4 Status:** 100% complete and fully verified.
- **Architectural Boundary:** Merchant inventory substitution and frontend client delivery have not been touched.
- **Phase 5 (Next Milestone):** Localized Merchant Substitution & Retail Matching Engine ($Q_s = Q_r \times (C_r / C_s)$, spatial PostGIS R-Tree queries within $d_{max}$, multi-objective dealer ranking by price, distance, and stock, and client delivery interface).
