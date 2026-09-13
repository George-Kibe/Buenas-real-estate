import type { Metadata } from "next";
import { Suspense } from "react";

import Pagination from "@/components/Pagination";
import PropertyCard from "@/components/PropertyCard";
import PropertyFilters from "@/components/PropertyFilters";
import Spinner from "@/components/Spinner";
import { listProperties } from "@/lib/server-api";
import type { PropertyQuery } from "@/lib/types";

export const metadata: Metadata = {
  title: "Properties",
  description: "Browse every property currently listed with Buenas Real Estate.",
};

// Keep in step with PropertyPagination.page_size in apps/properties/pagination.py.
const PAGE_SIZE = 12;

type SearchParams = Record<string, string | string[] | undefined>;

const first = (value: string | string[] | undefined) =>
  Array.isArray(value) ? value[0] : value;

export default async function PropertiesPage({
  searchParams,
}: {
  // searchParams is a Promise as of Next.js 15.
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const page = Number.parseInt(first(params.page) ?? "1", 10) || 1;

  const query: PropertyQuery = {
    page,
    search: first(params.search),
    advert_type: first(params.advert_type),
    property_type: first(params.property_type),
    price__lt: first(params.price__lt),
    ordering: first(params.ordering) ?? "-created_at",
  };

  const results = await listProperties(query);

  const baseParams = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (key !== "page" && value) baseParams.set(key, String(value));
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="text-3xl font-bold">Properties</h1>
      <p className="mt-1 text-muted">
        {results ? `${results.count} listing${results.count === 1 ? "" : "s"}` : "Listings"}
      </p>

      <div className="mt-6">
        <Suspense fallback={<Spinner label="Loading filters" />}>
          <PropertyFilters />
        </Suspense>
      </div>

      {!results ? (
        <p className="surface-card mt-8 rounded-xl p-8 text-center text-muted">
          The listings service is unavailable right now. Please try again shortly.
        </p>
      ) : results.results.length === 0 ? (
        <p className="surface-card mt-8 rounded-xl p-8 text-center text-muted">
          No properties match those filters.
        </p>
      ) : (
        <>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {results.results.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
          <Pagination
            page={page}
            count={results.count}
            pageSize={PAGE_SIZE}
            baseParams={baseParams.toString()}
          />
        </>
      )}
    </div>
  );
}
