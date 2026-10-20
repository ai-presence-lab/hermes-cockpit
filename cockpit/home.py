"""Locating the user's Hermes home and reading it, strictly read-only.

Two hard rules live here:
  * never read a secrets file (no ``.env``, no ``auth.json`` values);
  * never write anywhere except the cockpit's own ``<HERMES_HOME>/cockpit/``
    folder.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Keys we are willing to look at inside config.yaml. Anything not listed is
# ignored, so an unknown future field can never leak into the page.
_CONFIG_ALLOWLIST = (
    "plugins",
    "platforms",
    "platform_toolsets",
    "toolsets",
    "enabled_toolsets",
    "memory",
    "mcp_servers",
    "context",
    "image_gen",
    "tts",
    "stt",
    "transcription",
    "voice",
    "computer_use",
    "kanban",
    "model",
    "provider",
)


def hermes_home() -> Path:
    """Resolve the active Hermes home without importing Hermes when possible."""
    try:  # in-process: the authoritative answer
        from hermes_constants import get_hermes_home  # type: ignore

        return Path(get_hermes_home())
    except Exception:
        pass
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".hermes"


def cockpit_dir() -> Path:
    """The cockpit's own folder inside the Hermes home (created on demand)."""
    path = hermes_home() / "cockpit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def seen_path() -> Path:
    return cockpit_dir() / "seen.json"


def html_path() -> Path:
    return cockpit_dir() / "cockpit.html"


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore

        with open(path, "r", encoding="utf-8-sig") as handle:
            data = yaml.safe_load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_config() -> Dict[str, Any]:
    """Read the user's config read-only, filtered to keys we understand.

    Prefers Hermes' own loader (which applies defaults and migrations); falls
    back to a plain YAML read. Never raises.
    """
    cfg: Optional[Dict[str, Any]] = None
    try:
        from hermes_cli.config import load_config_readonly  # type: ignore

        loaded = load_config_readonly()
        if isinstance(loaded, dict):
            cfg = loaded
    except Exception:
        cfg = None
    if cfg is None:
        cfg = _load_yaml(hermes_home() / "config.yaml")
    if not isinstance(cfg, dict):
        return {}
    return {k: cfg.get(k) for k in _CONFIG_ALLOWLIST if k in cfg}


def read_json(path: Path, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    """Atomic-ish write inside the cockpit folder only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
