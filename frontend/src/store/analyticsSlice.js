import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  dashboard: {},
  readiness: {},
  loading: false,
};

const analyticsSlice = createSlice({
  name: "analytics",
  initialState,
  reducers: {
    setDashboard(state, action) {
      state.dashboard = action.payload;
    },

    setReadiness(state, action) {
      state.readiness = action.payload;
    },

    setAnalyticsLoading(state, action) {
      state.loading = action.payload;
    },
  },
});

export const {
  setDashboard,
  setReadiness,
  setAnalyticsLoading,
} = analyticsSlice.actions;

export default analyticsSlice.reducer;
