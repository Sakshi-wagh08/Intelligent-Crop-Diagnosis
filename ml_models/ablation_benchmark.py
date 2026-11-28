"""Ablation & Dosage Evaluation Benchmark (Section V of DT Project Paper).

Compares:
1. Image-Only Mode (no soil data, neutral Fs=1.00)
2. Soil-Only Mode (soil-driven fertilizer dosing with dynamic Fs, no vision diagnosis)
3. Combined Multimodal Mode (vision + soil + weather + statutory safety gates)
"""

import os
import sys
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.schemas.soil import SoilTelemetryResponse, SoilTelemetryParameters
from backend.app.fusion.service import FusionService
from backend.app.fusion.knowledge_base import AgronomicKnowledgeBase
from backend.app.fusion.engine import DosageCalculator


SCENARIOS = [
    {"crop": "Tomato", "stage": "Vegetative", "disease": "Early Blight", "conf": 0.95, "days": 20, "soil": ("low_oc", 5.8, 3.8, 70.0)},
    {"crop": "Tomato", "stage": "Flowering", "disease": "Early Blight", "conf": 0.91, "days": 5, "soil": ("normal", 6.5, 8.0, 40.0)},
    {"crop": "Tomato", "stage": "Vegetative", "disease": "Late Blight", "conf": 0.93, "days": 10, "soil": ("rich", 6.8, 14.5, 30.0)},
    {"crop": "Potato", "stage": "Tuber Initiation", "disease": "Late Blight", "conf": 0.94, "days": 18, "soil": ("low_oc", 5.4, 4.2, 68.0)},
    {"crop": "Rice", "stage": "Tillering", "disease": "Blast", "conf": 0.89, "days": 35, "soil": ("normal", 6.2, 7.5, 35.0)},
    {"crop": "Tomato", "stage": "Vegetative", "disease": "healthy", "conf": 0.97, "days": 25, "soil": ("low_oc", 6.0, 4.0, 66.0)},
    {"crop": "Rice", "stage": "Tillering", "disease": "Blast", "conf": 0.60, "days": 40, "soil": ("normal", 6.4, 8.0, 30.0)},
    {"crop": "Rice", "stage": "Tillering", "disease": "Blast", "conf": 0.92, "days": 10, "soil": ("normal", 6.4, 8.0, 30.0)},
]


def _make_soil_mock(tag: str, ph: float, soc: float, sand: float) -> MagicMock:
    mock = MagicMock()
    if tag == "unavailable":
        resp = SoilTelemetryResponse(
            latitude=12.52,
            longitude=76.90,
            telemetry_source="Unavailable",
            data_status="unavailable",
            is_fallback=True,
            retrieval_timestamp="2026-11-28T00:00:00Z",
            parameters=None,
            advisory_notice="Unavailable",
        )
    else:
        resp = SoilTelemetryResponse(
            latitude=12.52,
            longitude=76.90,
            telemetry_source="Benchmark_Soil",
            data_status="live",
            is_fallback=False,
            retrieval_timestamp="2026-11-28T00:00:00Z",
            parameters=SoilTelemetryParameters(
                pH=ph,
                organic_carbon_g_kg=soc,
                sand_fraction_percent=sand,
                clay_fraction_percent=20.0,
                silt_fraction_percent=max(0.0, 80.0 - sand),
            ),
            advisory_notice="Benchmark",
        )
    mock.get_telemetry = AsyncMock(return_value=resp)
    return mock


async def run_ablation() -> dict:
    results = []
    fert_abs_diffs = []

    for sc in SCENARIOS:
        tag, ph, soc, sand = sc["soil"]

        # 1. Image-Only (no soil telemetry)
        svc_img = FusionService(soil_svc=_make_soil_mock("unavailable", ph, soc, sand))
        res_img = await svc_img.fuse_and_recommend(
            crop_name=sc["crop"],
            crop_stage=sc["stage"],
            latitude=12.52,
            longitude=76.90,
            days_to_harvest=sc["days"],
            diagnosed_disease_override=sc["disease"],
            diagnostic_confidence_override=sc["conf"],
        )

        # 2. Soil-Only (fertilizer plan with soil Fs, no disease diagnosis)
        soil_mock = _make_soil_mock(tag, ph, soc, sand)
        soil_resp = await soil_mock.get_telemetry(12.52, 76.90)
        fert_plan = AgronomicKnowledgeBase.get_fertilizer_plan(sc["crop"], sc["stage"])
        fert_calc = DosageCalculator.compute_dosage(fert_plan, soil_result=soil_resp)

        # 3. Combined Multimodal (Image + Soil + Safety Gates)
        svc_comb = FusionService(soil_svc=_make_soil_mock(tag, ph, soc, sand))
        res_comb = await svc_comb.fuse_and_recommend(
            crop_name=sc["crop"],
            crop_stage=sc["stage"],
            latitude=12.52,
            longitude=76.90,
            days_to_harvest=sc["days"],
            diagnosed_disease_override=sc["disease"],
            diagnostic_confidence_override=sc["conf"],
        )

        fert_abs_diffs.append(abs(fert_calc.final_prescribed_dose - fert_calc.base_dose_D0))

        results.append({
            "scenario": f"{sc['crop']} / {sc['disease']} (conf={sc['conf']}, dth={sc['days']}, soil={tag})",
            "image_only_status": res_img.status,
            "image_only_pesticide_dose": res_img.dosage_breakdown.final_prescribed_dose if res_img.dosage_breakdown else 0.0,
            "soil_only_fertilizer_D0": fert_calc.base_dose_D0,
            "soil_only_Fs": fert_calc.soil_factor_Fs,
            "soil_only_fertilizer_D": fert_calc.final_prescribed_dose,
            "combined_status": res_comb.status,
            "combined_safe_to_apply": res_comb.safety_assessment.is_safe_to_apply,
        })

    summary = {
        "total_scenarios": len(results),
        "safety_blocks_triggered": sum(1 for r in results if not r["combined_safe_to_apply"]),
        "mean_soil_fertilizer_adjustment_kg_acre": round(sum(fert_abs_diffs) / max(len(fert_abs_diffs), 1), 3),
        "scenarios": results,
    }
    return summary


if __name__ == "__main__":
    out = asyncio.run(run_ablation())
    out_path = os.path.join("ml_models", "weights", "ablation_report.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Ablation benchmark complete ({out['total_scenarios']} scenarios). Saved to {out_path}")
    print(f"Safety blocks triggered: {out['safety_blocks_triggered']}, Mean soil Fs adjustment: {out['mean_soil_fertilizer_adjustment_kg_acre']} kg/acre")
