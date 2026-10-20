"""User-customisable radar sectors.

By default the radar has five fixed sectors (see ``capabilities.SECTORS``). A
user may replace them with their own with an optional file:

    <HERMES_HOME>/cockpit/sectors.yaml

    sectors:
      - id: conversation
        label: "Talking"
      - id: studio
        label: "My studio"
      - id: hands
    assign:                 # capability id or catalog plugin name -> sector id
      core:image_gen: studio
      catalog:some-plugin: studio
    catalog_category_map:   # optional: catalog category -> sector id
      media: studio

Rules (this module never raises on read):

  * missing or invalid file  -> the five default sectors (unchanged behaviour);
  * invalid entries are ignored with a warning carried into the summary;
  * between 2 and 8 sectors; labels at most 32 characters;
  * an ``assign`` that points at an unknown sector is ignored, so the item
    keeps its own default sector.

Writing (``set_sectors``) is the *only* write this plugin performs besides its
own state files, and it is atomic (temp file + ``os.replace``).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import home, i18n
from .capabilities import SECTORS as DEFAULT_SECTORS

MAX_SECTORS = 8
MIN_SECTORS = 2
MAX_LABEL = 32

_ID_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")


class SectorError(ValueError):
    """Raised by :func:`set_sectors` when the requested config is invalid."""


def sectors_path() -> Path:
    """The optional user file inside the cockpit's own state folder."""
    return home.cockpit_dir() / "sectors.yaml"


# ── small cleaners ──────────────────────────────────────────────────────────

