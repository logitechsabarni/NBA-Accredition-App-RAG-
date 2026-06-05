import api from "./api";

const chatService = {
  async sendMessage(message) {
    const response = await api.post(
      "/chat/message",
      {
        message,
      }
    );

    return response.data;
  },

  async getHistory() {
    const response = await api.get(
      "/chat/history"
    );

    return response.data;
  },

  async clearHistory() {
    const response = await api.delete(
      "/chat/history"
    );

    return response.data;
  },
};

export default chatService;
