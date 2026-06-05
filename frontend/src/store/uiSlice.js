import { createSlice } from "@reduxjs/toolkit";

const uiSlice = createSlice({
  name: "ui",

  initialState: {
    darkMode: true,
    sidebarOpen: true,
  },

  reducers: {
    toggleDarkMode(state) {
      state.darkMode = !state.darkMode;
    },

    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
  },
});

export const {
  toggleDarkMode,
  toggleSidebar,
} = uiSlice.actions;

export default uiSlice.reducer;