def _clean_id(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    sid = value.strip()
    if not sid or len(sid) > 64:
        return None
    if any(ch not in _ID_ALLOWED for ch in sid):
        return None
    return sid


def _default_label_pair(sid: str) -> Dict[str, str]:
    key = "sector_" + sid
    if key in i18n.STRINGS:
        return {"en": i18n.t(key, "en"), "pl": i18n.t(key, "pl")}
    pretty = sid.replace("_", " ").replace("-", " ").replace(".", " ").strip() or sid
    pretty = pretty[:1].upper() + pretty[1:]
    return {"en": pretty[:MAX_LABEL], "pl": pretty[:MAX_LABEL]}


def _label_for(sid: str, raw_label: Any, messages: List[str], index: int) -> Dict[str, str]:
    if raw_label is None:
        return _default_label_pair(sid)
    if not isinstance(raw_label, str):
        messages.append(f"sector #{index} ('{sid}'): label must be text — using the default")
        return _default_label_pair(sid)
    label = " ".join(raw_label.split())
    if not label:
        messages.append(f"sector #{index} ('{sid}'): empty label — using the default")
        return _default_label_pair(sid)
    if len(label) > MAX_LABEL:
        messages.append(f"sector #{index} ('{sid}'): label longer than {MAX_LABEL} characters — shortened")
        label = label[:MAX_LABEL].rstrip()
    return {"en": label, "pl": label}


def _collect_sectors(raw: List[Any], messages: List[str]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    seen: set = set()
    for i, item in enumerate(raw, start=1):
        if isinstance(item, str):
            sid, raw_label = _clean_id(item), None
        elif isinstance(item, dict):
            sid, raw_label = _clean_id(item.get("id")), item.get("label")
        else:
            messages.append(f"sector #{i}: expected a string or a mapping with 'id' — ignored")
            continue
        if sid is None:
            messages.append(f"sector #{i}: missing or invalid id (use letters, digits, _ - .) — ignored")
            continue
        if sid in seen:
            messages.append(f"sector #{i}: duplicate id '{sid}' — ignored")
            continue
        seen.add(sid)
        entries.append({"id": sid, "label": _label_for(sid, raw_label, messages, i)})
    return entries


def _default_sector_entries() -> List[Dict[str, Any]]:
    return [{"id": s, "label": _default_label_pair(s)} for s in DEFAULT_SECTORS]


def _parse_map_lenient(
    value: Any, ids: List[str], field: str, messages: List[str], *, lower: bool
) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if value is None:
        return out
    if not isinstance(value, dict):
        messages.append(f"{field} must be a mapping — ignored")
        return out
    valid = set(ids)
    for raw_key, raw_sid in value.items():
        key = str(raw_key)
        sid = raw_sid.strip() if isinstance(raw_sid, str) else None
        if sid is None or sid not in valid:
            messages.append(f"{field}: '{key}' → unknown sector '{raw_sid}' — ignored (keeps its default)")
            continue
        out[key.lower() if lower else key] = sid
    return out


def _parse_map_strict(value: Any, ids: List[str], field: str, *, lower: bool) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SectorError(f"{field} must be a mapping of item → sector id")
    out: Dict[str, str] = {}
    valid = set(ids)
    for raw_key, raw_sid in value.items():
        if not isinstance(raw_sid, str) or raw_sid.strip() not in valid:
            raise SectorError(
                f"{field}: '{raw_key}' → '{raw_sid}' is not one of the configured sectors "
                f"({', '.join(ids)})"
            )
        out[str(raw_key).lower() if lower else str(raw_key)] = raw_sid.strip()
    return out


# ── the config object ───────────────────────────────────────────────────────

class SectorConfig:
    """The resolved sector layout: the sectors themselves plus the assignments."""

    def __init__(
        self,
        sectors: List[Dict[str, Any]],
        assign: Optional[Dict[str, str]] = None,
        catalog_category_map: Optional[Dict[str, str]] = None,
        warnings: Optional[List[str]] = None,
        custom: bool = False,
    ) -> None:
        self.sectors = sectors
        self.assign = assign or {}
        self.catalog_category_map = catalog_category_map or {}
        self.warnings = list(warnings or [])
        self.custom = custom

    def ids(self) -> List[str]:
        return [s["id"] for s in self.sectors]

    def label_pair(self, sid: str) -> Dict[str, str]:
        for sector in self.sectors:
            if sector["id"] == sid:
                return sector["label"]
        return _default_label_pair(sid)

    def resolve(self, item_id: Any, default_sector: str, category: Any = None) -> str:
        if item_id and str(item_id) in self.assign:
            return self.assign[str(item_id)]
        if category is not None:
            key = str(category).lower()
            if key in self.catalog_category_map:
                return self.catalog_category_map[key]
        return default_sector

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sectors": [
                {"id": s["id"], "label": s["label"]["en"], "label_pl": s["label"]["pl"]}
                for s in self.sectors
            ],
            "assign": dict(self.assign),
            "catalog_category_map": dict(self.catalog_category_map),
            "custom": self.custom,
            "warnings": list(self.warnings),
        }


def default_config(warnings: Optional[List[str]] = None) -> SectorConfig:
    return SectorConfig(_default_sector_entries(), {}, {}, list(warnings or []), False)


# ── loading (lenient) ───────────────────────────────────────────────────────

def load(path: Optional[Path] = None) -> SectorConfig:
    """Read the optional user file. Never raises; falls back to the defaults."""
    yaml_path = Path(path) if path is not None else sectors_path()
    try:
        exists = yaml_path.is_file()
    except Exception:
        exists = False
    if not exists:
        return default_config()

    try:
        import yaml  # type: ignore

        with open(yaml_path, "r", encoding="utf-8-sig") as handle:
            doc = yaml.safe_load(handle)
    except Exception as exc:
        return default_config(
            [f"sectors.yaml could not be read ({type(exc).__name__}) — using the {len(DEFAULT_SECTORS)} default sectors"]
        )

    if doc is None:
        return default_config()
    if not isinstance(doc, dict):
        return default_config(
            [f"sectors.yaml is not a mapping — using the {len(DEFAULT_SECTORS)} default sectors"]
        )

    messages: List[str] = []
    raw_sectors = doc.get("sectors")
    custom = False
    if raw_sectors is None:
        sectors = _default_sector_entries()
    elif not isinstance(raw_sectors, list):
        messages.append("sectors must be a list — using the default sectors")
        sectors = _default_sector_entries()
    else:
        entries = _collect_sectors(raw_sectors, messages)
        if len(entries) > MAX_SECTORS:
            messages.append(f"more than {MAX_SECTORS} sectors configured — keeping the first {MAX_SECTORS}")
            entries = entries[:MAX_SECTORS]
        if len(entries) < MIN_SECTORS:
            messages.append(
                f"need between {MIN_SECTORS} and {MAX_SECTORS} valid sectors — using the default sectors"
            )
            sectors = _default_sector_entries()
        else:
            sectors = entries
            custom = True

    ids = [s["id"] for s in sectors]
    assign = _parse_map_lenient(doc.get("assign"), ids, "assign", messages, lower=False)
    cat_map = _parse_map_lenient(
        doc.get("catalog_category_map"), ids, "catalog_category_map", messages, lower=True
    )
    return SectorConfig(sectors, assign, cat_map, messages, custom)


