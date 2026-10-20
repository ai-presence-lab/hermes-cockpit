"""hermes-cockpit — a radar of what your Hermes already has, and of what it could.

Authorship: Agata Śliwińska × Drift. License: MIT.

This module is deliberately import-light and stdlib-only: Hermes may import it
in a bare interpreter (the plugin-admission capability probe does exactly that),
so nothing here reaches into Hermes internals at import time. Everything that
touches the user's Hermes home is done lazily, read-only, inside the handlers.

The plugin registers:
  * a tool ``cockpit`` (actions: scan, horizon, render, summary, all, sectors, set_sectors),
  * an in-session slash command ``/cockpit``,
  * a bundled skill ``hermes-cockpit:hermes-cockpit``.

It never installs, enables, or edits anything. Buttons in the generated page
only copy a prompt to the clipboard for the user to paste to their own agent.
The one file it may write (besides its own state) is the optional sector layout
``<HERMES_HOME>/cockpit/sectors.yaml``, via the ``set_sectors`` action.
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
        "path; 'all' runs scan + horizon + render in one go; 'sectors' returns the "
        "radar's current sectors and assignments; 'set_sectors' validates and writes a "
        "custom sector layout to <HERMES_HOME>/cockpit/sectors.yaml (2-8 sectors). This "
        "tool NEVER installs or enables anything; writing sectors.yaml is the only file "
        "it edits besides its own state."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["scan", "horizon", "summary", "render", "all", "sectors", "set_sectors"],
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
            "sectors": {
                "type": "array",
                "description": (
                    "Only for action='set_sectors'. The radar's sectors, 2 to 8 of them. "
                    "Each entry is {\"id\": \"studio\", \"label\": \"My studio\"} — id is "
                    "required (letters, digits, _ - .), label is optional (max 32 chars) and "
                    "falls back to the default wording for the built-in sector ids."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                    },
                    "required": ["id"],
                },
            },
            "assign": {
                "type": "object",
                "description": (
                    "Only for action='set_sectors'. Maps an item id — a capability id such as "
                    "\"core:image_gen\", or a catalog plugin name such as \"catalog:some-plugin\" "
                    "— to the id of one of the configured sectors. An unknown sector id is "
                    "rejected."
                ),
                "additionalProperties": {"type": "string"},
            },
            "catalog_category_map": {
                "type": "object",
                "description": (
                    "Only for action='set_sectors'. Optional: maps a catalog category (e.g. "
                    "\"media\") to the id of one of the configured sectors."
                ),
                "additionalProperties": {"type": "string"},
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
