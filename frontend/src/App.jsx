import { useSelector } from "react-redux";
import AppRoutes from "./routes/AppRoutes";

export default function App() {
  const darkMode = useSelector(
    (state) => state.ui.darkMode
  );

  return (
    <div
      className={
        darkMode ? "dark" : ""
      }
    >
      <div className="bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-white min-h-screen transition-all">
        <AppRoutes />
      </div>
    </div>
  );
}
