import Link from "next/link";

interface Props {
  page: number;
  count: number;
  pageSize: number;
  /** Current query string, minus `page`. */
  baseParams: string;
}

export default function Pagination({ page, count, pageSize, baseParams }: Props) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (totalPages <= 1) return null;

  const href = (target: number) => {
    const params = new URLSearchParams(baseParams);
    params.set("page", String(target));
    return `/properties?${params.toString()}`;
  };

  const linkClass =
    "rounded-md border border-[var(--line)] px-3 py-2 text-sm font-medium hover:bg-brand-50 hover:text-brand-700";

  return (
    <nav aria-label="Pagination" className="flex items-center justify-center gap-3 py-8">
      {page > 1 ? (
        <Link href={href(page - 1)} className={linkClass}>
          Previous
        </Link>
      ) : (
        <span className={`${linkClass} pointer-events-none opacity-40`}>Previous</span>
      )}

      <span className="text-sm text-muted">
        Page {page} of {totalPages}
      </span>

      {page < totalPages ? (
        <Link href={href(page + 1)} className={linkClass}>
          Next
        </Link>
      ) : (
        <span className={`${linkClass} pointer-events-none opacity-40`}>Next</span>
      )}
    </nav>
  );
}
