import { useEffect, useState } from "react";
import adminService from "../../services/adminService";

export default function SystemHealth() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    loadHealth();
  }, []);

  const loadHealth = async () => {
    const data = await adminService.getSystemHealth();
    setHealth(data);
  };

  if (!health) return null;

  return (
    <div className="bg-slate-900 p-6 rounded-xl">
      <h2 className="text-xl font-bold mb-4">
        System Health
      </h2>

      <div className="space-y-4">
        <Status
          title="API"
          value={health.api}
        />

        <Status
          title="Database"
          value={health.database}
        />

        <Status
          title="Redis"
          value={health.redis}
        />

        <Status
          title="Vector Store"
          value={health.vector}
        />
      </div>
    </div>
  );
}

function Status({ title, value }) {
  return (
    <div className="flex justify-between">
      <span>{title}</span>

      <span
        className={
          value === "healthy"
            ? "text-green-400"
            : "text-red-400"
        }
      >
        {value}
      </span>
    </div>
  );
}