# ── applying to rendered items ──────────────────────────────────────────────

def apply(cfg: SectorConfig, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return copies of *items* with their ``sector`` resolved against *cfg*.

    Items whose own default sector is not part of the configured layout fall
    back to the first configured sector, so the radar can always place them.
    """
    ids = cfg.ids()
    fallback = ids[0] if ids else DEFAULT_SECTORS[0]
    out: List[Dict[str, Any]] = []
    for item in items:
        item = dict(item)
        default_sector = item.get("sector")
        if default_sector not in ids:
            default_sector = fallback
        category = None
        if item.get("kind") == "catalog":
            category = (item.get("meta") or {}).get("category")
        item["sector"] = cfg.resolve(item.get("id"), default_sector, category)
        out.append(item)
    return out


# ── writing (strict, atomic) ────────────────────────────────────────────────

def _validate_explicit(raw_sectors: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    if not isinstance(raw_sectors, list) or not raw_sectors:
        return [], ["sectors must be a non-empty list of {id, label} entries"]
    entries = _collect_sectors(raw_sectors, errors)
    if len(entries) > MAX_SECTORS:
        errors.append(f"too many sectors ({len(entries)}) — the maximum is {MAX_SECTORS}")
    if len(entries) < MIN_SECTORS:
        errors.append(f"need at least {MIN_SECTORS} valid sectors — got {len(entries)}")
    return entries, errors


def _atomic_write_yaml(path: Path, data: Dict[str, Any]) -> None:
    import yaml  # type: ignore

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
    os.replace(tmp, path)


def _document(entries: List[Dict[str, Any]], assign: Dict[str, str], cat_map: Dict[str, str]) -> Dict[str, Any]:
    sectors_doc: List[Dict[str, Any]] = []
    for entry in entries:
        if entry["label"] == _default_label_pair(entry["id"]):
            sectors_doc.append({"id": entry["id"]})
        else:
            sectors_doc.append({"id": entry["id"], "label": entry["label"]["en"]})
    doc: Dict[str, Any] = {"sectors": sectors_doc}
    if assign:
        doc["assign"] = assign
    if cat_map:
        doc["catalog_category_map"] = cat_map
    return doc


def set_sectors(
    sectors: Any,
    assign: Any = None,
    catalog_category_map: Any = None,
    path: Optional[Path] = None,
) -> SectorConfig:
    """Validate and atomically write the user's sector layout.

    Raises :class:`SectorError` (before writing anything) if the input is
    invalid — wrong number of sectors, bad ids, unknown sector in ``assign``.
    """
    entries, errors = _validate_explicit(sectors)
    if errors:
        raise SectorError("; ".join(errors))
    ids = [e["id"] for e in entries]
    assign_map = _parse_map_strict(assign, ids, "assign", lower=False)
    cat_map = _parse_map_strict(catalog_category_map, ids, "catalog_category_map", lower=True)

    target = Path(path) if path is not None else sectors_path()
    _atomic_write_yaml(target, _document(entries, assign_map, cat_map))
    return SectorConfig(entries, assign_map, cat_map, [], True)
