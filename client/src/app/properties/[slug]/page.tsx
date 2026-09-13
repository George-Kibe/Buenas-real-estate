import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { FiEye, FiMapPin } from "react-icons/fi";

import { formatNumber, formatPrice, mediaUrl } from "@/lib/format";
import { getProperty } from "@/lib/server-api";

// params is a Promise as of Next.js 15.
type Params = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { slug } = await params;
  const property = await getProperty(slug);
  if (!property) return { title: "Property not found" };
  return {
    title: property.title,
    description: property.description.slice(0, 160),
  };
}

export default async function PropertyDetailPage({ params }: Params) {
  const { slug } = await params;
  const property = await getProperty(slug);

  if (!property) notFound();

  const gallery = [property.photo1, property.photo2, property.photo3, property.photo4].filter(
    Boolean,
  );

  const facts: Array<[string, string]> = [
    ["Reference", property.ref_code],
    ["Type", property.property_type],
    ["Advert", property.advert_type],
    ["Bedrooms", String(property.bedrooms)],
    ["Bathrooms", formatNumber(property.bathrooms)],
    ["Floors", String(property.total_floors)],
    ["Plot area", `${formatNumber(property.plot_area)} m²`],
    ["Street", property.street_address],
    ["Postal code", property.postal_code],
    ["Listed by", property.user],
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <Link href="/properties" className="text-sm text-brand-700 hover:underline">
        ← Back to properties
      </Link>

      <div className="relative mt-4 aspect-[16/9] w-full overflow-hidden rounded-xl bg-brand-50">
        <Image
          src={mediaUrl(property.cover_photo)}
          alt={property.title}
          fill
          priority
          sizes="(max-width: 1024px) 100vw, 1024px"
          className="object-cover"
        />
      </div>

      {gallery.length ? (
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {gallery.map((photo, index) => (
            <div
              key={photo}
              className="relative aspect-[4/3] overflow-hidden rounded-lg bg-brand-50"
            >
              <Image
                src={mediaUrl(photo)}
                alt={`${property.title} — photo ${index + 1}`}
                fill
                sizes="(max-width: 640px) 50vw, 25vw"
                className="object-cover"
              />
            </div>
          ))}
        </div>
      ) : null}

      <div className="mt-8 grid gap-8 lg:grid-cols-[2fr_1fr]">
        <div>
          <h1 className="text-3xl font-bold">{property.title}</h1>
          <p className="mt-2 flex items-center gap-2 text-muted">
            <FiMapPin className="size-4 shrink-0" aria-hidden />
            {property.street_address}, {property.city}, {property.country}
          </p>
          <p className="mt-1 flex items-center gap-2 text-sm text-muted">
            <FiEye className="size-4 shrink-0" aria-hidden />
            {property.views} view{property.views === 1 ? "" : "s"}
          </p>

          <h2 className="mt-8 text-lg font-semibold">About this property</h2>
          <p className="mt-2 whitespace-pre-line leading-relaxed text-muted">
            {property.description}
          </p>

          <h2 className="mt-8 text-lg font-semibold">Details</h2>
          <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
            {facts.map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs font-medium uppercase tracking-wide text-muted">
                  {label}
                </dt>
                <dd className="mt-0.5 font-medium">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <aside className="surface-card h-fit rounded-xl p-6 lg:sticky lg:top-24">
          <p className="text-sm text-muted">Asking price</p>
          <p className="text-3xl font-bold text-brand-700">{formatPrice(property.price)}</p>
          <p className="mt-1 text-sm text-muted">
            {formatPrice(property.final_property_price)} including{" "}
            {formatNumber(property.tax)} tax
          </p>
          <Link
            href={`/contact?subject=${encodeURIComponent(`Enquiry about ${property.ref_code}`)}`}
            className="mt-6 block rounded-md bg-brand-600 px-4 py-3 text-center font-medium text-white hover:bg-brand-700"
          >
            Enquire about this property
          </Link>
        </aside>
      </div>
    </div>
  );
}
