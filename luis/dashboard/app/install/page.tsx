"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PluginMarketplace } from "@/components/PluginMarketplace";
import { ClaudeDesktopMock } from "@/components/ClaudeDesktopMock";

type InstallStatus = {
  installed: boolean;
  config_exists: boolean;
  config_path: string;
  hap_entry: { command?: string; args?: string[]; env?: Record<string, string> } | null;
  other_plugins: string[];
};

const INSTALL_CMD = "cd luis/server && python install_mcp.py";
const REMOVE_CMD = "cd luis/server && python install_mcp.py --remove";

export default function InstallPage() {
  const [status, setStatus] = useState<InstallStatus | null>(null);
  const [manifest, setManifest] = useState<Record<string, unknown> | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const poll = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([
        fetch("/api/install/status", { cache: "no-store" }).then((r) => r.json()),
        fetch("/api/install/manifest", { cache: "no-store" }).then((r) => r.json()),
      ]);
      setStatus(s);
      setManifest(m);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, [poll]);

  const copy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 1800);
  };

  const installed = status?.installed ?? false;
  const otherPlugins = status?.other_plugins ?? [];
  const tools =
    (manifest && Array.isArray((manifest as { tools?: unknown }).tools)
      ? ((manifest as { tools: { name: string; description: string }[] }).tools)
      : []) ?? [];

  return (
    <div className="max-w-[1400px] mx-auto px-10 py-14">
      {/* hero */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-12">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.32em] text-bronze mb-3">
            Hospitality Agent Protocol · v0.1
          </div>
          <h1 className="font-serif text-6xl text-ink leading-[1.05] tracking-tight">
            Install HAP in your Claude.
          </h1>
          <p className="text-ink/65 mt-5 max-w-2xl text-lg leading-relaxed">
            HAP is an MCP plugin. You install it once. A scope-bounded session
            opens per stay. It auto-disconnects at checkout or TTL. The same
            mental model as Google Drive in your Claude — but for hospitality.
          </p>
        </div>
        <div className="text-right">
          {installed ? (
            <Badge className="bg-forest text-cream uppercase tracking-[0.22em] text-[0.7rem] px-3 py-1.5">
              ● Installed in Claude Desktop
            </Badge>
          ) : (
            <Badge
              variant="outline"
              className="border-bronze/45 text-bronze uppercase tracking-[0.22em] text-[0.7rem] px-3 py-1.5"
            >
              ○ Not installed yet
            </Badge>
          )}
        </div>
      </div>

      {/* install commands */}
      <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-7 mb-12">
        {/* left: command block */}
        <div className="bg-ink rounded-lg overflow-hidden shadow-[0_18px_42px_-24px_rgba(0,0,0,0.5)]">
          <div className="px-7 py-5 border-b border-cream/10 bg-[#1f1f1f]">
            <div className="text-[0.7rem] uppercase tracking-[0.24em] text-cream/55 mb-1.5">
              One command to install
            </div>
            <div className="font-serif text-2xl text-cream leading-tight">
              The whole plugin lifecycle
            </div>
          </div>
          <div className="p-7 space-y-5 text-cream/90 font-mono text-sm leading-relaxed">
            <div>
              <div className="text-cream/45 text-[0.7rem] uppercase tracking-[0.2em] mb-2">
                1 · Install (adds HAP to Claude Desktop config)
              </div>
              <div className="flex items-center gap-3">
                <code className="bg-cream/[0.06] border border-cream/10 rounded px-3.5 py-2.5 flex-1 overflow-x-auto whitespace-nowrap text-cream">
                  {INSTALL_CMD}
                </code>
                <Button
                  size="sm"
                  onClick={() => copy(INSTALL_CMD, "install")}
                  className="bg-cream/10 hover:bg-cream/20 text-cream border border-cream/15 uppercase tracking-[0.16em] text-[0.62rem]"
                >
                  {copied === "install" ? "✓ copied" : "copy"}
                </Button>
              </div>
            </div>
            <div>
              <div className="text-cream/45 text-[0.7rem] uppercase tracking-[0.2em] mb-2">
                2 · Restart Claude Desktop (Cmd+Q, then re-open)
              </div>
              <div className="bg-cream/[0.04] border border-cream/10 rounded px-3.5 py-2.5 text-cream/65 italic">
                You should see <span className="text-forest">hap-rosewood-sand-hill</span>{" "}
                under Settings · Developer · MCP servers.
              </div>
            </div>
            <div>
              <div className="text-cream/45 text-[0.7rem] uppercase tracking-[0.2em] mb-2">
                3 · Use it from any Claude chat
              </div>
              <div className="bg-cream/[0.04] border border-cream/10 rounded px-3.5 py-2.5 text-cream italic">
                "I'm going to Rosewood Sand Hill on May 18. Open the handshake."
              </div>
            </div>
            <div className="pt-2 border-t border-cream/10">
              <div className="text-cream/45 text-[0.7rem] uppercase tracking-[0.2em] mb-2">
                Uninstall
              </div>
              <div className="flex items-center gap-3">
                <code className="bg-cream/[0.06] border border-cream/10 rounded px-3.5 py-2.5 flex-1 overflow-x-auto whitespace-nowrap text-cream/85">
                  {REMOVE_CMD}
                </code>
                <Button
                  size="sm"
                  onClick={() => copy(REMOVE_CMD, "remove")}
                  className="bg-cream/10 hover:bg-cream/20 text-cream border border-cream/15 uppercase tracking-[0.16em] text-[0.62rem]"
                >
                  {copied === "remove" ? "✓ copied" : "copy"}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* right: status panel */}
        <div className="bg-card border border-bronze/20 rounded-lg p-7">
          <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze mb-1.5">
            Local install status
          </div>
          <div className="font-serif text-2xl text-ink leading-tight mb-4">
            On this Mac
          </div>
          <div className="space-y-3 text-sm text-ink/80">
            <Row
              label="Claude config"
              value={
                status?.config_exists
                  ? `found · ${status.config_path.split("/").slice(-3).join("/")}`
                  : "no config yet"
              }
              ok={status?.config_exists ?? false}
            />
            <Row
              label="HAP entry"
              value={installed ? "hap-rosewood-sand-hill registered" : "not yet"}
              ok={installed}
            />
            <Row
              label="Other plugins detected"
              value={
                otherPlugins.length === 0
                  ? "none"
                  : otherPlugins.slice(0, 3).join(", ") +
                    (otherPlugins.length > 3 ? `, +${otherPlugins.length - 3}` : "")
              }
              ok={otherPlugins.length > 0}
            />
            {installed && status?.hap_entry?.command && (
              <div className="pt-3 mt-2 border-t border-bronze/15">
                <div className="text-[0.65rem] text-bronze uppercase tracking-[0.2em] mb-1.5">
                  How Claude launches it
                </div>
                <code className="block bg-cream-soft border border-bronze/15 rounded px-2.5 py-2 text-[0.72rem] font-mono text-ink/75 overflow-x-auto whitespace-nowrap">
                  {status.hap_entry.command} {status.hap_entry.args?.join(" ")}
                </code>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* plugin marketplace + claude desktop mock */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 mb-12">
        <PluginMarketplace hapInstalled={installed} />
        <ClaudeDesktopMock hapInstalled={installed} otherPlugins={otherPlugins} />
      </div>

      {/* tools exposed */}
      <div className="mb-12">
        <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-2">
          What the plugin exposes
        </div>
        <h2 className="font-serif text-4xl text-ink leading-tight mb-2">
          Five tools, one open protocol
        </h2>
        <p className="text-ink/65 mb-7 max-w-2xl">
          Once installed, your Claude can call these directly. Every call is
          scope-checked, TTL-checked, and audit-logged.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {tools.map((t: { name: string; description: string }) => (
            <div
              key={t.name}
              className="bg-card border border-bronze/20 rounded-lg p-5 hover:border-forest/40 transition-colors"
            >
              <code className="font-mono text-[0.85rem] text-forest font-semibold">
                {t.name}
              </code>
              <p className="text-ink/70 text-sm mt-2.5 leading-relaxed">
                {t.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* manifest JSON */}
      {manifest && (
        <div className="bg-card border border-bronze/20 rounded-lg overflow-hidden">
          <div className="px-7 py-5 border-b border-bronze/15 flex items-center justify-between bg-cream-soft/50">
            <div>
              <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze mb-1">
                Plugin manifest
              </div>
              <div className="font-serif text-2xl text-ink leading-tight">
                hap-rosewood-manifest.json
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={() =>
                  copy(JSON.stringify(manifest, null, 2), "manifest")
                }
                className="bg-forest text-cream hover:bg-forest/90 uppercase tracking-[0.16em] text-[0.65rem] px-4"
              >
                {copied === "manifest" ? "✓ copied JSON" : "Copy JSON"}
              </Button>
              <a
                href="/api/install/manifest"
                download="hap-rosewood-manifest.json"
                className="inline-flex items-center bg-ink text-cream uppercase tracking-[0.16em] text-[0.65rem] px-4 py-2 rounded-md font-medium hover:bg-ink/85"
              >
                Download
              </a>
            </div>
          </div>
          <pre className="px-7 py-6 text-[0.78rem] leading-relaxed text-ink/80 overflow-x-auto bg-ink/[0.02] font-mono">
            {JSON.stringify(manifest, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-[0.7rem] uppercase tracking-[0.18em] text-bronze shrink-0 w-32">
        {label}
      </span>
      <span className="text-ink/85 flex items-center gap-2 text-right">
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${
            ok ? "bg-forest" : "bg-bronze/40"
          }`}
        />
        <span className="break-all">{value}</span>
      </span>
    </div>
  );
}
