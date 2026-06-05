import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center">

      <h1 className="text-8xl font-bold">
        404
      </h1>

      <p className="text-slate-500 mt-4">
        Page not found
      </p>

      <Link
        to="/dashboard"
        className="mt-6 px-5 py-3 bg-blue-600 text-white rounded-lg"
      >
        Go Home
      </Link>

    </div>
  );
}
