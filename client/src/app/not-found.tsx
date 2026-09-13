import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-4 py-24 text-center">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="mt-2 text-3xl font-bold">We could not find that page</h1>
      <p className="mt-3 text-muted">
        The listing may have been taken down, or the link may be out of date.
      </p>
      <Link
        href="/properties"
        className="mt-8 rounded-md bg-brand-600 px-5 py-3 font-medium text-white hover:bg-brand-700"
      >
        Browse properties
      </Link>
    </div>
  );
}
