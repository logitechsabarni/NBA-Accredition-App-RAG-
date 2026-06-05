import React from "react";
import { Clock, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

const statusStyles = {
  completed: "border-green-500 bg-green-500/10",
  running: "border-blue-500 bg-blue-500/10",
  failed: "border-red-500 bg-red-500/10",
  pending: "border-slate-700 bg-slate-900",
};

const statusIcon = {
  completed: <CheckCircle size={18} className="text-green-500" />,
  running: <Loader2 size={18} className="animate-spin text-blue-500" />,
  failed: <AlertCircle size={18} className="text-red-500" />,
  pending: <Clock size={18} className="text-gray-500" />,
};

export default function NodeCard({
  title,
  status = "pending",
  latency,
  description,
}) {
  return (
    <div
      className={`rounded-xl border p-4 transition-all ${statusStyles[status]}`}
    >
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">{title}</h3>
        {statusIcon[status]}
      </div>

      {description && (
        <p className="text-sm text-gray-400 mt-2">{description}</p>
      )}

      {latency && (
        <div className="mt-3 text-xs text-gray-500">
          Latency: {latency}
        </div>
      )}
    </div>
  );
}
