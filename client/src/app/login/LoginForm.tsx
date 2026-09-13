"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";

import Spinner from "@/components/Spinner";
import { login, reset } from "@/store/authSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

export default function LoginForm() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { status, error, isAuthenticated } = useAppSelector((state) => state.auth);
  const [form, setForm] = useState({ email: "", password: "" });

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/profile");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (status === "failed" && error) {
      toast.error(error);
      dispatch(reset());
    }
  }, [dispatch, error, status]);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void dispatch(login(form));
  };

  const inputClass =
    "w-full rounded-md border border-[var(--line)] bg-[var(--surface-raised)] px-3 py-2";

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-3xl font-bold">Sign in</h1>
      <p className="mt-1 text-muted">Welcome back. Use the email you registered with.</p>

      {status === "loading" ? (
        <Spinner label="Signing in" />
      ) : (
        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Email</span>
            <input
              type="email"
              required
              autoComplete="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              className={inputClass}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium">Password</span>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              className={inputClass}
            />
          </label>

          <button
            type="submit"
            className="w-full rounded-md bg-brand-600 px-4 py-3 font-medium text-white hover:bg-brand-700"
          >
            Sign in
          </button>
        </form>
      )}

      <p className="mt-6 text-sm text-muted">
        No account yet?{" "}
        <Link href="/register" className="text-brand-700 hover:underline">
          Create one
        </Link>
      </p>
    </div>
  );
}
