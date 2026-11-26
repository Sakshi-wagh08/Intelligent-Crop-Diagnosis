"""Dataset Preparation Pipeline for Intelligent Crop Diagnosis.

Sources genuine plant pathology images from verified academic repositories:
1. PlantVillage (David P. Hughes & Marcel Salathe, 2015, arXiv:1511.08060; Mohanty, Hughes, & Salathe, 2016, Frontiers in Plant Science)
   - Tomato Early Blight (Alternaria solani)
   - Tomato Late Blight (Phytophthora infestans)
   - Tomato Healthy
   - Potato Late Blight (Phytophthora infestans)
   - Potato Healthy
   - License: Mixed/Uncertain (Frontiers paper CC BY 4.0; Hugging Face CC BY-SA 3.0; GitHub repo lacks root license. CC0 non-authoritative)

2. Rice Leaf Diseases Dataset (Huy Minh Do, Kaggle / Jonathan Pereira wrapper)
   - Rice Blast (Magnaporthe oryzae)
   - Rice Healthy
   - License: Wrapper repository GPL-3.0; underlying photographs unverified Kaggle upload

Performs rigorous data hygiene:
- Corrupt image detection and rejection
- Format normalization (RGB JPEG)
- Cryptographic SHA-256 deduplication
- Zero-leakage stratified train / val / test splitting (70% / 15% / 15%)
- Manifest generation and distribution reporting
"""

import os
import sys
import json
import time
import shutil
import hashlib
import zipfile
import urllib.request
from typing import Dict, List, Tuple, Any, Optional
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.vision.model import DEFAULT_SUPPORTED_CLASSES


CANONICAL_CLASSES = DEFAULT_SUPPORTED_CLASSES

# Mapping from PlantVillage folder names to Canonical Class Names
PLANTVILLAGE_CLASS_MAP = {
    "Tomato___Early_blight": "Tomato___Early_Blight",
    "Tomato___Late_blight": "Tomato___Late_Blight",
    "Tomato___healthy": "Tomato___healthy",
    "Potato___Late_blight": "Potato___Late_Blight",
    "Potato___healthy": "Potato___healthy",
}

RICE_CLASS_MAP = {
    "LeafBlast": "Rice___Blast",
    "Healthy": "Rice___healthy",
}

DATASET_METADATA = {
    "PlantVillage": {
        "citation": "Hughes, D. P., & Salathe, M. (2015). arXiv:1511.08060; Mohanty, S. P., Hughes, D. P., & Salathe, M. (2016). Frontiers in Plant Science, 7, 1419.",
        "repository": "https://github.com/spMohanty/PlantVillage-Dataset",
        "license": "Uncertain / Mixed: Frontiers publication CC BY 4.0; Hugging Face card CC BY-SA 3.0; GitHub repo lacks root license. CC0 non-authoritative.",
        "capture_conditions": "Laboratory-controlled single-leaf photography against neutral/grey background",
        "known_limitations": "Lack of in-field canopy clutter, variable ambient daylight, and complex foliar backgrounds. Leaf grouping metadata (leaf_grouping/leaf-map.json) not ingested by pipeline."
    },
    "Rice_Diseases": {
        "citation": "Pereira, J. (2020). Rice Disease Classification Using Transfer Learning. GitHub: jonathanrjpereira/Rice-Disease-Classification (Original by Huy Minh Do, Kaggle: minhhuy2810/rice-diseases-image-dataset).",
        "repository": "https://github.com/jonathanrjpereira/Rice-Disease-Classification",
        "license": "Wrapper repository: GPL-3.0; Underlying images: Unverified Kaggle community upload.",
        "capture_conditions": "Isolated leaf blade on white paper background",
        "known_limitations": "Laboratory white background without natural field foliage or soil context. Underlying commercial/open-source image license unverified."
    }
}


def compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash of file content for exact duplicate detection."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_plantvillage_class(
    pv_folder_name: str,
    canonical_name: str,
    target_dir: str,
    max_images: int = 150
) -> int:
    """Downloads images for a specific PlantVillage class from GitHub contents."""
    os.makedirs(target_dir, exist_ok=True)
    api_url = f"https://api.github.com/repos/spMohanty/PlantVillage-Dataset/contents/raw/color/{pv_folder_name}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "PlantDiseaseResearch/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            items = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error querying GitHub API for {pv_folder_name}: {e}")
        return 0

    downloaded = 0
    # Deterministic selection
    items = sorted(items, key=lambda x: x["name"])[:max_images]

    for item in items:
        download_url = item["download_url"]
        filename = item["name"].replace(" ", "_")
        dest_path = os.path.join(target_dir, filename)

        if os.path.exists(dest_path):
            downloaded += 1
            continue

        try:
            req_dl = urllib.request.Request(download_url, headers={"User-Agent": "PlantDiseaseResearch/1.0"})
            with urllib.request.urlopen(req_dl, timeout=15) as dl_resp:
                img_data = dl_resp.read()
                with open(dest_path, "wb") as out_f:
                    out_f.write(img_data)
            downloaded += 1
            if downloaded % 25 == 0:
                print(f"  [{canonical_name}] Downloaded {downloaded}/{len(items)} images...")
        except Exception as err:
            print(f"  Failed to download {filename}: {err}")

    print(f"Completed {canonical_name}: {downloaded} images saved to {target_dir}")
    return downloaded


