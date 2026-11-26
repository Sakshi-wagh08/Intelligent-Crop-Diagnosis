# Phase 7: Plant Disease Dataset Preparation, Model Training, Validation & Comprehensive Technical Audit Report

**Project Title:** Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System  
**Academic Document:** Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution  
**Milestone:** Phase 7 Completion — Genuine Dataset Preparation, Model Training, Technical Audit & Final Clarification  
**Audit & Clarification Date:** November 2026  
**Status:** Audited, Reconciled, and Fully Clarified  

---

## 1. Executive Summary & Audit Context

Following completion of Phase 7 training, a comprehensive technical and scientific audit was conducted to verify dataset staging history, train/test leakage boundaries, licensing provenance, and benchmark evaluation integrity.

### Core Audit Disclosures
1. **Historical Training Dataset Staging:** The active model checkpoint (`efficientnet_b0_best.pth`) was trained using the historical **$1,129$-image staging dataset** ($770$ train, $176$ validation, $183$ test), **not** the regenerated $1,050$-image clean dataset.
2. **Historical Train/Test Contamination (Critical Disclosure):**
   - Across the regenerated $161$-image clean test set ($23$ images per class), **$17$ test images ($10.56\%$) were present in the model's historical training data**, and **$5$ test images ($3.11\%$) were present in historical validation**.
   - **$100\%$ of this contamination is concentrated in the `Rice___healthy` class**: $17$ of the $23$ clean test images ($73.91\%$) were in historical training, and $5$ ($21.74\%$) were in historical validation, leaving only $1$ strictly unseen sample.
   - For all other $6$ classes ($138$ test images: Tomato and Potato classes, and Rice Blast), **$0$ clean test images appeared in historical training or validation**.
   - **Scientific Assessment:** The $93.17\%$ test evaluation **cannot legitimately be described as a completely held-out, out-of-sample test evaluation** due to this historical split overlap in Rice Healthy.
3. **PlantVillage Grouping Metadata Investigation:**
   - The upstream PlantVillage repository (`spMohanty/PlantVillage-Dataset`) and its Hugging Face mirror provide `leaf_grouping/leaf-map.json` mapping image files to unique leaf identifiers (`leaf_id`).
   - The project's automated download pipeline did not ingest `leaf-map.json` and partitioned images using random image-level shuffling.
   - Consequently, **leaf-level and plant-level independence was not established** in the experimental splits; multiple photographs of the same physical leaf may exist across train, validation, and test splits.
4. **Dataset Licensing Clarification:**
   - **PlantVillage:** The Mohanty et al. (2016) paper in *Frontiers in Plant Science* declares open access under **CC BY 4.0** (governing the paper text and figures); the Hugging Face dataset card declares **CC BY-SA 3.0**; the original GitHub image repository contains no root `LICENSE` file. The paper's publication license cannot be treated as automatic proof of the image dataset's license. Claims of CC0 Public Domain cannot be legally substantiated.
   - **Rice Leaf Diseases:** Jonathan Pereira's wrapper GitHub repository carries a **GPL-3.0** license for its code, but the underlying images were harvested from Kaggle user Huy Minh Do (`minhhuy2810/rice-diseases-image-dataset`), where they were uploaded under standard Kaggle community terms without an explicit open-source or commercial license. The exact underlying image license remains **unverified**.
5. **Benchmark Performance Metrics Preserved:**
   - **Clean $161$-Sample Test Set ($23$/class):** Overall Top-1 Accuracy: **$93.17\%$** ($150 / 161$), Top-2 Accuracy: **$99.38\%$** ($160 / 161$), Macro F1: **$0.9313$**.
   - **Strictly Held-Out Subset Performance ($6$ non-rice-healthy classes, $138$ samples):** Top-1 Accuracy: **$94.20\%$** ($130 / 138$).
   - **Historical $183$-Sample Test Set (Reference):** Top-1 Accuracy: **$93.44\%$** ($171 / 183$), Top-2 Accuracy: **$99.45\%$**, Macro F1: **$0.9383$** (included $22$ duplicate Rice Healthy test images).
6. **Prediction Probabilities on Misclassified Rice Blast Test Samples:** All $5$ misclassified `Rice___Blast` test images had `Rice___Blast` as their immediate Top-2 prediction, with second-choice probabilities of $25.59\%$, $35.17\%$, $46.61\%$, $25.95\%$, and $14.52\%$ (mean: **$29.57\%$**).
7. **ONNX Export and Numerical Parity:** $100.00\%$ Top-1 prediction agreement across all $161$ test images with a maximum absolute probability difference of $1.43 \times 10^{-6}$ and an average CPU inference latency of $11.35\text{ ms}$ (vs. $38.88\text{ ms}$ in PyTorch).

