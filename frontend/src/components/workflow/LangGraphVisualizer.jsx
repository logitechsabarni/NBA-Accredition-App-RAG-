import React from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
} from "reactflow";

import "reactflow/dist/style.css";

const initialNodes = [
  {
    id: "1",
    position: { x: 100, y: 50 },
    data: { label: "Intent Classifier" },
  },
  {
    id: "2",
    position: { x: 100, y: 180 },
    data: { label: "Task Router" },
  },
  {
    id: "3",
    position: { x: 100, y: 310 },
    data: { label: "Specialist Agent" },
  },
  {
    id: "4",
    position: { x: 100, y: 440 },
    data: { label: "Validation Agent" },
  },
  {
    id: "5",
    position: { x: 450, y: 440 },
    data: { label: "RAG Retrieval" },
  },
  {
    id: "6",
    position: { x: 450, y: 280 },
    data: { label: "LLM Generation" },
  },
  {
    id: "7",
    position: { x: 450, y: 120 },
    data: { label: "Response" },
  },
];

const initialEdges = [
  { id: "e1", source: "1", target: "2" },
  { id: "e2", source: "2", target: "3" },
  { id: "e3", source: "3", target: "4" },
  { id: "e4", source: "4", target: "5" },
  { id: "e5", source: "5", target: "6" },
  { id: "e6", source: "6", target: "7" },
];

export default function LangGraphVisualizer() {
  return (
    <div className="h-[650px] bg-slate-900 rounded-xl overflow-hidden border border-slate-800">
      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}
