import UserTable from "../components/admin/UserTable";
import AuditLogs from "../components/admin/AuditLogs";
import SystemHealth from "../components/admin/SystemHealth";

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">
        Administration
      </h1>

      <SystemHealth />

      <UserTable />

      <AuditLogs />
    </div>
  );
}
