"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { toast } from "react-toastify";

import { describeError } from "@/lib/api";
import * as endpoints from "@/lib/endpoints";
import type { EnquiryPayload } from "@/lib/types";

export default function EnquiryForm() {
  const searchParams = useSearchParams();
  // A property page can prefill the subject with its reference code.
  const [form, setForm] = useState<EnquiryPayload>({
    name: "",
    email: "",
    phone_number: "",
    subject: searchParams.get("subject") ?? "",
    message: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      const payload: EnquiryPayload = { ...form };
      if (!payload.phone_number) delete payload.phone_number;

      await endpoints.sendEnquiry(payload);
      toast.success("Thank you — your enquiry is on its way.");
      setForm({ name: "", email: "", phone_number: "", subject: "", message: "" });
    } catch (error) {
      toast.error(describeError(error, "Your enquiry could not be sent"));
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    "w-full rounded-md border border-[var(--line)] bg-[var(--surface-raised)] px-3 py-2";

  return (
    <form onSubmit={handleSubmit} className="mt-8 space-y-4">
      <label className="block">
        <span className="mb-1 block text-sm font-medium">Your name</span>
        <input
          required
          autoComplete="name"
          value={form.name}
          onChange={(event) => setForm({ ...form, name: event.target.value })}
          className={inputClass}
        />
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
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
          <span className="mb-1 block text-sm font-medium">
            Phone <span className="text-muted">(optional)</span>
          </span>
          <input
            type="tel"
            autoComplete="tel"
            placeholder="+254712345678"
            value={form.phone_number}
            onChange={(event) => setForm({ ...form, phone_number: event.target.value })}
            className={inputClass}
          />
        </label>
      </div>

      <label className="block">
        <span className="mb-1 block text-sm font-medium">Subject</span>
        <input
          required
          maxLength={100}
          value={form.subject}
          onChange={(event) => setForm({ ...form, subject: event.target.value })}
          className={inputClass}
        />
      </label>

      <label className="block">
        <span className="mb-1 block text-sm font-medium">Message</span>
        <textarea
          required
          rows={5}
          value={form.message}
          onChange={(event) => setForm({ ...form, message: event.target.value })}
          className={inputClass}
        />
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-brand-600 px-4 py-3 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {submitting ? "Sending…" : "Send enquiry"}
      </button>
    </form>
  );
}
