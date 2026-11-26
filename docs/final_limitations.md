# Scientific and Technical Limitations Report

**Project Title:** Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System  
**Academic Context:** Design Thinking (DT) Final-Year Capstone Engineering Project  
**Date:** November 2026  
**Status:** Audited Academic Prototype / Experimental Demonstration System  

---

## Executive Summary

In adherence to strict scientific integrity and academic transparency, this document provides an exhaustive, unambiguous disclosure of the empirical, agronomic, regulatory, and technical limitations of the **Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System**. 

The system was engineered as a proof-of-concept multimodal fusion architecture that synthesizes visual deep learning, remote geospatial soil telemetry, rule-based agronomic guidelines, and localized dealer substitution. While the architectural integration, safety gates, and multi-objective ranking engines function predictably and achieve 100% test passage across 130 automated tests, the underlying datasets, sensory approximations, and empirical models possess fundamental boundaries that preclude unverified real-world agronomic deployment without human expert supervision.

---

## 1. Computer Vision & Machine Learning Limitations

### 1.1 Dataset Provenance and Licensing Uncertainty
- **PlantVillage Dataset:** The 5 canonical classes (`Potato___healthy`, `Potato___Late_Blight`, `Tomato___Early_Blight`, `Tomato___healthy`, `Tomato___Late_Blight`) originate from the crowd-sourced PlantVillage repository (Hughes & Salathé, 2015). Although frequently mirrored under permissive open-access wrappers, the upstream terms state that images are provided for research and educational purposes. A rigorous legal chain-of-title audit reveals residual ambiguity regarding commercial redistribution permissions.
- **Rice Leaf Diseases Dataset:** The 2 rice classes (`Rice___healthy`, `Rice___Leaf_Blast`) were sourced from the public domain dataset compiled by Pereira and Huy Minh Do (Kaggle). While the Kaggle wrapper is tagged as Open Data / CC0, the original collection protocol, exact image authorship, and underlying field ownership remain historically unverified. Consequently, the dataset cannot be certified as fully public domain under strict statutory IP standards.

### 1.2 Upstream PlantVillage Leaf Grouping and Contamination Audit
A critical vulnerability in plant pathology deep learning benchmarks is **leaf-level identity contamination** (or image-level versus plant-level leakage). Multiple photographs of the exact same physical leaf—captured under varying camera angles, lighting conditions, or distances—can be distributed across the training and testing sets, artificially inflating validation accuracy.

To evaluate this phenomenon empirically in our project:
1. The official upstream grouping manifest `leaf_grouping/leaf-map.json` (40,328 entries, compiled by Mohanty et al., 2016) was downloaded and mapped to the project's raw image corpus.
2. The mapping was established by matching the standardized filename suffix (e.g., `00fc2ee5-...___RS_HL_1864.JPG` $\to$ `rs_hl 1864`).
3. Out of 750 PlantVillage images in the project corpus:
   - **`Potato___healthy`:** 150/150 images mapped to only **69 unique physical leaves** (an average of 2.17 photographs per physical leaf).
   - **`Potato___Late_Blight`:** 150/150 images mapped to **116 unique physical leaves**.
   - **`Tomato___Early_Blight`:** 150/150 images mapped to **119 unique physical leaves**.
   - **`Tomato___healthy`:** 100/150 images mapped to unique physical leaves; 50 images were greenhouse photographs (`GH_HL_Leaf` subset) that were never indexed in the upstream `leaf-map.json`.
   - **`Tomato___Late_Blight`:** 66/150 images mapped to physical leaves; 84 images (`GHLB2` subset) were unindexed greenhouse photographs.
   - **`Rice Leaf Diseases`:** 0/300 images mapped, as the Rice dataset was collected independently and possesses zero physical plant grouping metadata.
