import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: {
    'Accept': 'application/json',
  },
  timeout: 30000, // 30s timeout for geospatial telemetry queries
});

export const apiService = {
  // System Health
  async getHealth() {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Crops & Pathologies
  async getCrops() {
    const response = await apiClient.get('/crops');
    return response.data;
  },

  // Vision Status & Diagnosis
  async getVisionStatus() {
    const response = await apiClient.get('/vision/status');
    return response.data;
  },

  async diagnoseLeafImage(imageFile, topK = 3) {
    const formData = new FormData();
    formData.append('file', imageFile);
    const response = await apiClient.post(`/vision/diagnose?top_k=${topK}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Soil Telemetry (ISRIC SoilGrids 2.0 / Regional fallback)
  async getSoilTelemetry(latitude, longitude, depth = '0-5cm') {
    const response = await apiClient.get('/soil/telemetry', {
      params: { latitude, longitude, depth },
    });
    return response.data;
  },

  // Agronomic Fusion & Bounded Dosage Recommendation
  async getSupportedPathologies() {
    const response = await apiClient.get('/fusion/pathologies');
    return response.data;
  },

  async getFusionRecommendation(params) {
    const formData = new FormData();
    formData.append('crop_name', params.crop_name);
    formData.append('crop_stage', params.crop_stage);
    formData.append('latitude', params.latitude);
    formData.append('longitude', params.longitude);

    if (params.days_to_harvest !== undefined && params.days_to_harvest !== null && params.days_to_harvest !== '') {
      formData.append('days_to_harvest', params.days_to_harvest);
    }
    if (params.co_applied_chemicals) {
      formData.append('co_applied_chemicals', params.co_applied_chemicals);
    }
    if (params.diagnosed_disease) {
      formData.append('diagnosed_disease', params.diagnosed_disease);
    }
    if (params.diagnostic_confidence !== undefined && params.diagnostic_confidence !== null && params.diagnostic_confidence !== '') {
      formData.append('diagnostic_confidence', params.diagnostic_confidence);
    }
    if (params.allow_demo !== undefined) {
      formData.append('allow_demo', params.allow_demo);
    }
    if (params.imageFile) {
      formData.append('image', params.imageFile);
    }

    const response = await apiClient.post('/fusion/recommend', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Nearby Agro-Dealers & Substitution
  async getNearbyMerchants(latitude, longitude, maxDistanceKm = 25.0, activeIngredientId = null) {
    const params = { latitude, longitude, max_distance_km: maxDistanceKm };
    if (activeIngredientId) {
      params.active_ingredient_id = activeIngredientId;
    }
    const response = await apiClient.get('/merchants/nearby', { params });
    return response.data;
  },

  async getMerchantById(merchantId) {
    const response = await apiClient.get(`/merchants/${merchantId}`);
    return response.data;
  },

  async getMerchantProducts(merchantId) {
    const response = await apiClient.get(`/merchants/${merchantId}/products`);
    return response.data;
  },

  async getProductById(productId) {
    const response = await apiClient.get(`/merchants/products/${productId}`);
    return response.data;
  },

  async calculateSubstitution(payload) {
    const response = await apiClient.post('/merchants/calculate-substitution', payload);
    return response.data;
  },

  async substituteAndRank(payload) {
    const response = await apiClient.post('/merchants/substitute-and-rank', payload);
    return response.data;
  },
};

export default apiService;
