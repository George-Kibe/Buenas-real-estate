import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-[var(--line)] bg-[var(--surface-raised)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm sm:flex-row sm:items-center sm:justify-between">
        <p className="text-muted">
          © {new Date().getFullYear()} Buenas Consultants. All rights reserved.
        </p>
        <div className="flex gap-4">
          <Link href="/properties" className="text-muted hover:text-brand-700">
            Properties
          </Link>
          <Link href="/contact" className="text-muted hover:text-brand-700">
            Contact
          </Link>
        </div>
      </div>
    </footer>
  );
}