---

## 2. Dataset Reconciliation & Provenance Analysis

### 2.1 Technical Mechanism of the 79 Duplicate Images in Historical Staging
The discrepancy between the canonical $1,050$-image clean dataset and the $1,129$-image training staging was traced through the execution history:

1. **Step 1667 (`ml_models/dataset_pipeline.py`):**
   - Tomato classes ($3 \times 150$), Potato classes ($2 \times 150$), and Rice Healthy ($150$) were downloaded, cleaned, and split using `random.seed(42)`.
   - Rice Blast extracted $0$ images due to folder naming (`LeafBlast` without hyphen in the zip archive).
   - Python's `random.shuffle()` was called sequentially for:
     - Class 0 (`Tomato___Early_Blight`): Call 1
     - Class 1 (`Tomato___Late_Blight`): Call 2
     - Class 2 (`Tomato___healthy`): Call 3
     - Class 3 (`Potato___Late_Blight`): Call 4
     - Class 4 (`Potato___healthy`): Call 5
     - Class 5 (`Rice___Blast`): Skipped ($0$ images)
     - Class 6 (`Rice___healthy`): Call 6 ($105$ train, $22$ val, $23$ test)
2. **Step 1772 (Rice Blast Integration & Re-split):**
   - Rice Blast ($150$ images) was extracted and placed in `data/raw/Rice___Blast`.
   - `create_stratified_splits` was re-executed with `random.seed(42)`. **However, `data/processed/` was not purged prior to copying.**
   - For Classes 0–4 (Tomato and Potato), shuffle calls 1–5 produced identical file sequences, overwriting identical destination paths.
   - For Class 5 (`Rice___Blast`), $150$ images were partitioned for the first time ($105$ train, $22$ val, $23$ test).
   - For Class 6 (`Rice___healthy`), shuffle call 7 was now executed instead of call 6, generating a **different permutation** of the exact same $150$ clean images.
3. **Accumulation in `data/processed/`:**
   - Because `shutil.copy2` does not delete existing directory contents, the newly permuted Rice Healthy files were copied into folders that already contained the Step 1667 files:
     - **Train:** $105$ (new shuffle) $+$ $35$ (overlapping leftovers from previous shuffle) = **$140$ files**
     - **Val:** $22$ (new shuffle) $+$ $22$ (overlapping leftovers from previous shuffle) = **$44$ files**
     - **Test:** $23$ (new shuffle) $+$ $22$ (overlapping leftovers from previous shuffle) = **$45$ files**
     - **Total Rice Healthy Files:** $140 + 44 + 45 = \mathbf{229}$ files ($150$ unique images $+$ $79$ duplicate instances).
   - **Historical Staging Partition Sizes at Training (`task-1814`):**
     - Train: $105 \times 6 + 140 = \mathbf{770}$ images
     - Val: $22 \times 6 + 44 = \mathbf{176}$ images
     - Test: $23 \times 6 + 45 = \mathbf{183}$ images
     - Total: $770 + 176 + 183 = \mathbf{1,129}$ images.

### 2.2 Image Identity and Cryptographic Hash Verification
- Cryptographic SHA-256 analysis of all $1,050$ images in `data/clean` confirmed exactly **$1,050$ unique SHA-256 hashes** with **zero internal duplicates**.
- The $79$ additional files present during `task-1814` training were identical cryptographic copies of existing files within the $150$-image Rice Healthy clean set.
- No separate photographs, distinct plants, or alternate resolutions contributed to the $79$-image difference.

---

## 3. Train/Test Contamination Audit (Historical Staging vs. Clean Test Set)

To evaluate whether the model's test evaluation represents an out-of-sample benchmark, an identity-level comparison was performed between the historical training staging used by `task-1814` ($770$ train, $176$ val, $183$ test) and the regenerated clean $161$-image test partition ($23$ images per class).

### 3.1 Overlap Quantification Across Partitions

