"""The horizon: what is new in the public Hermes plugin catalog since last time.

The only network call the whole plugin makes is the catalog JSON (public,
documented, read-only). Everything else is local. Offline, the last known
snapshot is reused so the page still renders.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import home

DEFAULT_CATALOG_URL = "https://hermes-agent.nousresearch.com/docs/api/plugin-catalog.json"
_MAX_NEW = 40


def catalog_url(override: Optional[str] = None) -> str:
    if override:
        return override
    return os.environ.get("HERMES_COCKPIT_CATALOG_URL") or DEFAULT_CATALOG_URL


def fetch_catalog(url: str, timeout: float = 15.0) -> Tuple[Optional[dict], str]:
    """Return ``(catalog, error)`` — exactly one is meaningful. Never raises."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "hermes-cockpit/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed public URL
            raw = response.read().decode("utf-8", "replace")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "catalog JSON is not an object"
        return data, ""
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _entry_summary(entry: dict) -> Dict[str, Any]:
    caps = entry.get("capabilities") if isinstance(entry.get("capabilities"), dict) else {}
    return {
        "name": str(entry.get("name") or ""),
        "description": str(entry.get("description") or ""),
        "category": str(entry.get("category") or "general"),
        "tier": str(entry.get("tier") or "community"),
        "version": str(entry.get("version") or ""),
        "repo": str(entry.get("repo") or ""),
        "docs_url": str(entry.get("docs_url") or ""),
        "platforms": list(entry.get("platforms") or []),
        "provides_tools": list(caps.get("provides_tools") or []),
        "provides_hooks": list(caps.get("provides_hooks") or []),
        "requires_env": list(caps.get("requires_env") or []),
        "sha": str(entry.get("sha") or ""),
    }


def horizon(
    *,
    url: Optional[str] = None,
    seen_file: Optional[Path] = None,
    installed: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fetch the catalog, diff it against the saved snapshot, return the new entries."""
    target = seen_file or home.seen_path()
    snapshot = home.read_json(target, default=None)
    if not isinstance(snapshot, dict):
        snapshot = {}
    seen_names = snapshot.get("names")
    if not isinstance(seen_names, dict):
        seen_names = {}

    catalog, error = fetch_catalog(catalog_url(url))
    offline = catalog is None
    if offline:
        cached = home.read_json(home.cockpit_dir() / "catalog-cache.json", default=None)
        catalog = cached if isinstance(cached, dict) else {"entries": [], "generated_at": None}

    entries = [e for e in (catalog.get("entries") or []) if isinstance(e, dict)]
    baseline = not seen_names and not snapshot.get("baseline_at")

    new: List[Dict[str, Any]] = []
    updated: List[Dict[str, Any]] = []
    installed_set = {str(x) for x in (installed or [])}

    if not baseline:
        for entry in entries:
            name = str(entry.get("name") or "")
            if not name:
                continue
            summary = _entry_summary(entry)
            if name not in seen_names:
                summary["installed"] = name in installed_set
                new.append(summary)
            elif seen_names.get(name) and summary["sha"] and seen_names.get(name) != summary["sha"]:
                summary["installed"] = name in installed_set
                updated.append(summary)

    # Persist the snapshot: union of everything seen, so a plugin that briefly
    # disappears and returns is not re-announced.
    names = dict(seen_names)
    for entry in entries:
        name = str(entry.get("name") or "")
        if name:
            names[name] = str(entry.get("sha") or "")
    home.write_json(
        target,
        {
            "names": names,
            "count": len(names),
            "baseline_at": snapshot.get("baseline_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "catalog_generated_at": catalog.get("generated_at"),
        },
    )

    if not offline:
        home.write_json(home.cockpit_dir() / "catalog-cache.json", catalog)

    new.sort(key=lambda e: (e.get("tier") != "official", e.get("name") or ""))
    return {
        "ok": True,
        "offline": offline,
        "error": error,
        "baseline": baseline,
        "catalog_url": catalog_url(url),
        "catalog_generated_at": catalog.get("generated_at"),
        "catalog_count": len(entries),
        "seen_count": len(names),
        "new": new[:_MAX_NEW],
        "new_count": len(new),
        "new_truncated": max(0, len(new) - _MAX_NEW),
        "updated": updated[:_MAX_NEW],
        "updated_count": len(updated),
        "removed": catalog.get("removed") or [],
        "seen_file": str(target),
    }
