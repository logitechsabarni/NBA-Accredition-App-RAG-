import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { useForm } from "react-hook-form";

import { loginSuccess } from "../store/authSlice";

const LoginPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const onSubmit = async (data) => {
    const mockUser = {
      id: "1",
      name: "Admin User",
      role: "admin",
      email: data.email,
    };

    dispatch(
      loginSuccess({
        user: mockUser,
        accessToken: "demo_access_token",
        refreshToken: "demo_refresh_token",
      })
    );

    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="w-full max-w-md bg-slate-900 p-8 rounded-2xl border border-slate-800">
        <h1 className="text-3xl font-bold text-white mb-2">
          Welcome Back
        </h1>

        <p className="text-slate-400 mb-6">
          Sign in to NBA Enterprise AI
        </p>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
        >
          <input
            {...register("email", {
              required: true,
            })}
            placeholder="Email"
            className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 text-white"
          />

          <input
            type="password"
            {...register("password", {
              required: true,
            })}
            placeholder="Password"
            className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 text-white"
          />

          {(errors.email || errors.password) && (
            <p className="text-red-400 text-sm">
              All fields required
            </p>
          )}

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 py-3 rounded-lg text-white font-medium"
          >
            Login
          </button>
        </form>

        <p className="text-slate-400 mt-6 text-center">
          No account?{" "}
          <Link
            className="text-blue-400"
            to="/register"
          >
            Register
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
