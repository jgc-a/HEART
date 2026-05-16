import type { Metadata } from "next";
import { Inter, Cormorant_Garamond } from "next/font/google";
import Link from "next/link";
import { RosewoodLogo } from "@/components/RosewoodLogo";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const cormorant = Cormorant_Garamond({
  variable: "--font-serif",
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "The View — Rosewood Sand Hill",
  description:
    "The View is Rosewood's operational lens — guests, agent handshakes, and reputation, observed in real time.",
};

const nav = [
  { href: "/", label: "Today's Arrivals" },
  { href: "/hap-console", label: "HAP Console" },
  { href: "/reputation", label: "Reputation Audit" },
  { href: "/welcome-email", label: "Welcome Email" },
  { href: "/install", label: "Install Plugin" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${cormorant.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-cream text-ink">
        <header className="border-b border-bronze/15 bg-cream/80 backdrop-blur-sm sticky top-0 z-30">
          <div className="max-w-[1400px] mx-auto flex items-center justify-between px-10 py-5">
            <Link href="/" className="flex items-baseline gap-3">
              <RosewoodLogo />
              <span className="hidden md:inline text-xs tracking-[0.32em] uppercase text-bronze">
                The View
              </span>
            </Link>
            <nav className="flex items-center gap-9">
              {nav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="text-sm tracking-wide text-ink/80 hover:text-forest transition-colors"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="mt-24 border-t border-bronze/15">
          <div className="max-w-[1400px] mx-auto px-10 py-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs tracking-[0.18em] uppercase text-bronze">
            <span>Powered by HAP — Open Protocol</span>
            <span className="text-ink/40 normal-case tracking-normal">
              Rosewood Sand Hill · Menlo Park
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
