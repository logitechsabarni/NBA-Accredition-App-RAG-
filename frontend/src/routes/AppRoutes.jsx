import { Routes, Route, Navigate } from "react-router-dom";

import DashboardPage from "../pages/DashboardPage";
import ChatPage from "../pages/ChatPage";
import WorkflowPage from "../pages/WorkflowPage";
import AnalyticsPage from "../pages/AnalyticsPage";
import AdminPage from "../pages/AdminPage";
import ProfilePage from "../pages/ProfilePage";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import NotFoundPage from "../pages/NotFoundPage";

import Sidebar from "../components/layout/Sidebar";
import Navbar from "../components/layout/Navbar";

function Layout({ children }) {
  return (
    <div className="flex bg-slate-950 text-white">
      <Sidebar />

      <div className="flex-1">
        <Navbar />

        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" />} />

      <Route
        path="/dashboard"
        element={
          <Layout>
            <DashboardPage />
          </Layout>
        }
      />

      <Route
        path="/chat"
        element={
          <Layout>
            <ChatPage />
          </Layout>
        }
      />

      <Route
        path="/workflow"
        element={
          <Layout>
            <WorkflowPage />
          </Layout>
        }
      />

      <Route
        path="/analytics"
        element={
          <Layout>
            <AnalyticsPage />
          </Layout>
        }
      />

      <Route
        path="/admin"
        element={
          <Layout>
            <AdminPage />
          </Layout>
        }
      />

      <Route
        path="/profile"
        element={
          <Layout>
            <ProfilePage />
          </Layout>
        }
      />

      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/register"
        element={<RegisterPage />}
      />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
