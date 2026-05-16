import { NextResponse } from "next/server";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

const CLAUDE_CONFIG = path.join(
  os.homedir(),
  "Library",
  "Application Support",
  "Claude",
  "claude_desktop_config.json"
);
const SERVER_KEY = "hap-rosewood-sand-hill";

type ClaudeConfig = {
  mcpServers?: Record<
    string,
    { command?: string; args?: string[]; env?: Record<string, string> }
  >;
};

export async function GET() {
  let installed = false;
  let raw_config: ClaudeConfig | null = null;
  let other_plugins: string[] = [];
  let hap_entry: ClaudeConfig["mcpServers"] extends infer T
    ? T extends Record<string, infer V>
      ? V | null
      : null
    : null = null;
  let config_path = CLAUDE_CONFIG;
  let config_exists = false;

  try {
    const raw = await fs.readFile(CLAUDE_CONFIG, "utf-8");
    config_exists = true;
    raw_config = JSON.parse(raw) as ClaudeConfig;
    const servers = raw_config.mcpServers || {};
    installed = SERVER_KEY in servers;
    hap_entry = (servers[SERVER_KEY] as never) ?? null;
    other_plugins = Object.keys(servers).filter((k) => k !== SERVER_KEY);
  } catch {
    // Config doesn't exist yet or isn't readable. That's fine.
  }

  return NextResponse.json({
    installed,
    config_exists,
    config_path,
    hap_entry,
    other_plugins,
  });
}
