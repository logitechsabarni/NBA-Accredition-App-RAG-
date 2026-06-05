import React from "react";

export default function WorkflowTimeline({ events = [] }) {
  return (
    <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
      <h2 className="text-lg font-bold mb-4">Execution Timeline</h2>

      <div className="space-y-5">
        {events.map((event, index) => (
          <div key={index} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              {index !== events.length - 1 && (
                <div className="w-[2px] flex-1 bg-slate-700" />
              )}
            </div>

            <div>
              <div className="text-sm font-medium">
                {event.node}
              </div>

              <div className="text-xs text-gray-400">
                {event.timestamp}
              </div>

              <div className="text-xs text-gray-500 mt-1">
                {event.status}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