4. **Leakage Implication:** Because only 616 out of 750 PlantVillage images (82.1%) could be mapped to upstream physical leaf IDs, and 0% of the Rice images possess leaf IDs, an absolute, leak-free physical plant-level split cannot be mathematically guaranteed across the entire 7-class taxonomy. Random splitting at the image file level introduces the risk that the model learns persistent physical leaf contours rather than pathology-specific chlorosis patterns.
5. **Academic Reporting Requirement:** The reported model accuracy ($93.17\%$ Top-1 on the 161-image test set) must be classified as an **academic experimental benchmark** and must not be cited as a field-generalized production metric.

### 1.3 Historical Staging Checkpoint and 6-Class vs. 7-Class Validation
- **Historical 7-Class Benchmark (93.17%):** The persisted model checkpoint (`ml_models/weights/efficientnet_b0_best.pth`, task-1814) was trained on a historical 1,129-image staging dataset. Forensic hash reconciliation revealed that this historical staging set contained **79 duplicate image files** within the `Rice___healthy` class (229 raw files representing 150 unique SHA-256 images). In the clean 161-image test set, **17 of 23 `Rice___healthy` test images appeared in the training set**. Therefore, the 93.17% (150/161) figure must strictly be described as an **experimental prototype staging benchmark with known duplicate contamination**, not an independent out-of-sample validation.
- **Uncontaminated Held-Out Result (6 Classes, 94.20%):** When the contaminated `Rice___healthy` class is isolated, the remaining 6 classes (138 samples total, 23 per class) achieve $130 / 138 \approx \mathbf{94.20\%}$ accuracy. This metric is strictly an **image-level held-out experimental result on uncontaminated classes**. It must not be cited as fully independent validation or proven generalization.
- **Zero Field Validation:** The model was tested exclusively on curated laboratory and greenhouse imagery. Performance under natural field conditions (variable sunlight, shadows, overlapping canopies, complex weed backgrounds) has **not been validated in the field**.

### 1.4 Architectural and Sensory Invariance
- **Single-Leaf Lab Photographs vs. Field Imagery:** The EfficientNet-B0 model was trained predominantly on isolated, single-leaf photographs taken against plain grey or black laboratory backgrounds.
- **Occlusion and Background Confusion:** In real-world agricultural fields, images contain complex backgrounds, soil patches, weeds, severe insect damage, overlapping canopies, dynamic shadows, and direct solar glare. Model confidence degrades substantially when exposed to in-situ field clutter.
- **Pathology Disambiguation:** Pathologies exhibiting similar macroscopic foliar lesions (e.g., Early Blight vs. Septoria Leaf Spot, or physiological nutrient deficiencies like potassium chlorosis) cannot be reliably distinguished without microscopic or molecular assay.

---

## 2. Foliar Severity Estimation ($S_{severity}$) Limitations

### 2.1 Heuristic Color-Space Segmentation
- The lesion severity engine relies on classical OpenCV computer vision algorithms: HSV/LAB color thresholding and Otsu adaptive binarization to segment green leaf tissue from necrotic/chlorotic lesions.
- **Formula:**
  $$S_{severity} = \frac{\text{Lesion Area (Pixels)}}{\text{Total Leaf Area (Pixels)}}$$
- **Limitations:**
  1. **Color Variation:** Natural leaf senescence, purple anthocyanin pigmentation, yellowing due to drought, or pesticide spray residue are easily misclassified as disease lesions.
  2. **Lighting Sensitivity:** Non-uniform illumination, specular highlights on waxy cuticles, and deep shadows distort the HSV/LAB color bounds.
  3. **Planar Assumption:** The 2D photograph assumes a flat, planar leaf perpendicular to the lens. In nature, diseased leaves curl, shrivel, and droop, causing severe projective distortion of the true surface area ratio.
  4. **Canopy-Level Generalization:** Single-leaf lesion percentage does not represent field canopy disease incidence or epidemic progression across an entire crop stand.

---

## 3. Remote Geospatial Soil Telemetry Limitations

