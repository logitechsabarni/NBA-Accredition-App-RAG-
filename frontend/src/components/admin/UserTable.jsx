export default function UserTable({
  users = [],
}) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl shadow overflow-hidden">

      <table className="w-full">

        <thead>
          <tr className="border-b">
            <th className="p-4 text-left">
              Name
            </th>
            <th className="p-4 text-left">
              Email
            </th>
            <th className="p-4 text-left">
              Role
            </th>
          </tr>
        </thead>

        <tbody>
          {users.map((user) => (
            <tr
              key={user.id}
              className="border-b"
            >
              <td className="p-4">
                {user.name}
              </td>

              <td className="p-4">
                {user.email}
              </td>

              <td className="p-4">
                {user.role}
              </td>
            </tr>
          ))}
        </tbody>

      </table>

    </div>
  );
}
