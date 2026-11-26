import os
import tempfile
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from PIL import Image

from ml_models.train import (
    get_data_transforms,
    load_datasets,
    train_one_epoch,
    evaluate,
)
from backend.app.vision.model import build_efficientnet_b0


def create_mock_dataset_dir(base_dir: str, classes=("Class_A", "Class_B"), samples_per_class=4):
    """Creates a temporary image folder structure with synthetic samples for testing pipeline logic."""
    for c in classes:
        class_dir = os.path.join(base_dir, c)
        os.makedirs(class_dir, exist_ok=True)
        for i in range(samples_per_class):
            img = Image.new("RGB", (32, 32), color=(i * 30, 100, 50))
            img.save(os.path.join(class_dir, f"sample_{i}.jpg"))


def test_data_transforms_specifications():
    """Verifies that transforms produce normalized tensors with 3 channels."""
    tforms = get_data_transforms((224, 224))
    assert "train" in tforms
    assert "val" in tforms
    assert "test" in tforms

    dummy_img = Image.new("RGB", (100, 100), color=(50, 150, 50))
    tensor = tforms["train"](dummy_img)
    assert tensor.shape == (3, 224, 224)
    assert tensor.dtype == torch.float32


def test_load_datasets_and_micro_training_step():
    """Verifies dataset loading, partitioning, and executing one micro-training step."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        classes = ["Class_Early_Blight", "Class_Healthy"]
        create_mock_dataset_dir(tmp_dir, classes=classes, samples_per_class=6)

        train_ds, val_ds, test_ds, loaded_classes, class_to_idx = load_datasets(
            data_dir=tmp_dir, val_split=0.25, test_split=0.25, random_seed=42
        )

        assert len(loaded_classes) == 2
        assert set(loaded_classes) == set(classes)
        assert len(train_ds) > 0
        assert len(val_ds) > 0
        assert len(test_ds) > 0

        # Run 1 micro training step
        device = torch.device("cpu")
        model = build_efficientnet_b0(num_classes=len(classes), pretrained_backbone=False)
        model.to(device)

        train_loader = DataLoader(train_ds, batch_size=2, shuffle=True)
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

        loss, acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        assert loss > 0.0
        assert 0.0 <= acc <= 1.0

        val_loader = DataLoader(val_ds, batch_size=2, shuffle=False)
        val_loss, val_acc, preds, targets = evaluate(model, val_loader, criterion, device)
        assert val_loss > 0.0
        assert 0.0 <= val_acc <= 1.0
        assert len(preds) == len(val_ds)
