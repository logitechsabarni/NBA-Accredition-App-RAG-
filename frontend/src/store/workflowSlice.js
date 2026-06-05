import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  workflows: [],
  currentWorkflow: null,
  loading: false,
};

const workflowSlice = createSlice({
  name: "workflow",
  initialState,
  reducers: {
    setWorkflows(state, action) {
      state.workflows = action.payload;
    },

    setCurrentWorkflow(state, action) {
      state.currentWorkflow = action.payload;
    },

    setWorkflowLoading(state, action) {
      state.loading = action.payload;
    },
  },
});

export const {
  setWorkflows,
  setCurrentWorkflow,
  setWorkflowLoading,
} = workflowSlice.actions;

export default workflowSlice.reducer;
