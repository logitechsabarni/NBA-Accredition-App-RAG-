import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  messages: [],
  loading: false,
  typing: false,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addMessage(state, action) {
      state.messages.push(action.payload);
    },

    clearMessages(state) {
      state.messages = [];
    },

    setLoading(state, action) {
      state.loading = action.payload;
    },

    setTyping(state, action) {
      state.typing = action.payload;
    },
  },
});

export const {
  addMessage,
  clearMessages,
  setLoading,
  setTyping,
} = chatSlice.actions;

export default chatSlice.reducer;