| Split Comparison | Clean Test Images Found | Total Clean Test Images | Contamination Percentage | Affected Classes |
| :--- | :---: | :---: | :---: | :--- |
| **Historical Training vs. Clean Test** | **17** | 161 | **10.56%** | `Rice___healthy` only ($17 / 23 = \mathbf{73.91\%}$) |
| **Historical Validation vs. Clean Test** | **5** | 161 | **3.11%** | `Rice___healthy` only ($5 / 23 = \mathbf{21.74\%}$) |
| **Historical Test vs. Clean Test** | **161** | 161 | **100.00%** | All 7 classes ($161 / 161 = 100\%$) |
| **Strictly Unseen in Train & Val** | **1** | 161 | **0.62%** | `Rice___healthy` only ($1 / 23 = 4.35\%$) |

### 3.2 Class-Wise Contamination Breakdown

| Canonical Class Identifier | Clean Test Samples | Historical Train Overlap | Historical Val Overlap | Unseen Samples | Contamination Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `Potato___Late_Blight` | 23 | **0** | **0** | **23** | Disjoint / Zero Overlap |
| `Potato___healthy` | 23 | **0** | **0** | **23** | Disjoint / Zero Overlap |
| `Rice___Blast` | 23 | **0** | **0** | **23** | Disjoint / Zero Overlap |
| `Rice___healthy` | 23 | **17** | **5** | **1** | **Contaminated ($73.91\%$ in train)** |
| `Tomato___Early_Blight` | 23 | **0** | **0** | **23** | Disjoint / Zero Overlap |
| `Tomato___Late_Blight` | 23 | **0** | **0** | **23** | Disjoint / Zero Overlap |
| `Tomato___healthy` | 23 | **0** | **0** | **23** | Disjoint / Zero Overlap |
| **Total Test Dataset** | **161** | **17** | **5** | **139** | **Overall Contamination: 10.56%** |

### 3.3 Identification of Contaminated Clean Test Samples
The $17$ clean test images from `Rice___healthy` that were present in the historical training set of `task-1814` are:
- `Rice___healthy_0015.jpg` (SHA-256: `b81fc0356002...`)
- `Rice___healthy_0019.jpg` (SHA-256: `6f7e60a7ba11...`)
- `Rice___healthy_0020.jpg` (SHA-256: `6105f34a0fe5...`)
- `Rice___healthy_0021.jpg` (SHA-256: `b04ecb5d3db0...`)
- `Rice___healthy_0025.jpg` (SHA-256: `ad4c283c86ac...`)
- `Rice___healthy_0030.jpg` (SHA-256: `cecc3deb58cd...`)
- `Rice___healthy_0040.jpg` (SHA-256: `12d02f36b4a4...`)
- `Rice___healthy_0044.jpg` (SHA-256: `e23cec2c0971...`)
- `Rice___healthy_0053.jpg` (SHA-256: `c1d801d5b04f...`)
- `Rice___healthy_0054.jpg` (SHA-256: `090e2888530f...`)
- `Rice___healthy_0061.jpg` (SHA-256: `0ec125e78613...`)
- `Rice___healthy_0067.jpg` (SHA-256: `eb7111fe3f87...`)
- `Rice___healthy_0076.jpg` (SHA-256: `e5632ece4d0c...`)
- `Rice___healthy_0097.jpg` (SHA-256: `39d8815f655d...`)
- `Rice___healthy_0113.jpg` (SHA-256: `d8128ef8e690...`)
- `Rice___healthy_0115.jpg` (SHA-256: `858dd02b6aa9...`)
- `Rice___healthy_0133.jpg` (SHA-256: `59b796a7b70f...`)

The $5$ clean test images from `Rice___healthy` that were present in historical validation are:
- `Rice___healthy_0057.jpg`
- `Rice___healthy_0063.jpg`
- `Rice___healthy_0078.jpg`
- `Rice___healthy_0106.jpg`
- `Rice___healthy_0142.jpg`

The single clean test image from `Rice___healthy` strictly absent from historical train and validation is:
- `Rice___healthy_0109.jpg`

### 3.4 Scientific Finding on Evaluation Legitimacy
Because $17$ of the $23$ `Rice___healthy` test images were present in the training set of `task-1814`, **the reported $93.17\%$ test accuracy cannot legitimately be characterized as a completely held-out, out-of-sample evaluation**. 

For the $6$ classes where historical training and clean test partitions were strictly disjoint ($138$ samples: Potato Late Blight, Potato healthy, Rice Blast, Tomato Early Blight, Tomato Late Blight, Tomato healthy), the model achieved **$94.20\%$ Top-1 Accuracy** ($130 / 138$ correct). On the $23$ Rice Healthy test samples, the model achieved **$86.96\%$ Accuracy** ($20 / 23$ correct), with $2$ of the $3$ misclassified images occurring on samples that had been present in the historical training set.

---

