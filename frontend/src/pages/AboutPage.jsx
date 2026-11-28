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
          Official Farming Guides &amp; Safety Rules
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Approved Crop Medicines &amp; Safety Guide
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed">
          All medicine and fertilizer doses shown in <strong>AgriMultimodal</strong> (Intelligent Crop Diagnosis &amp; Dosage Recommendation System) follow official Indian farming manuals (CIBRC and ICAR) so your crops, soil, and harvest stay safe.
        </p>
      </div>

      {/* Simple How Dose & Shop Match Works */}
      <section className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Scale className="w-5 h-5 text-emerald-600" />
          How We Keep Doses Safe
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-600 leading-relaxed">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="font-bold text-slate-900 text-sm">1. Safe Medicine &amp; Fertilizer Limits</h3>
            <p>
              • <strong>Never Over-Dose:</strong> We always stay under the legal maximum limit printed on official Indian pesticide labels.<br />
              • <strong>Healthy Crops Stay Chemical-Free:</strong> If your leaf is healthy, we never suggest pesticide sprays — only soil-friendly fertilizer tips.<br />
              • <strong>Wait Before Harvest:</strong> Every medicine shows the exact days you must wait before picking your crop so food stays safe.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <h3 className="font-bold text-slate-900 text-sm">2. Matching Different Shop Brands</h3>
            <p>
              • <strong>Same Medicine, Different Strength:</strong> If your local shop sells a different concentration (for example, 80% instead of 75%), we automatically adjust the grams per acre so you still use the exact safe amount.<br />
              • <strong>Best Local Shop Ranking:</strong> Nearby shops are ranked by lowest price, shortest distance from your field, and available stock.
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
              Approved Medicine Chart
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Taken from Govt. of India CIBRC label guides and ICAR / UAS Bengaluru crop manuals.
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
            5 Verified Guides
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 divide-y divide-slate-200">
            <thead className="bg-slate-50 font-semibold text-slate-900 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-3">Crop &amp; Problem</th>
                <th className="py-3 px-3">Medicine</th>
                <th className="py-3 px-3">Example Brand</th>
                <th className="py-3 px-3">Amount / Acre</th>
                <th className="py-3 px-3">Wait Before Harvest</th>
                <th className="py-3 px-3">Official Guide</th>
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

      {/* Simple Important Reminders */}
      <section className="p-6 rounded-2xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 space-y-3">
        <h3 className="font-bold text-amber-950 text-sm flex items-center gap-1.5">
          <Info className="w-4 h-4 text-amber-700" />
          Important Things to Remember
        </h3>
        <ul className="space-y-1.5 leading-relaxed text-amber-800">
          <li>
            • <strong>Soil Estimates:</strong> Soil numbers are area averages. Get a local soil lab test for exact farm soil measurements.
          </li>
          <li>
            • <strong>Sample Shop Listings:</strong> Shops marked <code>[DEMO]</code> are sample listings — please check real stock and price directly with your local dealer.
          </li>
          <li>
            • <strong>Ask an Expert When Unsure:</strong> Always read the packet label and check with your local agriculture officer if you are unsure.
          </li>
        </ul>
      </section>
    </div>
  );
}
