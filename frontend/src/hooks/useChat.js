import { useDispatch, useSelector } from "react-redux";

import {
  addMessage,
  setTyping,
  clearChat,
} from "../store/chatSlice";

export default function useChat() {
  const dispatch = useDispatch();

  const chat = useSelector(
    (state) => state.chat
  );

  const sendMessage = (message) => {
    dispatch(addMessage(message));
  };

  return {
    ...chat,
    sendMessage,
    clearChat: () => dispatch(clearChat()),
    setTyping: (value) =>
      dispatch(setTyping(value)),
  };
}
