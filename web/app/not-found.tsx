import Link from "next/link";

export default function NotFound() {
  return (
    <div className="editorial-shell text-center py-20">
      <p className="text-micro-label uppercase text-amber">404</p>
      <h1 className="font-display text-headline text-ink mt-2">
        Wedge not found
      </h1>
      <p className="text-charcoal mt-3">
        That idea isn't in the kiln.
      </p>
      <Link
        href="/"
        className="inline-block mt-6 text-amber hover:underline"
      >
        Back to ideas →
      </Link>
    </div>
  );
}