def download_and_extract_rice(
    target_raw_dir: str,
    max_images_per_class: int = 150
) -> Dict[str, int]:
    """Downloads Rice_All.zip and extracts Leaf-Blast and Healthy images."""
    zip_url = "https://raw.githubusercontent.com/jonathanrjpereira/Rice-Disease-Classification/master/Rice_All.zip"
    temp_zip_path = os.path.join(target_raw_dir, "temp_rice.zip")
    results = {}

    print("\nDownloading Rice Disease Archive (Rice_All.zip)...")
    req = urllib.request.Request(zip_url, headers={"User-Agent": "PlantDiseaseResearch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(temp_zip_path, "wb") as f:
            while chunk := resp.read(1024 * 512):
                f.write(chunk)
    print("Rice_All.zip download finished. Extracting relevant classes...")

    with zipfile.ZipFile(temp_zip_path, "r") as zf:
        namelist = zf.namelist()

        for src_folder, canon_class in RICE_CLASS_MAP.items():
            dest_dir = os.path.join(target_raw_dir, canon_class)
            os.makedirs(dest_dir, exist_ok=True)

            matching_files = [n for n in namelist if src_folder in n and n.lower().endswith((".jpg", ".jpeg", ".png"))]
            matching_files = sorted(matching_files)[:max_images_per_class]

            extracted = 0
            for member in matching_files:
                base_name = os.path.basename(member)
                dest_file = os.path.join(dest_dir, f"rice_{base_name}")
                with zf.open(member) as src_f, open(dest_file, "wb") as dst_f:
                    dst_f.write(src_f.read())
                extracted += 1

            results[canon_class] = extracted
            print(f"Extracted {extracted} images for {canon_class} into {dest_dir}")

    # Remove temporary zip
    if os.path.exists(temp_zip_path):
        os.remove(temp_zip_path)

    return results


def validate_and_clean_dataset(
    raw_dir: str,
    clean_dir: str
) -> Dict[str, Any]:
    """Validates image integrity, eliminates corrupt files and exact duplicates, converts to RGB."""
    os.makedirs(clean_dir, exist_ok=True)
    seen_hashes: Dict[str, str] = {}
    stats = {
        "total_inspected": 0,
        "valid_images": 0,
        "corrupt_images": 0,
        "duplicates_removed": 0,
        "class_counts": {}
    }

    print("\nValidating and deduplicating dataset images...")

    for canon_class in CANONICAL_CLASSES:
        src_class_dir = os.path.join(raw_dir, canon_class)
        dst_class_dir = os.path.join(clean_dir, canon_class)
        os.makedirs(dst_class_dir, exist_ok=True)

        if not os.path.exists(src_class_dir):
            print(f"Warning: Class directory {src_class_dir} does not exist.")
            continue

        class_valid = 0
        for fname in sorted(os.listdir(src_class_dir)):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue

            stats["total_inspected"] += 1
            src_path = os.path.join(src_class_dir, fname)

            # 1. Check integrity with PIL
            try:
                with Image.open(src_path) as img:
                    img.verify()
                # Reopen to convert & inspect properties
                with Image.open(src_path) as img:
                    img = img.convert("RGB")
                    w, h = img.size
                    if w < 64 or h < 64:
                        stats["corrupt_images"] += 1
                        continue

                    # 2. Duplicate detection via SHA-256
                    file_hash = compute_file_hash(src_path)
                    if file_hash in seen_hashes:
                        stats["duplicates_removed"] += 1
                        continue

                    seen_hashes[file_hash] = src_path

                    # 3. Save standardized clean image
                    dst_path = os.path.join(dst_class_dir, f"{canon_class}_{class_valid:04d}.jpg")
                    img.save(dst_path, format="JPEG", quality=95)
                    class_valid += 1
                    stats["valid_images"] += 1

            except Exception as e:
                stats["corrupt_images"] += 1
                print(f"Corrupt image rejected: {src_path} ({e})")

        stats["class_counts"][canon_class] = class_valid
        print(f"Class '{canon_class}': {class_valid} clean, validated images.")

    return stats


def create_stratified_splits(
    clean_dir: str,
    output_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42
) -> Dict[str, Dict[str, int]]:
    """Creates isolated, zero-leakage train, val, and test splits."""
    import random
    random.seed(random_seed)

    split_stats = {"train": {}, "val": {}, "test": {}}

    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(output_dir, split), exist_ok=True)

    print(f"\nPartitioning dataset into Train ({train_ratio*100:.0f}%), Val ({val_ratio*100:.0f}%), Test ({test_ratio*100:.0f}%)...")

    for canon_class in CANONICAL_CLASSES:
        class_src_dir = os.path.join(clean_dir, canon_class)
        if not os.path.exists(class_src_dir):
            continue

        images = sorted(os.listdir(class_src_dir))
        random.shuffle(images)

        n_total = len(images)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        n_test = n_total - n_train - n_val

        splits = {
            "train": images[:n_train],
            "val": images[n_train:n_train + n_val],
            "test": images[n_train + n_val:]
        }

        for split_name, split_files in splits.items():
            dest_split_dir = os.path.join(output_dir, split_name, canon_class)
            os.makedirs(dest_split_dir, exist_ok=True)
            for f in split_files:
                shutil.copy2(os.path.join(class_src_dir, f), os.path.join(dest_split_dir, f))
            split_stats[split_name][canon_class] = len(split_files)

        print(f"  {canon_class:22s} -> Train: {n_train:3d}, Val: {n_val:3d}, Test: {n_test:3d} (Total: {n_total})")

    return split_stats


def run_full_pipeline(
    data_root: str = "data",
    max_images_per_class: int = 150
) -> Dict[str, Any]:
    """Runs complete dataset acquisition, cleaning, deduplication, and splitting pipeline."""
    raw_dir = os.path.join(data_root, "raw")
    clean_dir = os.path.join(data_root, "clean")
    processed_dir = os.path.join(data_root, "processed")

    os.makedirs(raw_dir, exist_ok=True)

    print("==================================================================")
    print("PHASE 7: PLANT DISEASE DATASET PREPARATION PIPELINE")
    print("==================================================================")

    # 1. PlantVillage Downloads
    print("\nStep 1: Downloading PlantVillage image subsets...")
    for pv_folder, canon_class in PLANTVILLAGE_CLASS_MAP.items():
        target_dir = os.path.join(raw_dir, canon_class)
        download_plantvillage_class(pv_folder, canon_class, target_dir, max_images=max_images_per_class)

    # 2. Rice Dataset Download & Extraction
    print("\nStep 2: Downloading & Extracting Rice Disease subsets...")
    download_and_extract_rice(raw_dir, max_images_per_class=max_images_per_class)

    # 3. Validation, Deduplication, Standardization
    print("\nStep 3: Validating images, verifying hashes, and standardizing format...")
    clean_stats = validate_and_clean_dataset(raw_dir, clean_dir)

    # 4. Stratified Split
    print("\nStep 4: Creating isolated stratified splits...")
    split_stats = create_stratified_splits(clean_dir, processed_dir, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)

    # 5. Manifest & Report
    manifest = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "canonical_classes": CANONICAL_CLASSES,
        "dataset_sources": DATASET_METADATA,
        "clean_stats": clean_stats,
        "split_stats": split_stats,
        "data_directories": {
            "raw": os.path.abspath(raw_dir),
            "clean": os.path.abspath(clean_dir),
            "processed": os.path.abspath(processed_dir),
        }
    }

    manifest_path = os.path.join(data_root, "dataset_manifest.json")
    with open(manifest_path, "w") as mf:
        json.dump(manifest, mf, indent=2)

    print(f"\nDataset preparation complete! Manifest written to: {manifest_path}")
    return manifest


if __name__ == "__main__":
    run_full_pipeline()
