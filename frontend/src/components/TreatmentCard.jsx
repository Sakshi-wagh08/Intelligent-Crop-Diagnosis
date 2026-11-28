import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  FileCheck,
  Droplets,
  Scale,
  Sparkles,
  BookOpen,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Info,
  Volume2,
  Square,
  CloudSun,
  Sprout,
} from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function TreatmentCard({
  recommendation = null,
  fieldAreaAcres = 1.0,
  isManualTestPathology = false,
}) {
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  if (!recommendation) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
        <h3 className="font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-600" />
          Bounded Dosage & Agronomic Safety
        </h3>
        <p className="text-xs text-slate-500">
          Run the multimodal fusion engine to generate bounded chemical dosage and regulatory safety checks.
        </p>
      </div>
    );
  }

  const {
    recommendation_available,
    status,
    status_message,
    telemetry_summary = {},
    safety_assessment = {},
    treatment = {},
    dosage_breakdown = {},
    fertilizer_recommendation = null,
    weather_advisory = null,
    farmer_summary = null,
    advisory_notice = '',
  } = recommendation;

  const isApproved = safety_assessment.safety_status === 'APPROVED' || safety_assessment.is_safe_to_apply;
  const isHealthy = Boolean(telemetry_summary.is_healthy);
  const isVerified = treatment?.verification_status === 'VERIFIED';

  const handleToggleSpeech = () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      alert('Voice read-aloud is not supported in this browser.');
      return;
    }
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    const textToRead =
      farmer_summary?.speech_text ||
      (isHealthy
        ? 'Good news. Your plant looks healthy. No chemical pesticide spray is needed.'
        : status_message || 'Check the treatment instructions on screen.');
    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.cancel();
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-900 text-base sm:text-lg flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              Treatment Plan &amp; Safety Check
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Recommended dosage, safe water mixing, and harvest wait period
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {isManualTestPathology && (
            <StatusBadge status="demo" label="DEMO TEST EVALUATION" />
          )}
          <StatusBadge
            status={isApproved ? (isVerified ? 'verified' : 'demo') : isHealthy ? 'healthy' : 'rejected'}
            label={
              isApproved
                ? isVerified
                  ? 'SAFETY APPROVED'
                  : 'UNVERIFIED RECORD'
                : isHealthy
                ? 'HEALTHY CROP'
                : safety_assessment.safety_status || 'APPLICATION RESTRICTED'
            }
          />
        </div>
      </div>

      {/* Manual Pathology Demonstration Notice */}
      {isManualTestPathology && (
        <div className="p-4 rounded-xl bg-amber-50/90 border border-amber-300 text-xs text-amber-950 space-y-1.5 shadow-xs">
          <div className="flex items-center gap-2 font-bold text-amber-900">
            <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
            <span>DEMONSTRATION & RESEARCH EVALUATION ONLY</span>
          </div>
          <p className="leading-relaxed">
            The target pathology ({treatment?.crop_stage || ''} {telemetry_summary?.disease || ''}) was manually selected as a test input because AI vision model training is currently pending.
            <strong> This output is strictly for demonstration and research verification, NOT an active field treatment recommendation.</strong>
          </p>
        </div>
      )}

      {/* Simple Farmer Action Summary + Voice Read-Aloud */}
      {farmer_summary && (
        <div className="p-5 rounded-2xl bg-emerald-50/70 border border-emerald-200 space-y-3">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">
                Simple Farmer Action Plan
              </span>
              <h4 className="text-base sm:text-lg font-bold text-slate-900 mt-0.5">
                {farmer_summary.headline}
              </h4>
            </div>
            <button
              type="button"
              onClick={handleToggleSpeech}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-emerald-100 text-emerald-900 text-xs font-bold border border-emerald-300 shadow-xs transition-colors"
            >
              {isSpeaking ? <Square className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
              {isSpeaking ? 'Stop Voice' : 'Listen (Read Aloud)'}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
            <div className="p-3 rounded-xl bg-white border border-emerald-100">
              <span className="font-bold text-slate-800 block">1. What to Do</span>
              <p className="text-slate-700 mt-0.5">{farmer_summary.what_to_do}</p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-emerald-100">
              <span className="font-bold text-slate-800 block">2. How to Mix / Apply</span>
              <p className="text-slate-700 mt-0.5">{farmer_summary.how_to_mix}</p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-emerald-100">
              <span className="font-bold text-slate-800 block">3. Safety & Harvest Wait</span>
              <p className="text-slate-700 mt-0.5">{farmer_summary.safety_tip}</p>
            </div>
            {weather_advisory && (
              <div
                className={`p-3 rounded-xl border ${
                  weather_advisory.is_good_to_spray === false
                    ? 'bg-amber-50 border-amber-200 text-amber-950'
                    : 'bg-white border-emerald-100 text-slate-700'
                }`}
              >
                <span className="font-bold flex items-center gap-1.5">
                  <CloudSun className="w-3.5 h-3.5 text-emerald-700" />
                  4. Today's Spray Weather
                </span>
                <p className="mt-0.5">{weather_advisory.advisory}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Healthy Crop State */}
      {isHealthy && (
        <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 text-center space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
          <h4 className="font-bold text-emerald-900 text-sm">No Chemical Pesticide Treatment Required</h4>
          <p className="text-xs text-emerald-800 max-w-md mx-auto">
            Foliar analysis confirms healthy tissue without pathology. Routine field monitoring and good agricultural practices are recommended.
          </p>
        </div>
      )}

      {/* Soil-Adjusted Fertilizer Plan (Available for Healthy & Diseased Crops) */}
      {fertilizer_recommendation && (
        <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-200 space-y-2.5 text-xs">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="font-bold text-teal-900 flex items-center gap-1.5 uppercase tracking-wider">
              <Sprout className="w-4 h-4 text-teal-700" />
              Soil-Adjusted Fertilizer Plan ({fertilizer_recommendation.product_name})
            </span>
            <span className="px-2 py-0.5 rounded bg-white text-teal-800 font-semibold border border-teal-200">
              Soil Factor Fs = {Number(fertilizer_recommendation.soil_factor_Fs || 1).toFixed(2)}
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <div className="p-2.5 rounded-lg bg-white border border-teal-100">
              <span className="text-slate-500">Rate per Acre</span>
              <p className="text-base font-bold text-teal-900 font-mono">
                {fertilizer_recommendation.final_prescribed_dose} {fertilizer_recommendation.dose_unit}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-white border border-teal-100">
              <span className="text-slate-500">Total for {fieldAreaAcres} Acre(s)</span>
              <p className="text-base font-bold text-teal-900 font-mono">
                {(Number(fertilizer_recommendation.final_prescribed_dose) * fieldAreaAcres).toFixed(1)}{' '}
                {fertilizer_recommendation.dose_unit?.split('/')[0]}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-white border border-teal-100">
              <span className="text-slate-500">How to Apply</span>
              <p className="font-medium text-slate-800">{fertilizer_recommendation.application_method}</p>
            </div>
          </div>
          <p className="text-slate-600">
            <strong>Tip:</strong> {fertilizer_recommendation.instructions} ({fertilizer_recommendation.soil_factor_status})
          </p>
        </div>
      )}

      {/* Safety Compliance Assessment Card */}
      {!isHealthy && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Safety Checks
              </span>
              <span className={`text-xs font-bold ${isApproved ? 'text-emerald-700' : 'text-rose-700'}`}>
                {isApproved ? 'All Safety Checks Passed' : 'Spray Held Back for Safety'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.confidence_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Photo Check Confidence (≥ 70%)</span>
              </div>

              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.phi_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Safe Wait Before Harvest (PHI: {treatment?.phi_days !== undefined ? `${treatment.phi_days} days` : 'N/A'})</span>
              </div>

              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.compatibility_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Safe to Mix With Other Sprays</span>
              </div>

              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.verification_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Approved Official Guideline</span>
              </div>
            </div>

            {/* Warnings list if any from backend */}
            {safety_assessment.warnings && safety_assessment.warnings.length > 0 && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-900 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  Application Warnings & Restrictions:
                </div>
                {safety_assessment.warnings.map((w, idx) => (
                  <p key={idx}>• {w}</p>
                ))}
              </div>
            )}
          </div>

          {/* Mathematical Dosage Calculation Breakdown */}
          {dosage_breakdown && dosage_breakdown.final_prescribed_dose !== undefined && (
            <div className="p-5 rounded-xl bg-gradient-to-br from-emerald-50/50 to-teal-50/30 border border-emerald-200 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                    Recommended Medicine &amp; Water Amount
                  </span>
                  <div className="font-mono text-xs text-emerald-700 mt-0.5">
                    Safe Limit Cap: D = min(D₀ × Fₛ × Fᵥ, D_label_max)
                  </div>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Your Field: {fieldAreaAcres} Acre(s)
                </span>
              </div>

              {/* Main Dosage Display - All values from backend */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-white border border-emerald-200/80 shadow-xs">
                  <span className="text-xs text-slate-500">Dose per Acre</span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold text-emerald-800 font-mono">
                      {dosage_breakdown.final_prescribed_dose}
                    </span>
                    <span className="text-xs text-slate-600 font-medium">
                      {dosage_breakdown.dose_unit}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Authoritative Backend Rate (per acre)
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-emerald-200/80 shadow-xs">
                  <span className="text-xs text-slate-500">Total Needed for Field</span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold text-emerald-800 font-mono">
                      {(dosage_breakdown.final_prescribed_dose * fieldAreaAcres).toFixed(2)}
                    </span>
                    <span className="text-xs text-slate-600 font-medium">
                      {dosage_breakdown.dose_unit?.split('/')[0] || ''}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Scaled: D × {fieldAreaAcres} acre(s)
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-emerald-200/80 shadow-xs">
                  <span className="text-xs text-slate-500">Water to Mix With</span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold text-blue-700 font-mono">
                      {(dosage_breakdown.water_dilution_liters_per_acre * fieldAreaAcres).toFixed(0)}
                    </span>
                    <span className="text-xs text-slate-600 font-medium">Liters</span>
                  </div>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    {dosage_breakdown.water_dilution_liters_per_acre} L/acre (Clean water)
                  </span>
                </div>
              </div>

              {/* Factors Detail */}
              <div className="p-3 rounded-lg bg-white/80 border border-emerald-100 text-xs text-slate-600 space-y-1.5">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div>
                    <span className="text-slate-400">Standard Dose (D₀):</span>
                    <p className="font-semibold text-slate-800 font-mono">
                      {dosage_breakdown.base_dose_D0} {dosage_breakdown.dose_unit}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400">Soil Adjustment (Fₛ):</span>
                    <p className="font-semibold text-slate-800 font-mono">
                      {dosage_breakdown.soil_factor_Fs?.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400">Severity Factor (Fᵥ):</span>
                    <p className="font-semibold text-slate-800 font-mono">
                      {dosage_breakdown.severity_factor_Fv?.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400">Max Legal Limit:</span>
                    <p className="font-semibold text-slate-800 font-mono">
                      {dosage_breakdown.max_label_dose_cap} {dosage_breakdown.dose_unit}
                    </p>
                  </div>
                </div>
                <div className="pt-1.5 border-t border-slate-100 text-[11px] text-slate-500">
                  <em>Safety Limit Note:</em> The dose is always kept at or below the legal maximum label limit so it never harms your crop or soil.
                </div>
              </div>
            </div>
          )}

          {/* Treatment Specifications & PPE */}
          {treatment && treatment.active_ingredient && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Medicine &amp; Spraying Details
                </h4>
                <StatusBadge
                  status={isVerified ? 'verified' : 'demo'}
                  label={isVerified ? 'PEER-VERIFIED RECORD' : 'UNVERIFIED / DEMO'}
                  size="xs"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-slate-500">Medicine Name:</span>
                  <p className="font-bold text-slate-900">{treatment.active_ingredient}</p>
                </div>
                <div>
                  <span className="text-slate-500">Standard Product:</span>
                  <p className="font-medium text-slate-800">{treatment.registered_product_name || 'Standard Product'}</p>
                </div>
                <div>
                  <span className="text-slate-500">Product Strength:</span>
                  <p className="font-medium text-slate-800">
                    {treatment.reference_concentration_Cr} {treatment.concentration_unit}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">How to Apply:</span>
                  <p className="font-medium text-slate-800">{treatment.application_method}</p>
                </div>
                <div>
                  <span className="text-slate-500">Wait Before Harvest (PHI):</span>
                  <p className="font-bold text-emerald-800">
                    {treatment.phi_days !== undefined ? `${treatment.phi_days} Days` : 'Not specified'}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Crop Stage:</span>
                  <p className="font-medium text-slate-800">{treatment.crop_stage}</p>
                </div>
              </div>

              {/* PPE Requirements from backend */}
              {treatment.ppe_requirements && (
                <div className="p-3 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 space-y-1">
                  <span className="font-semibold text-slate-900 block">Protective Gear to Wear:</span>
                  <p className="text-slate-600">{treatment.ppe_requirements}</p>
                </div>
              )}

              {/* Source Citation from backend */}
              {treatment.source_citation && (
                <div className="p-3 rounded-lg bg-white border border-slate-200 text-xs space-y-1">
                  <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
                    Official Farming Guide Reference:
                  </span>
                  <p className="text-slate-700 font-medium">{treatment.source_citation}</p>
                  {treatment.official_citation_detail && (
                    <p className="text-slate-500">{treatment.official_citation_detail}</p>
                  )}
                  {treatment.statutory_source_url && (
                    <a
                      href={treatment.statutory_source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-800 font-semibold mt-1"
                    >
                      View Official Document <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
