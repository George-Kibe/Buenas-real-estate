"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "react-toastify";

import Spinner from "@/components/Spinner";
import { register, reset } from "@/store/authSlice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const EMPTY = {
  username: "",
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  re_password: "",
};

export default function RegisterForm() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { status } = useAppSelector((state) => state.auth);
  const [form, setForm] = useState(EMPTY);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (form.password !== form.re_password) {
      toast.error("The two passwords do not match");
      return;
    }

    const result = await dispatch(register(form));
    if (register.fulfilled.match(result)) {
      toast.success("Account created. Check your email to activate it.");
      dispatch(reset());
      router.push("/login");
    } else {
      toast.error(result.payload ?? "Unable to create the account");
      dispatch(reset());
    }
  };

  const inputClass =
    "w-full rounded-md border border-[var(--line)] bg-[var(--surface-raised)] px-3 py-2";

  const field = (
    name: keyof typeof EMPTY,
    label: string,
    type = "text",
    autoComplete?: string,
  ) => (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      <input
        type={type}
        required
        autoComplete={autoComplete}
        value={form[name]}
        onChange={(event) => setForm({ ...form, [name]: event.target.value })}
        className={inputClass}
      />
    </label>
  );

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-3xl font-bold">Create an account</h1>
      <p className="mt-1 text-muted">List properties and talk to agents directly.</p>

      {status === "loading" ? (
        <Spinner label="Creating your account" />
      ) : (
        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            {field("first_name", "First name", "text", "given-name")}
            {field("last_name", "Last name", "text", "family-name")}
          </div>
          {field("username", "Username", "text", "username")}
          {field("email", "Email", "email", "email")}
          {field("password", "Password", "password", "new-password")}
          {field("re_password", "Confirm password", "password", "new-password")}

          <button
            type="submit"
            className="w-full rounded-md bg-brand-600 px-4 py-3 font-medium text-white hover:bg-brand-700"
          >
            Create account
          </button>
        </form>
      )}

      <p className="mt-6 text-sm text-muted">
        Already registered?{" "}
        <Link href="/login" className="text-brand-700 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
