"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

const ADVERT_TYPES = ["For Sale", "For Rent", "Auction"];
const PROPERTY_TYPES = [
  "House",
  "Apartment",
  "Office",
  "Warehouse",
  "Commercial",
  "Other",
];

export default function PropertyFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const setParam = useCallback(
    (key: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
      // Any filter change invalidates the current page number.
      params.delete("page");
      router.push(`/properties?${params.toString()}`);
    },
    [router, searchParams],
  );

  const selectClass =
    "w-full rounded-md border border-[var(--line)] bg-[var(--surface-raised)] px-3 py-2 text-sm";

  return (
    <form
      className="surface-card grid gap-3 rounded-xl p-4 sm:grid-cols-2 lg:grid-cols-4"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        setParam("search", String(data.get("search") ?? ""));
      }}
    >
      <label className="block">
        <span className="mb-1 block text-xs font-medium text-muted">Location</span>
        <input
          name="search"
          type="search"
          defaultValue={searchParams.get("search") ?? ""}
          placeholder="City or country"
          className={selectClass}
        />
      </label>

      <label className="block">
        <span className="mb-1 block text-xs font-medium text-muted">Advert type</span>
        <select
          className={selectClass}
          defaultValue={searchParams.get("advert_type") ?? ""}
          onChange={(event) => setParam("advert_type", event.target.value)}
        >
          <option value="">Any</option>
          {ADVERT_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="mb-1 block text-xs font-medium text-muted">Property type</span>
        <select
          className={selectClass}
          defaultValue={searchParams.get("property_type") ?? ""}
          onChange={(event) => setParam("property_type", event.target.value)}
        >
          <option value="">Any</option>
          {PROPERTY_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="mb-1 block text-xs font-medium text-muted">Max price</span>
        <input
          type="number"
          min={0}
          step={1000}
          defaultValue={searchParams.get("price__lt") ?? ""}
          placeholder="No limit"
          className={selectClass}
          onBlur={(event) => setParam("price__lt", event.target.value)}
        />
      </label>

      <div className="sm:col-span-2 lg:col-span-4">
        <button
          type="submit"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Search
        </button>
      </div>
    </form>
  );
}
