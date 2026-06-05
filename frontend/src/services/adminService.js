import api from "./api";

const adminService = {
  async getUsers() {
    const response = await api.get(
      "/users"
    );

    return response.data;
  },

  async updateUser(id, payload) {
    const response = await api.patch(
      `/users/${id}`,
      payload
    );

    return response.data;
  },

  async getAuditLogs() {
    const response = await api.get(
      "/audit-logs"
    );

    return response.data;
  },

  async getSystemHealth() {
    const response = await api.get(
      "/health"
    );

    return response.data;
  },
};

export default adminService;
