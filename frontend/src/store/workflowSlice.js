import { createSlice } from "@reduxjs/toolkit";

const workflowSlice = createSlice({
  name: "workflow",

  initialState: {
    executions: [],
    currentWorkflow: null,
    loading: false,
  },

  reducers: {
    setWorkflow(state, action) {
      state.currentWorkflow = action.payload;
    },

    addExecution(state, action) {
      state.executions.unshift(action.payload);
    },

    setWorkflowLoading(state, action) {
      state.loading = action.payload;
    },
  },
});

export const {
  setWorkflow,
  addExecution,
  setWorkflowLoading,
} = workflowSlice.actions;

export default workflowSlice.reducer;
