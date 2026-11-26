import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, RefreshCw, Database, Sparkles, ShieldCheck, HelpCircle } from 'lucide-react';

export default function StatusBadge({ status, label, showIcon = true, size = 'sm' }) {
  const normalized = (status || '').toLowerCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  let Icon = HelpCircle;

  if (normalized.includes('live') || normalized.includes('healthy') || normalized.includes('approved') || normalized.includes('verified')) {
    colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-300';
    Icon = CheckCircle2;
  } else if (normalized.includes('cached')) {
    colorClasses = 'bg-blue-50 text-blue-800 border-blue-300';
    Icon = Database;
  } else if (normalized.includes('fallback') || normalized.includes('regional')) {
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-300';
    Icon = AlertTriangle;
  } else if (normalized.includes('demo')) {
    colorClasses = 'bg-purple-50 text-purple-800 border-purple-300';
    Icon = Sparkles;
  } else if (normalized.includes('pending') || normalized.includes('unverified') || normalized.includes('degraded')) {
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-300';
    Icon = RefreshCw;
  } else if (normalized.includes('rejected') || normalized.includes('unavailable') || normalized.includes('error')) {
    colorClasses = 'bg-rose-50 text-rose-800 border-rose-300';
    Icon = AlertCircle;
  }

  const sizeClasses = size === 'xs' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${colorClasses} ${sizeClasses}`}>
      {showIcon && <Icon className="w-3.5 h-3.5" />}
      <span>{label || status}</span>
    </span>
  );
}
