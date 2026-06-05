import { createSlice } from "@reduxjs/toolkit";

const token = localStorage.getItem("token");

const authSlice = createSlice({
  name: "auth",

  initialState: {
    token: token || null,
    user: null,
    isAuthenticated: !!token,
    loading: false,
  },

  reducers: {
    loginStart(state) {
      state.loading = true;
    },

    loginSuccess(state, action) {
      state.loading = false;
      state.token = action.payload.token;
      state.user = action.payload.user;
      state.isAuthenticated = true;
    },

    logout(state) {
      state.token = null;
      state.user = null;
      state.isAuthenticated = false;
      localStorage.removeItem("token");
    },

    setUser(state, action) {
      state.user = action.payload;
    },
  },
});

export const {
  loginStart,
  loginSuccess,
  logout,
  setUser,
} = authSlice.actions;

export default authSlice.reducer;
