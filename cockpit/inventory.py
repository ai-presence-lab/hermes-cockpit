"""The radar's raw data: a read-only inventory of the user's Hermes home.

Nothing here is personal by construction — the inventory reports *counts and
names of mechanisms*, never their contents, and never a secret value.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List

from . import home


def _plugin_dirs(root: Path) -> List[str]:
    names: List[str] = []
    try:
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name.startswith((".", "_", "__")):
                continue
            manifest = child / "plugin.yaml"
            if not manifest.is_file():
                manifest = child / "plugin.yml"
            if manifest.is_file():
                meta = home._load_yaml(manifest)
                names.append(str(meta.get("name") or child.name))
            else:
                names.append(child.name)
    except Exception:
        pass
    return names


def _count_skills(root: Path) -> int:
    try:
        return sum(1 for child in root.iterdir() if child.is_dir() and (child / "SKILL.md").is_file())
    except Exception:
        return 0


def _cron_summary(root: Path) -> Dict[str, Any]:
    data = home.read_json(root / "cron" / "jobs.json", default=None)
    jobs: List[Any] = []
    if isinstance(data, dict):
        jobs = data.get("jobs") or []
    elif isinstance(data, list):
        jobs = data
    enabled = 0
    for job in jobs:
        if isinstance(job, dict) and job.get("enabled", True):
            enabled += 1
    return {"jobs": len(jobs), "enabled": enabled}


def _toolsets(cfg: Dict[str, Any]) -> List[str]:
    found: List[str] = []
    for key in ("toolsets", "enabled_toolsets"):
        value = cfg.get(key)
        if isinstance(value, list):
            found.extend(str(v) for v in value)
    per_platform = cfg.get("platform_toolsets")
    if isinstance(per_platform, dict):
        for value in per_platform.values():
            if isinstance(value, list):
                found.extend(str(v) for v in value)
            elif isinstance(value, dict):
                for inner in value.values():
                    if isinstance(inner, list):
                        found.extend(str(v) for v in inner)
    seen: List[str] = []
    for name in found:
        if name not in seen:
            seen.append(name)
    return seen


def _platforms(cfg: Dict[str, Any]) -> List[str]:
    block = cfg.get("platforms")
    if not isinstance(block, dict):
        return []
    out: List[str] = []
    for name, value in block.items():
        if name in {"display", "enabled"}:
            continue
        if value:
            out.append(str(name))
    return sorted(out)


def scan(home_path: Path | None = None) -> Dict[str, Any]:
    """Return the inventory dict. Never raises."""
    root = Path(home_path) if home_path else home.hermes_home()
    cfg = home.load_config()

    plugins_cfg = cfg.get("plugins") if isinstance(cfg.get("plugins"), dict) else {}
    enabled = plugins_cfg.get("enabled") if isinstance(plugins_cfg.get("enabled"), list) else []
    disabled = plugins_cfg.get("disabled") if isinstance(plugins_cfg.get("disabled"), list) else []

    memory_cfg = cfg.get("memory") if isinstance(cfg.get("memory"), dict) else {}
    model_cfg = cfg.get("model") if isinstance(cfg.get("model"), dict) else {}
    mcp = cfg.get("mcp_servers") if isinstance(cfg.get("mcp_servers"), dict) else {}

    cron = _cron_summary(root)
    skills = _count_skills(root / "skills")
    installed = _plugin_dirs(root / "plugins")

    inv: Dict[str, Any] = {
        "hermes_home": str(root),
        "config_present": (root / "config.yaml").is_file(),
        "plugins": {
            "enabled": [str(x) for x in enabled],
            "disabled": [str(x) for x in disabled],
            "installed": installed,
        },
        "platforms": _platforms(cfg),
        "toolsets": _toolsets(cfg),
        "memory": {"provider": memory_cfg.get("provider") or None},
        "mcp_servers": sorted(str(k) for k in mcp.keys()),
        "cron": cron,
        "skills": {"count": skills},
        "model": {
            "provider": model_cfg.get("provider") or cfg.get("provider") or None,
            "name": model_cfg.get("name") or model_cfg.get("model") or None,
        },
        "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    inv["stats"] = {
        "enabled_plugins": len(inv["plugins"]["enabled"]),
        "installed_plugins": len(installed),
        "platforms": len(inv["platforms"]),
        "mcp_servers": len(inv["mcp_servers"]),
        "cron_jobs": cron["jobs"],
        "skills": skills,
    }
    return inv
