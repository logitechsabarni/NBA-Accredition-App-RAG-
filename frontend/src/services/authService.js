import api from "./api";

const authService = {
  async login(email, password) {
    const response = await api.post(
      "/auth/login",
      {
        email,
        password,
      }
    );

    return response.data;
  },

  async register(payload) {
    const response = await api.post(
      "/auth/register",
      payload
    );

    return response.data;
  },

  async refreshToken(refreshToken) {
    const response = await api.post(
      "/auth/refresh",
      {
        refresh_token: refreshToken,
      }
    );

    return response.data;
  },

  async getProfile() {
    const response = await api.get(
      "/users/me"
    );

    return response.data;
  },
};

export default authService;
