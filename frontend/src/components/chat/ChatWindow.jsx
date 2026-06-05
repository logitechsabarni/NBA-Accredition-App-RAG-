import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

export default function ChatWindow({
  messages,
  isTyping,
}) {
  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, isTyping]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold">
                NBA Enterprise AI
              </h2>

              <p className="text-gray-500 mt-2">
                Start a conversation with the AI Assistant
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
              />
            ))}

            {isTyping && <TypingIndicator />}

            <div ref={bottomRef} />
          </>
        )}
      </div>
    </div>
  );
}
