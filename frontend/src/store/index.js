import { configureStore } from "@reduxjs/toolkit";

import authReducer from "./authSlice";
import chatReducer from "./chatSlice";
import workflowReducer from "./workflowSlice";
import analyticsReducer from "./analyticsSlice";
import uiReducer from "./uiSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
    workflow: workflowReducer,
    analytics: analyticsReducer,
    ui: uiReducer,
  },
});
