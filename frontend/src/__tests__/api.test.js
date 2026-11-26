import { describe, it, expect } from 'vitest';
import apiService from '../services/api';

describe('API Service Client Definitions', () => {
  it('exposes all required API methods across all 4 architectural streams', () => {
    // Health & System
    expect(typeof apiService.getHealth).toBe('function');

    // Crops & Pathologies
    expect(typeof apiService.getCrops).toBe('function');
    expect(typeof apiService.getSupportedPathologies).toBe('function');

    // Vision Stream
    expect(typeof apiService.getVisionStatus).toBe('function');
    expect(typeof apiService.diagnoseLeafImage).toBe('function');

    // Soil Telemetry
    expect(typeof apiService.getSoilTelemetry).toBe('function');

    // Multimodal Fusion
    expect(typeof apiService.getFusionRecommendation).toBe('function');

    // Merchant Substitution & Spatial
    expect(typeof apiService.getNearbyMerchants).toBe('function');
    expect(typeof apiService.getMerchantById).toBe('function');
    expect(typeof apiService.getMerchantProducts).toBe('function');
    expect(typeof apiService.getProductById).toBe('function');
    expect(typeof apiService.calculateSubstitution).toBe('function');
    expect(typeof apiService.substituteAndRank).toBe('function');
  });
});
