import { NextResponse } from "next/server";
import os from "node:os";
import path from "node:path";

// Project paths so the manifest contains real, copy-pasteable absolute paths.
const PROJECT_ROOT = path.resolve(process.cwd(), "..");
const VENV_PYTHON = path.join(PROJECT_ROOT, "server", "venv", "bin", "python");
const MAIN_PY = path.join(PROJECT_ROOT, "server", "main.py");

const TOOLS = [
  {
    name: "hap_handshake",
    description: "Open a scope-bounded HAP session with the property. Mints a signed consent token with TTL.",
    inputs: ["guest_id", "scope_requested[]", "ttl_hours", "property_id", "client_kind"],
    returns: "session_id, consent_token (HMAC-SHA256), audit_url, consent_checklist_markdown",
  },
  {
    name: "hap_propose_arrival",
    description: "Negotiate an arrival orchestration with the concierge agent within authorized scope.",
    inputs: ["guest_id", "arrival_date", "property_id", "session_id"],
    returns: "staff_brief_markdown, voice_line, flow_profile, orchestration",
  },
  {
    name: "hap_in_stay_action",
    description: "Submit an in-stay intent (e.g. complaint, maintenance, request). Routes to humans per HAP-RULE 4.x when required.",
    inputs: ["guest_id", "intent", "context"],
    returns: "escalation, staff_brief, guest_response",
  },
  {
    name: "hap_post_stay_memory",
    description: "Receive the memory snapshot the property is returning to the guest's agent after checkout.",
    inputs: ["stay_id"],
    returns: "memory_snapshot, retention_confirmation, next_stay_carry_overs",
  },
  {
    name: "hap_generate_dispute_brief",
    description: "Generate a WARDEN-signed brief reconstructing a stay from the immutable audit log — for review disputes.",
    inputs: ["stay_id", "review_text"],
    returns: "brief_markdown, signature_sha256, timeline, total_minutes",
  },
];

export async function GET() {
  const manifest = {
    name: "hap-rosewood-sand-hill",
    display_name: "HAP · Rosewood Sand Hill",
    version: "0.1.0",
    description:
      "The Hospitality Agent Protocol plugin for Rosewood Sand Hill. Lets your Claude talk to the property's HEART agent with scope-bounded consent, TTL, and zero retention.",
    publisher: "Rosewood Hotels (reference implementation)",
    protocol: "HAP/0.1 over MCP",
    transport: "stdio",
    tools: TOOLS,
    lifecycle: {
      install: "python install_mcp.py",
      uninstall: "python install_mcp.py --remove",
      session_ttl_default_hours: 72,
      auto_disconnect: ["TTL expiry", "user checkout", "scope revocation"],
    },
    claude_desktop_config: {
      mcpServers: {
        "hap-rosewood-sand-hill": {
          command: VENV_PYTHON,
          args: [MAIN_PY],
          env: {
            ANTHROPIC_API_KEY: "<your-anthropic-key>",
            HAP_SIGNING_SECRET: "<your-hap-secret>",
            DEMO_MODE: "false",
          },
        },
      },
    },
    install_path_hint: path.join(
      os.homedir(),
      "Library",
      "Application Support",
      "Claude",
      "claude_desktop_config.json"
    ),
    guarantees: [
      "Scope-based consent (no data shared outside the manifest)",
      "Time-to-Live on every session (default 72h)",
      "Zero retention (property queries on demand, never stores)",
      "Hash-chained audit log (SHA-256, tamper-evident)",
      "Right-to-revoke at any time (checkout, /checkout, manual)",
    ],
  };

  return NextResponse.json(manifest, {
    headers: {
      "Content-Disposition": "inline; filename=hap-rosewood-manifest.json",
    },
  });
}
