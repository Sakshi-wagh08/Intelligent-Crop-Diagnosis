import React from 'react';
import { ShieldAlert, BookOpen, ExternalLink, Info, CheckCircle } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 mt-16 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* App Identity */}
          <div className="space-y-2.5">
            <div className="flex items-center gap-2 text-white font-bold text-lg">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              AgriMultimodal
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Intelligent Crop Diagnosis and Fertilizer/Pesticide Dosage Recommendation System — easy leaf check, safe dose guide, and nearby shop finder.
            </p>
          </div>

          {/* Trusted Farming Guides */}
          <div className="space-y-2.5">
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              Trusted Farming Guides
            </h4>
            <ul className="text-xs text-slate-400 space-y-1.5">
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span>Govt. of India Safe Pesticide Label Rules (CIBRC)</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span>Indian Council of Agricultural Research (ICAR) Guides</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span>UAS Bengaluru Crop Care Recommendations</span>
              </li>
            </ul>
          </div>

          {/* Simple Safety Rules */}
          <div className="space-y-2.5">
            <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              Important Safety Notes
            </h4>
            <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-300 space-y-1.5">
              <p>
                <strong>1. Soil &amp; Weather:</strong> Soil values are area estimates. Test soil at a local lab for exact fertilizer needs.
              </p>
              <p>
                <strong>2. Sample Shops:</strong> Shops marked <span className="text-purple-300 font-semibold">[DEMO]</span> are sample listings — confirm real stock and price at the store.
              </p>
              <p>
                <strong>3. Spray Safely:</strong> Always read the bottle label, wear gloves &amp; mask, and wait the full days before harvest.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
          <p>© 2026 Intelligent Crop Diagnosis &amp; Dosage Recommendation System</p>
          <span className="inline-flex items-center gap-1 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5" />
            Safe &amp; Simple Mode
          </span>
        </div>
      </div>
    </footer>
  );
}
