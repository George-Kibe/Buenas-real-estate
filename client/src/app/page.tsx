import Image from "next/image";
import Link from "next/link";

import PropertyCard from "@/components/PropertyCard";
import { listProperties } from "@/lib/server-api";

export default async function HomePage() {
  const page = await listProperties({ ordering: "-created_at" });
  const featured = page?.results.slice(0, 6) ?? [];

  return (
    <>
      <section className="relative isolate overflow-hidden">
        <Image
          src="/buildings.jpg"
          alt=""
          fill
          priority
          sizes="100vw"
          className="-z-10 object-cover"
        />
        <div className="-z-10 absolute inset-0 bg-gradient-to-r from-black/75 to-black/40" />
        <div className="mx-auto max-w-6xl px-4 py-24 sm:py-32">
          <h1 className="max-w-2xl text-4xl font-bold text-white sm:text-5xl">
            Find a place you will be glad to come home to.
          </h1>
          <p className="mt-4 max-w-xl text-lg text-white/85">
            Houses, apartments and commercial space for sale and for rent across Kenya,
            listed by agents you can talk to.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/properties"
              className="rounded-md bg-brand-600 px-5 py-3 font-medium text-white hover:bg-brand-700"
            >
              Browse properties
            </Link>
            <Link
              href="/contact"
              className="rounded-md bg-white/10 px-5 py-3 font-medium text-white ring-1 ring-white/40 hover:bg-white/20"
            >
              Talk to an agent
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold">Latest listings</h2>
            <p className="mt-1 text-muted">Fresh on the market this week.</p>
          </div>
          <Link
            href="/properties"
            className="shrink-0 text-sm font-medium text-brand-700 hover:underline"
          >
            View all →
          </Link>
        </div>

        {featured.length ? (
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
        ) : (
          <p className="surface-card mt-8 rounded-xl p-8 text-center text-muted">
            No listings yet. Add one from the{" "}
            <a href="/superadmin/" className="text-brand-700 hover:underline">
              admin
            </a>{" "}
            to see it here.
          </p>
        )}
      </section>
    </>
  );
}
