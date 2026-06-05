import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  sidebarOpen: true,
  darkMode: true,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },

    toggleTheme(state) {
      state.darkMode = !state.darkMode;
    },
  },
});

export const {
  toggleSidebar,
  toggleTheme,
} = uiSlice.actions;

export default uiSlice.reducer;
