import { useEffect, useState } from "react";
import adminService from "../../services/adminService";

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    const data = await adminService.getAuditLogs();
    setLogs(data);
  };

  return (
    <div className="bg-slate-900 rounded-xl p-6">
      <h2 className="text-xl font-bold mb-4">
        Audit Logs
      </h2>

      <div className="space-y-3 max-h-[500px] overflow-auto">
        {logs.map((log) => (
          <div
            key={log.id}
            className="p-4 bg-slate-800 rounded-lg"
          >
            <p className="font-semibold">
              {log.action}
            </p>

            <p className="text-sm text-gray-400">
              {log.user}
            </p>

            <p className="text-xs text-gray-500">
              {new Date(log.timestamp).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
