"""Turning raw facts into a plain-language verdict a non-technical human can act on.

The rule the cockpit follows:
  * TURN ON   — background or simplifying: it works for you without new accounts
                and removes work.
  * MAYBE LATER — worth having, but needs a key, an account, or a decision first.
  * NOT NOW   — heavy, experimental, or a duplicate of something already on.

This module is the *deterministic fallback*. The agent is expected to overwrite
the benefit line with something personal; when it does not, the catalog wording
is used verbatim.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

TURN_ON = "turn_on"
MAYBE_LATER = "maybe_later"
NOT_NOW = "not_now"
ON = "on"

_PROMPT = "Cockpit: I want to turn on {name}. What will it do for us and how do we fly?"

_SENTENCE = re.compile(r"(?<=[.!?])\s+")

# Categories that tend to be "works quietly in the background" — safe to recommend.
_BACKGROUND_CATEGORIES = {"automation", "memory", "general"}
# Categories that usually mean "install it and use it by hand".
_HEAVY_CATEGORIES = {"models", "desktop", "platform"}


def first_sentence(text: str, limit: int = 240) -> str:
    text = " ".join(str(text or "").split())
    if not text:
        return ""
    parts = _SENTENCE.split(text, maxsplit=1)
    sentence = parts[0]
    if len(sentence) < 40 and len(parts) > 1:
        sentence = sentence + " " + parts[1]
    if len(sentence) > limit:
        sentence = sentence[: limit - 1].rstrip() + "…"
    return sentence


def prompt_for(name: str) -> str:
    return _PROMPT.format(name=name)


def recommend_catalog(entry: Dict[str, Any]) -> Dict[str, str]:
    """Verdict + reason for one catalog entry."""
    name = str(entry.get("name") or "this plugin")
    category = str(entry.get("category") or "general").lower()
    tier = str(entry.get("tier") or "community").lower()
    requires_env = list(entry.get("requires_env") or [])
    platforms = list(entry.get("platforms") or [])

    if entry.get("installed"):
        return {
            "verdict": ON,
            "reason": {
                "en": "Already installed on this Hermes.",
                "pl": "Już zainstalowane w tym Hermesie.",
            },
        }

    if tier == "official" and category in _BACKGROUND_CATEGORIES and not requires_env:
        verdict, why_en, why_pl = (
            TURN_ON,
            "Official and works quietly in the background — little to configure.",
            "Oficjalna i działa cicho w tle — niewiele do ustawiania.",
        )
    elif requires_env:
        verdict, why_en, why_pl = (
            MAYBE_LATER,
            "Needs an account or an API key first — a five-minute decision, not a today job.",
            "Wymaga konta lub klucza API — decyzja na pięć minut, nie na dziś.",
        )
    elif category in _HEAVY_CATEGORIES:
        verdict, why_en, why_pl = (
            MAYBE_LATER,
            "Powerful but heavier — worth it once you know you need it.",
            "Mocna, ale cięższa — warto, gdy już wiesz, że jej potrzebujesz.",
        )
    elif category in _BACKGROUND_CATEGORIES:
        verdict, why_en, why_pl = (
            TURN_ON,
            "Background helper — set it up once and forget it.",
            "Pomocnik w tle — ustaw raz i zapomnij.",
        )
    else:
        verdict, why_en, why_pl = (
            MAYBE_LATER,
            "Useful for a specific job — try it when that job shows up.",
            "Przydatna do konkretnego zadania — wypróbuj, gdy się pojawi.",
        )

    if platforms and "windows" not in platforms and platforms != ["windows"]:
        # Only a note; never changes a TURN ON into a block on its own.
        pass

    return {"verdict": verdict, "reason": {"en": why_en, "pl": why_pl}}


def recommend_capability(item: Dict[str, Any]) -> Dict[str, str]:
    if item.get("on"):
        return {
            "verdict": ON,
            "reason": {
                "en": "Switched on and running.",
                "pl": "Włączone i działa.",
            },
        }
    base = item.get("rec") or MAYBE_LATER
    reasons = {
        TURN_ON: (
            "Works in the background and simplifies your day — a good first switch.",
            "Działa w tle i upraszcza dzień — dobry pierwszy przełącznik.",
        ),
        MAYBE_LATER: (
            "Nice to have; turn it on when the need is real.",
            "Miło mieć; włącz, gdy potrzeba stanie się realna.",
        ),
        NOT_NOW: (
            "Heavy and hands-on — leave it for later.",
            "Ciężkie i wymaga uwagi — zostaw na później.",
        ),
    }
    en, pl = reasons.get(base, reasons[MAYBE_LATER])
    return {"verdict": base, "reason": {"en": en, "pl": pl}}


def build_items(
    capabilities: List[Dict[str, Any]],
    horizon: Dict[str, Any],
    notes: Dict[str, str] | None = None,
) -> List[Dict[str, Any]]:
    """Merge capability slots and horizon entries into one render-ready list."""
    notes = notes or {}
    items: List[Dict[str, Any]] = []

    for cap in capabilities:
        rec = recommend_capability(cap)
        item_id = cap["id"]
        note = notes.get(item_id)
        items.append(
            {
                "id": item_id,
                "kind": "capability",
                "sector": cap["sector"],
                "name": cap["name"],
                "status": "on" if cap.get("on") else "off",
                "benefit": {
                    "en": note or cap["benefit"]["en"],
                    "pl": note or cap["benefit"]["pl"],
                },
                "reason": rec["reason"],
                "verdict": rec["verdict"],
                "hint": cap["hint"],
                "source": "core",
                "prompt": prompt_for(cap["name"]["en"]),
            }
        )

    sector_by_category = {
        "memory": "memory",
        "automation": "time",
        "models": "creativity",
        "voice": "conversation",
        "platform": "conversation",
        "web": "hands",
        "tools": "hands",
        "desktop": "hands",
        "general": "hands",
    }

    for entry in horizon.get("new") or []:
        rec = recommend_catalog(entry)
        item_id = f"catalog:{entry['name']}"
        note = notes.get(item_id)
        fallback = first_sentence(entry.get("description", "")) or "A plugin from the Hermes catalog."
        items.append(
            {
                "id": item_id,
                "kind": "catalog",
                "sector": sector_by_category.get(str(entry.get("category") or "").lower(), "hands"),
                "name": {"en": entry["name"], "pl": entry["name"]},
                "status": "new",
                "benefit": {"en": note or fallback, "pl": note or fallback},
                "reason": rec["reason"],
                "verdict": rec["verdict"],
                "hint": {
                    "en": f"From the catalog ({entry.get('tier') or 'community'}): {entry.get('name')}",
                    "pl": f"Z katalogu ({entry.get('tier') or 'community'}): {entry.get('name')}",
                },
                "source": "catalog",
                "prompt": prompt_for(entry["name"]),
                "meta": {
                    "category": entry.get("category"),
                    "tier": entry.get("tier"),
                    "repo": entry.get("repo"),
                    "docs_url": entry.get("docs_url"),
                    "requires_env": entry.get("requires_env"),
                },
            }
        )

    return items
