"""EfficientNet-B0 Plant Disease Detection Training Pipeline.

IEEE Implementation Specification:
- CNN Backbone: EfficientNet-B0 (PyTorch, Torchvision)
- Transfer learning with ImageNet pre-trained feature extractor
- Evaluation metrics: Accuracy, Precision, Recall, F1-score, Confusion Matrix
- Checkpointing: Saves best validation weights and class mappings
"""

import os
import sys
import argparse
import time
import shutil
import json
import random
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms, datasets
from sklearn.metrics import classification_report, confusion_matrix

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.vision.model import build_efficientnet_b0, DEFAULT_SUPPORTED_CLASSES
from backend.app.vision.preprocessing import EFFICIENTNET_INPUT_SIZE, IMAGENET_MEAN, IMAGENET_STD


def set_seed(seed: int = 42):
    """Sets random seeds for full experiment reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_data_transforms(input_size: Tuple[int, int] = EFFICIENTNET_INPUT_SIZE) -> Dict[str, transforms.Compose]:
    """Returns training and validation data augmentation pipelines."""
    train_transform = transforms.Compose([
        transforms.Resize(input_size, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(degrees=20),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    val_test_transform = transforms.Compose([
        transforms.Resize(input_size, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    return {"train": train_transform, "val": val_test_transform, "test": val_test_transform}


def load_datasets(
    data_dir: str,
    val_split: float = 0.15,
    test_split: float = 0.15,
    random_seed: int = 42
) -> Tuple[Dataset, Dataset, Dataset, List[str], Dict[str, int]]:
    """Loads and splits agricultural image dataset into train, val, and test subsets.

    Supports two directory structures:
    Structure A (Pre-split):
        data_dir/
            train/<class_name>/*.jpg
            val/<class_name>/*.jpg
            test/<class_name>/*.jpg

    Structure B (Flat class folders):
        data_dir/
            <class_name>/*.jpg
    """
    if not os.path.exists(data_dir):
        raise FileNotFoundError(
            f"Dataset directory '{data_dir}' does not exist. "
            "Please download the PlantVillage dataset subset and organize into class folders."
        )

    tforms = get_data_transforms()
    train_subdir = os.path.join(data_dir, "train")

    if os.path.exists(train_subdir) and os.path.isdir(train_subdir):
        # Structure A: Pre-split
        train_dataset = datasets.ImageFolder(train_subdir, transform=tforms["train"])
        val_subdir = os.path.join(data_dir, "val")
        test_subdir = os.path.join(data_dir, "test")

        if os.path.exists(val_subdir):
            val_dataset = datasets.ImageFolder(val_subdir, transform=tforms["val"])
        else:
            val_dataset = None

        if os.path.exists(test_subdir):
            test_dataset = datasets.ImageFolder(test_subdir, transform=tforms["test"])
        else:
            test_dataset = None

        classes = train_dataset.classes
        class_to_idx = train_dataset.class_to_idx
        return train_dataset, val_dataset, test_dataset, classes, class_to_idx

    else:
        # Structure B: Flat class directories -> partition dynamically
        full_dataset = datasets.ImageFolder(data_dir)
        classes = full_dataset.classes
        class_to_idx = full_dataset.class_to_idx
        total_samples = len(full_dataset)

        if total_samples == 0:
            raise ValueError(f"Dataset directory '{data_dir}' contains 0 images.")

        test_count = int(total_samples * test_split)
        val_count = int(total_samples * val_split)
        train_count = total_samples - val_count - test_count

        generator = torch.Generator().manual_seed(random_seed)
        train_subset, val_subset, test_subset = random_split(
            full_dataset, [train_count, val_count, test_count], generator=generator
        )

        # Apply specific transforms
        class TransformedSubset(Dataset):
            def __init__(self, subset, transform):
                self.subset = subset
                self.transform = transform

            def __len__(self):
                return len(self.subset)

            def __getitem__(self, idx):
                x, y = self.subset[idx]
                if self.transform:
                    x = self.transform(x)
                return x, y

        train_dataset = TransformedSubset(train_subset, tforms["train"])
        val_dataset = TransformedSubset(val_subset, tforms["val"])
        test_dataset = TransformedSubset(test_subset, tforms["test"])

        return train_dataset, val_dataset, test_dataset, classes, class_to_idx


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> Tuple[float, float]:
    """Executes a single training epoch."""
    model.train()
    running_loss = 0.0
    correct_count = 0
    total_count = 0

    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct_count += torch.sum(preds == labels.data).item()
        total_count += inputs.size(0)

    epoch_loss = running_loss / max(total_count, 1)
    epoch_acc = correct_count / max(total_count, 1)
    return epoch_loss, epoch_acc


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """Evaluates model on validation or test dataset."""
    model.eval()
    running_loss = 0.0
    correct_count = 0
    total_count = 0

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct_count += torch.sum(preds == labels.data).item()
            total_count += inputs.size(0)

            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())

    total_loss = running_loss / max(total_count, 1)
    total_acc = correct_count / max(total_count, 1)
    return total_loss, total_acc, np.array(all_preds), np.array(all_targets)


def run_training_pipeline(
    data_dir: str,
    output_dir: str = "ml_models/weights",
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-4,
    device_str: Optional[str] = None,
    patience: int = 7,
    seed: int = 42
) -> Dict[str, Any]:
    """Orchestrates complete dataset loading, model training, validation, and checkpointing."""
    os.makedirs(output_dir, exist_ok=True)
    set_seed(seed)

    if device_str:
        device = torch.device(device_str)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Executing training pipeline on compute device: {device} (Random Seed: {seed})")

    # 1. Load datasets
    train_ds, val_ds, test_ds, classes, class_to_idx = load_datasets(data_dir, random_seed=seed)
    print(f"Loaded {len(classes)} target classes: {classes}")
    print(f"Dataset split sizes: Train={len(train_ds)}, Val={len(val_ds) if val_ds else 0}, Test={len(test_ds) if test_ds else 0}")

    # Compute class weights for loss balancing
    class_counts = [0] * len(classes)
    for i in range(len(train_ds)):
        _, target = train_ds[i]
        class_counts[target] += 1
    total_samples = len(train_ds)
    weights = [total_samples / (len(classes) * max(c, 1)) for c in class_counts]
    class_weights_tensor = torch.tensor(weights, dtype=torch.float32).to(device)
    print(f"Computed inverse-frequency class weights: {[round(w, 3) for w in weights]}")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0) if val_ds else None

    # 2. Build model architecture
    model = build_efficientnet_b0(num_classes=len(classes), pretrained_backbone=True)
    model.to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    best_val_loss = float("inf")
    patience_counter = 0
    best_checkpoint_path = os.path.join(output_dir, "efficientnet_b0_best.pth")

    # Backup existing checkpoint if present
    if os.path.exists(best_checkpoint_path):
        backup_path = best_checkpoint_path + ".bak"
        shutil.copy2(best_checkpoint_path, backup_path)
        print(f"Existing model checkpoint backed up to: {backup_path}")

    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "lr": []}

    print("\nStarting Training Execution:")
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["lr"].append(current_lr)

        if val_loader:
            val_loss, val_acc, _, _ = evaluate(model, val_loader, criterion, device)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)
            epoch_duration = time.time() - epoch_start
            print(
                f"Epoch [{epoch:02d}/{epochs:02d}] ({epoch_duration:.1f}s) - "
                f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}"
            )

            # Checkpoint best model on validation accuracy and loss
            if val_acc > best_val_acc or (val_acc == best_val_acc and val_loss < best_val_loss):
                best_val_acc = val_acc
                best_val_loss = val_loss
                patience_counter = 0
                torch.save({
                    "epoch": epoch,
                    "state_dict": model.state_dict(),
                    "val_loss": val_loss,
                    "val_acc": val_acc,
                    "classes": classes,
                    "class_to_idx": class_to_idx,
                    "architecture": "efficientnet_b0",
                    "hyperparameters": {
                        "epochs": epochs,
                        "batch_size": batch_size,
                        "learning_rate": lr,
                        "seed": seed,
                        "class_weights": weights
                    },
                    "timestamp": time.time()
                }, best_checkpoint_path)
                print(f" -> Checkpoint saved to: {best_checkpoint_path} (Best Val Acc: {val_acc:.4f})")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"\nEarly stopping triggered after {patience} epochs without validation improvement.")
                    break
        else:
            epoch_duration = time.time() - epoch_start
            print(f"Epoch [{epoch:02d}/{epochs:02d}] ({epoch_duration:.1f}s) - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")

    total_training_time = time.time() - start_time
    print(f"\nTraining completed in {total_training_time:.1f}s. Best Validation Accuracy: {best_val_acc:.4f}")

    # Save training history and configuration
    history_path = os.path.join(output_dir, "training_history.json")
    with open(history_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "configuration": {
                "architecture": "efficientnet_b0",
                "pretrained": True,
                "epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": lr,
                "seed": seed,
                "classes": classes,
                "class_weights": weights,
                "total_training_time_seconds": round(total_training_time, 2)
            },
            "best_validation_accuracy": best_val_acc,
            "best_validation_loss": best_val_loss,
            "history": history
        }, f, indent=2)
    print(f"Training history saved to: {history_path}")

    # 3. Final evaluation on test dataset
    if test_ds:
        test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)
        # Load best weights
        if os.path.exists(best_checkpoint_path):
            ckpt = torch.load(best_checkpoint_path, map_location=device)
            model.load_state_dict(ckpt["state_dict"])

        test_loss, test_acc, preds, targets = evaluate(model, test_loader, criterion, device)
        print(f"\nFinal Test Set Evaluation: Loss={test_loss:.4f}, Accuracy={test_acc:.4f}")

        # Classification report & confusion matrix
        report = classification_report(targets, preds, target_names=classes, output_dict=True)
        conf_mat = confusion_matrix(targets, preds)
        print("\nClassification Report:\n", classification_report(targets, preds, target_names=classes))
        print("Confusion Matrix:\n", conf_mat)
    else:
        report, conf_mat = None, None

    return {
        "best_val_acc": best_val_acc,
        "best_checkpoint_path": best_checkpoint_path,
        "classes": classes,
        "class_to_idx": class_to_idx,
        "history": history,
        "test_report": report
    }


def main():
    parser = argparse.ArgumentParser(description="Train EfficientNet-B0 Plant Disease Classifier")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to plant disease dataset directory")
    parser.add_argument("--output_dir", type=str, default="ml_models/weights", help="Directory to save model checkpoints")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--device", type=str, default=None, help="Device: 'cuda' or 'cpu'")
    args = parser.parse_args()

    run_training_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device_str=args.device
    )


if __name__ == "__main__":
    main()
