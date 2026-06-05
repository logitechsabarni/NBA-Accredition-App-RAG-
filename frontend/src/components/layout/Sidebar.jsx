import React from "react";
import { NavLink } from "react-router-dom";
import { useSelector } from "react-redux";

const menuItems = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: "📊",
  },
  {
    name: "AI Chat",
    path: "/chat",
    icon: "🤖",
  },
  {
    name: "Workflow",
    path: "/workflow",
    icon: "⚙️",
  },
  {
    name: "Analytics",
    path: "/analytics",
    icon: "📈",
  },
  {
    name: "Profile",
    path: "/profile",
    icon: "👤",
  },
  {
    name: "Settings",
    path: "/settings",
    icon: "🔧",
  },
];

const Sidebar = () => {
  const { sidebarOpen } = useSelector(
    (state) => state.ui
  );

  return (
    <aside
      className={`${
        sidebarOpen ? "w-64" : "w-20"
      } bg-slate-900 border-r border-slate-800 min-h-screen transition-all duration-300`}
    >
      <div className="p-6">
        <h1 className="font-bold text-xl text-white">
          NBA AI
        </h1>
      </div>

      <nav className="px-3 space-y-2">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`
            }
          >
            <span>{item.icon}</span>

            {sidebarOpen && (
              <span>{item.name}</span>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
