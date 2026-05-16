"use client";

import type { FlowStep, FlowStepType } from "@/lib/handshake-flow";

const TYPE_LABEL: Record<FlowStepType, string> = {
  message: "msg",
  action: "thinks",
  consent: "consent",
  event: "event",
};

const TYPE_TINT: Record<FlowStepType, string> = {
  message: "border-bronze/30 bg-cream-soft",
  action: "border-forest/30 bg-forest/5",
  consent: "border-forest/45 bg-forest/8",
  event: "border-bronze/45 bg-bronze/10",
};

export function CommBubble({ step, active }: { step: FlowStep; active: boolean }) {
  return (
    <div
      className={`relative rounded-md border px-3.5 py-2.5 text-[0.78rem] leading-snug ${TYPE_TINT[step.type]} ${
        active ? "shadow-[0_6px_20px_-12px_rgba(45,74,62,0.4)] ring-1 ring-forest/30 animate-fade-in-up" : "opacity-60"
      } transition-all`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[0.6rem] uppercase tracking-[0.2em] text-bronze font-medium">
          {TYPE_LABEL[step.type]}
        </span>
        {step.to !== "self" && (
          <span className="text-[0.6rem] uppercase tracking-[0.18em] text-ink/40">
            → {step.to.replace("_", " ")}
          </span>
        )}
      </div>
      <div className="text-ink font-medium leading-snug">{step.label}</div>
      {step.detail && (
        <div className="text-ink/60 mt-1 text-[0.72rem] leading-snug">{step.detail}</div>
      )}
    </div>
  );
}
