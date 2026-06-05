import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const data = [
  { name: "COPO", score: 90 },
  { name: "SAR", score: 86 },
  { name: "Analytics", score: 94 },
  { name: "Chat", score: 89 },
];

export default function PerformanceChart() {
  return (
    <div className="bg-white dark:bg-slate-900 p-5 rounded-xl shadow">

      <h2 className="text-lg font-semibold mb-4">
        Module Performance
      </h2>

      <ResponsiveContainer
        width="100%"
        height={300}
      >
        <BarChart data={data}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="score" />
        </BarChart>
      </ResponsiveContainer>

    </div>
  );
}
