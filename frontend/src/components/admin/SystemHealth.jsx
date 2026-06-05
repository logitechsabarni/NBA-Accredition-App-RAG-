import { CheckCircle } from "lucide-react";

export default function SystemHealth() {
  const systems = [
    "API Gateway",
    "PostgreSQL",
    "Redis",
    "Vector DB",
    "LLM Router",
  ];

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl p-5 shadow">

      <h2 className="text-xl font-bold mb-5">
        System Health
      </h2>

      <div className="space-y-4">

        {systems.map((system) => (
          <div
            key={system}
            className="flex items-center justify-between"
          >
            <span>{system}</span>

            <CheckCircle
              className="text-green-500"
            />
          </div>
        ))}

      </div>

    </div>
  );
}
