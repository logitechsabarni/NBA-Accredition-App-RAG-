import UserTable from "../components/admin/UserTable";
import AuditLogs from "../components/admin/AuditLogs";
import SystemHealth from "../components/admin/SystemHealth";

export default function AdminPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">
          Administration Center
        </h1>

        <p className="text-slate-400 mt-2">
          Manage users, monitor infrastructure,
          inspect audit trails and oversee
          platform operations.
        </p>
      </div>

      {/* System Health */}
      <SystemHealth />

      {/* Statistics */}
      <div className="grid md:grid-cols-4 gap-4">
        <StatCard
          title="Active Users"
          value="1,248"
        />

        <StatCard
          title="Workflows"
          value="58,392"
        />

        <StatCard
          title="SAR Reports"
          value="431"
        />

        <StatCard
          title="Readiness Avg"
          value="84%"
        />
      </div>

      {/* Users */}
      <UserTable />

      {/* Audit Logs */}
      <AuditLogs />
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
      <p className="text-sm text-slate-400">
        {title}
      </p>

      <h2 className="text-3xl font-bold mt-2">
        {value}
      </h2>
    </div>
  );
}
