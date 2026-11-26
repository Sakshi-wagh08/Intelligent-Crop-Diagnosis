# Phase 2: Vision Stream — Implementation Report

**Project Title:** Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System  
**Academic Document:** Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution  
**Milestone:** Phase 2 Completion  

---

## 1. Resource Inspection Findings

Prior to making any code modifications, an exhaustive inventory of the existing workspace and runtime environment was conducted:

| Inspection Item | Finding | Status / Assessment |
| :--- | :--- | :--- |
| **Plant Disease Image Dataset** | **None found** in repository | No pre-existing image dataset existed in the workspace. In compliance with project guidelines, **no fake datasets were created**. |
| **Trained Model Weights** | **None found** in `ml_models/weights/` | Directory was empty (contained only `.gitkeep`). In compliance with instructions, **no fake weights were generated**. |
| **Supported Crop & Disease Classes** | 3 Crops, 4 Diseases from Phase 1 DB | Extended to 7 diagnostic classes including healthy counterparts: `Tomato___Early_Blight`, `Tomato___Late_Blight`, `Tomato___healthy`, `Potato___Late_Blight`, `Potato___healthy`, `Rice___Blast`, `Rice___healthy`. |
| **Installed Vision Dependencies** | Installed & Verified: | - PyTorch: `2.15.0+cpu`<br>- Torchvision: `0.29.2+cpu`<br>- OpenCV: `5.0.0`<br>- Pillow: `13.0.0`<br>- NumPy: `2.5.5`<br>- ONNX Runtime: `1.32.0`<br>- scikit-learn: `1.9.1`<br>- onnx / onnxscript: `1.23.2` / `0.7.2` |

---

## 2. Implemented Features and Modules

### 2.1 Image Preprocessing Pipeline (`backend/app/vision/preprocessing.py`)
- **Format & Size Validation:** Restricts uploads to JPEG, PNG, and WEBP formats; rejects empty payloads and oversized uploads (> 15 MB).
- **EXIF Orientation Correction:** Automatically transposes mobile camera photographs based on EXIF tag `0x0112`.
- **Normalization:** Resizes images to $(224 \times 224)$ via bicubic interpolation and applies standard ImageNet channel normalization ($\mu=[0.485, 0.456, 0.406]$, $\sigma=[0.229, 0.224, 0.225]$).
- **Format Decoupling:** Converts incoming images to both `torch.Tensor` of shape `(1, 3, 224, 224)` for PyTorch, NumPy `float32` array for ONNX Runtime, and OpenCV BGR format for segmentation.

### 2.2 EfficientNet-B0 Model Architecture (`backend/app/vision/model.py`)
- Implements `build_efficientnet_b0` using `torchvision.models.efficientnet_b0`.
- Replaces classification head with custom `Sequential(Dropout(p=0.2), Linear(1280, num_classes))`.
- Provides `load_model_checkpoint` with state dictionary verification, class-to-index mapping, and graceful error reporting via `ModelWeightsNotFoundError`.

### 2.3 Disease Classification Engine (`backend/app/vision/classifier.py`)
- Executes forward inference on normalized tensors.
- Computes softmax probability distribution across classes.
- Generates ranked top-k predictions with confidence scoring.
- Parses predictions into structured crop, pathology, and health flags.
- Rejects inference with clear error handling when weights are missing on disk.

### 2.4 Disease Severity Estimation (`backend/app/vision/segmentation.py`)
- Employs dual-color-space segmentation (HSV and LAB) to isolate the leaf blade from neutral or noisy backgrounds.
- Identifies necrotic brown/black lesion tissue and chlorotic yellowing strictly within the foliar boundary.
- Calculates the mathematical lesion-to-leaf surface area ratio:
  $$S_{severity} = \frac{\text{Lesion Pixels}}{\text{Leaf Pixels}}$$
