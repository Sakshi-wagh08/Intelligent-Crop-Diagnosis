"""Model Export and ONNX Runtime Optimization Script.

Exports a trained PyTorch EfficientNet-B0 checkpoint to ONNX format with dynamic batching
and validates numerical equivalence against the PyTorch reference implementation.
"""

import os
import sys
import argparse
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.vision.model import load_model_checkpoint
from backend.app.vision.onnx_engine import export_pytorch_to_onnx, ONNXDiseaseClassifier, compare_pytorch_and_onnx
from backend.app.core.logging import logger


def export_and_validate(
    checkpoint_path: str,
    output_onnx_path: str,
    fp16: bool = False
) -> str:
    """Exports a PyTorch model checkpoint to ONNX and validates inference consistency."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at: {checkpoint_path}")

    logger.info(f"Loading trained PyTorch model checkpoint from: {checkpoint_path}")
    model, classes, class_to_idx = load_model_checkpoint(checkpoint_path=checkpoint_path)

    logger.info(f"Exporting model to ONNX: {output_onnx_path}")
    exported_path = export_pytorch_to_onnx(model, output_onnx_path, opset_version=17)
    logger.info(f"ONNX model successfully written to: {exported_path}")

    # Optional FP16 post-training quantization
    if fp16:
        try:
            from onnxconverter_common import float16
            import onnx
            logger.info("Applying post-training FP16 quantization...")
            onnx_model = onnx.load(exported_path)
            model_fp16 = float16.convert_float_to_float16(onnx_model)
            fp16_path = exported_path.replace(".onnx", "_fp16.onnx")
            onnx.save(model_fp16, fp16_path)
            logger.info(f"Saved FP16 quantized model to: {fp16_path}")
            exported_path = fp16_path
        except ImportError:
            logger.warning(
                "Package 'onnxconverter_common' is not installed. "
                "Skipping FP16 quantization step and retaining optimized FP32 ONNX model."
            )

    # Validate numerical consistency between PyTorch and ONNX Runtime
    logger.info("Validating numerical equivalence between PyTorch and ONNX Runtime...")
    onnx_classifier = ONNXDiseaseClassifier(onnx_model_path=exported_path, classes=classes)
    dummy_tensor = torch.randn(1, 3, 224, 224, dtype=torch.float32)

    comp = compare_pytorch_and_onnx(model, onnx_classifier, dummy_tensor, tolerance=1e-3)
    logger.info(f"Consistency Validation Result: {comp}")

    return exported_path


def main():
    parser = argparse.ArgumentParser(description="Export Trained EfficientNet-B0 to ONNX")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to trained PyTorch .pth checkpoint")
    parser.add_argument("--output_onnx", type=str, default="ml_models/weights/efficientnet_b0.onnx", help="Output .onnx path")
    parser.add_argument("--fp16", action="store_true", help="Apply FP16 post-training quantization")
    args = parser.parse_args()

    export_and_validate(args.checkpoint, args.output_onnx, fp16=args.fp16)


if __name__ == "__main__":
    main()
