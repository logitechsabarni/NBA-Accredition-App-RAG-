import { NavLink } from "react-router-dom";

import {
  LayoutDashboard,
  MessageSquare,
  Workflow,
  BarChart3,
  Shield,
  User,
  Settings,
} from "lucide-react";

const links = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "AI Chat",
    path: "/chat",
    icon: MessageSquare,
  },
  {
    name: "Workflow Monitor",
    path: "/workflow",
    icon: Workflow,
  },
  {
    name: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
  {
    name: "Admin",
    path: "/admin",
    icon: Shield,
  },
  {
    name: "Profile",
    path: "/profile",
    icon: User,
  },
  {
    name: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 min-h-screen">
      <div className="p-6">
        <h1 className="text-xl font-bold text-white">
          NBA AI Platform
        </h1>
      </div>

      <nav className="px-4 space-y-2">
        {links.map((link) => {
          const Icon = link.icon;

          return (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-slate-800"
                }`
              }
            >
              <Icon size={18} />
              {link.name}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
