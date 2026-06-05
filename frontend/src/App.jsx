import { BrowserRouter, useLocation } from "react-router-dom";

import AppRoutes from "./routes/AppRoutes";

import Sidebar from "./components/layout/Sidebar";
import Navbar from "./components/layout/Navbar";
import Footer from "./components/layout/Footer";

function LayoutWrapper() {
  const location = useLocation();

  const publicRoutes = [
    "/login",
    "/register"
  ];

  const isPublicRoute = publicRoutes.includes(
    location.pathname
  );

  if (isPublicRoute) {
    return (
      <div className="min-h-screen bg-slate-950 text-white">
        <AppRoutes />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-950 text-white overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Layout */}
      <div className="flex flex-col flex-1 overflow-hidden">
        
        {/* Navbar */}
        <Navbar />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <AppRoutes />
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <LayoutWrapper />
    </BrowserRouter>
  );
}
