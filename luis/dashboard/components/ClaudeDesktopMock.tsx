"use client";

import { Badge } from "@/components/ui/badge";

type ServerEntry = {
  key: string;
  status: "running" | "stopped";
  tools: number;
};

export function ClaudeDesktopMock({
  hapInstalled,
  otherPlugins,
}: {
  hapInstalled: boolean;
  otherPlugins: string[];
}) {
  // Build a realistic-looking server list.
  const servers: ServerEntry[] = [];
  if (hapInstalled) {
    servers.push({ key: "hap-rosewood-sand-hill", status: "running", tools: 5 });
  }
  for (const p of otherPlugins.slice(0, 6)) {
    servers.push({ key: p, status: "running", tools: 4 });
  }
  if (servers.length === 0) {
    // empty state — keep a placeholder so the mock isn't empty
    servers.push({ key: "(no MCP servers installed)", status: "stopped", tools: 0 });
  }

  return (
    <div className="bg-ink rounded-lg overflow-hidden border border-ink/30 shadow-[0_18px_42px_-22px_rgba(0,0,0,0.55)]">
      {/* mock window chrome */}
      <div className="px-4 py-3 bg-[#2a2a2a] border-b border-ink/40 flex items-center gap-2">
        <span className="w-3 h-3 rounded-full bg-[#ff5f57]" />
        <span className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
        <span className="w-3 h-3 rounded-full bg-[#28c940]" />
        <span className="text-cream/55 text-[0.78rem] mx-auto font-medium">
          Claude · Settings · Developer
        </span>
      </div>

      <div className="px-7 py-7 text-cream/90">
        <div className="text-[0.7rem] uppercase tracking-[0.24em] text-cream/55 mb-2">
          MCP Servers
        </div>
        <div className="font-serif text-2xl text-cream mb-1 leading-tight">
          Local servers
        </div>
        <p className="text-cream/55 text-sm mb-7 max-w-md leading-relaxed">
          MCP servers expose tools, resources, and prompts to Claude.
        </p>

        <ul className="space-y-2.5">
          {servers.map((s, i) => {
            const isHap = s.key === "hap-rosewood-sand-hill";
            return (
              <li
                key={s.key + i}
                className={`flex items-center justify-between px-4 py-3 rounded-md border ${
                  isHap
                    ? "bg-forest/15 border-forest/45 ring-1 ring-forest/30"
                    : "bg-cream/[0.04] border-cream/10"
                }`}
              >
                <div className="min-w-0 flex items-center gap-3">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      s.status === "running"
                        ? isHap
                          ? "bg-forest animate-pulse-dot"
                          : "bg-cream/70"
                        : "bg-cream/25"
                    }`}
                  />
                  <span className="font-mono text-[0.84rem] text-cream truncate">
                    {s.key}
                  </span>
                  {isHap && (
                    <span className="px-1.5 py-0.5 rounded bg-forest/35 text-cream text-[0.6rem] uppercase tracking-[0.18em]">
                      new
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-cream/50 text-[0.72rem] font-mono">
                    {s.tools > 0 ? `${s.tools} tools` : "—"}
                  </span>
                  <span
                    className={`text-[0.65rem] uppercase tracking-[0.18em] ${
                      s.status === "running" ? "text-forest" : "text-cream/35"
                    }`}
                  >
                    {s.status}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>

        <div className="mt-7 pt-5 border-t border-cream/10 flex items-center justify-between text-[0.7rem] text-cream/45">
          <span>
            Servers load on Claude Desktop launch. Restart to apply changes.
          </span>
          {hapInstalled ? (
            <Badge className="bg-forest text-cream uppercase tracking-[0.16em] text-[0.6rem]">
              HAP detected
            </Badge>
          ) : (
            <Badge
              variant="outline"
              className="border-cream/25 text-cream/65 uppercase tracking-[0.16em] text-[0.6rem]"
            >
              HAP not installed
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}
