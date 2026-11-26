import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sprout,
  Camera,
  Layers,
  ShieldCheck,
  Store,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  FileText,
  Award,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

export default function HomePage() {
  const tiers = [
    {
      number: '01',
      title: 'Vision Stream & Lesion Severity',
      icon: Camera,
      badge: 'EfficientNet-B0 & OpenCV',
      description:
        'Analyzes foliar photographs to isolate infected leaf area and calculate severity surface ratios (S_severity) without hallucinating unverified diagnoses.',
    },
    {
      number: '02',
      title: 'Geospatial Soil Telemetry',
      icon: Layers,
      badge: 'ISRIC SoilGrids 2.0 & PostGIS',
      description:
        'Fetches 250m resolution baseline soil chemistry: pH, soil organic carbon, USDA texture, and available water capacity (AWC) with ICAR regional benchmark fallbacks.',
    },
    {
      number: '03',
      title: 'Bounded Dosage Fusion Engine',
      icon: ShieldCheck,
      badge: 'CIBRC & ICAR Certified',
      description:
        'Formulates statutory bounded chemical dosage D = min(D₀ × Fₛ × Fᵥ, D_label_max) with 4 safety gates: confidence ≥70%, PHI interval, and chemical compatibility.',
    },
    {
      number: '04',
      title: 'Localized Dealer Substitution',
      icon: Store,
      badge: 'PostGIS GiST & Ranking',
      description:
        'Calculates active ingredient product equivalence Qs = Qr × (Cr / Cs), checks local agro-dealer inventory, and ranks alternatives across price, distance, and stock.',
    },
  ];

  return (
    <div className="space-y-16 py-6 sm:py-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-900 via-teal-900 to-slate-900 text-white p-8 sm:p-14 shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-semibold backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5" />
            Design Thinking Academic Capstone · Phases 1–6 Complete
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
            Precision Crop Diagnosis & Bounded Dosage Recommendation
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
            A multimodal precision agriculture platform integrating deep vision analytics, satellite soil telemetry, regulatory safety enforcement, and localized agro-dealer substitution.
          </p>

          <div className="flex items-center gap-4 pt-2 flex-wrap">
            <Link
              to="/diagnose"
              className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-emerald-950 font-bold text-sm transition-all shadow-lg shadow-emerald-500/20 hover:scale-[1.02]"
            >
              Start Diagnosis Wizard
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/merchants"
              className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm border border-white/20 transition-all backdrop-blur-md"
            >
              Agro-Dealer Explorer
            </Link>
          </div>
        </div>

        {/* Ambient background decoration */}
        <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* 4-Tier Architecture Overview */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Four-Layer Multimodal Architecture
          </h2>
          <p className="text-sm text-slate-500">
            Engineered strictly according to IEEE system specifications and agronomic standards.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {tiers.map((t) => {
            const Icon = t.icon;
            return (
              <div
                key={t.number}
                className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs hover:border-emerald-300 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      TIER {t.number}
                    </span>
                    <Icon className="w-5 h-5 text-slate-400" />
                  </div>

                  <h3 className="font-bold text-slate-900 text-base">{t.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{t.description}</p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-500 block truncate">
                    {t.badge}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* System Integrity & Regulatory Highlights */}
      <section className="rounded-3xl bg-slate-900 text-slate-200 p-8 sm:p-12 border border-slate-800">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-white text-base">CIBRC Dosage Ceilings</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every chemical dosage recommendation is hard-capped by statutory label ceilings (D_label_max). Over-dosage is mathematically prohibited to protect crops and groundwater.
            </p>
          </div>

          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Award className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-white text-base">Zero Fabricated Diagnoses</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              When deep learning model weights are not loaded on the server, the system explicitly reports pending status rather than hallucinating fake disease diagnoses or probabilities.
            </p>
          </div>

          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
              <Store className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-white text-base">Spatial PostGIS GiST Radius</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Nearby agro-dealers are queried via spatial geodesic indices (SRID 4326), computing required retail packages and total cost based on active ingredient mass equivalence.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
