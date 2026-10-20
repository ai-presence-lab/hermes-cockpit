"""hermes-cockpit — a radar of what your Hermes already has, and of what it could.

Authorship: Agata Śliwińska × Drift. License: MIT.

This module is deliberately import-light and stdlib-only: Hermes may import it
in a bare interpreter (the plugin-admission capability probe does exactly that),
so nothing here reaches into Hermes internals at import time. Everything that
touches the user's Hermes home is done lazily, read-only, inside the handlers.

The plugin registers:
  * a tool ``cockpit`` (actions: scan, horizon, render, summary, all),
  * an in-session slash command ``/cockpit``,
  * a bundled skill ``hermes-cockpit:hermes-cockpit``.

It never installs, enables, or edits anything. Buttons in the generated page
only copy a prompt to the clipboard for the user to paste to their own agent.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).resolve().parent

COCKPIT_SCHEMA: Dict[str, Any] = {
    "name": "cockpit",
    "description": (
        "The Hermes cockpit. Reads the user's Hermes home (read-only) and produces a "
        "retro-futuristic radar page of what is already enabled, what exists but is not "
        "switched on yet, and which NEW catalog plugins appeared since the last check — "
        "each with a plain-language benefit and a TURN ON / MAYBE LATER / NOT NOW "
        "recommendation. Actions: 'scan' returns the raw inventory as JSON; 'horizon' "
        "fetches the public plugin catalog and diffs it against the saved snapshot; "
        "'summary' returns a compact, prompt-friendly briefing for you (the agent) to "
        "write the personal 'what this does for you' lines; 'render' writes the "
        "self-contained HTML page (optionally with your personal notes) and returns its "
        "path; 'all' runs scan + horizon + render in one go. This tool NEVER installs, "
        "enables, or changes anything."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["scan", "horizon", "summary", "render", "all"],
                "description": "Which part of the cockpit to produce. Default: all.",
            },
            "lang": {
                "type": "string",
                "enum": ["en", "pl"],
                "description": "Primary UI language for the rendered page. Default: en.",
            },
            "notes": {
                "type": "object",
                "description": (
                    "Optional personal lines you (the agent) wrote for this specific human, "
                    "keyed by item id (e.g. {\"core:memory\": \"Remembers your projects between "
                    "chats.\"}). Overrides the generic catalog wording in the modal's 'What it "
                    "gives you'. Only used by 'render'/'all'."
                ),
                "additionalProperties": {"type": "string"},
            },
            "catalog_url": {
                "type": "string",
                "description": (
                    "Override the catalog URL (defaults to the public Hermes plugin catalog; "
                    "the env var HERMES_COCKPIT_CATALOG_URL also overrides it). Useful for "
                    "offline tests."
                ),
            },
        },
    },
}


def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    from .cockpit.api import run_action  # lazy: keeps import-time surface stdlib-only

    return run_action(args or {})


def cockpit_handler(args: Dict[str, Any], **kwargs: Any) -> str:
    """Tool handler. Always returns a JSON string; never raises."""
    try:
        return json.dumps(_run(args or {}), ensure_ascii=False, indent=2)
    except Exception as exc:  # pragma: no cover - defensive
        return json.dumps(
            {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False
        )


def _slash_handler(raw_args: str) -> str:
    """`/cockpit` — scan + horizon + render, reply with the page path."""
    try:
        result = _run({"action": "all", "lang": "en", "raw": raw_args})
    except Exception as exc:  # pragma: no cover - defensive
        return f"Cockpit failed: {type(exc).__name__}: {exc}"
    if not result.get("ok", True):
        return f"Cockpit failed: {result.get('error', 'unknown error')}"
    path = (result.get("render") or {}).get("path") or result.get("path") or ""
    new = (result.get("horizon") or {}).get("new_count", 0)
    on = (result.get("inventory") or {}).get("stats", {}).get("enabled_features", "?")
    lines = [
        "🛰  Cockpit ready.",
        f"    Radar: {on} feature(s) switched on.",
        f"    On the horizon: {new} new catalog plugin(s) since the last check.",
    ]
    if path:
        lines.append(f"    Page: {path}")
    return "\n".join(lines)


def register(ctx: Any) -> None:
    """Wire the tool, the slash command and the bundled skill."""
    ctx.register_tool(
        name="cockpit",
        toolset="cockpit",
        schema=COCKPIT_SCHEMA,
        handler=cockpit_handler,
        description="Retro-futuristic radar of your Hermes: what is on, what is available, what is new.",
        emoji="🛰",
    )

    try:
        ctx.register_command(
            "cockpit",
            handler=_slash_handler,
            description="Build the Hermes cockpit page (radar + available features + new catalog plugins).",
        )
    except Exception:  # a host without slash-command support still gets the tool
        logger.debug("hermes-cockpit: slash command registration unavailable")

    try:
        skill_md = _PLUGIN_DIR / "skills" / "hermes-cockpit" / "SKILL.md"
        if skill_md.is_file():
            ctx.register_skill(
                "hermes-cockpit",
                skill_md,
                description="How to fly the Hermes cockpit: scan, horizon, render, and talk to your human.",
            )
    except Exception:
        logger.debug("hermes-cockpit: bundled skill registration unavailable")
