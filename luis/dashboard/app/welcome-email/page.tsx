"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type InstallStatus = {
  installed: boolean;
  config_exists: boolean;
  hap_entry: unknown | null;
};

type State =
  | { kind: "idle" }
  | { kind: "installing" }
  | { kind: "installed_pending_restart" }
  | { kind: "error"; message: string };

export default function WelcomeEmailPage() {
  const [status, setStatus] = useState<InstallStatus | null>(null);
  const [state, setState] = useState<State>({ kind: "idle" });

  const poll = useCallback(async () => {
    try {
      const r = await fetch("/api/install/status", { cache: "no-store" });
      if (!r.ok) return;
      setStatus((await r.json()) as InstallStatus);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 1500);
    return () => clearInterval(id);
  }, [poll]);

  const installed = status?.installed ?? false;
  const buttonDisabled = state.kind === "installing";

  const onConnect = async () => {
    setState({ kind: "installing" });
    try {
      const r = await fetch("/api/install/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const json = (await r.json()) as {
        ok: boolean;
        error?: string;
        stderr?: string;
      };
      if (!json.ok) {
        setState({
          kind: "error",
          message: json.stderr || json.error || "Install failed",
        });
        return;
      }
      setState({ kind: "installed_pending_restart" });
      poll();
    } catch (err) {
      setState({ kind: "error", message: (err as Error).message });
    }
  };

  return (
    <div className="bg-[#ece6d8] min-h-screen py-12 px-4">
      <div className="max-w-[640px] mx-auto">
        {/* Email envelope chrome — mimics an inbox preview */}
        <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-3 flex items-center justify-between">
          <span>Inbox · Rosewood Hotels</span>
          <span className="text-ink/45">May 16, 2026 · 10:42</span>
        </div>

        {/* The email */}
        <div className="bg-cream rounded-lg overflow-hidden shadow-[0_24px_60px_-28px_rgba(45,74,62,0.35)] border border-bronze/15">
          {/* Email header band */}
          <div className="bg-forest text-cream px-10 py-7">
            <div className="text-[0.7rem] tracking-[0.32em] uppercase opacity-70 mb-3">
              Rosewood Sand Hill
            </div>
            <div className="font-serif text-3xl leading-tight">
              Welcome ahead of time, Luis.
            </div>
            <div className="text-cream/75 mt-3 text-[0.95rem]">
              Your stay is set for May 18 — 24. We&apos;re ready when you are.
            </div>
          </div>

          {/* Email body */}
          <div className="px-10 py-9 text-ink/85 text-[0.95rem] leading-relaxed space-y-5">
            <p className="font-serif italic text-ink/70 text-lg leading-snug">
              Dear Luis,
            </p>
            <p>
              Thank you for choosing Rosewood Sand Hill. Your reservation has
              been confirmed, and we are preparing your stay with the same care
              you have come to expect from us.
            </p>

            <div className="rounded-md border border-bronze/25 bg-cream-soft p-5 my-5">
              <div className="text-[0.7rem] uppercase tracking-[0.24em] text-bronze mb-2">
                Something new — 2030
              </div>
              <p className="font-serif text-lg text-ink leading-snug mb-3">
                Let your agent meet ours.
              </p>
              <p className="text-ink/75 text-[0.92rem] leading-relaxed">
                If you use Claude as your personal AI assistant, you can now
                connect Rosewood directly. With one click, your Claude can
                speak to our concierge agent — only with your authorization,
                only for what you allow, only for the time you stay.
              </p>
              <ul className="mt-4 space-y-1.5 text-[0.88rem] text-ink/70">
                <li className="flex gap-2.5">
                  <span className="text-forest">✓</span>
                  Scope-bounded · you choose what to share
                </li>
                <li className="flex gap-2.5">
                  <span className="text-forest">✓</span>
                  Time-bounded · auto-disconnects at checkout (72h TTL)
                </li>
                <li className="flex gap-2.5">
                  <span className="text-forest">✓</span>
                  Zero retention · we query on demand, we never store
                </li>
                <li className="flex gap-2.5">
                  <span className="text-forest">✓</span>
                  Audit visible to you at any time
                </li>
              </ul>
            </div>

            {/* The CTA */}
            <div className="py-4">
              {installed ? (
                <div className="bg-forest/8 border border-forest/40 rounded-md p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="w-2 h-2 rounded-full bg-forest" />
                    <span className="text-forest text-[0.78rem] uppercase tracking-[0.22em] font-semibold">
                      HAP plugin connected
                    </span>
                  </div>
                  <p className="text-ink/80 text-[0.92rem] leading-relaxed">
                    Your Claude is connected to Rosewood. Open any Claude chat
                    and say
                    <em>
                      &nbsp;&ldquo;Open my Rosewood handshake&rdquo;&nbsp;
                    </em>
                    to begin. The plugin will disconnect automatically at
                    checkout — no action required.
                  </p>
                  <div className="mt-3 flex gap-3">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={onConnect}
                      className="border-forest/40 text-forest hover:bg-forest/10 uppercase tracking-[0.16em] text-[0.65rem]"
                    >
                      Reinstall / refresh
                    </Button>
                    <a
                      href="/hap-console"
                      className="inline-flex items-center text-forest text-[0.78rem] underline underline-offset-2 hover:text-forest/80"
                    >
                      Open the live console →
                    </a>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center text-center gap-4 py-4">
                  <Button
                    size="lg"
                    onClick={onConnect}
                    disabled={buttonDisabled}
                    className="bg-forest text-cream hover:bg-forest/90 uppercase tracking-[0.22em] text-[0.78rem] font-medium px-9 py-6 disabled:opacity-50"
                  >
                    {state.kind === "installing"
                      ? "Connecting your Claude…"
                      : "🤝 Connect HAP to my Claude"}
                  </Button>
                  <p className="text-ink/55 text-[0.78rem]">
                    Installs the Rosewood plugin on this Mac · 1 click
                  </p>
                </div>
              )}

              {state.kind === "installed_pending_restart" && !installed && (
                <div className="mt-4 bg-bronze/10 border border-bronze/30 rounded-md p-4 text-[0.85rem] text-ink/75">
                  <strong className="text-bronze uppercase tracking-[0.18em] text-[0.62rem] block mb-1.5">
                    Almost there
                  </strong>
                  The plugin was added. Quit Claude Desktop (Cmd+Q) and re-open
                  it, then come back to this page.
                </div>
              )}

              {state.kind === "error" && (
                <div className="mt-4 bg-rose-50 border border-rose-200 rounded-md p-4 text-[0.85rem] text-rose-900">
                  <strong className="uppercase tracking-[0.18em] text-[0.62rem] block mb-1.5">
                    Install hit a snag
                  </strong>
                  <code className="font-mono text-[0.78rem] block break-all">
                    {state.message}
                  </code>
                </div>
              )}
            </div>

            <p>
              The handshake is built on the open Hospitality Agent Protocol
              (HAP). It works with any AI agent that supports the spec, and we
              have published it openly so the rest of the industry can adopt
              it.
            </p>

            <p className="font-serif italic text-ink/70 mt-7">
              Until then, ahead of time —<br />
              The Rosewood Sand Hill team
            </p>
          </div>

          {/* Email footer */}
          <div className="px-10 py-5 border-t border-bronze/15 bg-cream-soft/40 text-[0.7rem] tracking-wide text-ink/55 flex flex-col md:flex-row justify-between gap-2">
            <span>Reservation SH-2026-0518-LV</span>
            <span>Rosewood Sand Hill · 2825 Sand Hill Road, Menlo Park, CA</span>
          </div>
        </div>

        {/* meta */}
        <div className="mt-6 flex items-center justify-between text-[0.7rem] tracking-wide text-ink/45">
          <span>
            This is the email a 2030 Rosewood guest would receive.
          </span>
          <Badge
            variant="outline"
            className="border-bronze/40 text-bronze uppercase tracking-[0.16em] text-[0.6rem]"
          >
            HAP · open protocol
          </Badge>
        </div>
      </div>
    </div>
  );
}