## 4. PlantVillage Grouping Investigation & Data Leakage Boundaries

### 4.1 Upstream PlantVillage Grouping Metadata
- **Investigation:** An audit of the upstream PlantVillage repository (`spMohanty/PlantVillage-Dataset`) and associated AIcrowd/Hugging Face distributions revealed that the repository contains **`leaf_grouping/leaf-map.json`**.
- **Role of `leaf-map.json`:** PlantVillage collected multiple photographic exposures of the same physical leaf under varying angles, background placements, and lighting conditions. The `leaf-map.json` metadata explicitly maps individual image filenames to unique leaf identifiers (`leaf_id`), enabling leaf-grouped splitting (ensuring that all photographs of a single physical leaf remain on one side of a train/val/test split).

### 4.2 Pipeline Implementation and Grouping Independence
- **Ingestion Audit:** The project's automated download pipeline (`ml_models/dataset_pipeline.py`) sampled files directly from `raw/color/{pv_folder_name}` via GitHub API contents queries without downloading, parsing, or cross-referencing `leaf_grouping/leaf-map.json`.
- **Partitioning Method:** Data partitioning in `create_stratified_splits` applied standard pseudorandom shuffling (`random.shuffle()`) at the individual image file level.
- **Scientific Determination:**
  - **Identical-File Leakage:** Successfully prevented (SHA-256 hashes of all $1,050$ images in `data/clean` are unique).
  - **Leaf-Level and Plant-Level Independence:** **Unestablished.** Because grouping metadata was not incorporated, multiple photographic instances of the same physical leaf may be distributed across the training, validation, and testing partitions.
  - **Corrected Claim:** PlantVillage **does** provide leaf-grouping metadata upstream, but this project's pipeline did not utilize it. Consequently, leaf-level independence cannot be claimed.

---

## 5. Dataset Source and Licensing Audit

### 5.1 PlantVillage Dataset Licensing
- **Academic Publication:** Mohanty, S. P., Hughes, D. P., & Salathé, M. (2016). *Using deep learning for image-based plant disease detection.* Frontiers in Plant Science, 7, 1419.
- **Repository:** `https://github.com/spMohanty/PlantVillage-Dataset`
- **Licensing Findings:**
  1. The *Frontiers in Plant Science* publication is released under **Creative Commons Attribution (CC BY 4.0)**. However, this license legally applies to the research paper text, tables, and figures, not automatically to the separate multi-gigabyte raw image repository.
  2. The Hugging Face dataset card (`mohanty/PlantVillage`) specifies **Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)**.
  3. The upstream GitHub repository (`spMohanty/PlantVillage-Dataset`) does not contain a root `LICENSE` file defining standalone image usage terms.
  4. Secondary platforms and community mirrors that labeled the dataset as "CC0 Public Domain" lack authoritative backing from the original authors.
  5. **Legal Status:** Use of PlantVillage images carries terms consistent with **CC BY-SA 3.0 / CC BY 4.0** (requiring formal attribution to Mohanty et al., 2016). CC0 Public Domain status cannot be legally substantiated.

### 5.2 Rice Leaf Diseases Dataset Licensing
- **Wrapper Repository:** Jonathan Pereira (2020), *Rice-Disease-Classification*, `https://github.com/jonathanrjpereira/Rice-Disease-Classification`.
- **Repository Code License:** **GNU General Public License v3.0 (GPL-3.0)**.
- **Underlying Image Provenance:**
  1. The image archive `Rice_All.zip` (2,092 images) was incorporated into Pereira's repository from Kaggle user **Huy Minh Do** (`minhhuy2810/rice-diseases-image-dataset`).
  2. Huy Minh Do uploaded the photographs to Kaggle under standard platform terms without a formal open-source license file (such as MIT, Apache, or Creative Commons).
  3. While independent rice pathology datasets exist on Mendeley Data with DOI registrations under CC BY 4.0 (e.g. Sethy, 2020; Chaudhari, 2019), the specific images in `Rice_All.zip` originate from Huy Minh Do's Kaggle repository.
  4. **Legal Status:** Pereira's GPL-3.0 code license applies only to the wrapper repository code, not to the underlying third-party photographs. The exact underlying license for the Rice leaf images remains **unverified**. The images are suitable for academic benchmarking with attribution, but commercial rights remain uncertified.

---

## 6. Model Evaluation Audit (Reconciled Metrics)

### 6.1 Benchmark Evaluation on Clean Isolated Test Set ($161$ Images)
Evaluated on `data/processed/test` ($23$ images per class, bicubic input resize to $224 \times 224$):

