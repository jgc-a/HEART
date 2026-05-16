"""Install the HAP MCP server into Claude Desktop's config.

Run from server/ once your venv is set up:

    python install_mcp.py [--remove]

What it does:
    1. Locates ~/Library/Application Support/Claude/claude_desktop_config.json
       (creates one if absent)
    2. Adds an mcpServers entry named "hap-rosewood-sand-hill" that points at
       this server (main.py) using the venv's python
    3. Reminds you to quit and re-open Claude Desktop

After this, in Claude Desktop you should see "hap-rosewood-sand-hill" listed
alongside any other MCP servers you have (Google Drive, GitHub, etc).
The HAP tools (hap_handshake, hap_propose_arrival, …) become callable from
Claude directly — same pattern as any other plugin.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_PATH = (
    Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
)
SERVER_KEY = "hap-rosewood-sand-hill"


def _venv_python() -> Path:
    candidate = HERE / "venv" / "bin" / "python"
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"⚠️  Existing Claude config is not valid JSON: {exc}")
        print("   I'll back it up to claude_desktop_config.json.bak and start fresh.")
        CONFIG_PATH.with_suffix(".json.bak").write_text(
            CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return {}


def _save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def install() -> int:
    python = _venv_python()
    main_py = HERE / "main.py"
    if not main_py.exists():
        print(f"❌ Can't find {main_py}")
        return 1

    env_extra: dict[str, str] = {}
    for key in ("ANTHROPIC_API_KEY", "DEMO_MODE", "HAP_SIGNING_SECRET"):
        v = os.environ.get(key)
        if v:
            env_extra[key] = v

    config = _load_config()
    servers = config.setdefault("mcpServers", {})
    servers[SERVER_KEY] = {
        "command": str(python),
        "args": [str(main_py)],
        "env": env_extra,
    }
    _save_config(config)

    print("✅ HAP MCP server installed into Claude Desktop")
    print(f"   Config:  {CONFIG_PATH}")
    print(f"   Server:  {main_py}")
    print(f"   Python:  {python}")
    if env_extra:
        print(f"   Env keys forwarded: {', '.join(env_extra.keys())}")
    print()
    print("Now quit Claude Desktop (Cmd+Q, not just the window) and re-open it.")
    print("You should see 'hap-rosewood-sand-hill' listed under Settings → Developer.")
    print("Then in any Claude chat say something like:")
    print('   "What HAP tools are available?"')
    print('   "I\'m going to Rosewood Sand Hill on May 18."')
    return 0


def remove() -> int:
    config = _load_config()
    servers = config.get("mcpServers", {})
    if SERVER_KEY not in servers:
        print("(Nothing to remove — HAP wasn't installed.)")
        return 0
    del servers[SERVER_KEY]
    _save_config(config)
    print("✅ HAP MCP server removed from Claude Desktop config.")
    print("Restart Claude Desktop for the change to take effect.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or remove HAP in Claude Desktop")
    parser.add_argument("--remove", action="store_true", help="Remove HAP from the config")
    args = parser.parse_args()
    return remove() if args.remove else install()


if __name__ == "__main__":
    raise SystemExit(main())
