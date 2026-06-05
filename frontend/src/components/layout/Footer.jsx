import React from "react";

const Footer = () => {
  return (
    <footer className="border-t border-slate-800 bg-slate-900 px-6 py-4">
      <div className="flex flex-col md:flex-row justify-between items-center">
        <p className="text-slate-400 text-sm">
          © 2026 NBA Enterprise AI Platform
        </p>

        <div className="flex gap-4 mt-2 md:mt-0">
          <span className="text-slate-500 text-sm">
            Version 1.0.0
          </span>

          <span className="text-slate-500 text-sm">
            Enterprise Edition
          </span>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
