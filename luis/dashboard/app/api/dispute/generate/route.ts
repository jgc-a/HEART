import { NextResponse } from "next/server";
import crypto from "node:crypto";
import type { DisputeData } from "@/components/DisputeBrief";

const SECRET =
  process.env.HAP_SIGNING_SECRET ||
  "rosewood-heart-warden-demo-secret-do-not-use-in-prod";

const TIMELINE = [
  { time: "17:42", text: "Guest temperature complaint logged via Shadow." },
  { time: "17:43", text: "Shadow silenced. Engineering escalation TRIGGERED." },
  { time: "17:43", text: "Duty Manager paged (dual escalation per HAP-RULE 4.1)." },
  { time: "17:47", text: "Engineer Marco D. arrived. ETA 4 min from page." },
  { time: "17:51", text: "AC unit cycle reset. Confirmed cool airflow." },
  { time: "17:53", text: "Guest acknowledged resolution. Tone: satisfied." },
  { time: "18:10", text: "Complimentary turndown amenity sent." },
];

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as {
    stay_id?: string;
    review_text?: string;
  };
  const stay_id = body.stay_id || "SH-20260518-LU";
  const review_text = body.review_text || "";

  const payload = {
    stay_id,
    review_text,
    timeline: TIMELINE,
    total_minutes: 11,
    dual_escalation: true,
    guest_mood: "satisfied",
  };

  const hash = crypto
    .createHmac("sha256", SECRET)
    .update(JSON.stringify(payload))
    .digest("hex");

  const data: DisputeData = {
    stay_id,
    signed_by: "WARDEN-HEART",
    hash: `${hash.slice(0, 24)}…`,
    generated_at: new Date().toISOString(),
    timeline: TIMELINE,
    total_minutes: 11,
    dual_escalation: true,
    guest_mood: "satisfied",
    summary:
      "Reconstructed from the immutable signal trail. The AC was repaired in eleven minutes under dual human escalation. The guest left the room satisfied. The review&rsquo;s account of &ldquo;forever to fix&rdquo; is not supported by the operational record.",
  };

  return NextResponse.json(data);
}
