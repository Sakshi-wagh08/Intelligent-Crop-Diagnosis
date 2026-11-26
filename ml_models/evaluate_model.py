"""Independent Model Evaluation & Validation Engine for Crop Disease Diagnosis.

Evaluates trained EfficientNet-B0 PyTorch checkpoints and ONNX Runtime models
on an isolated test dataset.

Calculates:
- Top-1 and Top-2 Accuracy
- Per-class Precision, Recall, F1-Score, and Support
- Macro and Weighted F1-Scores
- Confusion Matrix
- PyTorch vs ONNX Runtime Numerical Consistency & Parity
- Inference Latency Benchmarking (Mean, Median, P95, P99 in milliseconds)
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.vision.model import load_model_checkpoint, DEFAULT_SUPPORTED_CLASSES
from backend.app.vision.preprocessing import EFFICIENTNET_INPUT_SIZE, IMAGENET_MEAN, IMAGENET_STD
from backend.app.vision.onnx_engine import ONNXDiseaseClassifier


def get_test_transform():
    return transforms.Compose([
        transforms.Resize(EFFICIENTNET_INPUT_SIZE, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def evaluate_pytorch_model(
    checkpoint_path: str,
    test_dir: str,
    device_str: Optional[str] = None
) -> Dict[str, Any]:
    """Runs complete evaluation of PyTorch model on test dataset."""
    if device_str:
        device = torch.device(device_str)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"\n[PyTorch Evaluation] Loading checkpoint: {checkpoint_path} on {device}")
    model, classes, class_to_idx = load_model_checkpoint(checkpoint_path, device=device)
    model.eval()

    test_transform = get_test_transform()
    test_dataset = datasets.ImageFolder(test_dir, transform=test_transform)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)

    all_preds = []
    all_top2_preds = []
    all_targets = []
    all_probs = []
    latencies_ms = []

    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs = inputs.to(device)
            target_idx = targets.item()

            t0 = time.perf_counter()
            logits = model(inputs)
            probs = F.softmax(logits, dim=1).squeeze(0)
            latency = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(latency)

            top2 = torch.topk(probs, k=min(2, len(classes)))[1].cpu().numpy()
            pred_idx = top2[0]

            all_preds.append(pred_idx)
            all_top2_preds.append(top2)
            all_targets.append(target_idx)
            all_probs.append(probs.cpu().numpy().tolist())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    # Metrics
    accuracy = float(np.mean(all_preds == all_targets))
    top2_hits = sum(t in top2 for t, top2 in zip(all_targets, all_top2_preds))
    top2_accuracy = float(top2_hits / len(all_targets))

    target_names = [test_dataset.classes[i] for i in range(len(test_dataset.classes))]
    clf_report = classification_report(all_targets, all_preds, target_names=target_names, output_dict=True, zero_division=0)
    conf_mat = confusion_matrix(all_targets, all_preds).tolist()

    latency_stats = {
        "mean_ms": float(np.mean(latencies_ms)),
        "median_ms": float(np.median(latencies_ms)),
        "min_ms": float(np.min(latencies_ms)),
        "max_ms": float(np.max(latencies_ms)),
        "p95_ms": float(np.percentile(latencies_ms, 95)),
        "p99_ms": float(np.percentile(latencies_ms, 99)),
    }

    return {
        "engine": "PyTorch",
        "device": str(device),
        "total_test_samples": len(test_dataset),
        "classes": target_names,
        "accuracy": accuracy,
        "top2_accuracy": top2_accuracy,
        "macro_f1": clf_report["macro avg"]["f1-score"],
        "weighted_f1": clf_report["weighted avg"]["f1-score"],
        "classification_report": clf_report,
        "confusion_matrix": conf_mat,
        "latency_stats": latency_stats,
        "probabilities": all_probs,
        "predictions": all_preds.tolist(),
        "targets": all_targets.tolist()
    }


def evaluate_onnx_model(
    onnx_path: str,
    test_dir: str,
    classes: List[str]
) -> Dict[str, Any]:
    """Runs evaluation of exported ONNX Runtime model on test dataset."""
    print(f"\n[ONNX Runtime Evaluation] Loading session: {onnx_path}")
    onnx_classifier = ONNXDiseaseClassifier(onnx_model_path=onnx_path, classes=classes)

    test_transform = get_test_transform()
    test_dataset = datasets.ImageFolder(test_dir, transform=test_transform)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)

    all_preds = []
    all_targets = []
    all_probs = []
    latencies_ms = []

    for inputs, targets in test_loader:
        target_idx = targets.item()
        numpy_input = inputs.numpy()

        t0 = time.perf_counter()
        ort_inputs = {onnx_classifier.input_name: numpy_input}
        ort_outs = onnx_classifier.session.run(None, ort_inputs)
        logits = ort_outs[0]
        # Softmax
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        latency = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(latency)

        pred_idx = int(np.argmax(probs[0]))
        all_preds.append(pred_idx)
        all_targets.append(target_idx)
        all_probs.append(probs[0].tolist())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    accuracy = float(np.mean(all_preds == all_targets))
    target_names = [test_dataset.classes[i] for i in range(len(test_dataset.classes))]
    clf_report = classification_report(all_targets, all_preds, target_names=target_names, output_dict=True, zero_division=0)
    conf_mat = confusion_matrix(all_targets, all_preds).tolist()

    latency_stats = {
        "mean_ms": float(np.mean(latencies_ms)),
        "median_ms": float(np.median(latencies_ms)),
        "min_ms": float(np.min(latencies_ms)),
        "max_ms": float(np.max(latencies_ms)),
        "p95_ms": float(np.percentile(latencies_ms, 95)),
        "p99_ms": float(np.percentile(latencies_ms, 99)),
    }

    return {
        "engine": "ONNX_Runtime",
        "total_test_samples": len(test_dataset),
        "classes": target_names,
        "accuracy": accuracy,
        "macro_f1": clf_report["macro avg"]["f1-score"],
        "weighted_f1": clf_report["weighted avg"]["f1-score"],
        "classification_report": clf_report,
        "confusion_matrix": conf_mat,
        "latency_stats": latency_stats,
        "probabilities": all_probs,
        "predictions": all_preds.tolist(),
        "targets": all_targets.tolist()
    }


def compare_pytorch_and_onnx_test_set(
    py_results: Dict[str, Any],
    ox_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Validates prediction consistency and numerical drift between PyTorch and ONNX Runtime."""
    py_preds = np.array(py_results["predictions"])
    ox_preds = np.array(ox_results["predictions"])
    matching_preds = int(np.sum(py_preds == ox_preds))
    pred_agreement_pct = float((matching_preds / len(py_preds)) * 100.0)

    py_probs = np.array(py_results["probabilities"])
    ox_probs = np.array(ox_results["probabilities"])
    abs_diff = np.abs(py_probs - ox_probs)
    max_abs_diff = float(np.max(abs_diff))
    mean_abs_diff = float(np.mean(abs_diff))

    is_consistent = (pred_agreement_pct >= 99.0) and (max_abs_diff < 1e-3)

    return {
        "total_compared_samples": len(py_preds),
        "matching_predictions": matching_preds,
        "prediction_agreement_percentage": pred_agreement_pct,
        "max_absolute_probability_difference": max_abs_diff,
        "mean_absolute_probability_difference": mean_abs_diff,
        "is_numerically_consistent": is_consistent,
        "tolerance_threshold": 1e-3
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Crop Disease Classifier on Test Set")
    parser.add_argument("--test_dir", type=str, default="data/processed/test", help="Path to isolated test dataset directory")
    parser.add_argument("--checkpoint", type=str, default="ml_models/weights/efficientnet_b0_best.pth", help="Path to PyTorch .pth checkpoint")
    parser.add_argument("--onnx_path", type=str, default="ml_models/weights/efficientnet_b0.onnx", help="Path to ONNX model")
    parser.add_argument("--output_dir", type=str, default="ml_models/weights", help="Directory to save evaluation reports")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    py_res = evaluate_pytorch_model(args.checkpoint, args.test_dir)
    print("\n=======================================================")
    print(f"PYTORCH TEST SET ACCURACY: {py_res['accuracy']*100:.2f}% (Top-2: {py_res['top2_accuracy']*100:.2f}%)")
    print(f"Macro F1: {py_res['macro_f1']:.4f} | Weighted F1: {py_res['weighted_f1']:.4f}")
    print(f"Inference Latency: Mean {py_res['latency_stats']['mean_ms']:.2f}ms | P95 {py_res['latency_stats']['p95_ms']:.2f}ms")
    print("=======================================================")

    eval_summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pytorch_evaluation": {k: v for k, v in py_res.items() if k not in ["probabilities", "predictions", "targets"]},
    }

    if os.path.exists(args.onnx_path):
        ox_res = evaluate_onnx_model(args.onnx_path, args.test_dir, py_res["classes"])
        comp_res = compare_pytorch_and_onnx_test_set(py_res, ox_res)
        print("\n=======================================================")
        print(f"ONNX RUNTIME TEST SET ACCURACY: {ox_res['accuracy']*100:.2f}%")
        print(f"Inference Latency: Mean {ox_res['latency_stats']['mean_ms']:.2f}ms | P95 {ox_res['latency_stats']['p95_ms']:.2f}ms")
        print(f"PyTorch vs ONNX Agreement: {comp_res['prediction_agreement_percentage']:.2f}% (Max Diff: {comp_res['max_absolute_probability_difference']:.2e})")
        print("=======================================================")
        eval_summary["onnx_evaluation"] = {k: v for k, v in ox_res.items() if k not in ["probabilities", "predictions", "targets"]}
        eval_summary["parity_comparison"] = comp_res

    report_path = os.path.join(args.output_dir, "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(eval_summary, f, indent=2)
    print(f"\nEvaluation summary written to: {report_path}")


if __name__ == "__main__":
    main()
