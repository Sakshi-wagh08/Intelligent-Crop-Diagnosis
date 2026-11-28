import React, { useState } from 'react';
import {
  Store,
  MapPin,
  Phone,
  Package,
  IndianRupee,
  Layers,
  Sparkles,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function SubstitutionCard({
  substitutionData = null,
  selectedOffering = null,
  onSelectOffering = () => {},
}) {
  const [showIneligible, setShowIneligible] = useState(false);

  if (!substitutionData) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
        <h3 className="font-bold text-slate-900 flex items-center gap-2">
          <Store className="w-5 h-5 text-emerald-600" />
          Agro-Dealer Product Substitution & Ranking
        </h3>
        <p className="text-xs text-slate-500">
          Dealer discovery and product substitution calculation will execute based on the prescribed active ingredient and farmer coordinates.
        </p>
      </div>
    );
  }

  const {
    status,
    message,
    target_crop,
    target_disease,
    reference_active_ingredient,
    reference_dose_Qr,
    reference_dose_unit,
    reference_concentration_Cr,
    field_area_acres,
    total_merchants_searched = 0,
    total_eligible_products = 0,
    ranked_offerings = [],
    ineligible_candidates = [],
    demonstration_advisory = '',
  } = substitutionData;

  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-900 text-base sm:text-lg flex items-center gap-2">
              <Store className="w-5 h-5 text-emerald-600" />
              Nearby Shops &amp; Product Options
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Recommended Medicine: <strong className="text-slate-800">{reference_active_ingredient}</strong> ({reference_dose_Qr} {reference_dose_unit} at {reference_concentration_Cr}% strength)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <StatusBadge status="demo" label="DEMONSTRATION SEED DATA" />
        </div>
      </div>

      {/* Demonstration Data Warning Advisory */}
      <div className="p-3.5 rounded-xl bg-purple-50/80 border border-purple-200 text-xs text-purple-900 space-y-1">
        <div className="flex items-center gap-1.5 font-bold text-purple-950">
          <Sparkles className="w-3.5 h-3.5 text-purple-700" />
          Sample Shop Listings Notice:
        </div>
        <p className="leading-relaxed">
          {demonstration_advisory ||
            'Shops, stock counts, and prices shown here are sample listings. Always confirm live stock and price directly with the dealer.'}
        </p>
      </div>

      {/* Summary Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <span className="text-slate-500">Shops Checked</span>
          <p className="text-lg font-bold text-slate-900 font-mono mt-0.5">{total_merchants_searched}</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <span className="text-slate-500">Matching Products</span>
          <p className="text-lg font-bold text-emerald-700 font-mono mt-0.5">{total_eligible_products}</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <span className="text-slate-500">Adjusted for Brand</span>
          <p className="text-xs font-semibold text-slate-800 mt-1 truncate" title="Qs = Qr * (Cr / Cs)">
            Same Active Dose
          </p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <span className="text-slate-500">Your Field Size</span>
          <p className="text-lg font-bold text-slate-900 font-mono mt-0.5">{field_area_acres} Acre(s)</p>
        </div>
      </div>

      {/* Ranked Offerings List */}
      <div className="space-y-4">
        <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Best Local Options (Ranked by Price, Distance &amp; Stock)
        </h4>

        {ranked_offerings.length === 0 ? (
          <div className="p-8 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
            <AlertCircle className="w-8 h-8 text-amber-500 mx-auto" />
            <p className="text-sm font-semibold text-slate-800">No Matching Products Found Nearby</p>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              No shops within your search distance currently have this product in stock. Try increasing the search distance or check the excluded items below.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {ranked_offerings.map((item) => {
              const isSelected = selectedOffering?.product_id === item.product_id;

              return (
                <div
                  key={`${item.merchant_id}-${item.product_id}`}
                  onClick={() => onSelectOffering(item)}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-50/30 shadow-md ring-1 ring-emerald-500'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                  }`}
                >
                  {/* Top Bar: Rank, Product Brand, Composite Score */}
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                          item.rank === 1
                            ? 'bg-amber-400 text-amber-950 shadow-xs'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        #{item.rank}
                      </span>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h5 className="font-bold text-slate-900 text-base">{item.brand_name}</h5>
                          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                            {item.concentration_Cs}% {item.formulation_type}
                          </span>
                          <StatusBadge status="demo" label="DEMO" size="xs" />
                        </div>
                        <p className="text-xs text-slate-500">
                          Active Ingredient: {item.active_ingredient} · Reg #{item.registration_number}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-xs text-slate-400 block">Match Score</span>
                      <span className="text-lg font-bold text-emerald-800 font-mono">
                        {(item.composite_score * 100).toFixed(1)} / 100
                      </span>
                    </div>
                  </div>

                  {/* Substitution & Quantity Metrics */}
                  <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-500">Dose for This Brand</span>
                      <p className="text-base font-bold text-slate-900 font-mono mt-0.5">
                        {item.substitute_dose_Qs} {item.dose_unit}
                      </p>
                      <span className="text-[10px] text-slate-400">Adjusted for brand strength</span>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-500">Packs to Buy</span>
                      <p className="text-base font-bold text-emerald-800 font-mono mt-0.5">
                        {item.packages_needed} Pack(s)
                      </p>
                      <span className="text-[10px] text-slate-400">Pack Size: {item.package_size}</span>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-500">Total Cost</span>
                      <p className="text-base font-bold text-slate-900 font-mono mt-0.5 flex items-baseline">
                        <span className="text-xs font-sans mr-0.5">₹</span>
                        {item.estimated_total_cost}
                      </p>
                      <span className="text-[10px] text-slate-400">₹{item.unit_price} / pack</span>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-500">In Stock</span>
                      <p className="text-base font-bold text-blue-700 font-mono mt-0.5">
                        {item.stock_quantity} in stock
                      </p>
                      <span className="text-[10px] text-slate-400">Packs available at shop</span>
                    </div>
                  </div>

                  {/* Dealer Info & Distance */}
                  <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600 flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <Store className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-semibold text-slate-800">{item.merchant_name}</span>
                      <span className="text-slate-400">·</span>
                      <span className="text-slate-500 truncate max-w-xs">{item.address}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {item.distance_km} km away
                      </span>

                      {item.contact_phone && (
                        <a
                          href={`tel:${item.contact_phone}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-800 font-medium"
                        >
                          <Phone className="w-3.5 h-3.5" />
                          {item.contact_phone}
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Why Ranked Here */}
                  <div className="mt-2.5 p-2.5 rounded-lg bg-slate-50 text-[11px] text-slate-600 border border-slate-100">
                    <span className="font-semibold text-slate-700">Why Ranked Here: </span>
                    <span>{item.ranking_explanation}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Ineligible Candidates Collapsible Accordion */}
      {ineligible_candidates.length > 0 && (
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <button
            type="button"
            onClick={() => setShowIneligible(!showIneligible)}
            className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 flex items-center justify-between text-xs font-semibold text-slate-700 transition-colors"
          >
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-slate-500" />
              <span>Excluded / Ineligible Offerings ({ineligible_candidates.length})</span>
            </div>
            {showIneligible ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showIneligible && (
            <div className="p-4 space-y-2.5 bg-white divide-y divide-slate-100">
              {ineligible_candidates.map((c, idx) => (
                <div key={idx} className="pt-2 first:pt-0 text-xs flex items-start justify-between gap-3">
                  <div>
                    <span className="font-semibold text-slate-900">{c.brand_name}</span>
                    <span className="text-slate-500 ml-1">({c.merchant_name})</span>
                    <p className="text-[11px] text-rose-700 font-medium mt-0.5">
                      Reason: {c.ineligibility_reason}
                    </p>
                  </div>
                  {c.distance_km && (
                    <span className="text-slate-400 shrink-0 text-[11px]">{c.distance_km} km</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
