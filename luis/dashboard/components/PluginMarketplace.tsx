"use client";

import { Badge } from "@/components/ui/badge";

type PluginCardData = {
  name: string;
  publisher: string;
  description: string;
  status: "installed" | "available" | "current";
  icon: string;
  toolCount: number;
};

const PEERS: PluginCardData[] = [
  {
    name: "Google Drive",
    publisher: "Google",
    description: "Read and write files in your Drive.",
    status: "installed",
    icon: "📁",
    toolCount: 6,
  },
  {
    name: "GitHub",
    publisher: "GitHub",
    description: "Manage repos, issues, and pull requests.",
    status: "installed",
    icon: "🐙",
    toolCount: 12,
  },
  {
    name: "Google Calendar",
    publisher: "Google",
    description: "Read and create calendar events.",
    status: "installed",
    icon: "📅",
    toolCount: 4,
  },
  {
    name: "Slack",
    publisher: "Slack",
    description: "Read channels and send messages.",
    status: "available",
    icon: "💬",
    toolCount: 8,
  },
];

export function PluginMarketplace({ hapInstalled }: { hapInstalled: boolean }) {
  const hap: PluginCardData = {
    name: "HAP · Rosewood Sand Hill",
    publisher: "Rosewood Hotels",
    description: "Scope-bounded handshake with the property's concierge agent.",
    status: hapInstalled ? "installed" : "current",
    icon: "🏨",
    toolCount: 5,
  };

  const all = [hap, ...PEERS];

  return (
    <div className="bg-card border border-bronze/20 rounded-lg overflow-hidden">
      <div className="px-7 py-4 border-b border-bronze/15 bg-cream-soft/50">
        <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-1">
          Claude · Apps & Plugins
        </div>
        <p className="text-ink/60 text-sm">
          HAP sits next to your everyday plugins. Install once, sessions open per stay.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
        {all.map((p, idx) => (
          <div
            key={p.name}
            className={`px-6 py-5 border-bronze/10 ${
              idx % 2 === 0 ? "md:border-r" : ""
            } ${idx >= 2 ? "border-t" : ""} ${
              p.name.startsWith("HAP")
                ? "bg-forest/[0.04] relative"
                : ""
            }`}
          >
            {p.name.startsWith("HAP") && (
              <div className="absolute top-3 right-4 text-[0.6rem] uppercase tracking-[0.22em] text-forest font-semibold">
                ↳ this plugin
              </div>
            )}
            <div className="flex items-start gap-3.5">
              <span className="text-3xl shrink-0 mt-0.5">{p.icon}</span>
              <div className="min-w-0 flex-1">
                <div className="font-serif text-lg text-ink leading-tight">
                  {p.name}
                </div>
                <div className="text-[0.7rem] text-bronze uppercase tracking-[0.16em] mt-0.5">
                  {p.publisher} · {p.toolCount} tools
                </div>
                <p className="text-ink/65 text-sm mt-2 leading-snug">
                  {p.description}
                </p>
                <div className="mt-3">
                  {p.status === "installed" ? (
                    <Badge className="bg-forest text-cream uppercase tracking-[0.16em] text-[0.6rem]">
                      ✓ Installed
                    </Badge>
                  ) : p.status === "current" ? (
                    <Badge
                      variant="outline"
                      className="border-bronze/45 text-bronze uppercase tracking-[0.16em] text-[0.6rem]"
                    >
                      Available · ready to install
                    </Badge>
                  ) : (
                    <Badge
                      variant="outline"
                      className="border-ink/15 text-ink/55 uppercase tracking-[0.16em] text-[0.6rem]"
                    >
                      Available
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