| Canonical Class Identifier | Precision | Recall | F1-Score | Support | Benchmark Observations |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `Potato___Late_Blight` | **1.0000** | **1.0000** | **1.0000** | 23 | Complete recall on dark necrotic lesions |
| `Potato___healthy` | **1.0000** | **1.0000** | **1.0000** | 23 | Complete precision and recall on healthy potato foliage |
| `Rice___Blast` | 0.8571 | 0.7826 | 0.8182 | 23 | Spindle lesions identified; 5 misclassified as healthy |
| `Rice___healthy` | 0.8000 | 0.8696 | 0.8333 | 23 | Elongated leaf blades; 3 misclassified as blast (contaminated split) |
| `Tomato___Early_Blight` | **1.0000** | 0.8696 | 0.9302 | 23 | Concentric rings identified; 2 as late blight, 1 as healthy |
| `Tomato___Late_Blight` | 0.9200 | **1.0000** | 0.9583 | 23 | Complete recall on severe water-soaked lesions |
| `Tomato___healthy` | 0.9583 | **1.0000** | 0.9787 | 23 | Clean separation on healthy tomato foliage |
| **Macro Average** | **0.9336** | **0.9317** | **0.9313** | **161** | In-distribution test partition metric |
| **Weighted Average** | **0.9336** | **0.9317** | **0.9313** | **161** | In-distribution test partition metric |

- **Top-1 Test Accuracy:** **$93.17\%$** ($150 / 161$)
- **Top-2 Test Accuracy:** **$99.38\%$** ($160 / 161$)
- **Strictly Held-Out Non-Rice-Healthy Classes ($138$ Samples):** Top-1 Accuracy: **$94.20\%$** ($130 / 138$)
- **Contaminated Rice Healthy Class ($23$ Samples):** Top-1 Accuracy: **$86.96\%$** ($20 / 23$)
- **Historical 183-Sample Test Result (Reference):** Top-1 Accuracy: **$93.44\%$** ($171 / 183$), Top-2: **$99.45\%$**, Macro F1: **$0.9383$** (evaluated on historical staging containing $22$ duplicate Rice Healthy samples).

### 6.2 Confusion Matrix ($7 \times 7$, Clean 161 Samples)

