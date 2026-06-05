import { Inbox } from "lucide-react";

export default function EmptyState({
  title = "No Data Available",
  description = "Nothing to display."
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16">

      <Inbox size={60} className="text-slate-400" />

      <h3 className="text-xl font-semibold mt-4">
        {title}
      </h3>

      <p className="text-slate-500 mt-2">
        {description}
      </p>

    </div>
  );
}
