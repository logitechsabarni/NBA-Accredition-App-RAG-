import { io } from "socket.io-client";

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  "http://localhost:5000";

let socket = null;

export const connectSocket = () => {
  if (!socket) {
    socket = io(WS_URL, {
      transports: ["websocket"],
      autoConnect: true,
    });
  }

  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

export const getSocket = () => socket;
