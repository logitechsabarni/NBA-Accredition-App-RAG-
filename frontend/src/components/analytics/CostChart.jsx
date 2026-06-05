import {
  PieChart,
  Pie,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const data = [
  { name: "OpenAI", value: 45 },
  { name: "Granite", value: 30 },
  { name: "Infrastructure", value: 25 },
];

export default function CostChart() {
  return (
    <div className="bg-white dark:bg-slate-900 p-5 rounded-xl shadow">

      <h2 className="text-lg font-semibold mb-4">
        Cost Distribution
      </h2>

      <ResponsiveContainer
        width="100%"
        height={300}
      >
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
          />
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>

    </div>
  );
}
