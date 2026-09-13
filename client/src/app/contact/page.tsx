import type { Metadata } from "next";
import { Suspense } from "react";

import Spinner from "@/components/Spinner";

import EnquiryForm from "./EnquiryForm";

export const metadata: Metadata = {
  title: "Contact",
  description: "Send an enquiry to the Buenas Real Estate team.",
};

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-xl px-4 py-16">
      <h1 className="text-3xl font-bold">Get in touch</h1>
      <p className="mt-1 text-muted">
        Tell us what you are looking for and an agent will come back to you.
      </p>
      <Suspense fallback={<Spinner label="Loading form" />}>
        <EnquiryForm />
      </Suspense>
    </div>
  );
}
