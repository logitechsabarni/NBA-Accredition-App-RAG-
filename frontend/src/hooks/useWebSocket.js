import { useEffect, useState } from "react";
import { io } from "socket.io-client";

export default function useWebSocket(url) {
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const socketInstance = io(url, {
      transports: ["websocket"],
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, [url]);

  return socket;
}
