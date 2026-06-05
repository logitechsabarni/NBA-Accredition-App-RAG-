import React from "react";
import Layout from "../components/layout/Layout";

const WorkflowPage = () => {
  const nodes = [
    "Intent Classification",
    "Task Routing",
    "Compliance Check",
    "Agent Execution",
    "Validation",
    "RAG Retrieval",
    "LLM Generation",
    "Audit Logging",
  ];

  return (
    <Layout>
      <h1 className="text-3xl font-bold mb-8">
        Workflow Monitor
      </h1>

      <div className="space-y-4">
        {nodes.map((node, index) => (
          <div
            key={node}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4"
          >
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
              {index + 1}
            </div>

            <div>
              <h3 className="font-semibold">
                {node}
              </h3>

              <p className="text-slate-400 text-sm">
                Active
              </p>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
};

export default WorkflowPage;
