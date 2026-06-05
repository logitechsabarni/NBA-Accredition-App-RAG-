import React from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  toggleSidebar,
  toggleTheme,
} from "../../store/uiSlice";

const Navbar = () => {
  const dispatch = useDispatch();

  const { darkMode } = useSelector(
    (state) => state.ui
  );

  const user = useSelector(
    (state) => state.auth.user
  );

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() =>
            dispatch(toggleSidebar())
          }
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700"
        >
          ☰
        </button>

        <h2 className="font-semibold text-white">
          NBA Enterprise AI Platform
        </h2>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={() =>
            dispatch(toggleTheme())
          }
          className="px-3 py-2 rounded-lg bg-slate-800"
        >
          {darkMode ? "🌙" : "☀️"}
        </button>

        <button className="relative">
          🔔

          <span className="absolute -top-2 -right-2 bg-red-500 rounded-full w-4 h-4 text-[10px] flex items-center justify-center">
            3
          </span>
        </button>

        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white">
            {user?.name?.[0] || "U"}
          </div>

          <div className="hidden md:block">
            <p className="text-sm text-white">
              {user?.name || "User"}
            </p>

            <p className="text-xs text-slate-400">
              {user?.role || "Faculty"}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
