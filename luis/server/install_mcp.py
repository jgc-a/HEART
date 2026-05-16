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

# Where each Claude surface keeps its MCP config on macOS.
DESKTOP_CONFIG = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Claude"
    / "claude_desktop_config.json"
)
CODE_CONFIG = Path.home() / ".claude.json"

SERVER_KEY = "hap-rosewood-sand-hill"

TARGETS = {
    "desktop": DESKTOP_CONFIG,
    "code": CODE_CONFIG,
}


def _venv_python() -> Path:
    candidate = HERE / "venv" / "bin" / "python"
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def _load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"⚠️  Config at {path} is not valid JSON: {exc}")
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"   Backed up to {backup}; starting fresh.")
        return {}


def _save_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def _read_dotenv() -> dict[str, str]:
    """Read key=value pairs from server/.env if it exists.

    Used to forward real credentials to Claude Desktop's config, since the
    shell where `python install_mcp.py` runs typically doesn't have them
    exported (and load_dotenv only affects the current process).
    """
    env_file = HERE / ".env"
    result: dict[str, str] = {}
    if not env_file.exists():
        return result
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and v:
            result[k] = v
    return result


def _install_into(target: str, path: Path, python: Path, main_py: Path, env_extra: dict[str, str]) -> bool:
    """Install the HAP MCP server into ONE Claude surface's config."""
    config = _load_config(path)
    servers = config.setdefault("mcpServers", {})
    servers[SERVER_KEY] = {
        "command": str(python),
        "args": [str(main_py)],
        "env": env_extra,
    }
    _save_config(path, config)
    return True


def _remove_from(target: str, path: Path) -> bool:
    config = _load_config(path)
    servers = config.get("mcpServers", {})
    if SERVER_KEY not in servers:
        return False
    del servers[SERVER_KEY]
    if not servers:
        # Don't leave an empty mcpServers key behind if we created it.
        del config["mcpServers"]
    _save_config(path, config)
    return True


def _resolve_targets(target_arg: str) -> list[tuple[str, Path]]:
    """Return [(name, path), ...] for the targets the user asked for."""
    if target_arg == "both":
        return list(TARGETS.items())
    if target_arg in TARGETS:
        return [(target_arg, TARGETS[target_arg])]
    raise ValueError(f"Unknown target: {target_arg}")


def install(target_arg: str) -> int:
    python = _venv_python()
    main_py = HERE / "main.py"
    if not main_py.exists():
        print(f"❌ Can't find {main_py}")
        return 1

    dotenv_vars = _read_dotenv()
    env_extra: dict[str, str] = {}
    for key in (
        "ANTHROPIC_API_KEY",
        "DEMO_MODE",
        "HAP_SIGNING_SECRET",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID",
        "TELEGRAM_BOT_TOKEN",
        "HAP_CLAUDE_MODEL",
    ):
        v = dotenv_vars.get(key) or os.environ.get(key)
        if v:
            env_extra[key] = v

    targets = _resolve_targets(target_arg)
    surfaces: list[str] = []
    for name, path in targets:
        _install_into(name, path, python, main_py, env_extra)
        surfaces.append(name)

    label = {"desktop": "Claude Desktop", "code": "Claude Code"}
    surface_names = " + ".join(label[s] for s in surfaces)
    print(f"✅ HAP MCP server installed into {surface_names}")
    for name, path in targets:
        print(f"   {label[name]:<14} · {path}")
    print(f"   Server:        {main_py}")
    print(f"   Python:        {python}")
    if env_extra:
        print(f"   Env keys forwarded ({len(env_extra)}):")
        for k in env_extra.keys():
            print(f"     · {k}")
    else:
        print("   ⚠️  No env vars forwarded. Create server/.env with at least")
        print("       ANTHROPIC_API_KEY and HAP_SIGNING_SECRET, then re-run.")
    print()
    if "desktop" in surfaces:
        print("Claude Desktop: Cmd+Q to quit fully, then re-open.")
        print("   Confirm under Settings → Developer → MCP servers.")
    if "code" in surfaces:
        print("Claude Code: tools available in the next session.")
        print("   Confirm with `claude mcp list` or open ~/.claude.json.")
    print('Then say in any Claude chat: "I\'m going to Rosewood Sand Hill on May 18."')
    return 0


def remove(target_arg: str) -> int:
    targets = _resolve_targets(target_arg)
    any_removed = False
    for name, path in targets:
        removed = _remove_from(name, path)
        label = {"desktop": "Claude Desktop", "code": "Claude Code"}[name]
        if removed:
            any_removed = True
            print(f"✅ Removed from {label} · {path}")
        else:
            print(f"(Nothing to remove in {label} · {path})")
    if any_removed:
        print()
        print("Restart Claude Desktop (Cmd+Q) and/or open a new Claude Code session.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install or remove HAP in Claude Desktop and/or Claude Code"
    )
    parser.add_argument(
        "--target",
        choices=["desktop", "code", "both"],
        default="both",
        help="Which Claude surface to write to (default: both)",
    )
    parser.add_argument(
        "--remove", action="store_true", help="Remove HAP instead of installing"
    )
    args = parser.parse_args()
    return remove(args.target) if args.remove else install(args.target)


if __name__ == "__main__":
    raise SystemExit(main())
