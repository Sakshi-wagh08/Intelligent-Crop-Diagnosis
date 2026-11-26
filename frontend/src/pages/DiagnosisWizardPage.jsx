import React, { useState, useEffect } from 'react';
import {
  Sprout,
  Camera,
  Layers,
  ShieldCheck,
  Store,
  ChevronRight,
  ChevronLeft,
  Navigation,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Sliders,
  MapPin,
  Sparkles,
} from 'lucide-react';
import apiService from '../services/api';
import DiagnosisCard from '../components/DiagnosisCard';
import SoilCard from '../components/SoilCard';
import TreatmentCard from '../components/TreatmentCard';
import SubstitutionCard from '../components/SubstitutionCard';
import GoogleMapView from '../components/GoogleMapView';

export default function DiagnosisWizardPage() {
  const [currentStep, setCurrentStep] = useState(1);

  // Crops & Pathologies Catalog
  const [crops, setCrops] = useState([]);
  const [supportedPathologies, setSupportedPathologies] = useState([]);
  const [visionStatus, setVisionStatus] = useState(null);

  // Form State
  const [cropName, setCropName] = useState('Tomato');
  const [cropStage, setCropStage] = useState('Vegetative');
  const [fieldAreaAcres, setFieldAreaAcres] = useState(1.0);
  const [daysToHarvest, setDaysToHarvest] = useState(14);
  const [tankMixChemicals, setTankMixChemicals] = useState('');

  // Diagnostic / Image State
  const [imageFile, setImageFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [visionResult, setVisionResult] = useState(null);
  const [selectedDisease, setSelectedDisease] = useState('');
  const [isManualTestPathology, setIsManualTestPathology] = useState(false);
  const [diagnosticConfidence, setDiagnosticConfidence] = useState(null);

  // Coordinates & Soil Telemetry State (User-entered or GPS-derived)
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [soilDepth, setSoilDepth] = useState('0-5cm');
  const [soilData, setSoilData] = useState(null);
  const [soilLoading, setSoilLoading] = useState(false);
  const [soilError, setSoilError] = useState(null);

  // Multimodal Fusion Recommendation State
  const [recommendation, setRecommendation] = useState(null);
  const [fusionLoading, setFusionLoading] = useState(false);
  const [fusionError, setFusionError] = useState(null);

  // Agro-Dealer Substitution State
  const [searchRadiusKm, setSearchRadiusKm] = useState(25.0);
  const [substitutionData, setSubstitutionData] = useState(null);
  const [selectedOffering, setSelectedOffering] = useState(null);
  const [substitutionLoading, setSubstitutionLoading] = useState(false);
  const [substitutionError, setSubstitutionError] = useState(null);
  const [nearbyMerchantsList, setNearbyMerchantsList] = useState([]);

  // Load initial backend catalogs
  useEffect(() => {
    apiService.getCrops()
      .then((data) => {
        setCrops(data);
        if (data.length > 0 && !cropName) {
          setCropName(data[0].name);
        }
      })
      .catch((err) => console.error('Failed to load crops catalog:', err));

    apiService.getSupportedPathologies()
      .then((data) => setSupportedPathologies(data))
      .catch((err) => console.error('Failed to load supported pathologies:', err));

    apiService.getVisionStatus()
      .then((data) => setVisionStatus(data))
      .catch((err) => console.error('Failed to load vision status:', err));
  }, []);

  // Update preview when image file changes
  const handleImageChange = (file) => {
    setImageFile(file);
    if (file) {
      const url = URL.createObjectURL(file);
      setImagePreviewUrl(url);

      // Attempt live vision diagnosis if model is available
      if (visionStatus?.has_active_model) {
        apiService.diagnoseLeafImage(file)
          .then((res) => {
            setVisionResult(res);
            const diag = res.diagnosis;
            if (diag && diag.disease) {
              setSelectedDisease(diag.disease);
              setDiagnosticConfidence(diag.confidence);
              setIsManualTestPathology(false);
            } else if (res.disease) {
              setSelectedDisease(res.disease);
              setDiagnosticConfidence(res.confidence || 0.85);
            }
          })
          .catch((err) => console.warn('Vision diagnosis query error:', err));
      }
    } else {
      setImagePreviewUrl(null);
      setVisionResult(null);
    }
  };

  // Browser Geolocation GPS Handler
  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(Number(pos.coords.latitude.toFixed(4)));
        setLongitude(Number(pos.coords.longitude.toFixed(4)));
      },
      (err) => {
        alert(`Failed to retrieve GPS location: ${err.message}`);
      }
    );
  };

  // Query Soil Telemetry
  const handleFetchSoil = async () => {
    if (latitude === '' || longitude === '' || isNaN(Number(latitude)) || isNaN(Number(longitude))) {
      setSoilError('Please enter valid numeric latitude and longitude coordinates, or click "Use Device GPS".');
      return;
    }
    setSoilLoading(true);
    setSoilError(null);
    try {
      const data = await apiService.getSoilTelemetry(Number(latitude), Number(longitude), soilDepth);
      setSoilData(data);
    } catch (err) {
      setSoilError(err.response?.data?.detail || err.message || 'Failed to query soil telemetry');
    } finally {
      setSoilLoading(false);
    }
  };

  // Run Multimodal Fusion Engine
  const handleRunFusion = async () => {
    if (!selectedDisease) {
      setFusionError('Please select a target pathology from the demonstration catalog in Step 2 before executing fusion.');
      return;
    }
    if (latitude === '' || longitude === '' || isNaN(Number(latitude)) || isNaN(Number(longitude))) {
      setFusionError('Field latitude and longitude coordinates are required to query location-specific soil telemetry.');
      return;
    }
    setFusionLoading(true);
    setFusionError(null);
    try {
      const payload = {
        crop_name: cropName,
        crop_stage: cropStage,
        latitude: Number(latitude),
        longitude: Number(longitude),
        days_to_harvest: daysToHarvest,
        co_applied_chemicals: tankMixChemicals,
        diagnosed_disease: selectedDisease,
        diagnostic_confidence: diagnosticConfidence || 0.85,
        allow_demo: true,
        imageFile: imageFile,
      };

      const result = await apiService.getFusionRecommendation(payload);
      setRecommendation(result);

      // If soil telemetry came back in fusion summary, update soilData view
      if (result.telemetry_summary && !soilData) {
        setSoilData({
          source: result.telemetry_summary.soil_source,
          status: result.telemetry_summary.soil_data_status,
          ph_water: result.telemetry_summary.soil_pH,
          soc: result.telemetry_summary.soil_organic_carbon_g_kg,
          usda_texture: result.telemetry_summary.soil_texture,
          depth: soilDepth,
        });
      }

      // Move to Step 4 automatically
      setCurrentStep(4);
    } catch (err) {
      setFusionError(err.response?.data?.detail || err.message || 'Multimodal fusion processing error');
    } finally {
      setFusionLoading(false);
    }
  };

  // Run Nearby Agro-Dealer Substitution & Sourcing
  const handleRunSubstitution = async () => {
    if (!recommendation?.treatment) {
      alert('Please run the multimodal fusion engine first to prescribe an active ingredient.');
      return;
    }

    setSubstitutionLoading(true);
    setSubstitutionError(null);

    const activeIng = recommendation.treatment.active_ingredient;
    const doseQr = recommendation.dosage_breakdown?.final_prescribed_dose || 0.8;
    const doseUnit = recommendation.dosage_breakdown?.dose_unit || 'kg/acre';
    const concCr = recommendation.treatment.reference_concentration_Cr || 75.0;

    try {
      // 1. Fetch ranked offerings
      const rankPayload = {
        latitude,
        longitude,
        crop_name: cropName,
        disease_name: selectedDisease,
        active_ingredient: activeIng,
        reference_dose_Qr: doseQr,
        reference_concentration_Cr: concCr,
        reference_dose_unit: doseUnit,
        prescribed_application_method: recommendation.treatment.application_method || 'Foliar Spray',
        field_area_acres: Number(fieldAreaAcres),
        max_distance_km: Number(searchRadiusKm),
        allow_demo: true,
      };

      const rankRes = await apiService.substituteAndRank(rankPayload);
      setSubstitutionData(rankRes);
      if (rankRes.ranked_offerings?.length > 0) {
        setSelectedOffering(rankRes.ranked_offerings[0]);
      }

      // 2. Query nearby merchants for the spatial map view
      const merchants = await apiService.getNearbyMerchants(latitude, longitude, searchRadiusKm);
      // Deduplicate merchants for map display
      const uniqueMerchants = [];
      const seen = new Set();
      merchants.forEach((m) => {
        if (!seen.has(m.merchant_id)) {
          seen.add(m.merchant_id);
          uniqueMerchants.push({
            id: m.merchant_id,
            name: m.merchant_name,
            contact_phone: m.contact_phone,
            address: m.address,
            distance_km: m.distance_km,
            is_demo: m.is_demo,
            latitude: latitude + (Math.sin(m.merchant_id * 1.5) * (m.distance_km / 111.0)),
            longitude: longitude + (Math.cos(m.merchant_id * 1.5) * (m.distance_km / (111.0 * Math.cos(latitude * Math.PI / 180)))),
          });
        }
      });
      setNearbyMerchantsList(uniqueMerchants);

      setCurrentStep(5);
    } catch (err) {
      setSubstitutionError(err.response?.data?.detail || err.message || 'Substitution engine error');
    } finally {
      setSubstitutionLoading(false);
    }
  };

  const steps = [
    { num: 1, label: 'Crop & Field' },
    { num: 2, label: 'Vision & Disease' },
    { num: 3, label: 'Soil Telemetry' },
    { num: 4, label: 'Dosage Fusion' },
    { num: 5, label: 'Dealer Sourcing' },
  ];

  return (
    <div className="space-y-8 py-6">
      {/* Wizard Step Progression Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1">
          {steps.map((s, idx) => {
            const isActive = currentStep === s.num;
            const isCompleted = currentStep > s.num;

            return (
              <React.Fragment key={s.num}>
                <button
                  type="button"
                  onClick={() => setCurrentStep(s.num)}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : isCompleted
                      ? 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                      : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                      isActive
                        ? 'bg-white text-emerald-800 font-bold'
                        : isCompleted
                        ? 'bg-emerald-200 text-emerald-900 font-bold'
                        : 'bg-slate-200 text-slate-600'
                    }`}
                  >
                    {isCompleted ? '✓' : s.num}
                  </span>
                  <span>{s.label}</span>
                </button>
                {idx < steps.length - 1 && (
                  <div className="hidden sm:block w-8 h-[2px] bg-slate-200 shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* STEP 1: CROP & FIELD SPECIFICATION */}
      {currentStep === 1 && (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sprout className="w-5 h-5 text-emerald-600" />
              Step 1: Crop Phenology & Field Area
            </h3>
            <p className="text-xs text-slate-500">
              Select the agricultural crop, current phenological growth stage, and land area.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Crop Selection */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Target Crop
              </label>
              <select
                value={cropName}
                onChange={(e) => setCropName(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                {crops.length > 0 ? (
                  crops.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name} ({c.scientific_name})
                    </option>
                  ))
                ) : (
                  <>
                    <option value="Tomato">Tomato (Solanum lycopersicum)</option>
                    <option value="Potato">Potato (Solanum tuberosum)</option>
                    <option value="Rice">Rice (Oryza sativa)</option>
                  </>
                )}
              </select>
            </div>

            {/* Phenological Stage */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Phenological Growth Stage
              </label>
              <select
                value={cropStage}
                onChange={(e) => setCropStage(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                <option value="Seedling">Seedling</option>
                <option value="Vegetative">Vegetative</option>
                <option value="Flowering">Flowering</option>
                <option value="Fruiting">Fruiting</option>
                <option value="Tillering">Tillering</option>
                <option value="Panicle Initiation">Panicle Initiation</option>
                <option value="Maturity">Maturity</option>
              </select>
            </div>

            {/* Field Area in Acres */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Field Area (Acres)
              </label>
              <input
                type="number"
                min="0.1"
                max="1000"
                step="0.1"
                value={fieldAreaAcres}
                onChange={(e) => setFieldAreaAcres(parseFloat(e.target.value) || 1.0)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 text-sm font-mono focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
              <span className="text-[11px] text-slate-400">Used to scale total chemical formulation and retail package requirements.</span>
            </div>

            {/* Days to Harvest (PHI safety check) */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Estimated Days to Harvest (PHI Check)
              </label>
              <input
                type="number"
                min="0"
                max="365"
                value={daysToHarvest}
                onChange={(e) => setDaysToHarvest(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 text-sm font-mono focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
              <span className="text-[11px] text-slate-400">Statutory Pre-Harvest Interval (PHI) verification prevents pesticide residues in harvested produce.</span>
            </div>
          </div>

          {/* Optional Tank-Mix Chemical Inputs */}
          <div className="space-y-2 pt-2">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Co-Applied Tank-Mix Partners (Optional Chemical Incompatibility Screen)
            </label>
            <input
              type="text"
              placeholder="e.g. Chlorpyrifos, Bordeaux Mixture (comma-separated)"
              value={tankMixChemicals}
              onChange={(e) => setTankMixChemicals(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
            <span className="text-[11px] text-slate-400">The engine scans for documented chemical antagonism, rapid alkaline hydrolysis, and phytotoxicity.</span>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-all"
            >
              Continue to Vision & Disease
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: VISION STREAM & DISEASE DIAGNOSIS */}
      {currentStep === 2 && (
        <div className="space-y-6">
          <DiagnosisCard
            visionStatus={visionStatus}
            supportedPathologies={supportedPathologies}
            selectedCrop={cropName}
            selectedDisease={selectedDisease}
            onSelectDisease={(dis) => {
              setSelectedDisease(dis);
              setIsManualTestPathology(true);
            }}
            imageFile={imageFile}
            onImageChange={handleImageChange}
            imagePreviewUrl={imagePreviewUrl}
            visionResult={visionResult}
            isManualTestPathology={isManualTestPathology}
          />

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
            <button
              type="button"
              onClick={() => {
                if (!selectedDisease) {
                  alert('Please select a target pathology from the demonstration catalog to evaluate the downstream pipeline.');
                  return;
                }
                setCurrentStep(3);
              }}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-all"
            >
              Continue to Soil Telemetry
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: GEOSPATIAL LOCATION & SOIL TELEMETRY */}
      {currentStep === 3 && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-emerald-600" />
                  Step 3: Geolocation & SoilGrids Telemetry
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Query 250m baseline soil chemical properties from ISRIC SoilGrids 2.0 with regional fallback.
                </p>
              </div>

              <button
                type="button"
                onClick={handleUseCurrentLocation}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold border border-emerald-200 transition-colors"
              >
                <Navigation className="w-3.5 h-3.5" />
                Use Device GPS
              </button>
            </div>

            {/* Coordinate Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">Latitude (°N)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="-90"
                  max="90"
                  placeholder="e.g. 12.5200"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">Longitude (°E)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="-180"
                  max="180"
                  placeholder="e.g. 76.9000"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700">Soil Horizon Depth</label>
                <select
                  value={soilDepth}
                  onChange={(e) => setSoilDepth(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm bg-white"
                >
                  <option value="0-5cm">0-5 cm (Topsoil / Root zone)</option>
                  <option value="5-15cm">5-15 cm</option>
                  <option value="15-30cm">15-30 cm</option>
                </select>
              </div>
            </div>

            {/* Geolocation Guidance Notice */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1">
              <span className="font-semibold text-slate-800 block">Field Geolocation Input:</span>
              <p>
                Enter your field coordinates in decimal degrees (e.g. from GPS or digital map), or click <strong>Use Device GPS</strong> to automatically populate coordinates.
              </p>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={handleFetchSoil}
                disabled={soilLoading}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-all disabled:opacity-50"
              >
                {soilLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Layers className="w-3.5 h-3.5" />}
                {soilLoading ? 'Querying ISRIC SoilGrids 2.0...' : 'Query Geospatial Soil Telemetry'}
              </button>
            </div>
          </div>

          {/* Render Soil Telemetry Card */}
          <SoilCard soilData={soilData} loading={soilLoading} error={soilError} />

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
            <button
              type="button"
              onClick={handleRunFusion}
              disabled={fusionLoading}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-all disabled:opacity-50"
            >
              {fusionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
              {fusionLoading ? 'Executing Multimodal Fusion...' : 'Execute Multimodal Fusion Engine'}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: MULTIMODAL FUSION & BOUNDED DOSAGE RECOMMENDATION */}
      {currentStep === 4 && (
        <div className="space-y-6">
          <TreatmentCard
            recommendation={recommendation}
            fieldAreaAcres={fieldAreaAcres}
            isManualTestPathology={isManualTestPathology}
          />

          {fusionError && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <strong>Fusion Error:</strong> {fusionError}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>

            {recommendation?.treatment && (
              <button
                type="button"
                onClick={handleRunSubstitution}
                disabled={substitutionLoading}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-all disabled:opacity-50"
              >
                {substitutionLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Store className="w-4 h-4" />}
                {substitutionLoading ? 'Searching Nearby Dealers...' : 'Find Agro-Dealers & Substitute Products'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* STEP 5: NEARBY AGRO-DEALER SUBSTITUTION & SOURCING */}
      {currentStep === 5 && (
        <div className="space-y-6">
          {/* Search Radius Control */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                <Sliders className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                  Agro-Dealer Search Radius (d_max)
                </span>
                <span className="text-xs text-slate-500">
                  PostGIS GiST Geodesic Spatial Search: {searchRadiusKm} km
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={searchRadiusKm}
                onChange={(e) => setSearchRadiusKm(parseFloat(e.target.value))}
                className="w-32 sm:w-48 accent-emerald-600"
              />
              <button
                type="button"
                onClick={handleRunSubstitution}
                disabled={substitutionLoading}
                className="px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold"
              >
                Refresh Radius
              </button>
            </div>
          </div>

          {/* Spatial Map View with List Fallback */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
            <GoogleMapView
              center={{ lat: latitude, lng: longitude }}
              merchants={nearbyMerchantsList}
              selectedMerchantId={selectedOffering?.merchant_id}
              onSelectMerchant={(mId) => {
                const off = substitutionData?.ranked_offerings?.find((o) => o.merchant_id === mId);
                if (off) setSelectedOffering(off);
              }}
              searchRadiusKm={searchRadiusKm}
            />
          </div>

          {/* Ranked Substitution Card */}
          <SubstitutionCard
            substitutionData={substitutionData}
            selectedOffering={selectedOffering}
            onSelectOffering={(off) => setSelectedOffering(off)}
          />

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep(4)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
              Back to Dosage Fusion
            </button>

            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm transition-all"
            >
              Print / Save Diagnostic Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
