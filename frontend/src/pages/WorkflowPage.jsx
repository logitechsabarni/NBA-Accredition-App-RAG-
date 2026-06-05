import React from "react";

import LangGraphVisualizer from "../components/workflow/LangGraphVisualizer";
import ExecutionPanel from "../components/workflow/ExecutionPanel";
import WorkflowTimeline from "../components/workflow/WorkflowTimeline";

export default function WorkflowPage() {
  const workflowNodes = [
    {
      id: 1,
      title: "Intent Classifier",
      status: "completed",
      latency: "24 ms",
      description: "Classified request type",
    },
    {
      id: 2,
      title: "Task Router",
      status: "completed",
      latency: "11 ms",
      description: "Selected specialist agent",
    },
    {
      id: 3,
      title: "COPO Agent",
      status: "completed",
      latency: "211 ms",
      description: "Generated CO-PO mappings",
    },
    {
      id: 4,
      title: "Validation Agent",
      status: "completed",
      latency: "46 ms",
      description: "Validated output",
    },
    {
      id: 5,
      title: "RAG Retrieval",
      status: "running",
      latency: "321 ms",
      description: "Searching NBA knowledge base",
    },
    {
      id: 6,
      title: "LLM Generation",
      status: "pending",
      description: "Awaiting context",
    },
  ];

  const timelineEvents = [
    {
      node: "Intent Classifier",
      status: "Completed",
      timestamp: "09:42:12",
    },
    {
      node: "Task Router",
      status: "Completed",
      timestamp: "09:42:13",
    },
    {
      node: "COPO Agent",
      status: "Completed",
      timestamp: "09:42:14",
    },
    {
      node: "Validation Agent",
      status: "Completed",
      timestamp: "09:42:15",
    },
    {
      node: "RAG Retrieval",
      status: "Running",
      timestamp: "09:42:16",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          LangGraph Workflow Monitor
        </h1>

        <p className="text-gray-400 mt-2">
          Real-time orchestration tracking for AI agents,
          validation, RAG retrieval, and LLM generation.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <LangGraphVisualizer />
        </div>

        <WorkflowTimeline events={timelineEvents} />
      </div>

      <div className="mt-6">
        <ExecutionPanel nodes={workflowNodes} />
      </div>
    </div>
  );
}
