import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";

const RegisterPage = () => {
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
  } = useForm();

  const onSubmit = () => {
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="w-full max-w-lg bg-slate-900 p-8 rounded-2xl border border-slate-800">
        <h1 className="text-3xl font-bold text-white mb-6">
          Create Account
        </h1>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
        >
          <input
            {...register("name")}
            placeholder="Full Name"
            className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 text-white"
          />

          <input
            {...register("email")}
            placeholder="Email"
            className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 text-white"
          />

          <input
            type="password"
            {...register("password")}
            placeholder="Password"
            className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 text-white"
          />

          <button
            className="w-full py-3 bg-blue-600 rounded-lg text-white"
          >
            Register
          </button>
        </form>

        <p className="text-center text-slate-400 mt-4">
          Already registered?{" "}
          <Link
            to="/login"
            className="text-blue-400"
          >
            Login
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
