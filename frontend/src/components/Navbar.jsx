import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sprout, Activity, Store, BookOpen, Menu, X, ShieldAlert, Cpu } from 'lucide-react';
import apiService from '../services/api';

export default function Navbar() {
  const [health, setHealth] = useState({ status: 'checking', postgis: false });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    let mounted = true;
    apiService.getHealth()
      .then((data) => {
        if (mounted) {
          setHealth({
            status: data.status,
            postgis: Boolean(data.database?.postgis_enabled),
            version: data.version,
          });
        }
      })
      .catch((err) => {
        if (mounted) {
          setHealth({ status: 'offline', postgis: false, error: err.message });
        }
      });
    return () => { mounted = false; };
  }, []);

  const navLinks = [
    { to: '/', label: 'Overview', icon: Sprout },
    { to: '/diagnose', label: 'Diagnosis Wizard', icon: Activity },
    { to: '/merchants', label: 'Dealer Substitution', icon: Store },
    { to: '/about', label: 'Citations & Architecture', icon: BookOpen },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Academic Project Title */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-200 group-hover:scale-105 transition-transform">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 tracking-tight text-base sm:text-lg leading-tight">
                  AgriMultimodal
                </span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  DT v0.6
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Precision Crop Diagnosis & Bounded Dosage Engine
              </p>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.to;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-700 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Backend Status Diagnostic Indicator */}
          <div className="hidden lg:flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  health.status === 'healthy'
                    ? 'bg-emerald-500 animate-pulse'
                    : health.status === 'checking'
                    ? 'bg-amber-400 animate-spin'
                    : 'bg-rose-500'
                }`}
              />
              <span className="font-medium text-slate-700">
                {health.status === 'healthy' ? 'API Online' : health.status === 'checking' ? 'Connecting...' : 'API Offline'}
              </span>
              {health.postgis && (
                <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                  PostGIS
                </span>
              )}
            </div>
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="md:hidden flex items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-base font-medium ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-700 font-semibold'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                {link.label}
              </Link>
            );
          })}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Backend Status:</span>
            <span className={`font-semibold ${health.status === 'healthy' ? 'text-emerald-600' : 'text-rose-600'}`}>
              {health.status.toUpperCase()}
            </span>
          </div>
        </div>
      )}
    </header>
  );
}
