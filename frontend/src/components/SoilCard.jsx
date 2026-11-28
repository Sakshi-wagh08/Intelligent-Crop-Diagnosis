import React from 'react';
import { Layers, Droplets, FlaskConical, Gauge, Compass, Info, AlertTriangle, ShieldCheck } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function SoilCard({ soilData, loading = false, error = null }) {
  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-6 w-48 bg-slate-200 rounded"></div>
          <div className="h-5 w-24 bg-slate-200 rounded-full"></div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-slate-100 rounded-xl"></div>
          ))}
        </div>
        <div className="h-12 bg-slate-100 rounded-xl"></div>
      </div>
    );
  }

  if (error || !soilData) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-600" />
            Geospatial Soil Telemetry
          </h3>
          <StatusBadge status="unavailable" label="Data Unavailable" />
        </div>
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <p>
            {error || 'Soil telemetry data has not been queried yet. Enter field coordinates or use GPS to fetch geospatial soil properties.'}
          </p>
        </div>
      </div>
    );
  }

  const params = soilData.parameters || {};
  const source = soilData.telemetry_source || soilData.source || 'ISRIC SoilGrids 2.0';
  const depth = soilData.depth || '0-5cm';
  const ph_water = soilData.ph_water ?? params.pH ?? null;
  const soc = soilData.soc ?? params.organic_carbon_g_kg ?? null;
  const nitrogen = soilData.nitrogen ?? params.nitrogen_g_kg ?? null;
  const sand = soilData.sand ?? params.sand_fraction_percent ?? null;
  const silt = soilData.silt ?? params.silt_fraction_percent ?? null;
  const clay = soilData.clay ?? params.clay_fraction_percent ?? null;
  const usda_texture = soilData.usda_texture ?? params.soil_texture_class ?? 'Unknown';
  const awc = soilData.awc ?? params.water_retention?.available_water_capacity_percent ?? params.soil_moisture_estimate ?? null;
  const status = soilData.data_status || soilData.status || 'live';
  const disclaimers = soilData.disclaimers || (soilData.advisory_notice ? [soilData.advisory_notice] : []);

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-900 text-base sm:text-lg flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-600" />
              Field Soil Summary
            </h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              Depth: {depth}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Source: <strong className="text-slate-700">{source}</strong>
          </p>
        </div>

        <StatusBadge
          status={status}
          label={
            status === 'live'
              ? 'ISRIC SoilGrids (Live)'
              : status === 'cached'
              ? 'Spatial Cache'
              : status === 'fallback'
              ? 'ICAR Regional Benchmark'
              : 'Soil Telemetry'
          }
        />
      </div>

      {/* Grid of Soil Properties */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Soil pH */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Soil pH (Acidity)</span>
            <FlaskConical className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {ph_water !== null ? Number(ph_water).toFixed(2) : '—'}
            </span>
            <span className="text-xs text-slate-500 font-medium">pH</span>
          </div>
          <span className="text-[11px] text-slate-500 block mt-0.5">
            {ph_water < 6.0 ? 'Slightly Acidic' : ph_water > 7.5 ? 'Alkaline' : 'Balanced / Neutral'}
          </span>
        </div>

        {/* Soil Organic Carbon */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Organic Carbon</span>
            <Gauge className="w-3.5 h-3.5 text-teal-600" />
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {soc !== null ? Number(soc).toFixed(1) : '—'}
            </span>
            <span className="text-xs text-slate-500 font-medium">g / kg</span>
          </div>
          <span className="text-[11px] text-slate-500 block mt-0.5">
            {soc < 5 ? 'Low Organic Matter' : soc > 10 ? 'Rich Organic Matter' : 'Moderate Organic Matter'}
          </span>
        </div>

        {/* Soil Type */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Soil Type</span>
            <Compass className="w-3.5 h-3.5 text-amber-600" />
          </div>
          <div className="mt-1">
            <span className="text-sm font-bold text-slate-900 block truncate" title={usda_texture}>
              {usda_texture || 'Loam'}
            </span>
            <span className="text-[11px] text-slate-500 block mt-0.5">
              Sand {sand || 0}% · Clay {clay || 0}%
            </span>
          </div>
        </div>

        {/* Water Holding Capacity */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Water Holding</span>
            <Droplets className="w-3.5 h-3.5 text-blue-600" />
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {awc !== null ? Number(awc).toFixed(3) : '—'}
            </span>
            <span className="text-xs text-slate-500 font-medium">cm³/cm³</span>
          </div>
          <span className="text-[11px] text-slate-500 block mt-0.5">
            Moisture storage capacity
          </span>
        </div>
      </div>

      {/* Disclaimers & Soil Fact Callout */}
      <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-amber-950">
          <Info className="w-3.5 h-3.5 text-amber-700" />
          Soil Telemetry Scientific Notes:
        </div>
        <p className="text-amber-800 leading-relaxed">
          • Soil properties are 250m resolution spatial machine learning estimates from ISRIC SoilGrids. They model baseline horizons and are not real-time in-situ IoT sensor telemetry.
        </p>
        <p className="text-amber-800 leading-relaxed">
          • Available Water Capacity (AWC) indicates soil hydraulic storage capacity between field capacity and wilting point, not current moisture level. Total Nitrogen is not equivalent to readily plant-available mineral nitrogen (NO₃⁻/NH₄⁺).
        </p>
      </div>
    </div>
  );
}
