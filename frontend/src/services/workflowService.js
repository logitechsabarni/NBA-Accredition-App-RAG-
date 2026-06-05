import api from "./api";

const workflowService = {
  async executeWorkflow(payload) {
    const response = await api.post(
      "/workflow/execute",
      payload
    );

    return response.data;
  },

  async getWorkflowHistory() {
    const response = await api.get(
      "/workflow/history"
    );

    return response.data;
  },

  async getWorkflow(id) {
    const response = await api.get(
      `/workflow/${id}`
    );

    return response.data;
  },
};

export default workflowService;
