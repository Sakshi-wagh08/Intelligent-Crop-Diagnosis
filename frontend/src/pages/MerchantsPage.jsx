import React, { useState, useEffect } from 'react';
import {
  Store,
  Calculator,
  Search,
  MapPin,
  Phone,
  Package,
  IndianRupee,
  Navigation,
  Sparkles,
  Info,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import apiService from '../services/api';
import StatusBadge from '../components/StatusBadge';
import GoogleMapView from '../components/GoogleMapView';

export default function MerchantsPage() {
  const [activeTab, setActiveTab] = useState('directory'); // 'directory' or 'calculator'

  // Directory Search State
  const [latitude, setLatitude] = useState(12.5200);
  const [longitude, setLongitude] = useState(76.9000);
  const [radiusKm, setRadiusKm] = useState(25.0);
  const [merchants, setMerchants] = useState([]);
  const [loadingMerchants, setLoadingMerchants] = useState(false);
  const [selectedMerchant, setSelectedMerchant] = useState(null);

  // Standalone Substitution Calculator State
  const [calcQr, setCalcQr] = useState(0.80);
  const [calcCr, setCalcCr] = useState(75.0);
  const [calcCs, setCalcCs] = useState(50.0);
  const [calcUnit, setCalcUnit] = useState('kg/acre');
  const [calcArea, setCalcArea] = useState(2.0);
  const [calcPackSize, setCalcPackSize] = useState('500 g');
  const [calcPrice, setCalcPrice] = useState(380.0);
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcError, setCalcError] = useState(null);

  // Load nearby merchants on mount
  useEffect(() => {
    fetchMerchants();
  }, [latitude, longitude, radiusKm]);

  const fetchMerchants = async () => {
    setLoadingMerchants(true);
    try {
      const data = await apiService.getNearbyMerchants(latitude, longitude, radiusKm);
      // Group products by merchant
      const merchantMap = new Map();
      data.forEach((row) => {
        if (!merchantMap.has(row.merchant_id)) {
          merchantMap.set(row.merchant_id, {
            id: row.merchant_id,
            name: row.merchant_name,
            phone: row.contact_phone,
            address: row.address,
            distance_km: row.distance_km,
            is_demo: row.is_demo,
            latitude: latitude + (Math.sin(row.merchant_id) * (row.distance_km / 111.0)),
            longitude: longitude + (Math.cos(row.merchant_id) * (row.distance_km / (111.0 * Math.cos(latitude * Math.PI / 180)))),
            products: [],
          });
        }
        if (row.product_id) {
          merchantMap.get(row.merchant_id).products.push({
            id: row.product_id,
            name: row.brand_name,
            concentration: row.concentration_Cs,
            price: row.price,
            stock: row.stock_quantity,
          });
        }
      });
      const list = Array.from(merchantMap.values());
      setMerchants(list);
      if (list.length > 0 && !selectedMerchant) {
        setSelectedMerchant(list[0]);
      }
    } catch (err) {
      console.error('Failed to query nearby merchants:', err);
    } finally {
      setLoadingMerchants(false);
    }
  };

  const handleCalculateSubstitution = async (e) => {
    e.preventDefault();
    setCalcLoading(true);
    setCalcError(null);
    try {
      const payload = {
        reference_dose_Qr: Number(calcQr),
        reference_concentration_Cr: Number(calcCr),
        substitute_concentration_Cs: Number(calcCs),
        reference_dose_unit: calcUnit,
        concentration_unit_Cr: '%',
        concentration_unit_Cs: '%',
        field_area_acres: Number(calcArea),
        package_size_str: calcPackSize,
        product_price: Number(calcPrice),
      };
      const result = await apiService.calculateSubstitution(payload);
      setCalcResult(result);
    } catch (err) {
      setCalcError(err.response?.data?.detail || err.message || 'Substitution calculation error');
    } finally {
      setCalcLoading(false);
    }
  };

  return (
    <div className="space-y-8 py-6">
      {/* Header & Academic Advisory */}
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-2">
              <Store className="w-6 h-6 text-emerald-600" />
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                Agro-Dealer Discovery & Product Substitution
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Geodesic spatial radius search (PostGIS GiST) and chemical active ingredient equivalence formulation.
            </p>
          </div>

          <StatusBadge status="demo" label="DEMONSTRATION DIRECTORY" />
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 border-b border-slate-200 pt-2">
          <button
            type="button"
            onClick={() => setActiveTab('directory')}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'directory'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Store className="w-4 h-4" />
            Nearby Dealer Directory ({merchants.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('calculator')}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'calculator'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Calculator className="w-4 h-4" />
            Active Ingredient Equivalence Calculator
          </button>
        </div>
      </div>

      {/* TAB 1: DEALER DIRECTORY & SPATIAL SEARCH */}
      {activeTab === 'directory' && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Geospatial Search Parameters (SRID 4326)
              </span>
              <button
                type="button"
                onClick={() => {
                  if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                      (pos) => {
                        setLatitude(Number(pos.coords.latitude.toFixed(4)));
                        setLongitude(Number(pos.coords.longitude.toFixed(4)));
                      },
                      (err) => alert(`GPS retrieval error: ${err.message}`)
                    );
                  }
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold border border-emerald-200"
              >
                <Navigation className="w-3.5 h-3.5" />
                Use Device GPS
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Field Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  placeholder="e.g. 12.5200"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Field Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  placeholder="e.g. 76.9000"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Search Radius: {radiusKm} km
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="5"
                    max="100"
                    step="5"
                    value={radiusKm}
                    onChange={(e) => setRadiusKm(parseFloat(e.target.value))}
                    className="w-full accent-emerald-600"
                  />
                  <button
                    type="button"
                    onClick={fetchMerchants}
                    className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white shrink-0"
                    title="Search"
                  >
                    <Search className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Map View & List Fallback */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
            <GoogleMapView
              center={{ lat: latitude, lng: longitude }}
              merchants={merchants}
              selectedMerchantId={selectedMerchant?.id}
              onSelectMerchant={(id) => {
                const found = merchants.find((m) => m.id === id);
                if (found) setSelectedMerchant(found);
              }}
              searchRadiusKm={radiusKm}
            />
          </div>

          {/* Selected Dealer Inventory Panel */}
          {selectedMerchant && (
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-slate-900 text-base">{selectedMerchant.name}</h3>
                    <StatusBadge status="demo" label="DEMO" size="xs" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{selectedMerchant.address}</p>
                </div>
                {selectedMerchant.phone && (
                  <a
                    href={`tel:${selectedMerchant.phone}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold"
                  >
                    <Phone className="w-3.5 h-3.5" />
                    Call Dealer: {selectedMerchant.phone}
                  </a>
                )}
              </div>

              {/* Stocked Commercial Products */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
                  Catalog Inventory ({selectedMerchant.products?.length || 0} Products Stocked)
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {selectedMerchant.products?.map((p) => (
                    <div key={p.id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900">{p.name}</span>
                        <span className="font-mono text-emerald-700 font-bold">₹{p.price}</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-500">
                        <span>Concentration: {p.concentration}%</span>
                        <span className={p.stock > 0 ? 'text-blue-700 font-medium' : 'text-rose-600 font-medium'}>
                          {p.stock > 0 ? `${p.stock} units available` : 'Out of Stock'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: ACTIVE INGREDIENT EQUIVALENCE CALCULATOR */}
      {activeTab === 'calculator' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Inputs Card */}
          <form onSubmit={handleCalculateSubstitution} className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Calculator className="w-5 h-5 text-emerald-600" />
              Equivalence Formulation Parameters
            </h3>
            <p className="text-xs text-slate-500">
              Calculates equivalent chemical dosage: <strong className="font-mono text-slate-700">Qs = Qr × (Cr / Cs)</strong>.
            </p>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Baseline Dose (Qr)</label>
                <input
                  type="number"
                  step="0.01"
                  value={calcQr}
                  onChange={(e) => setCalcQr(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Dose Unit</label>
                <select
                  value={calcUnit}
                  onChange={(e) => setCalcUnit(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm bg-white"
                >
                  <option value="kg/acre">kg / acre (Mass basis)</option>
                  <option value="L/acre">L / acre (Volume basis)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Ref. Concentration (Cr %)</label>
                <input
                  type="number"
                  step="0.1"
                  value={calcCr}
                  onChange={(e) => setCalcCr(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Sub. Concentration (Cs %)</label>
                <input
                  type="number"
                  step="0.1"
                  value={calcCs}
                  onChange={(e) => setCalcCs(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Field Area (Acres)</label>
                <input
                  type="number"
                  step="0.1"
                  value={calcArea}
                  onChange={(e) => setCalcArea(parseFloat(e.target.value) || 1.0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Package Size</label>
                <input
                  type="text"
                  value={calcPackSize}
                  onChange={(e) => setCalcPackSize(e.target.value)}
                  placeholder="e.g. 500 g, 1 kg, 500 mL"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm"
                />
              </div>

              <div className="col-span-2">
                <label className="block font-semibold text-slate-700 mb-1">Unit Package Retail Price (₹)</label>
                <input
                  type="number"
                  step="1"
                  value={calcPrice}
                  onChange={(e) => setCalcPrice(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={calcLoading}
              className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {calcLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Calculator className="w-3.5 h-3.5" />}
              Calculate Substitute Equivalent
            </button>
          </form>

          {/* Results Display Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-base">Mathematical Dosage Output</h3>

            {calcError && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs">
                {calcError}
              </div>
            )}

            {calcResult ? (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Substitute Dose (Qs)</span>
                    <span className="text-xs font-mono font-bold text-emerald-800">
                      Ratio: {calcResult.concentration_ratio.toFixed(2)}x
                    </span>
                  </div>
                  <div className="text-3xl font-extrabold text-emerald-800 font-mono">
                    {calcResult.substitute_dose_Qs} {calcResult.dose_unit}
                  </div>
                  <span className="text-[11px] text-slate-500 block">
                    Total required for {calcResult.field_area_acres} acres: <strong>{calcResult.total_substitute_quantity} {calcResult.dose_unit.split('/')[0]}</strong>
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-slate-500">Packages Needed</span>
                    <p className="text-lg font-bold text-slate-900 font-mono mt-0.5">
                      {calcResult.packages_needed !== null ? `${calcResult.packages_needed} Pack(s)` : '—'}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-slate-500">Estimated Total Cost</span>
                    <p className="text-lg font-bold text-slate-900 font-mono mt-0.5">
                      {calcResult.estimated_total_cost !== null ? `₹${calcResult.estimated_total_cost}` : '—'}
                    </p>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-600">
                  <strong className="text-slate-800 block mb-1">Explanation:</strong>
                  <p className="leading-relaxed">{calcResult.explanation}</p>
                </div>
              </div>
            ) : (
              <div className="p-8 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
                Enter parameters on the left and click calculate to view active ingredient dosage equivalence.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
