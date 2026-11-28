import React, { useRef } from 'react';
import { Camera, Upload, AlertCircle, CheckCircle, Info, Sparkles, FileImage, ShieldAlert, Cpu } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function DiagnosisCard({
  visionStatus = null,
  supportedPathologies = [],
  selectedCrop = '',
  selectedDisease = '',
  onSelectDisease = () => {},
  imageFile = null,
  onImageChange = () => {},
  imagePreviewUrl = null,
  visionResult = null,
  isManualTestPathology = false,
}) {
  const fileInputRef = useRef(null);

  const hasActiveModel = Boolean(visionStatus?.has_active_model);

  // Filter pathologies for selected crop if selected
  const relevantPathologies = supportedPathologies.filter((p) => {
    if (!selectedCrop) return true;
    return p.crop.toLowerCase() === selectedCrop.toLowerCase();
  });

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 15 * 1024 * 1024) {
      alert('Selected image exceeds maximum allowed size of 15 MB.');
      return;
    }

    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert('Please upload a valid image file (JPEG, PNG, or WEBP).');
      return;
    }

    onImageChange(file);
  };

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-900 text-base sm:text-lg flex items-center gap-2">
              <Camera className="w-5 h-5 text-emerald-600" />
              Step 2: Check Your Plant Leaf
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Take or upload a clear photo of 1 leaf, or pick a leaf problem below.
          </p>
        </div>

        <StatusBadge
          status={hasActiveModel ? 'live' : 'pending'}
          label={hasActiveModel ? 'Photo Check Ready' : 'Model Training Pending'}
        />
      </div>

      {/* Transparent Model Status Alert */}
      {!hasActiveModel ? (
        <div className="p-4 rounded-xl bg-amber-50/90 border border-amber-300 text-xs text-amber-950 space-y-2">
          <div className="flex items-center gap-2 font-bold text-amber-900">
            <Cpu className="w-4 h-4 text-amber-700 shrink-0" />
            <span>Auto Leaf Check Unavailable (Model Training Pending)</span>
          </div>
          <p className="leading-relaxed">
            The trained EfficientNet-B0 disease classifier checkpoint is currently not loaded on the backend.
            <strong> No automatic leaf detection is running right now.</strong>
          </p>
          <p className="leading-relaxed text-amber-900 font-medium">
            Please pick the leaf problem from the list below to see the dose and nearby shop guide.
          </p>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 text-xs text-emerald-950 space-y-1.5">
          <div className="flex items-center gap-2 font-bold text-emerald-900">
            <Cpu className="w-4 h-4 text-emerald-700 shrink-0" />
            <span>Leaf Photo Check is Ready</span>
          </div>
          <p className="leading-relaxed text-emerald-900">
            Take a close photo of 1 leaf against a plain background. We will check if it is healthy or sick and how much of the leaf is damaged. (Or you can pick the disease yourself below.)
          </p>
        </div>
      )}

      {/* Image Upload Area */}
      <div className="space-y-3">
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Upload or Take a Leaf Photo
        </label>

        <div
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
            imagePreviewUrl
              ? 'border-emerald-300 bg-emerald-50/20'
              : 'border-slate-300 hover:border-emerald-500 hover:bg-slate-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            className="hidden"
            onChange={handleFileSelect}
          />

          {imagePreviewUrl ? (
            <div className="flex flex-col items-center gap-3">
              <div className="relative w-40 h-40 rounded-lg overflow-hidden border border-slate-200 shadow-xs">
                <img
                  src={imagePreviewUrl}
                  alt="Leaf specimen preview"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="text-xs text-slate-600">
                <span className="font-semibold text-emerald-700">{imageFile?.name}</span> (
                {(imageFile?.size / 1024 / 1024).toFixed(2)} MB)
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onImageChange(null);
                }}
                className="text-xs text-rose-600 hover:text-rose-700 font-medium underline"
              >
                Remove / Change Image
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                <Upload className="w-6 h-6" />
              </div>
              <div className="text-sm font-semibold text-slate-700">
                Click or drag & drop leaf photo
              </div>
              <p className="text-xs text-slate-400">
                Supports JPEG, PNG, WEBP up to 15 MB. Mobile camera capture enabled.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Live AI Vision Classification Result */}
      {visionResult?.diagnosis && (
        <div className="p-5 rounded-xl bg-slate-50 border border-emerald-200 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Automated Disease Classification (EfficientNet-B0)
              </span>
            </div>
            <StatusBadge
              status={visionResult.diagnosis.is_confident ? 'live' : 'warning'}
              label={visionResult.diagnosis.is_confident ? 'CONFIDENT PREDICTION' : 'LOW CONFIDENCE / UNCERTAIN'}
              size="xs"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-white p-4 rounded-lg border border-slate-200">
            <div>
              <span className="text-xs text-slate-500">Detected Condition</span>
              <p className="text-base font-bold text-slate-900 mt-0.5">
                {visionResult.diagnosis.crop}: {visionResult.diagnosis.disease}
              </p>
              {visionResult.diagnosis.is_healthy && (
                <span className="text-xs font-semibold text-emerald-700">Healthy Leaf</span>
              )}
            </div>
            <div>
              <span className="text-xs text-slate-500">How Sure the Check Is</span>
              <p className="text-base font-bold text-slate-900 mt-0.5">
                {((visionResult.diagnosis.confidence || 0) * 100).toFixed(1)}%
              </p>
              <div className="w-full bg-slate-200 rounded-full h-1.5 mt-1.5">
                <div
                  className={`h-1.5 rounded-full ${
                    visionResult.diagnosis.is_confident ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${Math.min(100, (visionResult.diagnosis.confidence || 0) * 100)}%` }}
                />
              </div>
            </div>
            <div>
              <span className="text-xs text-slate-500">Leaf Check Mode</span>
              <p className="text-xs font-semibold text-slate-700 mt-1">
                {visionResult.diagnosis.inference_device || 'Fast Auto Check'}
              </p>
            </div>
          </div>

          {/* Low Confidence Advisory */}
          {!visionResult.diagnosis.is_confident && (
            <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <p>
                <strong>Diagnostic Uncertainty Alert:</strong> The photo check is only {((visionResult.diagnosis.confidence || 0) * 100).toFixed(1)}% sure (below 70%). For your safety, please take a clearer photo or ask your local agriculture officer before spraying.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Foliar Severity Analysis Result (OpenCV Segmentation) */}
      {visionResult && (visionResult.severity_estimation || visionResult.severity) && (() => {
        const sev = visionResult.severity_estimation || visionResult.severity;
        const ratio = sev.lesion_to_leaf_ratio ?? sev.affected_ratio ?? 0;
        const tier = sev.severity_tier ?? sev.scale_1_to_5 ?? 'Low';
        const factor = sev.severity_factor_Fv ?? sev.severity_score ?? 1.0;
        const disclaimer = sev.estimation_disclaimer || sev.status_message;

        return (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                OpenCV Foliar Lesion Surface Segmentation (S_severity)
              </span>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                Severity Tier: {tier}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <span className="text-xs text-slate-500">Affected Surface Ratio</span>
                <p className="text-xl font-bold text-slate-900 font-mono mt-0.5">
                  {(ratio * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Chemical Multiplier (F_v)</span>
                <p className="text-xl font-bold text-slate-900 font-mono mt-0.5">
                  {typeof factor === 'number' ? factor.toFixed(2) : factor}
                  <span className="text-xs font-normal text-slate-500 ml-1">(Neutral)</span>
                </p>
              </div>
              {sev.leaf_coverage_percent !== undefined && (
                <div>
                  <span className="text-xs text-slate-500">Leaf Foliar Coverage</span>
                  <p className="text-xl font-bold text-slate-900 font-mono mt-0.5">
                    {sev.leaf_coverage_percent?.toFixed(1)}%
                  </p>
                </div>
              )}
            </div>

            {disclaimer && (
              <p className="text-[11px] text-slate-500 border-t border-slate-200 pt-2 italic">
                {disclaimer}
              </p>
            )}
          </div>
        );
      })()}

      {/* Manual Problem Selection */}
      <div className="space-y-3 pt-2 border-t border-slate-100">
        <div className="space-y-1">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider">
                Or Pick a Crop Problem Yourself (Manual Selection)
              </label>
              <StatusBadge status="demo" label={hasActiveModel ? 'MANUAL PICK' : 'MANUAL TEST INPUT'} size="xs" />
            </div>
            <span className="text-xs text-slate-500">
              {relevantPathologies.length} Crop Problem(s) Available
            </span>
          </div>
          <p className="text-[11px] text-slate-600">
            {hasActiveModel
              ? 'If you do not have a leaf photo right now, tap the problem you see on your crop below.'
              : 'Manual Pathology Selection is active for testing because auto photo check is offline.'}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {relevantPathologies.map((pathology, idx) => {
            const isSelected = selectedDisease === pathology.disease;
            return (
              <div
                key={`${pathology.crop}-${pathology.disease}-${idx}`}
                onClick={() => onSelectDisease(pathology.disease)}
                className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                  isSelected
                    ? 'border-emerald-500 bg-emerald-50/50 shadow-xs ring-1 ring-emerald-500'
                    : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-semibold text-slate-900 text-sm">
                        {pathology.crop}: {pathology.disease}
                      </span>
                    </div>
                    {pathology.active_ingredient && (
                      <span className="text-xs text-slate-500 mt-0.5 block">
                        Medicine: {pathology.active_ingredient}
                      </span>
                    )}
                  </div>
                  {isSelected ? (
                    <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-300 shrink-0 mt-0.5" />
                  )}
                </div>

                <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span>{pathology.application_method || 'Foliar Spray'}</span>
                  <span className="text-emerald-700 font-medium">Verified Safe Guide</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
