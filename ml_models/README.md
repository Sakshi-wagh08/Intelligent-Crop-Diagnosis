# Machine Learning Models Directory

This directory contains the computer vision training scripts, dataset preparation pipelines, trained neural network weights, ONNX export tools, and evaluation benchmarks for the **Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System**.

## 1. Specifications & Architecture
- **CNN Backbone:** EfficientNet-B0 (`torchvision.models.efficientnet_b0`) initialized with ImageNet-1K pretrained weights (`rwightman-7f5810bc`).
- **Classification Head:** `nn.Sequential(nn.Dropout(p=0.2), nn.Linear(1280, 7))`
- **Input Resolution:** $(3, 224, 224)$ normalized with ImageNet statistics ($\mu=[0.485, 0.456, 0.406], \sigma=[0.229, 0.224, 0.225]$).
- **Inference Runtimes:**
  - **PyTorch (Development & Training):** Full backward pass, autograd, and checkpoint serialization.
  - **ONNX Runtime (Production Inference):** Opset 17 dynamic batch inference optimized for low CPU/edge latency.
- **Severity Segmentation:** Foliar contour extraction and dual-color-space (HSV & LAB) lesion-to-leaf surface area ratio estimation:
  $$S_{severity} = \frac{\text{Lesion Pixels}}{\text{Leaf Pixels}}$$

---

## 2. Supported Canonical Diagnostic Classes

The model classifies 7 canonical agricultural classes covering 3 crops:

1. `Potato___Late_Blight` (*Phytophthora infestans*)
2. `Potato___healthy`
3. `Rice___Blast` (*Magnaporthe oryzae*)
4. `Rice___healthy`
5. `Tomato___Early_Blight` (*Alternaria solani*)
6. `Tomato___Late_Blight` (*Phytophthora infestans*)
7. `Tomato___healthy`

---

## 3. Directory Layout

```
ml_models/
├── dataset_pipeline.py     # Automated dataset download, cleaning, SHA-256 deduplication, stratified split
├── train.py                # EfficientNet-B0 transfer learning with AdamW, Cosine Annealing, and class weights
├── export_onnx.py          # PyTorch checkpoint to ONNX Opset 17 exporter
├── evaluate_model.py       # Isolated test set evaluation, classification report, and latency benchmarking
├── README.md               # Directory documentation
└── weights/                # Model artifacts (persisted on disk)
    ├── efficientnet_b0_best.pth       # Best PyTorch checkpoint (16.3 MB)
    ├── efficientnet_b0.onnx           # ONNX model topology (659 KB)
    ├── efficientnet_b0.onnx.data      # ONNX tensor weights (16.0 MB)
    ├── training_history.json          # 12-epoch loss, accuracy, and learning rate curves
    └── evaluation_report.json         # Per-class metrics, confusion matrix, and latency benchmarks
```

---

## 4. Model Evaluation Summary (Audited Test Set)

Evaluated on the audited clean 161-image test set (strictly 23 images per class, zero cross-split leakage):

| Metric | PyTorch Engine (CPU) | ONNX Runtime Engine (CPU) |
| :--- | :---: | :---: |
| **Top-1 Accuracy** | **93.17%** | **93.17%** |
| **Top-2 Accuracy** | **99.38%** | **99.38%** |
| **Macro F1-Score** | **0.9313** | **0.9313** |
| **Weighted F1-Score** | **0.9313** | **0.9313** |
| **Prediction Parity** | — | **100.00% match** (max abs diff: $1.43 \times 10^{-6}$) |
| **Mean Inference Latency** | $38.88\text{ ms}$ | **$11.35\text{ ms}$** ($3.42\times$ speedup) |
| **P95 Latency** | $50.52\text{ ms}$ | **$14.42\text{ ms}$** |

*(Historical reference: Evaluated on initial 183-sample partition before Rice duplicate purging: Top-1 Accuracy: 93.44%, Top-2 Accuracy: 99.45%, Macro F1: 0.9383).*

---

## 5. Execution & Reproduction Commands

### 5.1 Dataset Pipeline
```powershell
python ml_models/dataset_pipeline.py
```
Ingests genuine PlantVillage and Rice Leaf Diseases imagery, cleans corrupt files, removes SHA-256 duplicates, creates 70/15/15 stratified splits, and writes `data/dataset_manifest.json`.

### 5.2 Training
```powershell
python ml_models/train.py --data_dir data/processed --output_dir ml_models/weights --epochs 12 --batch_size 32 --lr 1e-4 --seed 42
```

### 5.3 ONNX Export
```powershell
python ml_models/export_onnx.py --checkpoint ml_models/weights/efficientnet_b0_best.pth --output_onnx ml_models/weights/efficientnet_b0.onnx
```

### 5.4 Test Evaluation
```powershell
python ml_models/evaluate_model.py
```

### 5.5 Verification Tests
```powershell
python -m pytest tests/test_vision_phase7_model.py -v
```