- Maps $S_{severity}$ to agronomic severity tiers: **None / Trace** ($<1\%$), **Low** ($1\%-10\%$), **Moderate** ($10\%-25\%$), **High** ($>25\%$).
- Generates severity factor $F_v$ ($1.00$ to $1.25$) for downstream dosage calculation in Phase 4.
- Includes reliability checks (e.g. `leaf_detected`, minimum foliage area threshold) and standard heuristic advisory disclaimers.

### 2.5 ONNX Optimization & Consistency Testing (`backend/app/vision/onnx_engine.py`)
- Implements `export_pytorch_to_onnx` with Opset 17 and dynamic batch axes.
- Implements `ONNXDiseaseClassifier` using `onnxruntime.InferenceSession` with automatic provider selection (`CPUExecutionProvider` / `CUDAExecutionProvider`).
- Implements `compare_pytorch_and_onnx` ensuring absolute difference between PyTorch and ONNX Runtime predictions remains within $\le 10^{-3}$.

### 2.6 Training Pipeline (`ml_models/train.py`)
- Complete CLI training script supporting both partitioned (`train/`, `val/`, `test/`) and unpartitioned class directory structures.
- Incorporates data augmentations (RandomHorizontalFlip, RandomVerticalFlip, RandomRotation, ColorJitter).
- Implements AdamW optimizer, Cosine Annealing learning rate schedule, CrossEntropyLoss, and best-model checkpointing.
- Evaluates class-wise Precision, Recall, F1-Score, and Confusion Matrix using `scikit-learn`.

### 2.7 Model Export CLI (`ml_models/export_onnx.py`)
- Standalone CLI utility exporting trained `.pth` checkpoints to `.onnx` and applying optional FP16 post-training quantization.

### 2.8 Unified Vision Service & REST API Integration (`backend/app/api/v1/endpoints/vision.py`)
- Coordinates image preprocessing, severity estimation, and disease diagnosis.
- Endpoints:
  - `GET /api/v1/vision/status`: Reports runtime initialization and supported classes.
  - `POST /api/v1/vision/diagnose`: Accepts leaf photograph upload, executes severity segmentation, and returns diagnostic results (or informative model status when weights are not yet trained).
  - Complies with architectural boundary: does **not** link predictions to chemical dosage or merchant substitution in this phase.

---

## 3. Dataset Acquisition and Model Training Guide

Because no verified image dataset was pre-loaded in the workspace, the training pipeline has been constructed and validated on synthetic verification batches. To train the production weights:

1. **Obtain the Dataset:**
   - Download the public **PlantVillage Dataset** (or university/government agricultural extension field imagery).
2. **Organize Classes:**
   Create a directory with class folders matching the supported database classes:
   ```
   dataset/
   ├── Tomato___Early_Blight/
   ├── Tomato___Late_Blight/
   ├── Tomato___healthy/
   ├── Potato___Late_Blight/
   ├── Potato___healthy/
   ├── Rice___Blast/
   └── Rice___healthy/
   ```
3. **Execute Training:**
   ```powershell
   python ml_models/train.py --data_dir path/to/dataset --output_dir ml_models/weights --epochs 25 --batch_size 32 --lr 1e-4
   ```
4. **Export to ONNX:**
   ```powershell
   python ml_models/export_onnx.py --checkpoint ml_models/weights/efficientnet_b0_best.pth --output_onnx ml_models/weights/efficientnet_b0_fp16.onnx
   ```

---

## 4. Automated Test Results

The automated test suite (`pytest tests/ -v`) was executed across all 35 tests (10 from Phase 1 + 25 from Phase 2), achieving a **100% pass rate**:

