import React from "react";
import NodeCard from "./NodeCard";

export default function ExecutionPanel({
  nodes = [],
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <h2 className="text-lg font-bold mb-4">
        Workflow Nodes
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {nodes.map((node) => (
          <NodeCard
            key={node.id}
            title={node.title}
            status={node.status}
            latency={node.latency}
            description={node.description}
          />
        ))}
      </div>
    </div>
  );
}
