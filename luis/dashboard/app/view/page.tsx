import Link from "next/link";

export const metadata = {
  title: "The View · Rosewood Sand Hill",
};

type ViewEntry = {
  href: string;
  title: string;
  for: string;
  description: string;
  status: "ready" | "next" | "later";
};

const entries: ViewEntry[] = [
  {
    href: "/view/morning-brief",
    title: "The Morning Brief",
    for: "for the General Manager",
    description:
      "The single page a GM opens at 7 AM. Six questions answered in thirty seconds.",
    status: "ready",
  },
  {
    href: "/view/in-stay",
    title: "In-Stay Matters",
    for: "for the Duty Manager",
    description: "Live shift view of the property — what's open, what's quiet, what just shifted.",
    status: "next",
  },
  {
    href: "/view/arrivals",
    title: "Today's Arrivals",
    for: "for Front Office",
    description: "Each arriving guest with their flow profile, ETA, and adaptive friction settings.",
    status: "next",
  },
  {
    href: "/view/echo",
    title: "ECHO Matters",
    for: "for Housekeeping & Concierge",
    description: "Property restitution signals, discreet recovery, and pre-arrival staging.",
    status: "later",
  },
];

export default function ViewLanding() {
  return (
    <div className="max-w-[1100px] mx-auto px-10 py-20">
      <div className="mb-14">
        <div className="text-[0.7rem] uppercase tracking-[0.32em] text-bronze mb-3">
          Rosewood Sand Hill · The View
        </div>
        <h1 className="font-serif text-6xl text-ink leading-[1.05] tracking-tight">
          The operator views
        </h1>
        <p className="text-ink/65 mt-5 max-w-2xl text-lg leading-relaxed">
          Four screens written for four kinds of attention. Each one is built
          to be read, not navigated.
        </p>
      </div>

      <ul className="space-y-px bg-bronze/20 border border-bronze/20">
        {entries.map((e) => {
          const inner = (
            <div className="bg-cream px-9 py-8 flex items-baseline justify-between gap-10 hover:bg-cream-soft/60 transition-colors">
              <div>
                <h2 className="font-serif text-3xl text-ink leading-tight">{e.title}</h2>
                <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mt-2">
                  {e.for}
                </div>
                <p className="text-ink/65 mt-4 max-w-2xl text-[0.95rem] leading-relaxed">
                  {e.description}
                </p>
              </div>
              <div className="text-[0.7rem] uppercase tracking-[0.24em] shrink-0">
                {e.status === "ready" ? (
                  <span className="text-forest">Attend to →</span>
                ) : e.status === "next" ? (
                  <span className="text-bronze/70">Next</span>
                ) : (
                  <span className="text-ink/30">Later</span>
                )}
              </div>
            </div>
          );
          return (
            <li key={e.href}>
              {e.status === "ready" ? (
                <Link href={e.href} className="block">
                  {inner}
                </Link>
              ) : (
                inner
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