```
tests/test_crops_api.py::test_get_crops_returns_seeded_crops PASSED      [  2%]
tests/test_database_models.py::test_crops_and_diseases_relationship PASSED [  5%]
tests/test_database_models.py::test_base_treatments_and_active_ingredients PASSED [  8%]
tests/test_database_models.py::test_merchant_product_relationships PASSED [ 11%]
tests/test_database_models.py::test_chemical_incompatibilities PASSED    [ 14%]
tests/test_health.py::test_root_endpoint PASSED                          [ 17%]
tests/test_health.py::test_health_endpoint PASSED                        [ 20%]
tests/test_merchants_api.py::test_get_nearby_merchants_within_radius PASSED [ 22%]
tests/test_merchants_api.py::test_get_nearby_merchants_filtered_by_active_ingredient PASSED [ 25%]
tests/test_soil_api.py::test_soil_telemetry_endpoint PASSED              [ 28%]
tests/test_vision_api.py::test_get_vision_status_endpoint PASSED         [ 31%]
tests/test_vision_api.py::test_diagnose_leaf_image_endpoint_valid_image PASSED [ 34%]
tests/test_vision_api.py::test_diagnose_leaf_image_invalid_empty_file PASSED [ 37%]
tests/test_vision_api.py::test_diagnose_leaf_image_corrupt_file PASSED   [ 40%]
tests/test_vision_model_and_inference.py::test_build_efficientnet_b0_architecture PASSED [ 42%]
tests/test_vision_model_and_inference.py::test_load_model_checkpoint_missing_raises_error PASSED [ 45%]
tests/test_vision_model_and_inference.py::test_disease_classifier_unloaded_predict_raises_error PASSED [ 48%]
tests/test_vision_model_and_inference.py::test_disease_classifier_inference_with_trained_checkpoint PASSED [ 51%]
tests/test_vision_onnx_and_export.py::test_export_pytorch_to_onnx_and_inference PASSED [ 54%]
tests/test_vision_onnx_and_export.py::test_compare_pytorch_and_onnx_numerical_consistency PASSED [ 57%]
tests/test_vision_onnx_and_export.py::test_onnx_missing_file_raises_error PASSED [ 60%]
tests/test_vision_preprocessing.py::test_valid_image_loading_and_conversion PASSED [ 62%]
tests/test_vision_preprocessing.py::test_empty_image_raises_invalid_image_error PASSED [ 65%]
tests/test_vision_preprocessing.py::test_oversized_image_raises_image_too_large_error PASSED [ 68%]
tests/test_vision_preprocessing.py::test_corrupt_bytes_raises_corrupt_image_error PASSED [ 71%]
tests/test_vision_preprocessing.py::test_preprocessing_pytorch_tensor_output PASSED [ 74%]
tests/test_vision_preprocessing.py::test_preprocessing_onnx_numpy_output PASSED [ 77%]
tests/test_vision_preprocessing.py::test_to_cv2_bgr_conversion PASSED    [ 80%]
tests/test_vision_severity.py::test_clean_healthy_leaf_severity PASSED   [ 82%]
tests/test_vision_severity.py::test_moderate_disease_leaf_severity PASSED [ 85%]
tests/test_vision_severity.py::test_high_disease_leaf_severity PASSED    [ 88%]
tests/test_vision_severity.py::test_non_foliar_image_undetected PASSED   [ 91%]
tests/test_vision_severity.py::test_pil_image_input_compatibility PASSED [ 94%]
tests/test_vision_training_pipeline.py::test_data_transforms_specifications PASSED [ 97%]
tests/test_vision_training_pipeline.py::test_load_datasets_and_micro_training_step PASSED [100%]

======================= 35 passed, 5 warnings in 36.69s =======================
```

---

## 5. Remaining Items & Readiness for Phase 3

- **Phase 2 Status:** 100% complete and fully verified.
- **Model Weights:** The training pipeline and ONNX export engines are ready; actual model weights (`.pth` / `.onnx`) will be generated whenever the user trains on their selected image dataset.
- **Phase 3 (Next Step):** Remote Soil Telemetry integration (ISRIC SoilGrids 2.0 RESTful Spatial API client with asynchronous HTTPX, coordinate caching, and regional agronomic fallback matrix).
