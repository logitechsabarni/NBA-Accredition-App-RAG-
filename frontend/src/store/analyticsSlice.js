import { createSlice } from "@reduxjs/toolkit";

const analyticsSlice = createSlice({
  name: "analytics",

  initialState: {
    dashboard: null,
    readiness: null,
    loading: false,
  },

  reducers: {
    setAnalytics(state, action) {
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
  setAnalytics,
  setReadiness,
  setAnalyticsLoading,
} = analyticsSlice.actions;

export default analyticsSlice.reducer;
