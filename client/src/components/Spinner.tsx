export default function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-10">
      <span className="size-6 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
      <span className="sr-only">{label}</span>
    </div>
  );
}
