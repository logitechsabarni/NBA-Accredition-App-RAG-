import { createSlice } from "@reduxjs/toolkit";

const chatSlice = createSlice({
  name: "chat",

  initialState: {
    messages: [],
    loading: false,
    isTyping: false,
  },

  reducers: {
    addMessage(state, action) {
      state.messages.push(action.payload);
    },

    setLoading(state, action) {
      state.loading = action.payload;
    },

    setTyping(state, action) {
      state.isTyping = action.payload;
    },

    clearChat(state) {
      state.messages = [];
    },
  },
});

export const {
  addMessage,
  setLoading,
  setTyping,
  clearChat,
} = chatSlice.actions;

export default chatSlice.reducer;
