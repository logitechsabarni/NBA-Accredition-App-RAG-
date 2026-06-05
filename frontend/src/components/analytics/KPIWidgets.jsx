import {
  Users,
  Activity,
  BarChart3,
  Brain,
} from "lucide-react";

const cards = [
  {
    title: "Users",
    value: "1,245",
    icon: Users,
  },
  {
    title: "Workflows",
    value: "3,870",
    icon: Activity,
  },
  {
    title: "Analytics Reports",
    value: "682",
    icon: BarChart3,
  },
  {
    title: "AI Requests",
    value: "18,422",
    icon: Brain,
  },
];

export default function KPIWidgets() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">

      {cards.map((card) => {
        const Icon = card.icon;

        return (
          <div
            key={card.title}
            className="bg-white dark:bg-slate-900 p-5 rounded-xl shadow"
          >
            <div className="flex justify-between">

              <div>
                <p className="text-slate-500">
                  {card.title}
                </p>

                <h2 className="text-3xl font-bold mt-2">
                  {card.value}
                </h2>
              </div>

              <Icon size={32} />

            </div>
          </div>
        );
      })}
    </div>
  );
}
