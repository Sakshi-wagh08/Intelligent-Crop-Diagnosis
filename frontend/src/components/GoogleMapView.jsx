import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation, Phone, ExternalLink, AlertCircle, Info } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function GoogleMapView({
  center = { lat: 12.9716, lng: 77.5946 },
  merchants = [],
  selectedMerchantId = null,
  onSelectMerchant = () => {},
  searchRadiusKm = 25,
}) {
  const mapContainerRef = useRef(null);
  const [mapError, setMapError] = useState(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

  useEffect(() => {
    // If no API key provided, fall back immediately to list view
    if (!apiKey) {
      setMapError('No Google Maps API Key configured (VITE_GOOGLE_MAPS_API_KEY). Showing accessible list fallback.');
      return;
    }

    // Check if google maps script is already loaded
    if (window.google && window.google.maps) {
      initMap();
      return;
    }

    // Load Google Maps script dynamically
    const scriptId = 'google-maps-script';
    let script = document.getElementById(scriptId);

    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=geometry`;
      script.async = true;
      script.defer = true;
      script.onload = () => initMap();
      script.onerror = () => {
        setMapError('Failed to load Google Maps script. Switching to fallback view.');
      };
      document.head.appendChild(script);
    } else {
      script.addEventListener('load', () => initMap());
    }

    function initMap() {
      if (!mapContainerRef.current || !window.google || !window.google.maps) return;

      try {
        const map = new window.google.maps.Map(mapContainerRef.current, {
          center: { lat: center.lat, lng: center.lng },
          zoom: 11,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
        });

        // Add farmer location marker (Blue marker)
        new window.google.maps.Marker({
          position: { lat: center.lat, lng: center.lng },
          map,
          title: 'Farmer Field Location',
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: '#2563eb',
            fillOpacity: 1,
            strokeColor: '#ffffff',
            strokeWeight: 2,
          },
        });

        // Add search radius circle
        new window.google.maps.Circle({
          strokeColor: '#059669',
          strokeOpacity: 0.8,
          strokeWeight: 1.5,
          fillColor: '#10b981',
          fillOpacity: 0.1,
          map,
          center: { lat: center.lat, lng: center.lng },
          radius: searchRadiusKm * 1000,
        });

        // Add merchant markers
        const bounds = new window.google.maps.LatLngBounds();
        bounds.extend(new window.google.maps.LatLng(center.lat, center.lng));

        merchants.forEach((m) => {
          if (m.latitude && m.longitude) {
            const marker = new window.google.maps.Marker({
              position: { lat: m.latitude, lng: m.longitude },
              map,
              title: m.name || m.merchant_name,
            });

            marker.addListener('click', () => {
              onSelectMerchant(m.id || m.merchant_id);
            });

            bounds.extend(marker.getPosition());
          }
        });

        if (merchants.length > 0) {
          map.fitBounds(bounds);
        }

        setMapLoaded(true);
      } catch (err) {
        console.error('Google Maps initialization error:', err);
        setMapError('Interactive map view unavailable. Showing accessible dealer list.');
      }
    }
  }, [apiKey, center, merchants, searchRadiusKm]);

  return (
    <div className="space-y-4">
      {/* Google Map Canvas (when active) */}
      {apiKey && !mapError && (
        <div className="relative w-full h-80 sm:h-96 rounded-xl overflow-hidden border border-slate-200 shadow-inner">
          <div ref={mapContainerRef} className="w-full h-full" />
          {!mapLoaded && (
            <div className="absolute inset-0 bg-slate-100 flex items-center justify-center text-sm text-slate-500">
              Loading spatial map view...
            </div>
          )}
        </div>
      )}

      {/* Fallback Notice when API key is missing */}
      {mapError && (
        <div className="p-3.5 rounded-lg bg-amber-50/80 border border-amber-200 flex items-start gap-2.5 text-xs text-amber-900">
          <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Spatial Map Fallback Mode:</span> Google Maps API key is not configured in environment variables. Operating in native list mode with direct navigation links.
          </div>
        </div>
      )}

      {/* Responsive Dealer Directory View */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-emerald-600" />
            Nearby Agro-Dealers ({merchants.length} Found within {searchRadiusKm} km)
          </h4>
          <span className="text-xs text-slate-500">
            Field Origin: {center.lat.toFixed(4)}, {center.lng.toFixed(4)}
          </span>
        </div>

        {merchants.length === 0 ? (
          <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center">
            <p className="text-sm text-slate-600 font-medium">No agro-dealers found within {searchRadiusKm} km radius.</p>
            <p className="text-xs text-slate-400 mt-1">Try expanding the search radius up to 50 km or adjusting field coordinates.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {merchants.map((m) => {
              const id = m.id || m.merchant_id;
              const name = m.name || m.merchant_name;
              const distance = m.distance_km !== undefined ? m.distance_km : null;
              const isSelected = selectedMerchantId === id;
              const isDemo = m.is_demo !== false;

              return (
                <div
                  key={id}
                  onClick={() => onSelectMerchant(id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer text-left ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-50/40 shadow-sm ring-1 ring-emerald-500'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-semibold text-slate-900 text-sm">{name}</span>
                        {isDemo && <StatusBadge status="demo" label="DEMO DEALER" size="xs" />}
                      </div>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">{m.address}</p>
                    </div>
                    {distance !== null && (
                      <span className="shrink-0 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        {distance} km
                      </span>
                    )}
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                    {m.contact_phone ? (
                      <a
                        href={`tel:${m.contact_phone}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-800 font-medium"
                      >
                        <Phone className="w-3.5 h-3.5" />
                        {m.contact_phone}
                      </a>
                    ) : (
                      <span className="text-slate-400">Phone not listed</span>
                    )}

                    {m.latitude && m.longitude && (
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${m.latitude},${m.longitude}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-800"
                      >
                        <Navigation className="w-3.5 h-3.5" />
                        Navigate
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
