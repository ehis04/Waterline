import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Waterline — Financial Risk Dashboard",
  description: "Financial risk monitoring and stress testing dashboard",
};

const NAV_TABS = [
  { label: "Home", href: "/" },
  { label: "X-Ray", href: "/x-ray" },
  { label: "Stress", href: "/stress" },
  { label: "Risk Diff", href: "/risk-diff" },
  { label: "Receipts", href: "/receipts" },
] as const;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full min-w-[320px] flex flex-col bg-slate-900 text-slate-50 font-sans">
        <header className="border-b border-slate-800 bg-slate-900/95">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-base font-semibold tracking-tight text-emerald-500">
              Waterline
            </span>
            <nav aria-label="Main navigation" className="overflow-x-auto">
              <ul className="flex items-center gap-1 sm:gap-2">
                {NAV_TABS.map((tab) => (
                  <li key={tab.href} className="shrink-0">
                    <Link
                      href={tab.href}
                      className="inline-block rounded-md px-3 py-1.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                    >
                      {tab.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
