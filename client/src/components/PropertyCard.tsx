import Image from "next/image";
import Link from "next/link";
import { FiMapPin } from "react-icons/fi";
import { LuBath, LuBedDouble, LuRuler } from "react-icons/lu";

import { formatNumber, formatPrice, mediaUrl } from "@/lib/format";
import type { Property } from "@/lib/types";

export default function PropertyCard({ property }: { property: Property }) {
  return (
    <article className="surface-card group overflow-hidden rounded-xl transition-shadow hover:shadow-lg">
      <Link href={`/properties/${property.slug}`} className="block">
        <div className="relative aspect-[4/3] w-full overflow-hidden bg-brand-50">
          <Image
            src={mediaUrl(property.cover_photo)}
            alt={property.title}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
          <span className="absolute left-3 top-3 rounded-full bg-brand-600 px-3 py-1 text-xs font-semibold text-white">
            {property.advert_type}
          </span>
        </div>

        <div className="space-y-3 p-4">
          <div>
            <h3 className="line-clamp-1 font-semibold">{property.title}</h3>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-muted">
              <FiMapPin className="size-3.5 shrink-0" aria-hidden />
              <span className="line-clamp-1">
                {property.city}, {property.country}
              </span>
            </p>
          </div>

          <p className="text-lg font-bold text-brand-700">{formatPrice(property.price)}</p>

          <dl className="flex flex-wrap gap-x-4 gap-y-1 border-t border-[var(--line)] pt-3 text-sm text-muted">
            <div className="flex items-center gap-1.5">
              <LuBedDouble className="size-4" aria-hidden />
              <dt className="sr-only">Bedrooms</dt>
              <dd>{property.bedrooms}</dd>
            </div>
            <div className="flex items-center gap-1.5">
              <LuBath className="size-4" aria-hidden />
              <dt className="sr-only">Bathrooms</dt>
              <dd>{formatNumber(property.bathrooms)}</dd>
            </div>
            <div className="flex items-center gap-1.5">
              <LuRuler className="size-4" aria-hidden />
              <dt className="sr-only">Plot area</dt>
              <dd>{formatNumber(property.plot_area)} m²</dd>
            </div>
          </dl>
        </div>
      </Link>
    </article>
  );
}
