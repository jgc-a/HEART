import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The Morning Brief · Rosewood Sand Hill",
  description:
    "The single page a Rosewood Sand Hill General Manager opens at 7 AM. Six questions answered in thirty seconds.",
};

export default function MorningBriefLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
