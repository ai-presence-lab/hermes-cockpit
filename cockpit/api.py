"""The single entry point the tool, the slash command and the tests all call."""

from __future__ import annotations

from typing import Any, Dict, List

from . import capabilities, home, horizon as horizon_mod, inventory, recommend, render
from . import sectors as sectors_mod

_EMPTY_HORIZON = {
    "ok": True,
    "offline": False,
    "baseline": False,
    "new": [],
    "new_count": 0,
    "updated": [],
    "updated_count": 0,
    "catalog_generated_at": None,
    "catalog_count": 0,
    "seen_count": 0,
}


def _clean_notes(raw: Any) -> Dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, str) and value.strip():
            out[str(key)] = value.strip()
    return out


def build_summary(
    inv: Dict[str, Any],
    items: List[Dict[str, Any]],
    hz: Dict[str, Any],
    sector_cfg: "sectors_mod.SectorConfig | None" = None,
) -> str:
    """A compact briefing for the agent to write personal lines from."""
    lines: List[str] = []
    stats = inv.get("stats") or {}
    lines.append("COCKPIT BRIEFING (raw facts — write your own plain-language lines, one per item).")
    lines.append(
        f"Radar: {sum(1 for i in items if i['status'] == 'on')} on · "
        f"{sum(1 for i in items if i['status'] == 'off')} available · "
        f"{hz.get('new_count', 0)} new on the horizon. "
        f"Scheduled jobs: {stats.get('cron_jobs', 0)}. Skills: {stats.get('skills', 0)}."
    )

    if sector_cfg is not None:
        lines.append("")
        if sector_cfg.custom:
            lines.append(
                "RADAR SECTORS (this human's own layout): "
                + ", ".join(f"{s['id']} = \"{s['label']['en']}\"" for s in sector_cfg.sectors)
            )
        if sector_cfg.assign:
            lines.append(
                "SECTOR ASSIGNMENTS: "
                + ", ".join(f"{k} → {v}" for k, v in sector_cfg.assign.items())
            )
        if sector_cfg.catalog_category_map:
            lines.append(
                "CATEGORY → SECTOR: "
                + ", ".join(f"{k} → {v}" for k, v in sector_cfg.catalog_category_map.items())
            )
        for warning in sector_cfg.warnings:
            lines.append(f"WARNING (cockpit/sectors.yaml): {warning} — the affected entry was ignored.")

    off = [i for i in items if i["status"] == "off"]
    if off:
        lines.append("")
        lines.append("AVAILABLE, NOT SWITCHED ON (id · sector · machine verdict):")
        for item in off:
            lines.append(
                f"  {item['id']} · {item['sector']} · {item['verdict']} · {item['name']['en']}"
            )
    new = [i for i in items if i["kind"] == "catalog"]
    if new:
        lines.append("")
        lines.append("NEW IN THE CATALOG (id · tier · machine verdict):")
        for item in new:
            meta = item.get("meta") or {}
            lines.append(
                f"  {item['id']} · {meta.get('tier')} · {item['verdict']} · {item['name']['en']}"
            )
    if hz.get("baseline"):
        lines.append("")
        lines.append("NOTE: this was the first sweep — the baseline is recorded, so the next check will show what is genuinely new.")
    if hz.get("offline"):
        lines.append("")
        lines.append("NOTE: the catalog was unreachable this sweep; the horizon is from the last known snapshot.")

    lines.append("")
    lines.append(
        "NEXT: write one short, personal sentence per item you want to speak about (tie it to what "
        "you know about your human), then call cockpit(action='render', notes={...}) with those "
        "sentences keyed by the ids above. Recommend TURN ON only for background/simplifying "
        "things. Never enable anything without discussing it first."
    )
    return "\n".join(lines)


def run_action(args: Dict[str, Any]) -> Dict[str, Any]:
    action = str(args.get("action") or "all").strip().lower()
    if action not in {"scan", "horizon", "summary", "render", "all", "sectors", "set_sectors"}:
        action = "all"
    lang = str(args.get("lang") or "en").strip().lower()
    if lang not in ("en", "pl"):
        lang = "en"
    notes = _clean_notes(args.get("notes"))
    url = args.get("catalog_url") or None

    # ── sector management: read and write the optional sectors.yaml ──────────
    if action == "sectors":
        cfg = sectors_mod.load()
        return {"ok": True, "action": action, **cfg.to_dict()}

    if action == "set_sectors":
        try:
            cfg = sectors_mod.set_sectors(
                args.get("sectors"),
                args.get("assign"),
                args.get("catalog_category_map"),
            )
        except sectors_mod.SectorError as exc:
            return {"ok": False, "action": action, "error": str(exc)}
        payload = cfg.to_dict()
        payload.update({"ok": True, "action": action, "path": str(sectors_mod.sectors_path())})
        return payload

    inv = inventory.scan()
    cfg = home.load_config()

    if action == "scan":
        return {"ok": True, "action": action, "inventory": inv}

    caps = capabilities.detect_all(cfg, inv)

    hz: Dict[str, Any] = dict(_EMPTY_HORIZON)
    if action in {"horizon", "summary", "render", "all"}:
        hz = horizon_mod.horizon(
            url=url,
            installed=list(inv["plugins"]["enabled"]) + list(inv["plugins"]["installed"]),
        )

    sector_cfg = sectors_mod.load()
    items = recommend.build_items(caps, hz, notes)
    items = sectors_mod.apply(sector_cfg, items)

    result: Dict[str, Any] = {
        "ok": True,
        "action": action,
        "lang": lang,
        "inventory": inv,
        "horizon": hz,
        "items": items,
        "sectors": sector_cfg.to_dict(),
        "stats": {
            "on": sum(1 for i in items if i["status"] == "on"),
            "available": sum(1 for i in items if i["status"] == "off"),
            "new": hz.get("new_count", 0),
        },
    }

    if action in {"render", "all"}:
        result["render"] = render.render_html(items, inv, hz, lang=lang, sectors=sector_cfg)

    if action in {"summary", "render", "horizon", "all"}:
        result["summary"] = build_summary(inv, items, hz, sector_cfg)

    return result
