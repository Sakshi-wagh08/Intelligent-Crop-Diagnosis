import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SubstitutionCard from '../components/SubstitutionCard';

describe('SubstitutionCard Component Ranking & Safety', () => {
  const mockSubstitutionData = {
    status: 'SUBSTITUTION_AND_RANKING_SUCCESS',
    message: 'Ranked 1 eligible products',
    target_crop: 'Tomato',
    target_disease: 'Early Blight',
    reference_active_ingredient: 'Mancozeb',
    reference_dose_Qr: 0.8,
    reference_dose_unit: 'kg/acre',
    reference_concentration_Cr: 75.0,
    field_area_acres: 2.0,
    total_merchants_searched: 3,
    total_eligible_products: 1,
    demonstration_advisory: 'Simulated demonstration dealer inventory',
    ranked_offerings: [
      {
        rank: 1,
        composite_score: 0.92,
        merchant_id: 101,
        merchant_name: 'Cauvery Agro Inputs',
        contact_phone: '+91-9876543210',
        address: 'APMC Market Yard',
        distance_km: 8.4,
        product_id: 201,
        brand_name: 'Dithane M-45',
        active_ingredient: 'Mancozeb',
        concentration_Cs: 75.0,
        formulation_type: 'WP',
        package_size: '1 kg',
        unit_price: 650.0,
        stock_quantity: 12,
        registration_number: 'CIR-10294/2012',
        is_legally_registered: true,
        substitute_dose_Qs: 0.8,
        dose_unit: 'kg/acre',
        packages_needed: 2,
        estimated_total_cost: 1300.0,
        ranking_explanation: 'Lowest distance and full stock availability',
        score_breakdown: {
          price_score: 0.9,
          distance_score: 0.95,
          stock_score: 1.0,
          weights_applied: { price: 0.4, distance: 0.35, stock: 0.25 },
        },
        is_demo: true,
      },
    ],
    ineligible_candidates: [
      {
        merchant_name: 'Sri Krishna Agro',
        brand_name: 'Unregistered Generic',
        active_ingredient: 'Mancozeb',
        ineligibility_reason: 'Product lacks statutory CIBRC registration',
      },
    ],
  };

  it('renders ranked offerings with Qs, packages needed, total cost, and demo badges', () => {
    render(
      <SubstitutionCard
        substitutionData={mockSubstitutionData}
        selectedOffering={null}
        onSelectOffering={vi.fn()}
      />
    );

    expect(screen.getByText('Dithane M-45')).toBeDefined();
    expect(screen.getByText(/Cauvery Agro Inputs/i)).toBeDefined();
    expect(screen.getByText('2 Pack(s)')).toBeDefined();
    expect(screen.getByText('1300')).toBeDefined();
    expect(screen.getByText(/DEMONSTRATION SEED DATA/i)).toBeDefined();
    expect(screen.getByText(/Simulated demonstration dealer inventory/i)).toBeDefined();
  });

  it('renders ineligible candidates in an expandable accordion with specific rejection reasons', () => {
    render(
      <SubstitutionCard
        substitutionData={mockSubstitutionData}
        selectedOffering={null}
        onSelectOffering={vi.fn()}
      />
    );

    const accordionBtn = screen.getByText(/Excluded \/ Ineligible Offerings \(1\)/i);
    expect(accordionBtn).toBeDefined();

    // Expand accordion
    fireEvent.click(accordionBtn);
    expect(screen.getByText(/Unregistered Generic/i)).toBeDefined();
    expect(screen.getByText(/Product lacks statutory CIBRC registration/i)).toBeDefined();
  });
});
