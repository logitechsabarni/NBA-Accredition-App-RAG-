export default function AuditLogs({
  logs = [],
}) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl shadow p-5">

      <h2 className="text-xl font-bold mb-4">
        Audit Logs
      </h2>

      <div className="space-y-3">

        {logs.map((log) => (
          <div
            key={log.id}
            className="border rounded-lg p-3"
          >
            <p>{log.action}</p>

            <p className="text-sm text-slate-500">
              {log.timestamp}
            </p>
          </div>
        ))}

      </div>

    </div>
  );
}
