import "./globals.css";
import "highlight.js/styles/github.css";

import type { Metadata } from "next";
import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";

export const metadata: Metadata = {
  title: "HypoKiln — capability-wedge-driven idea kiln",
  description:
    "A six-stage idea kiln. Type a paragraph, get a ranked top-3 of micro-SaaS hypotheses anchored on fresh AI capability wedges, with a built-in Market Skeptic.",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-mist bg-cream/80 backdrop-blur sticky top-0 z-30">
          <div className="editorial-shell flex items-center justify-between py-4">
            <Link
              href="/"
              className="flex items-center gap-3 group"
              aria-label="HypoKiln home"
            >
              <span className="inline-block w-8 h-8">
                {/* Inline mark to avoid a network hop */}
                <svg viewBox="0 0 96 96" fill="none" className="w-full h-full">
                  <rect width="96" height="96" rx="20" fill="oklch(96% 0.02 80)" />
                  <path d="M28 18 c2 -6 6 -6 8 0 s6 6 8 0" stroke="oklch(60% 0.18 50)" strokeWidth="2.5" strokeLinecap="round" fill="none" />
                  <path d="M52 18 c2 -6 6 -6 8 0 s6 6 8 0" stroke="oklch(60% 0.18 50)" strokeWidth="2.5" strokeLinecap="round" fill="none" />
                  <path d="M16 80 V54 a32 32 0 0 1 64 0 V80 Z" fill="oklch(28% 0.04 40)" />
                  <path d="M30 80 V64 a18 18 0 0 1 36 0 V80 Z" fill="oklch(96% 0.02 80)" />
                  <path d="M48 78 c-5 -2 -8 -7 -7 -12 c0 -3 2 -5 3 -8 c1 4 2 4 4 6 c0 -4 1 -7 2 -10 c4 4 8 8 8 14 c0 5 -3 9 -8 10 Z" fill="oklch(70% 0.22 55)" />
                  <path d="M48 75 c-2 -1 -4 -3 -3 -6 c2 -1 3 -3 3 -5 c2 3 4 5 4 8 c0 2 -2 4 -4 3 Z" fill="oklch(88% 0.18 80)" />
                </svg>
              </span>
              <span className="font-display text-2xl tracking-tight text-ink group-hover:text-amber transition-colors">
                <span>Hypo</span>
                <span className="text-amber">Kiln</span>
              </span>
            </Link>
            <nav className="flex items-center gap-5 text-supporting text-charcoal">
              <Link href="/" className="hover:text-amber transition-colors">
                Ideas
              </Link>
              <Link href="/wedges" className="hover:text-amber transition-colors">
                Wedges
              </Link>
              <Link href="/portfolio" className="hover:text-amber transition-colors">
                Portfolio
              </Link>
              <Link href="/stats" className="hover:text-amber transition-colors">
                Stats
              </Link>
              <Link href="/templates" className="hover:text-amber transition-colors">
                Templates
              </Link>
              <Link href="/search" className="hover:text-amber transition-colors">
                Search
              </Link>
              <ThemeToggle />
              <Link
                href="/runs/new"
                className="bg-ink text-paper px-4 py-2 rounded-md hover:bg-amber transition-colors"
              >
                New idea
              </Link>
            </nav>
          </div>
        </header>
        <main className="pb-24 pt-12">{children}</main>
      </body>
    </html>
  );
}
