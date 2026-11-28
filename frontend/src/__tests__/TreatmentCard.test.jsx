import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import TreatmentCard from '../components/TreatmentCard';

describe('TreatmentCard Component Safety & Display', () => {
  const mockRecommendation = {
    recommendation_available: true,
    status: 'RECOMMENDATION_SUCCESS',
    status_message: 'Treatment recommendation generated',
    telemetry_summary: {
      crop: 'Tomato',
      disease: 'Early Blight',
      is_healthy: false,
    },
    safety_assessment: {
      is_safe_to_apply: true,
      safety_status: 'APPROVED',
      confidence_check_passed: true,
      phi_check_passed: true,
      compatibility_check_passed: true,
      verification_check_passed: true,
      warnings: [],
    },
    treatment: {
      active_ingredient: 'Mancozeb',
      registered_product_name: 'Indofil M-45',
      reference_concentration_Cr: 75.0,
      concentration_unit: '% WP',
      crop_stage: 'Vegetative',
      application_method: 'Foliar Spray',
      phi_days: 7,
      ppe_requirements: 'Chemical-resistant gloves, protective eye goggles',
      source_citation: 'CIBRC Registered Uses of Mancozeb (Item #42)',
      verification_status: 'VERIFIED',
    },
    dosage_breakdown: {
      base_dose_D0: 0.8,
      dose_unit: 'kg/acre',
      soil_factor_Fs: 1.0,
      soil_factor_status: 'Disabled (Foliar application)',
      severity_factor_Fv: 1.0,
      severity_factor_status: 'Neutral 1.0',
      raw_calculated_dose: 0.8,
      max_label_dose_cap: 1.0,
      final_prescribed_dose: 0.8,
      water_dilution_liters_per_acre: 200.0,
      is_capped_by_label_max: false,
    },
  };

  it('displays DEMONSTRATION / RESEARCH EVALUATION notice when pathology is a manual test input', () => {
    render(
      <TreatmentCard
        recommendation={mockRecommendation}
        fieldAreaAcres={2.0}
        isManualTestPathology={true}
      />
    );

    // Expect the prominent demo banner
    expect(screen.getByText(/DEMONSTRATION & RESEARCH EVALUATION ONLY/i)).toBeDefined();
    expect(screen.getByText(/strictly for demonstration and research verification, NOT an active field treatment recommendation/i)).toBeDefined();
    expect(screen.getByText(/DEMO TEST EVALUATION/i)).toBeDefined();
  });

  it('displays authoritative backend dosage rate and scaled field requirement without independent calculation', () => {
    render(
      <TreatmentCard
        recommendation={mockRecommendation}
        fieldAreaAcres={2.5}
        isManualTestPathology={false}
      />
    );

    // Rate D = 0.8 kg/acre
    expect(screen.getByText('0.8')).toBeDefined();
    expect(screen.getByText(/Authoritative Backend Rate/i)).toBeDefined();

    // Field scaled total = 0.8 * 2.5 = 2.00
    expect(screen.getByText('2.00')).toBeDefined();
    expect(screen.getByText(/Scaled: D × 2.5 acre\(s\)/i)).toBeDefined();

    // Carrier water = 200.0 L/acre * 2.5 = 500
    expect(screen.getByText('500')).toBeDefined();
  });

  it('correctly labels PEER-VERIFIED RECORD status badge for verified CIBRC entries', () => {
    render(
      <TreatmentCard
        recommendation={mockRecommendation}
        fieldAreaAcres={1.0}
        isManualTestPathology={false}
      />
    );

    expect(screen.getByText(/PEER-VERIFIED RECORD/i)).toBeDefined();
    expect(screen.getByText(/CIBRC Registered Uses of Mancozeb/i)).toBeDefined();
  });

  it('displays healthy crop notification when plant is healthy without prescribing pesticides', () => {
    const healthyRec = {
      ...mockRecommendation,
      telemetry_summary: { ...mockRecommendation.telemetry_summary, is_healthy: true },
    };

    render(
      <TreatmentCard
        recommendation={healthyRec}
        fieldAreaAcres={1.0}
      />
    );

    expect(screen.getByText(/No Chemical Pesticide Treatment Required/i)).toBeDefined();
  });

  it('displays Simple Farmer Action Plan, weather advisory, and fertilizer plan when provided', () => {
    const richRec = {
      ...mockRecommendation,
      weather_advisory: {
        weather_status: 'live',
        is_good_to_spray: true,
        advisory: 'Good weather to spray now: calm wind.',
      },
      fertilizer_recommendation: {
        product_name: 'Neem Coated Urea (46% N)',
        soil_factor_Fs: 1.15,
        soil_factor_status: 'Active (low carbon)',
        final_prescribed_dose: 40.25,
        dose_unit: 'kg/acre',
        application_method: 'Soil Application',
        instructions: 'Apply in moist soil.',
      },
      farmer_summary: {
        headline: 'Detected Tomato Early Blight.',
        what_to_do: 'Use Indofil M-45 (0.8 kg/acre).',
        how_to_mix: 'Mix 0.8 kg in 200 liters of water.',
        safety_tip: 'Wear gloves. Wait 7 days before harvest.',
        speech_text: 'Detected Tomato Early Blight.',
      },
    };

    render(<TreatmentCard recommendation={richRec} fieldAreaAcres={2.0} />);

    expect(screen.getByText(/Simple Farmer Action Plan/i)).toBeDefined();
    expect(screen.getByText(/Listen \(Read Aloud\)/i)).toBeDefined();
    expect(screen.getByText(/Good weather to spray now/i)).toBeDefined();
    expect(screen.getByText(/Soil-Adjusted Fertilizer Plan/i)).toBeDefined();
    expect(screen.getByText(/80.5 kg/i)).toBeDefined();
  });
});
