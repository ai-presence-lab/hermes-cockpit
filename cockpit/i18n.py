"""Tiny two-language dictionary for the cockpit UI (English default, Polish included).

Everything the page shows as *chrome* lives here. Item text (benefits, reasons)
travels with each item so the same page can flip language client-side without a
re-render.
"""

from __future__ import annotations

from typing import Dict

LANGUAGES = ("en", "pl")

STRINGS: Dict[str, Dict[str, str]] = {
    # header
    "tagline": {
        "en": "You navigate. Your agent pilots.",
        "pl": "Ty nawigujesz. Twój agent pilotuje.",
    },
    "subtitle": {
        "en": "A radar of what your Hermes already has — and of what it could.",
        "pl": "Radar tego, co Twój Hermes już ma — i tego, co mógłby mieć.",
    },
    "lang_button": {"en": "PL", "pl": "EN"},
    # radar
    "radar_title": {"en": "Radar", "pl": "Radar"},
    "radar_legend_on": {"en": "on", "pl": "włączone"},
    "radar_legend_off": {"en": "available", "pl": "dostępne"},
    "radar_legend_new": {"en": "new", "pl": "nowe"},
    # sectors
    "sector_conversation": {"en": "Conversation", "pl": "Rozmowa"},
    "sector_memory": {"en": "Memory", "pl": "Pamięć"},
    "sector_time": {"en": "Time & initiative", "pl": "Czas i inicjatywa"},
    "sector_creativity": {"en": "Creativity", "pl": "Kreatywność"},
    "sector_hands": {"en": "Hands in the world", "pl": "Ręce w świecie"},
    # panel
    "panel_title": {
        "en": "Available — not switched on yet",
        "pl": "Dostępne — jeszcze nie włączone",
    },
    "panel_empty": {
        "en": "Everything the cockpit knows about is already switched on. Nice flying.",
        "pl": "Wszystko, o czym wie kokpit, jest już włączone. Dobrego lotu.",
    },
    "horizon_title": {"en": "On the horizon", "pl": "Na horyzoncie"},
    "horizon_empty": {
        "en": "No new catalog plugins since the last check.",
        "pl": "Brak nowych wtyczek w katalogu od ostatniego sprawdzenia.",
    },
    "horizon_baseline": {
        "en": "First sweep — baseline recorded. New plugins will show up from the next check.",
        "pl": "Pierwszy skan — zapisano punkt odniesienia. Nowe wtyczki pojawią się od następnego sprawdzenia.",
    },
    "horizon_offline": {
        "en": "Catalog unreachable — showing the last known horizon.",
        "pl": "Katalog nieosiągalny — pokazuję ostatni znany horyzont.",
    },
    # stats
    "stat_features": {"en": "features on", "pl": "włączonych funkcji"},
    "stat_available": {"en": "available", "pl": "dostępnych"},
    "stat_new": {"en": "new on the horizon", "pl": "nowych na horyzoncie"},
    "stat_jobs": {"en": "scheduled jobs", "pl": "zadań w harmonogramie"},
    "stat_skills": {"en": "skills", "pl": "umiejętności"},
    # recommendations
    "rec_turn_on": {"en": "TURN ON", "pl": "WŁĄCZ"},
    "rec_maybe_later": {"en": "MAYBE LATER", "pl": "MOŻE PÓŹNIEJ"},
    "rec_not_now": {"en": "NOT NOW", "pl": "NIE TERAZ"},
    "rec_on": {"en": "ON", "pl": "WŁĄCZONE"},
    "rec_label": {"en": "Recommendation", "pl": "Rekomendacja"},
    # modal / card
    "status_on": {"en": "switched on", "pl": "włączone"},
    "status_off": {"en": "not switched on", "pl": "nie włączone"},
    "what_it_gives": {"en": "What it gives you", "pl": "Co Ci to daje"},
    "turn_on_button": {
        "en": "Turn on → talk to my agent",
        "pl": "Włącz → porozmawiaj z moim agentem",
    },
    "copy_button": {"en": "Copy prompt", "pl": "Kopiuj zapytanie"},
    "copied": {"en": "Prompt copied ✓", "pl": "Zapytanie skopiowane ✓"},
    "copy_manual": {
        "en": "Copy the text below and paste it to your agent:",
        "pl": "Skopiuj tekst poniżej i wklej go swojemu agentowi:",
    },
    "close": {"en": "Close", "pl": "Zamknij"},
    "how_to_turn_on": {"en": "How to turn it on", "pl": "Jak to włączyć"},
    "source_core": {"en": "Built into Hermes", "pl": "Wbudowane w Hermes"},
    "source_catalog": {"en": "From the plugin catalog", "pl": "Z katalogu wtyczek"},
    "more": {"en": "Details", "pl": "Szczegóły"},
    "generated": {"en": "Sweep", "pl": "Skan"},
    "never_installs": {
        "en": "This page changes nothing. It only tells your agent what you want.",
        "pl": "Ta strona niczego nie zmienia. Mówi tylko Twojemu agentowi, czego chcesz.",
    },
    "no_notes": {"en": "", "pl": ""},
}


def t(key: str, lang: str = "en") -> str:
    """Return the string for *key* in *lang*, falling back to English then the key."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get("en") or key


def all_strings() -> Dict[str, Dict[str, str]]:
    return {k: dict(v) for k, v in STRINGS.items()}
