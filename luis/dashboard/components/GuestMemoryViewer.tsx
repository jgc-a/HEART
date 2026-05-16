"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

type MemoryEntry = {
  chat_id: number | null;
  title: string;
  updated_at_iso: string;
  size_bytes: number;
  filename: string;
  markdown: string;
};

export function GuestMemoryViewer() {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);

  const poll = useCallback(async () => {
    try {
      const r = await fetch("/api/guest-memory", { cache: "no-store" });
      if (!r.ok) return;
      const data = (await r.json()) as { memories: MemoryEntry[] };
      setMemories(data.memories || []);
    } catch {
      /* swallow */
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 2500);
    return () => clearInterval(id);
  }, [poll]);

  const selected = memories[selectedIdx] ?? null;

  return (
    <div className="bg-card border border-bronze/20 rounded-lg overflow-hidden shadow-[0_8px_24px_-12px_rgba(45,74,62,0.18)]">
      <div className="px-7 py-5 border-b border-bronze/15 bg-cream-soft/50 flex flex-col md:flex-row gap-3 md:items-center justify-between">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-1.5 flex items-center gap-2">
            Guest Agent · internalized memory
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                memories.length ? "bg-forest animate-pulse-dot" : "bg-bronze/30"
              }`}
            />
          </div>
          <h3 className="font-serif text-2xl text-ink leading-tight">
            What your Claude now knows
          </h3>
          <p className="text-ink/60 text-sm mt-1 max-w-2xl">
            Returned to the guest agent via{" "}
            <code className="font-mono text-forest">hap_post_stay_memory</code>
            . The agent internalizes it the same way it absorbs data from any
            other MCP plugin. Nothing for the guest to download or open.
            Rendered here read-only so you can verify what crossed the wire.
          </p>
        </div>
        <Badge
          variant="outline"
          className="border-bronze/40 text-bronze uppercase tracking-[0.18em] text-[0.65rem]"
        >
          {memories.length} agent{memories.length === 1 ? "" : "s"} carrying memory
        </Badge>
      </div>

      {memories.length === 0 ? (
        <div className="px-7 py-12 text-center">
          <p className="font-serif italic text-ink/55 text-lg leading-relaxed max-w-xl mx-auto">
            No memory has been handed off yet. Complete a three-phase HAP
            flow (
            <code className="not-italic text-bronze font-mono">/start</code> →
            authorize → confirm) and the property will return the snapshot to
            the guest agent via{" "}
            <code className="not-italic text-bronze font-mono">
              hap_post_stay_memory
            </code>
            .
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] min-h-[480px]">
          {/* sidebar */}
          <div className="border-r border-bronze/15 max-h-[640px] overflow-y-auto">
            {memories.map((m, i) => (
              <button
                key={m.filename}
                onClick={() => setSelectedIdx(i)}
                className={`w-full text-left px-5 py-3.5 border-b border-bronze/10 transition-colors ${
                  i === selectedIdx
                    ? "bg-forest/[0.06] border-l-2 border-l-forest"
                    : "hover:bg-cream-soft/50"
                }`}
              >
                <div className="font-serif text-base text-ink leading-tight line-clamp-2">
                  {m.title.replace(/^Guest Memory · /, "")}
                </div>
                <div className="flex items-center justify-between mt-2 text-[0.65rem] text-ink/45">
                  <span className="font-mono">{m.filename}</span>
                  <span>{(m.size_bytes / 1024).toFixed(1)} KB</span>
                </div>
              </button>
            ))}
          </div>

          {/* viewer */}
          <div className="flex flex-col">
            <div className="px-6 py-3.5 border-b border-bronze/10 bg-cream-soft/30 flex items-center justify-between gap-3 flex-wrap">
              <div className="text-[0.7rem] uppercase tracking-[0.22em] text-bronze">
                {selected
                  ? `Handed off ${new Date(selected.updated_at_iso).toLocaleTimeString()}`
                  : ""}
              </div>
              {selected && (
                <div className="flex items-center gap-2 text-[0.65rem] tracking-[0.18em] uppercase text-forest">
                  <span className="w-1 h-1 rounded-full bg-forest animate-pulse-dot" />
                  internalized via hap_post_stay_memory
                </div>
              )}
            </div>
            <div className="px-7 py-6 overflow-y-auto max-h-[640px] bg-ink/[0.02]">
              {selected ? (
                <pre className="font-mono text-[0.78rem] leading-relaxed text-ink/85 whitespace-pre-wrap">
                  {selected.markdown}
                </pre>
              ) : (
                <div className="text-ink/40 italic text-center py-12">
                  Pick a memory on the left to preview.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="px-7 py-3 border-t border-bronze/15 bg-cream-soft/40 text-[0.7rem] tracking-wide text-ink/55 text-center">
        Schema <code className="font-mono text-bronze">hap-guest-memory/v0.1</code>{" "}
        · transferred agent-to-agent · never persisted on the property side.
      </div>
    </div>
  );
}
