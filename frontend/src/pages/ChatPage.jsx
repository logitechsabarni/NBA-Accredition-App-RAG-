import React, { useState } from "react";
import Layout from "../components/layout/Layout";

const ChatPage = () => {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello. How can I help with NBA accreditation today?",
    },
  ]);

  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (!input.trim()) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: input,
      },
      {
        role: "assistant",
        content:
          "Processing request through LangGraph workflow...",
      },
    ]);

    setInput("");
  };

  return (
    <Layout>
      <div className="flex flex-col h-[80vh]">
        <h1 className="text-3xl font-bold mb-6">
          AI Chat Assistant
        </h1>

        <div className="flex-1 overflow-auto bg-slate-900 rounded-xl p-6 border border-slate-800">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`mb-4 ${
                msg.role === "user"
                  ? "text-right"
                  : "text-left"
              }`}
            >
              <div
                className={`inline-block p-4 rounded-xl max-w-xl ${
                  msg.role === "user"
                    ? "bg-blue-600"
                    : "bg-slate-800"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3 mt-4">
          <input
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            placeholder="Ask about CO-PO mapping, SAR generation..."
            className="flex-1 p-4 rounded-xl bg-slate-900 border border-slate-800"
          />

          <button
            onClick={sendMessage}
            className="bg-blue-600 px-6 rounded-xl"
          >
            Send
          </button>
        </div>
      </div>
    </Layout>
  );
};

export default ChatPage;