### 3.1 Coarse Spatial Resolution and Service Availability Notice
- Remote soil telemetry is fetched from the **ISRIC SoilGrids 2.0 RESTful API**.
- **Official Service Status:** Official ISRIC advisory notices indicate that technical difficulties have led to **temporary pauses of the SoilGrids REST API**, with no formal timeline for full operational restoration. ISRIC emphasizes that the REST endpoint is a complementary, beta-stage service without uptime guarantees or formal production SLAs.
- **Availability Classification:** The API is classified as **availability-not-guaranteed**. While an isolated empirical probe succeeded on Nov 26, 2026 (HTTP 200 in 1.20s), a single successful request does not establish service restoration or reliability. The regional agronomic fallback remains an essential operational safeguard.
- **Coarse Resolution (250m Grid):** SoilGrids generates predictions using machine learning models (Quantile Random Forests) trained on global soil profiles and satellite environmental covariates at a spatial resolution of **250 meters per pixel**. A single 250m grid cell covers approximately $6.25\text{ hectares}$ ($15.4\text{ acres}$). Within a smallholder farm of 0.5 to 2.0 acres, localized soil amendments exist that cannot be resolved at 250m satellite resolution. Telemetry cannot reflect live dynamic field moisture.

### 3.2 Modeled Estimates vs. Laboratory Soil Core Testing
- **Statutory Notice:** SoilGrids data provides statistical expected medians and quantile intervals ($Q_{0.05}, Q_{0.50}, Q_{0.95}$), not empirical measurements of the farmer's physical soil.
- Soil pH, Soil Organic Carbon (SOC), and Available Water Capacity (AWC) derived from telemetry must be treated as indicative background baselines. They cannot replace certified wet-chemistry laboratory soil core analysis for regulatory compliance or fertilizer billing.

### 3.3 Regional Fallback Agronomic Boundaries
- When the external ISRIC RESTful API times out, returns HTTP 5xx, or fails during offline deployment, the system triggers the **Regional Soil Fallback** engine based on published ICAR-NBSS&LUP agro-climatic zones.
- **Geographic Coverage:** The documented fallback covers Karnataka's 10 Agro-Climatic Zones (Coastal, Hilly, Northern/Southern Dry, Eastern Dry, Central/Southern Transition). Coordinates outside Karnataka return an explicit `data_status: "unavailable"`.
- Fabricated or synthetic soil values are strictly prohibited across all application layers.

---

## 4. Multimodal Fusion & Chemical Recommendation Limitations

### 4.1 Statutory Dosage Bounds ($D_{\text{label\_max}}$) & Severity Multiplier Neutralization
- In the multimodal dosage formulation:
  $$D = \min(D_0 \times F_s \times F_v, D_{\text{label\_max}})$$
- **Severity Factor ($F_v$):** In strict accordance with the Central Insecticides Board & Registration Committee (CIBRC) statutory guidelines, chemical active ingredient dosage multipliers based on severity are **disabled ($F_v = 1.00$)**. Increasing chemical pesticide concentration above the approved label claim to combat severe infection violates statutory regulations and promotes phytotoxicity and chemical resistance.
- **Neutral Severity Factor ($F_v = 1.00$):** Following a comprehensive release audit, all unsupported severity-based chemical multipliers have been eliminated. Both the standalone vision diagnosis API (`POST /api/v1/vision/diagnose`) and the multimodal fusion engine (`POST /api/v1/fusion/recommend`) strictly return neutral $F_v = 1.00$. Visual foliar lesion percentage ($S_{\text{severity}}$) is strictly distinguished from pesticide dosage calculations.
- **Carrier Water Volume:** Unsupported severity-based carrier water multipliers have also been removed; carrier water volume strictly remains at certified package-of-practices baselines.
- **Soil Uptake Factor ($F_s$):** Soil properties do not alter foliar spray application rates ($F_s = 1.00$). $F_s$ scaling is mathematically reserved exclusively for soil-applied systemic chemicals.

