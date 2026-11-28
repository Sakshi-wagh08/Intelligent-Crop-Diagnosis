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
      number: 'STEP 01',
      title: 'Check Leaf Photo',
      icon: Camera,
      badge: 'Photo Check',
      description:
        'Take or upload a photo of 1 plant leaf to check if the plant is healthy or has a disease.',
    },
    {
      number: 'STEP 02',
      title: 'Check Field Soil & Weather',
      icon: Layers,
      badge: 'Town or GPS',
      description:
        'Automatically checks soil type, nutrients, and rain/wind forecast for your village or town.',
    },
    {
      number: 'STEP 03',
      title: 'Safe Dose & Mixing Guide',
      icon: ShieldCheck,
      badge: 'Govt-Safe Limits',
      description:
        'Gives the exact safe amount of medicine or fertilizer to use per acre, how much water to mix, and when it is safe to harvest.',
    },
    {
      number: 'STEP 04',
      title: 'Find Nearby Agro-Shops',
      icon: Store,
      badge: 'Map & Prices',
      description:
        'Shows nearby shops on a map, compares prices and stock, and adjusts the dose if a shop sells a different strength.',
    },
  ];

  return (
    <div className="space-y-14 py-6 sm:py-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-900 via-teal-900 to-slate-900 text-white p-8 sm:p-14 shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-6">
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
            Check Your Crop &amp; Get Safe Treatment Advice
          </h1>

          <p className="text-sm sm:text-base text-slate-200 leading-relaxed max-w-2xl">
            Take a leaf photo, pick your town or GPS, and get simple step-by-step medicine, fertilizer, weather, and nearby shop guidance.
          </p>

          <div className="flex items-center gap-4 pt-2 flex-wrap">
            <Link
              to="/diagnose"
              className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-emerald-950 font-bold text-sm transition-all shadow-lg shadow-emerald-500/20 hover:scale-[1.02]"
            >
              Check My Crop Now
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/merchants"
              className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm border border-white/20 transition-all backdrop-blur-md"
            >
              Find Nearby Shops
            </Link>
          </div>
        </div>

        {/* Ambient background decoration */}
        <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* 4 Simple Steps Overview */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            How It Works in 4 Easy Steps
          </h2>
          <p className="text-sm text-slate-500">
            Simple guidance made for everyday farming.
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
                      {t.number}
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

      {/* Safety Highlights */}
      <section className="rounded-3xl bg-slate-900 text-slate-200 p-8 sm:p-12 border border-slate-800">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-white text-base">Safe Medicine Limits</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Never suggests more medicine than the legal safe limit, protecting your crop, soil, and harvest.
            </p>
          </div>

          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Award className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-white text-base">No Guessing When Unsure</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              If a photo is blurry or unclear, it will warn you instead of giving wrong spray advice, and healthy crops never get pesticide sprays.
            </p>
          </div>

          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
              <Store className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-white text-base">Easy Local Shop Match</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Shows shops near you on a map and tells you exactly how many packs to buy and their total cost.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
