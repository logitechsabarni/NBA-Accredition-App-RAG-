import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  Workflow,
  BarChart3,
  Settings,
  ShieldCheck,
  User,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

const menuItems = [
  {
    title: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "AI Chat",
    path: "/chat",
    icon: MessageSquare,
  },
  {
    title: "Workflows",
    path: "/workflow",
    icon: Workflow,
  },
  {
    title: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
  {
    title: "Profile",
    path: "/profile",
    icon: User,
  },
  {
    title: "Admin",
    path: "/admin",
    icon: ShieldCheck,
    adminOnly: true,
  },
  {
    title: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  const userRole = localStorage.getItem("role") || "faculty";

  return (
    <aside
      className={`h-screen bg-slate-950 border-r border-slate-800 transition-all duration-300 ${
        collapsed ? "w-20" : "w-72"
      }`}
    >
      {/* Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
        {!collapsed && (
          <div>
            <h1 className="font-bold text-lg text-white">
              NBA AI Platform
            </h1>

            <p className="text-xs text-slate-400">
              Enterprise Edition
            </p>
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-lg hover:bg-slate-800"
        >
          {collapsed ? (
            <ChevronRight size={18} />
          ) : (
            <ChevronLeft size={18} />
          )}
        </button>
      </div>

      {/* Menu */}
      <nav className="p-4 space-y-2">
        {menuItems
          .filter(
            (item) =>
              !item.adminOnly ||
              userRole === "admin"
          )
          .map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `
                  flex items-center gap-3 px-4 py-3 rounded-xl
                  transition-all duration-200
                  ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-slate-400 hover:bg-slate-800 hover:text-white"
                  }
                `
                }
              >
                <Icon size={20} />

                {!collapsed && (
                  <span>{item.title}</span>
                )}
              </NavLink>
            );
          })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="absolute bottom-5 left-4 right-4">
          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <p className="text-sm font-medium">
              NBA Accreditation
            </p>

            <p className="text-xs text-slate-400 mt-1">
              AI-Powered Readiness Platform
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}