| Ground Truth \ Predicted | PLB | PH | RB | RH | TEB | TLB | TH | Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Potato___Late_Blight`** | **23** | 0 | 0 | 0 | 0 | 0 | 0 | **100.0%** |
| **`Potato___healthy`** | 0 | **23** | 0 | 0 | 0 | 0 | 0 | **100.0%** |
| **`Rice___Blast`** | 0 | 0 | **18** | 5 | 0 | 0 | 0 | **78.3%** |
| **`Rice___healthy`** | 0 | 0 | 3 | **20** | 0 | 0 | 0 | **87.0%** |
| **`Tomato___Early_Blight`** | 0 | 0 | 0 | 0 | **20** | 2 | 1 | **87.0%** |
| **`Tomato___Late_Blight`** | 0 | 0 | 0 | 0 | 0 | **23** | 0 | **100.0%** |
| **`Tomato___healthy`** | 0 | 0 | 0 | 0 | 0 | 0 | **23** | **100.0%** |
| **Precision** | **100%** | **100%** | **85.7%** | **80.0%** | **100%** | **92.0%** | **95.8%** | — |

---

## 7. Individual Prediction Distributions: Misclassified Rice Blast Samples

Below are the exact softmax prediction probabilities for the **$5$ ground-truth `Rice___Blast` test samples** misclassified as `Rice___healthy`:

| Test Image Filename | Top-1 Prediction | Top-1 Probability | Top-2 Prediction | Top-2 Probability | $P(\text{Rice Blast})$ | Top-3 Prediction ($P$) | Correct in Top-2? |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- | :---: |
| `Rice___Blast_0027.jpg` | `Rice___healthy` | $72.35\%$ | `Rice___Blast` | $25.59\%$ | **$25.59\%$** | `Potato___healthy` ($0.51\%$) | **Yes** |
| `Rice___Blast_0039.jpg` | `Rice___healthy` | $63.72\%$ | `Rice___Blast` | $35.17\%$ | **$35.17\%$** | `Potato___healthy` ($0.38\%$) | **Yes** |
| `Rice___Blast_0082.jpg` | `Rice___healthy` | $51.76\%$ | `Rice___Blast` | $46.61\%$ | **$46.61\%$** | `Potato___healthy` ($0.74\%$) | **Yes** |
| `Rice___Blast_0087.jpg` | `Rice___healthy` | $72.19\%$ | `Rice___Blast` | $25.95\%$ | **$25.95\%$** | `Potato___healthy` ($0.58\%$) | **Yes** |
| `Rice___Blast_0088.jpg` | `Rice___healthy` | $84.70\%$ | `Rice___Blast` | $14.52\%$ | **$14.52\%$** | `Potato___healthy` ($0.27\%$) | **Yes** |

### Clarification on Second-Choice Confidences
- **Previous Claim:** *"In all 5 cases, Rice Blast was the immediate second choice with $>30\%$ confidence."*
- **Audit Correction:** While `Rice___Blast` was the immediate second prediction (`Top-2`) in all $5$ cases ($100\%$), its probability exceeded $30\%$ in **$2$ of the $5$ cases** ($35.17\%$ and $46.61\%$). In the other $3$ cases, probabilities were $25.59\%$, $25.95\%$, and $14.52\%$, yielding an average second-choice probability of **$29.57\%$**.
- **Morphological Analysis:** These misclassified samples feature early nascent lesions where downsampling to $224 \times 224$ leaves a low ratio of lesion pixels relative to the predominantly green leaf blade.

---

## 8. ONNX Export Verification & Latency Benchmarks

### 8.1 Numerical Parity Audit
Evaluated against all $161$ test images:
- **Total Samples Compared:** $161$
- **Top-1 Prediction Agreement:** **$161 / 161$ ($100.00\%$)**
- **Maximum Absolute Probability Difference:** **$1.43 \times 10^{-6}$** (below $1.0 \times 10^{-3}$ threshold)
- **Mean Absolute Probability Difference:** **$4.31 \times 10^{-8}$**
- **Parity Status:** Numerically Consistent

### 8.2 Preprocessing Alignment
- Bicubic resize to $(224 \times 224)$ with ImageNet channel normalization: mean $[0.485, 0.456, 0.406]$, standard deviation $[0.229, 0.224, 0.225]$.
- Identical alphabetical class ordering in both PyTorch and ONNX runtimes:
  `['Potato___Late_Blight', 'Potato___healthy', 'Rice___Blast', 'Rice___healthy', 'Tomato___Early_Blight', 'Tomato___Late_Blight', 'Tomato___healthy']`.

### 8.3 Latency Benchmarking (CPU Forward Pass, Batch Size = 1)
- **PyTorch CPU Engine:** Mean: **$38.88\text{ ms}$**, Median: **$35.20\text{ ms}$**, P95: **$50.52\text{ ms}$**
- **ONNX Runtime CPU Engine:** Mean: **$11.35\text{ ms}$**, Median: **$9.56\text{ ms}$**, P95: **$14.42\text{ ms}$**
- **Inference Speedup:** **$3.42\times$ reduction** in forward latency on CPU execution.

---

## 9. System Regression Testing Verification

All unit, integration, and endpoint tests pass with zero failures:
- **Backend Test Suite ([`tests/`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/tests/)):** **$115 / 115$ tests passed** ($100\%$) in $41.64\text{ s}$.
- **Frontend Vitest Suite ([`frontend/`](file:///c:/Users/admin/OneDrive/Desktop/Intelligent-Crop-Diagnosis/frontend/)):** **$13 / 13$ tests passed** ($100\%$) in $9.08\text{ s}$.
- **Total Suite Passing:** **$128 / 128$ tests passing** ($100\%$).

---

## 10. Conclusion & Scientific Boundaries

Phase 7 implementation, training history, and evaluation metrics have been fully audited and reconciled:
1. Historical training was performed on the $1,129$-sample staging dataset.
2. Contamination between historical training and the clean test set occurred exclusively in the `Rice___healthy` class ($17 / 23$ test samples seen during training). Consequently, the overall $93.17\%$ test accuracy cannot be described as a completely held-out out-of-sample evaluation.
3. For the $6$ uncontaminated classes ($138$ samples), out-of-sample test accuracy is **$94.20\%$**.
4. PlantVillage grouping metadata (`leaf_grouping/leaf-map.json`) exists upstream but was not utilized, meaning leaf-level independence remains unestablished.
5. Licensing terms have been clarified: PlantVillage is associated with CC BY-SA 3.0 / CC BY 4.0 (CC0 unbacked), while underlying Rice images from Huy Minh Do remain unverified under Kaggle upload terms.
6. Phase 8 will not proceed until directed.