### 4.2 Diagnostic Confidence Safety Gate
- Any visual classification yielding a Softmax confidence probability below **70% ($< 0.70$)** is automatically rejected by the Safety Gate.
- In uncertain cases, chemical treatment recommendations are suppressed, and the user is directed to physical inspection by a certified Agricultural Extension Officer.

### 4.3 Pre-Harvest Interval (PHI) Residue Safety
- The system enforces published statutory Pre-Harvest Intervals (e.g., Mancozeb: 14 days; Dimethomorph: 14 days; Azoxystrobin: 5 days).
- If the farmer's scheduled harvest falls within the PHI window, chemical application is strictly forbidden to prevent hazardous consumer residue contamination.

---

## 5. Localized Merchant Substitution & Ranking Limitations

### 5.1 Single Active Ingredient Equivalence Boundary
- The substitution engine evaluates direct product substitution using the active ingredient equivalence formula:
  $$Q_s = Q_r \times \left(\frac{C_r}{C_s}\right)$$
- **Boundary:** The substitution logic is certified **only for single active ingredient fungicides and pesticides** sharing compatible formulations (e.g., WP $\leftrightarrow$ WDG $\leftrightarrow$ SC foliar suspensions).
- **Multi-Active Tank Mixes:** Ready-mix combination formulations (e.g., Metalaxyl 8% + Mancozeb 64% WP) possess complex synergistic ratios and proprietary adjuvants that cannot be safely substituted with generic single-active products using linear concentration ratios.

### 5.2 Unit Conversion Assumptions
- Concentration conversions between $\% \text{ w/w}$, $\% \text{ w/v}$, $\text{g/kg}$, and $\text{g/L}$ require verifiable physical density data ($\rho$).
- Conversions between mass (kg) and volume (L) without verified product specific gravity are explicitly rejected by the calculation engine.

### 5.4 Database Host Availability and PostGIS Status
- Host port 5432 is currently closed/offline.
- While database-offline fallbacks function without application crashes, live PostGIS spatial SQL indexing (`ST_DWithin`, GiST spatial index scans) remains **unverified** in live execution until PostgreSQL is started (`docker compose up -d`). Database-offline fallback handling does not constitute successful live PostGIS verification.

### 5.5 Interactive Browser Testing Scope
- Automated testing encompasses 15 Vitest component integration tests and clean production Vite asset builds.
- However, live automated browser interaction timed out on local desktop origin permission prompts and was not completed. Serving HTTP 200 for SPA routes confirms web server routing and reverse-proxy connectivity, not interactive browser workflow execution.

---

## 6. Summary Compliance Matrix

| Subsystem | Metric / Assumption | Empirical Prototype Status | Production Prerequisite |
| :--- | :--- | :--- | :--- |
| **Vision Model** | 93.17% Top-1 Accuracy | Experimental Benchmark on Staging Dataset | Multi-source field dataset with physical plant isolation and verified licenses |
| **Lesion Severity** | Planar 2D Color Ratio | Heuristic Color-Space Approximation | Multi-spectral 3D canopy LiDAR or semantic segmentation |
| **Soil Telemetry** | 250m Grid Modeled Medians | Global Covariate Estimate (ISRIC SoilGrids 2.0) | GPS-stamped wet-chemistry laboratory soil core test |
| **Chemical Dosage** | $D = \min(D_0 \cdot F_s \cdot F_v, D_{\max})$ | Bounded Rule-Based Regulatory Formulations | Ground verification by Certified Extension Officer |
| **Substitution** | $Q_s = Q_r \cdot (C_r / C_s)$ | Valid for Single Active Ingredient Products | Formulation adjuvant compatibility and distributor verification |
| **Dealer Spatial** | PostGIS GiST Radius Search | Synthetic Demonstration Records | Real-time ERP/POS integration with licensed local dealers |
