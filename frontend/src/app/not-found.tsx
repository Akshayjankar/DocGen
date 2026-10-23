import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-start justify-center px-4 py-20 sm:px-6">
      <p className="font-mono text-sm text-brand">404</p>
      <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight">
        Sheet not on the press
      </h1>
      <p className="mt-3 text-fg-muted">
        That route isn&apos;t in the folio. Head home or open Studio.
      </p>
      <div className="mt-8 flex gap-3">
        <Link href="/">
          <Button variant="primary">Home</Button>
        </Link>
        <Link href="/studio">
          <Button variant="secondary">Studio</Button>
        </Link>
      </div>
    </div>
  );
}
