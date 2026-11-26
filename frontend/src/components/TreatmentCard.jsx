import React from 'react';
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
} from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function TreatmentCard({
  recommendation = null,
  fieldAreaAcres = 1.0,
  isManualTestPathology = false,
}) {
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
    advisory_notice = '',
  } = recommendation;

  const isApproved = safety_assessment.safety_status === 'APPROVED' || safety_assessment.is_safe_to_apply;
  const isHealthy = Boolean(telemetry_summary.is_healthy);
  const isVerified = treatment?.verification_status === 'VERIFIED';

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-900 text-base sm:text-lg flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              Agronomic Dosage & Safety Assessment
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Multimodal Data Fusion: Bounded Chemical Dosage & Statutory Pre-Harvest Verification
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

      {/* Safety Compliance Assessment Card */}
      {!isHealthy && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Regulatory Safety Gate Verification
              </span>
              <span className={`text-xs font-bold ${isApproved ? 'text-emerald-700' : 'text-rose-700'}`}>
                {isApproved ? 'Safety Gates Passed' : 'Regulatory Restriction Triggered'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.confidence_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Diagnostic Confidence Gate (≥ 70%)</span>
              </div>

              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.phi_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Pre-Harvest Interval (PHI: {treatment?.phi_days !== undefined ? `${treatment.phi_days} days` : 'N/A'})</span>
              </div>

              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.compatibility_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Tank-Mix Compatibility & Phytotoxicity</span>
              </div>

              <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200/60">
                {safety_assessment.verification_check_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>Statutory Source Verification</span>
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
                    Bounded Precision Dosage Formulation
                  </span>
                  <div className="font-mono text-xs text-emerald-700 mt-0.5">
                    D = min(D₀ × Fₛ × Fᵥ, D_label_max)
                  </div>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Target Field: {fieldAreaAcres} Acre(s)
                </span>
              </div>

              {/* Main Dosage Display - All values from backend */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-white border border-emerald-200/80 shadow-xs">
                  <span className="text-xs text-slate-500">Prescribed Rate (D)</span>
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
                  <span className="text-xs text-slate-500">Field Total Quantity</span>
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
                  <span className="text-xs text-slate-500">Spray Carrier Water</span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold text-blue-700 font-mono">
                      {(dosage_breakdown.water_dilution_liters_per_acre * fieldAreaAcres).toFixed(0)}
                    </span>
                    <span className="text-xs text-slate-600 font-medium">Liters</span>
                  </div>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    {dosage_breakdown.water_dilution_liters_per_acre} L/acre (Backend value)
                  </span>
                </div>
              </div>

              {/* Factors Detail */}
              <div className="p-3 rounded-lg bg-white/80 border border-emerald-100 text-xs text-slate-600 space-y-1.5">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div>
                    <span className="text-slate-400">Base Dose (D₀):</span>
                    <p className="font-semibold text-slate-800 font-mono">
                      {dosage_breakdown.base_dose_D0} {dosage_breakdown.dose_unit}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400">Soil Factor (Fₛ):</span>
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
                    <span className="text-slate-400">Label Cap (D_max):</span>
                    <p className="font-semibold text-slate-800 font-mono">
                      {dosage_breakdown.max_label_dose_cap} {dosage_breakdown.dose_unit}
                    </p>
                  </div>
                </div>
                <div className="pt-1.5 border-t border-slate-100 text-[11px] text-slate-500">
                  <em>Dosage Formulation Notice:</em> The dosage calculation D = min(D₀ × Fₛ × Fᵥ, D_label_max) is strictly capped at the registered label ceiling (D_label_max). Soil factor (Fₛ) and severity factor (Fᵥ) values are evaluated and returned directly by the backend fusion service.
                </div>
              </div>
            </div>
          )}

          {/* Treatment Specifications & PPE */}
          {treatment && treatment.active_ingredient && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Prescribed Chemical & Application Protocols
                </h4>
                <StatusBadge
                  status={isVerified ? 'verified' : 'demo'}
                  label={isVerified ? 'PEER-VERIFIED RECORD' : 'UNVERIFIED / DEMO'}
                  size="xs"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-slate-500">Active Chemical:</span>
                  <p className="font-bold text-slate-900">{treatment.active_ingredient}</p>
                </div>
                <div>
                  <span className="text-slate-500">Registered Product:</span>
                  <p className="font-medium text-slate-800">{treatment.registered_product_name || 'Commercial Formulation'}</p>
                </div>
                <div>
                  <span className="text-slate-500">Reference Strength:</span>
                  <p className="font-medium text-slate-800">
                    {treatment.reference_concentration_Cr} {treatment.concentration_unit}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Application Method:</span>
                  <p className="font-medium text-slate-800">{treatment.application_method}</p>
                </div>
                <div>
                  <span className="text-slate-500">Pre-Harvest Interval (PHI):</span>
                  <p className="font-bold text-emerald-800">
                    {treatment.phi_days !== undefined ? `${treatment.phi_days} Days` : 'Not specified'}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Phenological Stage:</span>
                  <p className="font-medium text-slate-800">{treatment.crop_stage}</p>
                </div>
              </div>

              {/* PPE Requirements from backend */}
              {treatment.ppe_requirements && (
                <div className="p-3 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 space-y-1">
                  <span className="font-semibold text-slate-900 block">Personal Protective Equipment (PPE):</span>
                  <p className="text-slate-600">{treatment.ppe_requirements}</p>
                </div>
              )}

              {/* Source Citation from backend */}
              {treatment.source_citation && (
                <div className="p-3 rounded-lg bg-white border border-slate-200 text-xs space-y-1">
                  <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
                    Statutory Agronomic Source & Verification:
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
