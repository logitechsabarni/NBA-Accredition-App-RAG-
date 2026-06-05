import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

const data = [
  { month: "Jan", usage: 100 },
  { month: "Feb", usage: 220 },
  { month: "Mar", usage: 400 },
  { month: "Apr", usage: 650 },
  { month: "May", usage: 810 },
];

export default function UsageChart() {
  return (
    <div className="bg-white dark:bg-slate-900 p-5 rounded-xl shadow">

      <h2 className="text-lg font-semibold mb-4">
        Platform Usage
      </h2>

      <ResponsiveContainer
        width="100%"
        height={300}
      >
        <LineChart data={data}>
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="usage"
          />
        </LineChart>
      </ResponsiveContainer>

    </div>
  );
}
