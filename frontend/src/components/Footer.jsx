import React from 'react';
import { ShieldAlert, BookOpen, ExternalLink, Info, CheckCircle } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 mt-20 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Project Academic Identity */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white font-bold text-lg">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              AgriMultimodal DT Platform
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Design Thinking Academic Capstone: <em>Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution</em>.
            </p>
            <p className="text-xs text-slate-500">
              Built on 4-Layer Architecture: EfficientNet-B0 Vision Stream, ISRIC SoilGrids 2.0 Remote Telemetry, Bounded Regulatory Fusion, and PostGIS Spatial Substitution.
            </p>
          </div>

          {/* Scientific & Regulatory Citations */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              Agronomic Standards
            </h4>
            <ul className="text-xs text-slate-400 space-y-2">
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span>Central Insecticide Board & Registration Committee (CIBRC), Govt. of India.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span>ICAR - National Bureau of Soil Survey and Land Use Planning (NBSS&LUP).</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span>University of Agricultural Sciences, Bangalore (UASB) Package of Practices.</span>
              </li>
            </ul>
          </div>

          {/* Statutory & Scientific Disclaimers */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              Statutory Research Notice
            </h4>
            <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-400 space-y-1.5">
              <p>
                <strong className="text-slate-200">1. Remote Soil Telemetry:</strong> Values are 250m resolution modeled estimates from ISRIC SoilGrids. They do not replace local laboratory soil tests or live IoT sensor grids.
              </p>
              <p>
                <strong className="text-slate-200">2. Demonstration Data:</strong> Agro-dealers and products marked with <span className="text-purple-300 font-semibold">[DEMO]</span> are simulated academic seed records for evaluation purposes.
              </p>
              <p>
                <strong className="text-slate-200">3. Chemical Safety:</strong> Always inspect the physical product label and adhere strictly to maximum statutory dosage ceilings (<span className="text-emerald-300 font-mono">D_label_max</span>) and Pre-Harvest Intervals (PHI).
              </p>
            </div>
          </div>

        </div>

        <div className="mt-8 pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 Intelligent Crop Diagnosis Research Team. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1 text-emerald-400">
              <CheckCircle className="w-3.5 h-3.5" />
              Phases 1–6 Certified
            </span>
            <span className="text-slate-600">|</span>
            <span>FastAPI & React PWA Stack</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
