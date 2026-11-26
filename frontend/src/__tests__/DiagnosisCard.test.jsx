import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import DiagnosisCard from '../components/DiagnosisCard';

describe('DiagnosisCard Component Integrity', () => {
  it('displays "Model Training Pending" badge and transparent alert when model weights are missing', () => {
    const visionStatus = { has_active_model: false };
    render(
      <DiagnosisCard
        visionStatus={visionStatus}
        supportedPathologies={[]}
      />
    );

    // Expect "Model Training Pending" badge and alert notice
    const pendingElements = screen.getAllByText(/Model Training Pending/i);
    expect(pendingElements.length).toBeGreaterThanOrEqual(1);

    // Expect explicit alert that model training is pending and no automated detection occurred
    expect(
      screen.getByText(/The trained EfficientNet-B0 disease classifier checkpoint is currently not loaded/i)
    ).toBeDefined();

    // Must NOT display any fabricated disease detection claims
    expect(screen.queryByText(/85%/)).toBeNull();
    expect(screen.queryByText(/95%/)).toBeNull();
  });

  it('labels manual pathology selection explicitly as demonstration/testing input', () => {
    const supportedPathologies = [
      {
        crop: 'Tomato',
        disease: 'Early Blight',
        active_ingredient: 'Mancozeb',
        application_method: 'Foliar Spray',
      },
    ];
    const onSelectDisease = vi.fn();

    render(
      <DiagnosisCard
        visionStatus={{ has_active_model: false }}
        supportedPathologies={supportedPathologies}
        selectedCrop="Tomato"
        selectedDisease=""
        onSelectDisease={onSelectDisease}
      />
    );

    // Expect explicit "MANUAL TEST INPUT" label
    expect(screen.getByText(/MANUAL TEST INPUT/i)).toBeDefined();
    expect(screen.getByText(/Manual Pathology Selection/i)).toBeDefined();

    // Clicking a pathology invokes the callback
    const pathologyCard = screen.getByText(/Tomato: Early Blight/i);
    fireEvent.click(pathologyCard);
    expect(onSelectDisease).toHaveBeenCalledWith('Early Blight');
  });

  it('renders OpenCV lesion surface segmentation metrics when vision result is provided', () => {
    const visionResult = {
      severity: {
        affected_ratio: 0.125,
        severity_score: 1.25,
        scale_1_to_5: 'Moderate',
      },
    };

    render(
      <DiagnosisCard
        visionStatus={{ has_active_model: false }}
        supportedPathologies={[]}
        visionResult={visionResult}
      />
    );

    expect(screen.getByText(/OpenCV Foliar Lesion Surface Segmentation/i)).toBeDefined();
    expect(screen.getByText(/12.5%/i)).toBeDefined();
    expect(screen.getByText(/Severity Tier: Moderate/i)).toBeDefined();
  });

  it('renders live automated classification and confidence bar when visionResult has diagnosis', () => {
    const visionResult = {
      diagnosis: {
        predicted_class: 'Tomato___Early_Blight',
        crop: 'Tomato',
        disease: 'Early Blight',
        is_healthy: false,
        confidence: 0.942,
        is_confident: true,
        confidence_threshold: 0.70,
        top_k_predictions: [
          { class_name: 'Tomato___Early_Blight', confidence: 0.942 },
          { class_name: 'Tomato___Late_Blight', confidence: 0.048 },
        ],
        inference_device: 'ONNX Runtime CPU (FP16)',
      },
      severity_estimation: {
        lesion_to_leaf_ratio: 0.084,
        severity_tier: 'Low',
        severity_factor_Fv: 1.0,
      },
    };

    render(
      <DiagnosisCard
        visionStatus={{ has_active_model: true }}
        supportedPathologies={[]}
        visionResult={visionResult}
      />
    );

    expect(screen.getByText(/Automated Disease Classification/i)).toBeDefined();
    expect(screen.getByText(/Tomato: Early Blight/i)).toBeDefined();
    expect(screen.getAllByText(/94.2%/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/CONFIDENT PREDICTION/i)).toBeDefined();
    expect(screen.getByText(/Severity Tier: Low/i)).toBeDefined();
    expect(screen.getByText(/8.4%/i)).toBeDefined();
  });

  it('displays diagnostic uncertainty alert when classification confidence is below threshold', () => {
    const visionResult = {
      diagnosis: {
        predicted_class: 'Rice___Blast',
        crop: 'Rice',
        disease: 'Blast',
        is_healthy: false,
        confidence: 0.521,
        is_confident: false,
        confidence_threshold: 0.70,
        top_k_predictions: [
          { class_name: 'Rice___Blast', confidence: 0.521 },
          { class_name: 'Rice___healthy', confidence: 0.465 },
        ],
      },
    };

    render(
      <DiagnosisCard
        visionStatus={{ has_active_model: true }}
        supportedPathologies={[]}
        visionResult={visionResult}
      />
    );

    expect(screen.getByText(/LOW CONFIDENCE \/ UNCERTAIN/i)).toBeDefined();
    expect(screen.getByText(/Diagnostic Uncertainty Alert/i)).toBeDefined();
    expect(screen.getAllByText(/52.1%/i).length).toBeGreaterThanOrEqual(1);
  });
});
