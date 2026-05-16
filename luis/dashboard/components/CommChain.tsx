"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { CommBubble } from "@/components/CommBubble";
import { ResourceChip } from "@/components/ResourceChip";
import {
  LANES,
  luisHandshakeFlow,
  type FlowStep,
  type Lane,
} from "@/lib/handshake-flow";

type RunState = "idle" | "playing" | "paused" | "done";

export function CommChain({
  onStaffBriefReady,
}: {
  onStaffBriefReady?: () => void;
}) {
  const flow = useMemo(() => luisHandshakeFlow, []);
  const [runState, setRunState] = useState<RunState>("idle");
  const [index, setIndex] = useState(-1); // -1 = nothing fired yet
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // group steps by lane (for rendering columns)
  const byLane = useMemo(() => {
    const map: Record<Lane, { step: FlowStep; order: number }[]> = {
      human: [],
      guest_agent: [],
      hotel: [],
      concierge: [],
      arp: [],
    };
    flow.forEach((s, i) => {
      // a step lives in the lane that emits it; ARP messages live in concierge BUT
      // their resources accumulate in arp
      map[s.from].push({ step: s, order: i });
    });
    return map;
  }, [flow]);

  // accumulated ARP resources up to current index
  const arpResources = useMemo(() => {
    const out: { label: string; firedAt: number }[] = [];
    flow.forEach((s, i) => {
      if (i > index) return;
      if (s.to === "arp" && s.resources) {
        s.resources.forEach((r) => out.push({ label: r, firedAt: i }));
      }
    });
    return out;
  }, [flow, index]);

  const advance = useCallback(() => {
    setIndex((prev) => {
      const next = prev + 1;
      if (next >= flow.length) {
        setRunState("done");
        return prev;
      }
      // staff brief is ready by step 9 (concierge → guest_agent suggestions)
      if (flow[next].id === "f9") {
        onStaffBriefReady?.();
      }
      return next;
    });
  }, [flow, onStaffBriefReady]);

  // autoplay
  useEffect(() => {
    if (runState !== "playing") {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }
    if (index >= flow.length - 1) {
      setRunState("done");
      return;
    }
    const currentStep = flow[index >= 0 ? index : 0];
    const delay = index < 0 ? 200 : currentStep.durationMs;
    timerRef.current = setTimeout(advance, delay);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [runState, index, flow, advance]);

  const play = () => setRunState("playing");
  const pause = () => setRunState("paused");
  const step = () => {
    setRunState("paused");
    advance();
  };
  const reset = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setIndex(-1);
    setRunState("idle");
  };

  const currentStep = index >= 0 && index < flow.length ? flow[index] : null;
  const progressPct = ((Math.max(0, index + 1) / flow.length) * 100).toFixed(0);

  return (
    <div className="bg-card border border-bronze/20 rounded-lg shadow-[0_8px_24px_-12px_rgba(45,74,62,0.18)] overflow-hidden">
      {/* header / controls */}
      <div className="px-7 py-5 border-b border-bronze/15 bg-cream-soft/50 flex flex-col md:flex-row gap-4 md:items-center justify-between">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-1.5">
            The Handshake — agent-to-agent
          </div>
          <h3 className="font-serif text-2xl text-ink leading-tight">
            Pre-arrival choreography
          </h3>
          <p className="text-ink/60 text-sm mt-1">
            Five actors. One open protocol. Scope-bounded, time-bounded, audited.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {runState === "playing" ? (
            <Button
              size="sm"
              variant="outline"
              onClick={pause}
              className="border-bronze/40 text-bronze hover:bg-bronze/10 uppercase tracking-[0.18em] text-[0.7rem]"
            >
              Pause
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={play}
              disabled={runState === "done"}
              className="bg-forest text-cream hover:bg-forest/90 uppercase tracking-[0.18em] text-[0.7rem] font-medium px-4"
            >
              {index < 0 ? "Play full sequence" : "Resume"}
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={step}
            disabled={runState === "done"}
            className="border-bronze/40 text-bronze hover:bg-bronze/10 uppercase tracking-[0.18em] text-[0.7rem]"
          >
            Step
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={reset}
            className="text-ink/55 hover:text-ink uppercase tracking-[0.18em] text-[0.7rem]"
          >
            Reset
          </Button>
        </div>
      </div>

      {/* progress bar */}
      <div className="h-[3px] bg-bronze/10 w-full overflow-hidden">
        <div
          className="h-full bg-forest transition-all duration-700 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* 5 swim lanes */}
      <div className="grid grid-cols-5 gap-0 min-h-[520px]">
        {LANES.map((lane, laneIdx) => (
          <div
            key={lane.id}
            className={`flex flex-col ${laneIdx > 0 ? "border-l border-bronze/15" : ""}`}
          >
            <div className="px-4 py-4 border-b border-bronze/15 bg-cream-soft/40 text-center">
              <div className="text-[0.6rem] uppercase tracking-[0.24em] text-bronze mb-1">
                {lane.title}
              </div>
              <div className="font-serif text-[0.95rem] text-ink leading-tight">
                {lane.subtitle}
              </div>
            </div>
            <div className="flex-1 px-3 py-4 space-y-2.5 overflow-y-auto">
              {lane.id === "arp" ? (
                arpResources.length === 0 ? (
                  <div className="text-ink/35 italic text-xs text-center mt-8 font-sans">
                    No resources reserved yet.
                  </div>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    <div className="text-[0.6rem] uppercase tracking-[0.22em] text-bronze mb-1">
                      Reserved
                    </div>
                    {arpResources.map((r, i) => (
                      <ResourceChip
                        key={r.label + i}
                        label={r.label}
                        fresh={r.firedAt === index}
                      />
                    ))}
                  </div>
                )
              ) : (
                byLane[lane.id]
                  .filter(({ order }) => order <= index)
                  .map(({ step: s, order }) => (
                    <CommBubble
                      key={s.id}
                      step={s}
                      active={order === index || order === index - 1}
                    />
                  ))
              )}
              {lane.id !== "arp" && byLane[lane.id].filter(({ order }) => order <= index).length === 0 && (
                <div className="text-ink/35 italic text-xs text-center mt-8 font-sans">
                  Standing by.
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* footer status */}
      <div className="px-7 py-4 border-t border-bronze/15 bg-cream-soft/40 flex items-center justify-between text-[0.72rem] tracking-wide">
        <div className="text-ink/55">
          {currentStep ? (
            <>
              <span className="text-bronze uppercase tracking-[0.18em] mr-2">Now</span>
              <span className="text-ink/75">{currentStep.label}</span>
            </>
          ) : runState === "done" ? (
            <span className="text-forest uppercase tracking-[0.18em]">
              Sequence complete · Stay is ready
            </span>
          ) : (
            <span className="text-ink/40 italic">
              Press Play to begin the handshake.
            </span>
          )}
        </div>
        <div className="text-ink/40 font-mono text-[0.7rem]">
          step {Math.max(0, index + 1)} / {flow.length}
        </div>
      </div>
    </div>
  );
}
