import { useState } from "react";
import { Send } from "lucide-react";

export default function ChatInput({
  onSend,
  loading,
}) {
  const [message, setMessage] = useState("");

  const submit = () => {
    if (!message.trim()) return;

    onSend(message);
    setMessage("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t dark:border-slate-700 p-4">
      <div className="flex gap-3 items-end">
        <textarea
          value={message}
          disabled={loading}
          onChange={(e) =>
            setMessage(e.target.value)
          }
          onKeyDown={handleKeyDown}
          rows={2}
          placeholder="Ask anything..."
          className="flex-1 resize-none rounded-xl border dark:border-slate-700 bg-white dark:bg-slate-800 p-3 outline-none"
        />

        <button
          disabled={loading}
          onClick={submit}
          className="bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-xl transition"
        >
          <Send size={18} />
        </button>
      </div>

      <div className="text-xs text-gray-500 mt-2 text-right">
        {message.length}/4000
      </div>
    </div>
  );
}
