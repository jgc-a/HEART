"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DisputeBrief, type DisputeData } from "@/components/DisputeBrief";

const FAKE_REVIEW = {
  source: "Tripadvisor",
  stars: 2,
  author: "@anonguest_72",
  text:
    "Stayed at Rosewood Sand Hill — terrible AC, took forever to fix. Worst service. Will not return.",
  postedAt: "May 22, 2026 · 09:14",
};

export default function ReputationPage() {
  const [reviewShown, setReviewShown] = useState(false);
  const [briefLoading, setBriefLoading] = useState(false);
  const [brief, setBrief] = useState<DisputeData | null>(null);

  const simulate = () => {
    setReviewShown(true);
    setBrief(null);
  };

  const generate = async () => {
    setBriefLoading(true);
    try {
      const res = await fetch("/api/dispute/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stay_id: "SH-20260518-LU",
          review_text: FAKE_REVIEW.text,
        }),
      });
      const data = (await res.json()) as DisputeData;
      // small artificial delay so the "generating" state is felt
      await new Promise((r) => setTimeout(r, 600));
      setBrief(data);
    } finally {
      setBriefLoading(false);
    }
  };

  const reset = () => {
    setReviewShown(false);
    setBrief(null);
  };

  return (
    <div className="max-w-[1400px] mx-auto px-10 py-14">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-10">
        <div>
          <div className="text-[0.7rem] uppercase tracking-[0.32em] text-bronze mb-3">
            Rosewood Sand Hill · The View
          </div>
          <h1 className="font-serif text-6xl text-ink leading-[1.05] tracking-tight">
            Reputation Audit
          </h1>
          <p className="text-ink/65 mt-5 max-w-2xl text-lg leading-relaxed">
            When a negative review lands, the General Manager doesn&apos;t scramble.
            The audit trail is already written. A signed brief is one click away.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            size="sm"
            onClick={simulate}
            className="bg-ink text-cream hover:bg-ink/90 uppercase tracking-[0.18em] text-[0.7rem] font-medium px-5"
          >
            Simulate review
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={reset}
            disabled={!reviewShown}
            className="text-ink/55 hover:text-ink uppercase tracking-[0.18em] text-[0.7rem]"
          >
            Reset
          </Button>
        </div>
      </div>

      {!reviewShown ? (
        <div className="bg-card border border-bronze/20 rounded-lg p-16 text-center">
          <div className="text-[0.7rem] uppercase tracking-[0.28em] text-bronze mb-4">
            Standing by
          </div>
          <p className="font-serif italic text-ink/55 text-xl max-w-xl mx-auto leading-relaxed">
            Click <span className="not-italic text-ink/85">Simulate review</span>{" "}
            to drop a hostile 2-star review on the desk and watch the dispute
            workflow.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* the incoming review */}
          <div className="border border-rose-900/20 bg-rose-50/40 rounded-lg p-7 animate-fade-in-up">
            <div className="flex items-center justify-between mb-4">
              <Badge
                variant="outline"
                className="border-rose-900/30 text-rose-900 uppercase tracking-[0.2em] text-[0.65rem]"
              >
                Incoming · {FAKE_REVIEW.source}
              </Badge>
              <div className="text-rose-900 font-mono text-sm">
                {"★".repeat(FAKE_REVIEW.stars)}
                {"☆".repeat(5 - FAKE_REVIEW.stars)}
              </div>
            </div>
            <p className="font-serif text-xl text-ink/85 italic leading-relaxed">
              &ldquo;{FAKE_REVIEW.text}&rdquo;
            </p>
            <div className="text-xs text-ink/50 mt-3 tracking-wide">
              {FAKE_REVIEW.author} · {FAKE_REVIEW.postedAt}
            </div>
          </div>

          {/* CTA + brief */}
          {!brief && (
            <div className="flex items-center justify-center py-6">
              <Button
                size="lg"
                onClick={generate}
                disabled={briefLoading}
                className="bg-forest text-cream hover:bg-forest/90 uppercase tracking-[0.22em] text-[0.78rem] font-medium px-9 py-6"
              >
                {briefLoading ? "Reconstructing timeline…" : "Generate dispute brief"}
              </Button>
            </div>
          )}

          {brief && <DisputeBrief data={brief} />}
        </div>
      )}
    </div>
  );
}
