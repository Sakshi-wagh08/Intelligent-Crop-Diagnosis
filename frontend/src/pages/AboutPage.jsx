import React from 'react';
import {
  BookOpen,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Layers,
  Sparkles,
  Info,
  Scale,
  Award,
} from 'lucide-react';

export default function AboutPage() {
  const verifiedTreatments = [
    {
      crop: 'Tomato',
      disease: 'Early Blight',
      active_ingredient: 'Mancozeb',
      product: 'Indofil M-45',
      concentration: '75% WP',
      dose: '0.80 kg / acre',
      phi: 7,
      citation: 'CIBRC Registered Uses of Mancozeb (Item #42); UAS Bangalore Package of Practices for Tomato (2020, p. 114)',
    },
    {
      crop: 'Tomato',
      disease: 'Late Blight',
      active_ingredient: 'Metalaxyl-M + Mancozeb',
      product: 'Ridomil Gold 68 WG',
      concentration: '68% WG (4% + 64%)',
      dose: '0.60 kg / acre',
      phi: 7,
      citation: 'CIBRC Registered Uses of Metalaxyl-M + Mancozeb; ICAR-IIHR Tomato Disease Management Guidelines (2021)',
    },
    {
      crop: 'Potato',
      disease: 'Late Blight',
      active_ingredient: 'Mancozeb',
      product: 'Dithane M-45',
      concentration: '75% WP',
      dose: '0.90 kg / acre',
      phi: 7,
      citation: 'CIBRC Registered Uses of Mancozeb (Item #42); ICAR-CPRI Shimla Late Blight Technical Bulletin (2019, p. 28)',
    },
    {
      crop: 'Rice',
      disease: 'Blast (Pyricularia oryzae)',
      active_ingredient: 'Tricyclazole',
      product: 'Beam 75 WP',
      concentration: '75% WP',
      dose: '0.12 kg / acre',
      phi: 21,
      citation: 'CIBRC Registered Uses of Tricyclazole; ICAR-NRRI Rice Pathology Manual (2020, p. 55)',
    },
    {
      crop: 'Rice',
      disease: 'Brown Spot',
      active_ingredient: 'Propiconazole',
      product: 'Tilt 25 EC',
      concentration: '25% EC',
      dose: '0.20 L / acre',
      phi: 30,
      citation: 'CIBRC Registered Uses of Propiconazole; UAS Dharwad Package of Practices for Paddy (2021, p. 82)',
    },
  ];

  return (
    <div className="space-y-12 py-6 sm:py-10 max-w-5xl mx-auto">
      {/* Header */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
          <BookOpen className="w-3.5 h-3.5" />
          Academic Capstone Methodology & Citations
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          System Specifications & Agronomic Evidence
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed">
          Design Thinking Project Title: <em>Multimodal Data Fusion for Precision Agricultural Chemical Dosages with Dynamic Localized Merchant Substitution</em>.
        </p>
      </div>

      {/* Mathematical Formulations Section */}
      <section className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Scale className="w-5 h-5 text-emerald-600" />
          Mathematical Principles & Governing Equations
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-600 leading-relaxed">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="font-bold text-slate-900 text-sm">1. Bounded Dosage Formulation</h3>
            <div className="font-mono text-emerald-800 font-bold text-sm bg-white p-2.5 rounded-lg border border-slate-200">
              D = min(D₀ × Fₛ × Fᵥ, D_label_max)
            </div>
            <p>
              • <strong>D₀:</strong> Base statutory active ingredient dosage for targeted crop phenology.<br />
              • <strong>Fₛ:</strong> Soil correction factor (1.00 for foliar applied fungicides).<br />
              • <strong>Fᵥ:</strong> Severity factor. Set strictly to 1.00 as chemical active ingredient escalation is prohibited by CIBRC. Carrier water volume is scaled +15% instead.<br />
              • <strong>D_label_max:</strong> Statutory upper legal bound preventing phytotoxicity and residue accumulation.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="font-bold text-slate-900 text-sm">2. Active Ingredient Mass Equivalence</h3>
            <div className="font-mono text-emerald-800 font-bold text-sm bg-white p-2.5 rounded-lg border border-slate-200">
              Qs = Qr × (Cr / Cs)
            </div>
            <p>
              • <strong>Qr, Cr:</strong> Reference dosage and concentration (%) of baseline product.<br />
              • <strong>Qs, Cs:</strong> Required dosage and concentration (%) of substitute commercial product.<br />
              • <strong>Package Estimation:</strong> Ceiled count: <code>⌈(Qs × Acres) / Package Size⌉</code>.<br />
              • <strong>Ranking Score:</strong> Weighted utility across affordability (40%), proximity (35%), and stock (25%).
            </p>
          </div>
        </div>
      </section>

      {/* Verified Agronomic Knowledge Base Table */}
      <section className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Award className="w-5 h-5 text-emerald-600" />
              Verified Agronomic Treatment Catalog
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Strictly peer-verified from CIBRC registered pesticide schedules and ICAR / UAS Bangalore agronomic manuals.
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
            5 Verified Pathologies
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 divide-y divide-slate-200">
            <thead className="bg-slate-50 font-semibold text-slate-900 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-3">Crop & Disease</th>
                <th className="py-3 px-3">Active Chemical</th>
                <th className="py-3 px-3">Registered Product</th>
                <th className="py-3 px-3">Prescribed Rate</th>
                <th className="py-3 px-3">PHI</th>
                <th className="py-3 px-3">Statutory Source Citation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {verifiedTreatments.map((t, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-3 font-semibold text-slate-900">
                    {t.crop} — {t.disease}
                  </td>
                  <td className="py-3 px-3">{t.active_ingredient}</td>
                  <td className="py-3 px-3">
                    <span className="font-medium text-slate-800">{t.product}</span> ({t.concentration})
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-700">{t.dose}</td>
                  <td className="py-3 px-3 font-bold text-slate-800">{t.phi} Days</td>
                  <td className="py-3 px-3 text-slate-500 text-[11px] leading-relaxed max-w-xs">
                    {t.citation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Disclaimers & Ethics */}
      <section className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 space-y-3">
        <h3 className="font-bold text-amber-950 text-sm flex items-center gap-1.5">
          <Info className="w-4 h-4 text-amber-700" />
          Academic & Legal Disclaimers
        </h3>
        <ul className="space-y-1.5 leading-relaxed text-amber-800">
          <li>
            • <strong>No Unsubstantiated Machine Learning Diagnoses:</strong> When trained weights are absent from <code>ml_models/weights/</code>, the platform transparently indicates pending status rather than outputting simulated probabilities.
          </li>
          <li>
            • <strong>SoilGrids 2.0 Limitations:</strong> Properties represent 250m machine-learning derived estimates. They are intended for regional baseline characterization and cannot replace certified laboratory soil chemistry tests.
          </li>
          <li>
            • <strong>Simulated Dealer Data:</strong> Dealers and stock records marked with <code>[DEMO]</code> are seeded for software evaluation and do not reflect real-time retail inventory.
          </li>
        </ul>
      </section>
    </div>
  );
}
