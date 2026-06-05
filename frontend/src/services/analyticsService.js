import api from "./api";

const analyticsService = {
  async getDashboard() {
    const response = await api.get(
      "/analytics/dashboard"
    );

    return response.data;
  },

  async getReadiness() {
    const response = await api.get(
      "/analytics/readiness"
    );

    return response.data;
  },

  async getAttainmentTrend() {
    const response = await api.get(
      "/analytics/attainment/trend"
    );

    return response.data;
  },

  async getCOPOAnalytics() {
    const response = await api.get(
      "/analytics/co-po"
    );

    return response.data;
  },
};

export default analyticsService;
