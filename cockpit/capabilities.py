"""The curated map of Hermes capabilities the cockpit knows how to recognise.

This is deliberately *generic*: no personal names, no site URLs, no machine
paths. Each slot describes one thing Hermes can do, how to tell whether it is
switched on (from the user's own config/inventory), and what it gives a human in
plain language. The cockpit never invents capabilities it cannot describe, and
never claims something is off unless the evidence says so.

A slot's ``detect`` receives ``(config: dict, inventory: dict)`` and returns
True when the capability looks enabled.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

SECTORS = ("conversation", "memory", "time", "creativity", "hands")


def _get(cfg: Any, *path: str) -> Any:
    node = cfg
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _any_platform(cfg: dict, inv: dict) -> bool:
    platforms = _get(cfg, "platforms")
    if isinstance(platforms, dict):
        for name, block in platforms.items():
            if name in {"display", "enabled"}:
                continue
            if block:
                return True
    return bool(inv.get("platforms"))


def _has_mcp(cfg: dict, inv: dict) -> bool:
    servers = _get(cfg, "mcp_servers")
    return bool(isinstance(servers, dict) and servers)


def _has_memory(cfg: dict, inv: dict) -> bool:
    provider = _get(cfg, "memory", "provider")
    if not provider:
        return False
    return str(provider).strip().lower() not in {"", "none", "off", "null"}


def _has_tts(cfg: dict, inv: dict) -> bool:
    return bool(_get(cfg, "tts", "provider"))


def _has_stt(cfg: dict, inv: dict) -> bool:
    return bool(_get(cfg, "stt") or _get(cfg, "transcription") or _get(cfg, "voice"))


def _has_context_engine(cfg: dict, inv: dict) -> bool:
    return bool(_get(cfg, "context", "engine"))


def _has_image_gen(cfg: dict, inv: dict) -> bool:
    return bool(_get(cfg, "image_gen"))


def _has_computer_use(cfg: dict, inv: dict) -> bool:
    return bool(_get(cfg, "computer_use"))


def _toolset_on(inv: dict, name: str) -> bool:
    return name in set(inv.get("toolsets") or [])


SLOTS: List[Dict[str, Any]] = [
    # ── Conversation ────────────────────────────────────────────────────────
    {
        "id": "core:platforms",
        "sector": "conversation",
        "name": {"en": "Chat channels", "pl": "Kanały rozmowy"},
        "benefit": {
            "en": "Talk to your agent from the apps you already have open, instead of only in a terminal.",
            "pl": "Rozmawiaj z agentem z aplikacji, które już masz otwarte, a nie tylko w terminalu.",
        },
        "hint": {
            "en": "Connect a messaging platform (Telegram, Discord, Slack, Signal …).",
            "pl": "Podłącz komunikator (Telegram, Discord, Slack, Signal …).",
        },
        "rec": "turn_on",
        "detect": _any_platform,
    },
    {
        "id": "core:voice_out",
        "sector": "conversation",
        "name": {"en": "Spoken replies", "pl": "Odpowiedzi głosem"},
        "benefit": {
            "en": "Let your agent answer with a voice, so you can listen instead of read.",
            "pl": "Pozwól agentowi odpowiadać głosem — możesz słuchać zamiast czytać.",
        },
        "hint": {"en": "Pick a text-to-speech provider.", "pl": "Wybierz dostawcę mowy (TTS)."},
        "rec": "maybe_later",
        "detect": _has_tts,
    },
    {
        "id": "core:voice_in",
        "sector": "conversation",
        "name": {"en": "Voice messages in", "pl": "Wiadomości głosowe na wejściu"},
        "benefit": {
            "en": "Send a voice note and have it transcribed, so you never have to type a long message.",
            "pl": "Wyślij notatkę głosową, a zostanie przepisana — nie musisz pisać długich wiadomości.",
        },
        "hint": {"en": "Turn on speech-to-text.", "pl": "Włącz rozpoznawanie mowy (STT)."},
        "rec": "maybe_later",
        "detect": _has_stt,
    },
    # ── Memory ──────────────────────────────────────────────────────────────
    {
        "id": "core:memory",
        "sector": "memory",
        "name": {"en": "Long-term memory", "pl": "Pamięć długoterminowa"},
        "benefit": {
            "en": "Your agent remembers who you are and what you are working on, across separate chats.",
            "pl": "Agent pamięta, kim jesteś i nad czym pracujesz — między osobnymi rozmowami.",
        },
        "hint": {"en": "Choose a memory provider.", "pl": "Wybierz dostawcę pamięci."},
        "rec": "turn_on",
        "detect": _has_memory,
    },
    {
        "id": "core:skills",
        "sector": "memory",
        "name": {"en": "Skills", "pl": "Umiejętności (skille)"},
        "benefit": {
            "en": "Reusable written know-how, so your agent does a recurring job the same good way every time.",
            "pl": "Zapisana, wielokrotnego użytku wiedza — agent robi powtarzalną rzecz za każdym razem tak samo dobrze.",
        },
        "hint": {"en": "Add a skill (a folder with a SKILL.md).", "pl": "Dodaj skill (katalog z SKILL.md)."},
        "rec": "turn_on",
        "detect": lambda cfg, inv: bool((inv.get("skills") or {}).get("count")),
    },
    {
        "id": "core:context_engine",
        "sector": "memory",
        "name": {"en": "Context engine", "pl": "Silnik kontekstu"},
        "benefit": {
            "en": "Keeps long conversations coherent by compressing the past instead of forgetting it.",
            "pl": "Utrzymuje spójność długich rozmów — kompresuje przeszłość, zamiast o niej zapominać.",
        },
        "hint": {"en": "Select a context engine.", "pl": "Wybierz silnik kontekstu."},
        "rec": "maybe_later",
        "detect": _has_context_engine,
    },
    # ── Time & initiative ───────────────────────────────────────────────────
    {
        "id": "core:cron",
        "sector": "time",
        "name": {"en": "Scheduled tasks", "pl": "Zadania w harmonogramie"},
        "benefit": {
            "en": "Your agent does things on its own clock — a morning brief, a nightly tidy, a watch on a page.",
            "pl": "Agent robi rzeczy według własnego zegara — poranny przegląd, nocne porządki, pilnowanie strony.",
        },
        "hint": {"en": "Create a cron job.", "pl": "Utwórz zadanie cron."},
        "rec": "turn_on",
        "detect": lambda cfg, inv: bool((inv.get("cron") or {}).get("jobs")),
    },
    {
        "id": "core:kanban",
        "sector": "time",
        "name": {"en": "Kanban board", "pl": "Tablica kanban"},
        "benefit": {
            "en": "A shared task board your agent can pick work from and report back on.",
            "pl": "Wspólna tablica zadań, z której agent bierze pracę i zdaje relację.",
        },
        "hint": {"en": "Enable the kanban plugin.", "pl": "Włącz wtyczkę kanban."},
        "rec": "maybe_later",
        "detect": lambda cfg, inv: "kanban" in set((inv.get("plugins") or {}).get("enabled") or []),
    },
    # ── Creativity ──────────────────────────────────────────────────────────
    {
        "id": "core:image_gen",
        "sector": "creativity",
        "name": {"en": "Image generation", "pl": "Generowanie obrazów"},
        "benefit": {
            "en": "Turn a sentence into a picture — moodboards, sketches, illustrations.",
            "pl": "Zamień zdanie w obraz — moodboardy, szkice, ilustracje.",
        },
        "hint": {"en": "Choose an image-generation backend.", "pl": "Wybierz backend generowania obrazów."},
        "rec": "maybe_later",
        "detect": _has_image_gen,
    },
    {
        "id": "catalog:spotify",
        "sector": "creativity",
        "name": {"en": "Music control", "pl": "Sterowanie muzyką"},
        "benefit": {
            "en": "Your agent can build a playlist or start the right track for the moment.",
            "pl": "Agent potrafi zbudować playlistę albo puścić właściwy utwór w danej chwili.",
        },
        "hint": {"en": "Install a music plugin from the catalog.", "pl": "Zainstaluj wtyczkę muzyczną z katalogu."},
        "rec": "maybe_later",
        "detect": lambda cfg, inv: "spotify" in set((inv.get("plugins") or {}).get("enabled") or []),
    },
    # ── Hands in the world ──────────────────────────────────────────────────
    {
        "id": "core:mcp",
        "sector": "hands",
        "name": {"en": "Connected tools (MCP)", "pl": "Podłączone narzędzia (MCP)"},
        "benefit": {
            "en": "Plug your agent into the other services you use — calendars, notes, code, files.",
            "pl": "Podłącz agenta do innych usług, których używasz — kalendarze, notatki, kod, pliki.",
        },
        "hint": {"en": "Add an MCP server.", "pl": "Dodaj serwer MCP."},
        "rec": "turn_on",
        "detect": _has_mcp,
    },
    {
        "id": "core:web",
        "sector": "hands",
        "name": {"en": "Web search & reading", "pl": "Szukanie i czytanie w sieci"},
        "benefit": {
            "en": "Your agent can look things up and read pages, then tell you what actually matters.",
            "pl": "Agent potrafi wyszukać i przeczytać strony, a potem powiedzieć, co naprawdę ma znaczenie.",
        },
        "hint": {"en": "Enable the web toolset.", "pl": "Włącz zestaw narzędzi web."},
        "rec": "turn_on",
        "detect": lambda cfg, inv: _toolset_on(inv, "web"),
    },
    {
        "id": "core:browser",
        "sector": "hands",
        "name": {"en": "Browser", "pl": "Przeglądarka"},
        "benefit": {
            "en": "Your agent can drive a real browser for pages that need clicking, not just reading.",
            "pl": "Agent prowadzi prawdziwą przeglądarkę tam, gdzie trzeba klikać, a nie tylko czytać.",
        },
        "hint": {"en": "Enable the browser toolset.", "pl": "Włącz zestaw narzędzi przeglądarki."},
        "rec": "maybe_later",
        "detect": lambda cfg, inv: _toolset_on(inv, "browser"),
    },
    {
        "id": "core:computer_use",
        "sector": "hands",
        "name": {"en": "Desktop control", "pl": "Sterowanie pulpitem"},
        "benefit": {
            "en": "Let your agent work your computer's screen and mouse for the last mile of a task.",
            "pl": "Pozwól agentowi pracować na ekranie i myszą — na ostatnim odcinku zadania.",
        },
        "hint": {"en": "Turn on computer-use.", "pl": "Włącz computer-use."},
        "rec": "not_now",
        "detect": _has_computer_use,
    },
]


def detect_all(config: dict, inventory: dict) -> List[Dict[str, Any]]:
    """Return one record per slot with its on/off status and metadata."""
    out: List[Dict[str, Any]] = []
    for slot in SLOTS:
        detect: Callable[[dict, dict], bool] = slot["detect"]
        try:
            on = bool(detect(config or {}, inventory or {}))
        except Exception:
            on = False
        out.append(
            {
                "id": slot["id"],
                "kind": "capability",
                "sector": slot["sector"],
                "name": dict(slot["name"]),
                "benefit": dict(slot["benefit"]),
                "hint": dict(slot["hint"]),
                "rec": slot["rec"],
                "on": on,
            }
        )
    return out
