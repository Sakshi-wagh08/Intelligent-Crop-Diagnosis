import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import SoilCard from '../components/SoilCard';

describe('SoilCard Component Integrity & Disclaimers', () => {
  const mockSoilData = {
    source: 'ISRIC SoilGrids 2.0',
    depth: '0-5cm',
    ph_water: 6.45,
    soc: 8.2,
    sand: 62,
    clay: 22,
    usda_texture: 'Sandy Clay Loam',
    awc: 0.142,
    status: 'live',
  };

  it('renders soil telemetry properties accurately from backend data', () => {
    render(<SoilCard soilData={mockSoilData} />);

    expect(screen.getByText('6.45')).toBeDefined();
    expect(screen.getByText('8.2')).toBeDefined();
    expect(screen.getByText('Sandy Clay Loam')).toBeDefined();
    expect(screen.getByText('0.142')).toBeDefined();
    expect(screen.getByText(/ISRIC SoilGrids \(Live\)/i)).toBeDefined();
  });

  it('renders mandatory educational disclaimers regarding modeled 250m resolution', () => {
    render(<SoilCard soilData={mockSoilData} />);

    expect(screen.getByText(/Soil Telemetry Scientific Notes:/i)).toBeDefined();
    expect(screen.getByText(/250m resolution spatial machine learning estimates/i)).toBeDefined();
    expect(screen.getByText(/Available Water Capacity \(AWC\) indicates soil hydraulic storage capacity/i)).toBeDefined();
  });

  it('gracefully renders fallback or unavailable notice when soil telemetry is absent', () => {
    render(<SoilCard soilData={null} error="Coordinates outside regional benchmark coverage" />);

    expect(screen.getByText(/Data Unavailable/i)).toBeDefined();
    expect(screen.getByText(/Coordinates outside regional benchmark coverage/i)).toBeDefined();
  });
});
