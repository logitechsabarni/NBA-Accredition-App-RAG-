import { useEffect, useState } from "react";
import adminService from "../../services/adminService";

export default function UserTable() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    const data = await adminService.getUsers();
    setUsers(data);
  };

  return (
    <div className="bg-slate-900 rounded-xl p-6">
      <h2 className="text-xl font-bold mb-4">Users</h2>

      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="text-left py-2">Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {users.map((user) => (
            <tr key={user.id} className="border-b border-slate-800">
              <td className="py-3">{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    user.active
                      ? "bg-green-500/20 text-green-400"
                      : "bg-red-500/20 text-red-400"
                  }`}
                >
                  {user.active ? "Active" : "Inactive"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
