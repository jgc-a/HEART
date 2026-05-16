import { NextResponse } from "next/server";
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

const execFileP = promisify(execFile);

const PROJECT_ROOT = path.resolve(process.cwd(), "..");
const SERVER_DIR = path.join(PROJECT_ROOT, "server");
const VENV_PYTHON = path.join(SERVER_DIR, "venv", "bin", "python");
const INSTALL_SCRIPT = path.join(SERVER_DIR, "install_mcp.py");

/**
 * Executes install_mcp.py from the dashboard.
 *
 * This is intentionally localhost-only — the dashboard's purpose is to demo
 * the lifecycle. A real hotel deployment would replace this with a deep
 * link or a Claude-Desktop-native install protocol.
 */
export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as { remove?: boolean };
  const args = [INSTALL_SCRIPT];
  if (body.remove) args.push("--remove");

  try {
    const { stdout, stderr } = await execFileP(VENV_PYTHON, args, {
      cwd: SERVER_DIR,
      timeout: 15_000,
    });
    return NextResponse.json({ ok: true, stdout, stderr });
  } catch (err) {
    const e = err as Error & { stdout?: string; stderr?: string };
    return NextResponse.json(
      {
        ok: false,
        error: e.message,
        stdout: e.stdout,
        stderr: e.stderr,
      },
      { status: 500 }
    );
  }
}
