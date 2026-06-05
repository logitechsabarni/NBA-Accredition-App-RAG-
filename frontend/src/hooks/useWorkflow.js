import { useDispatch, useSelector } from "react-redux";

import {
  setWorkflow,
  addExecution,
} from "../store/workflowSlice";

export default function useWorkflow() {
  const dispatch = useDispatch();

  const workflow = useSelector(
    (state) => state.workflow
  );

  return {
    ...workflow,

    updateWorkflow(data) {
      dispatch(setWorkflow(data));
    },

    addExecution(data) {
      dispatch(addExecution(data));
    },
  };
}
