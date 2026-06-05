import api from "./api";

const adminService = {
  getUsers: async () => {
    const res = await api.get("/admin/users");
    return res.data;
  },

  getAuditLogs: async () => {
    const res = await api.get("/admin/audit");
    return res.data;
  },

  getSystemHealth: async () => {
    const res = await api.get("/health");
    return res.data;
  }
};

export default adminService;
