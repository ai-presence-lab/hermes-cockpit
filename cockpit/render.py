"""Render the cockpit page: one self-contained HTML file, no external assets.

Design: dark #05070d, glowing amber / cyan / tangerine, scanlines, a rotating
radar sweep, five sectors, a toggle panel grouped by theme, a horizon section, a
modal per item, and a "Turn on → talk to my agent" button that only copies a
prompt to the clipboard. Mobile-first (works at 390px).

Both languages are baked in so the EN/PL toggle needs no re-render.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from . import home, i18n
from . import sectors as sectors_mod


def _esc(text: Any) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _attr_pair(pair: Dict[str, str]) -> str:
    """data-en / data-pl attributes for a two-language string."""
    return f'data-en="{_esc(pair.get("en", ""))}" data-pl="{_esc(pair.get("pl", ""))}"'


def _blip_position(
    item: Dict[str, Any], index_in_sector: int, sector_ids: List[str], sector_angle: float
) -> Dict[str, float]:
    sector_index = sector_ids.index(item["sector"]) if item["sector"] in sector_ids else 0
    # Centre each sector's blips within its wedge.
    base = sector_index * sector_angle + sector_angle / 2.0
    spread = (index_in_sector % 3 - 1) * 9.0
    angle = (base + spread) % 360.0
    status = item.get("status")
    radius = {"on": 70.0, "new": 95.0}.get(status, 118.0)
    return {"angle": angle, "radius": radius}


def _radar(items: List[Dict[str, Any]], sector_list: List[Dict[str, Any]]) -> str:
    cx = cy = 200.0
    n = max(1, len(sector_list))
    sector_angle = 360.0 / n
    sector_ids = [s["id"] for s in sector_list]
    parts: List[str] = []
    parts.append('<svg class="radar" viewBox="0 0 400 400" role="img" aria-label="Radar">')
    parts.append('<defs><radialGradient id="rg" cx="50%" cy="50%" r="50%">'
                 '<stop offset="0%" stop-color="#0a1a22"/><stop offset="100%" stop-color="#05070d"/>'
                 "</radialGradient></defs>")
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="150" fill="url(#rg)"/>')
    for r in (40, 75, 110, 150):
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" class="ring"/>')
    import math

    for i in range(n):
        angle = math.radians(i * sector_angle - 90)
        x = cx + 150 * math.cos(angle)
        y = cy + 150 * math.sin(angle)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" class="spoke"/>')
    # sector labels
    for i, sector in enumerate(sector_list):
        pair = sector["label"]
        angle = math.radians(i * sector_angle + sector_angle / 2 - 90)
        lx = cx + 168 * math.cos(angle)
        ly = cy + 168 * math.sin(angle)
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" class="sector-label" text-anchor="middle" '
            f'{_attr_pair(pair)}'
            f'>{_esc(pair.get("en", sector["id"]))}</text>'
        )
    # sweep
    parts.append(
        '<g class="sweep"><path d="M200,200 L200,50 A150,150 0 0,1 306,94 Z" fill="url(#sweepGrad)"/><animateTransform attributeName="transform" type="rotate" from="0 200 200" to="360 200 200" dur="4.6s" repeatCount="indefinite"/></g>'
    )
    parts.append(
        '<defs><linearGradient id="sweepGrad" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="#3ff3ff" stop-opacity="0"/>'
        '<stop offset="100%" stop-color="#3ff3ff" stop-opacity="0.35"/></linearGradient></defs>'
    )
    # blips
    counts: Dict[str, int] = {}
    for item in items:
        idx = counts.get(item["sector"], 0)
        counts[item["sector"]] = idx + 1
        pos = _blip_position(item, idx, sector_ids, sector_angle)
        angle = math.radians(pos["angle"] - 90)
        x = cx + pos["radius"] * math.cos(angle)
        y = cy + pos["radius"] * math.sin(angle)
        cls = {"on": "blip-on", "new": "blip-new"}.get(item.get("status"), "blip-off")
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="blip {cls}" '
            f'data-item="{_esc(item["id"])}" tabindex="0" role="button">'
            f'<title>{_esc(item["name"]["en"])}</title></circle>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _card(item: Dict[str, Any]) -> str:
    verdict = item.get("verdict", "maybe_later")
    led = {
        "turn_on": "led-amber",
        "maybe_later": "led-cyan",
        "not_now": "led-dim",
        "on": "led-green",
    }.get(verdict, "led-cyan")
    return (
        f'<button class="card" data-item="{_esc(item["id"])}">'
        f'<span class="led {led}"></span>'
        f'<span class="card-name" {_attr_pair(item["name"])}>{_esc(item["name"]["en"])}</span>'
        f'<span class="card-benefit" {_attr_pair(item["benefit"])}>{_esc(item["benefit"]["en"])}</span>'
        f'<span class="card-verdict" {_attr_pair({"en": i18n.t("rec_" + verdict, "en"), "pl": i18n.t("rec_" + verdict, "pl")})}>'
        f'{_esc(i18n.t("rec_" + verdict, "en"))}</span>'
        "</button>"
    )


def render_html(
    items: List[Dict[str, Any]],
    inventory: Dict[str, Any],
    horizon: Dict[str, Any],
    *,
    lang: str = "en",
    out_path: Path | None = None,
    sectors: "sectors_mod.SectorConfig | None" = None,
) -> Dict[str, Any]:
    lang = lang if lang in i18n.LANGUAGES else "en"
    sector_cfg = sectors if sectors is not None else sectors_mod.load()
    sector_list = sector_cfg.sectors

    available = [i for i in items if i.get("status") == "off"]
    horizon_items = [i for i in items if i.get("kind") == "catalog"]
    on_count = sum(1 for i in items if i.get("status") == "on")
    stats = inventory.get("stats") or {}

    # group available by sector
    grouped: Dict[str, List[Dict[str, Any]]] = {s["id"]: [] for s in sector_list}
    for item in available:
        grouped.setdefault(item["sector"], []).append(item)
    panel = []
    for sector in sector_list:
        bucket = grouped.get(sector["id"]) or []
        if not bucket:
            continue
        pair = sector["label"]
        panel.append(
            f'<h3 class="sector-head" {_attr_pair(pair)}>'
            f'{_esc(pair.get(lang, pair.get("en", sector["id"])))}</h3>'
        )
        panel.append('<div class="cards">' + "".join(_card(i) for i in bucket) + "</div>")
    if not panel:
        panel.append(f'<p class="muted" {_attr_pair({"en": i18n.t("panel_empty", "en"), "pl": i18n.t("panel_empty", "pl")})}>'
                     f'{_esc(i18n.t("panel_empty", lang))}</p>')

    if horizon.get("baseline"):
        horizon_note = i18n.t("horizon_baseline", lang)
        horizon_note_pair = {"en": i18n.t("horizon_baseline", "en"), "pl": i18n.t("horizon_baseline", "pl")}
    elif horizon.get("offline"):
        horizon_note = i18n.t("horizon_offline", lang)
        horizon_note_pair = {"en": i18n.t("horizon_offline", "en"), "pl": i18n.t("horizon_offline", "pl")}
    else:
        horizon_note = ""
        horizon_note_pair = {"en": "", "pl": ""}

    if horizon_items:
        horizon_html = '<div class="cards">' + "".join(_card(i) for i in horizon_items) + "</div>"
    else:
        horizon_html = f'<p class="muted" {_attr_pair(horizon_note_pair or {"en": i18n.t("horizon_empty", "en"), "pl": i18n.t("horizon_empty", "pl")})}>' \
                       f'{_esc(horizon_note or i18n.t("horizon_empty", lang))}</p>'

    data = {
        "items": items,
        "strings": i18n.all_strings(),
        "lang": lang,
        "generated": inventory.get("scanned_at"),
        "catalog_generated_at": horizon.get("catalog_generated_at"),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    title = "HERMES COCKPIT"
    html = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{title}</title>
<style>
:root{{--bg:#05070d;--amber:#ffb347;--cyan:#3ff3ff;--tang:#ff8a3d;--dim:#5a6b7a;--ink:#cfe3ee;}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--bg);color:var(--ink);
 font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace;line-height:1.45}}
body{{position:relative;padding:14px 12px 40px;overflow-x:hidden}}
body::after{{content:"";position:fixed;inset:0;pointer-events:none;z-index:9;
 background:repeating-linear-gradient(0deg,rgba(63,243,255,.045) 0 1px,transparent 1px 3px)}}
header{{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:space-between}}
h1{{font-size:19px;letter-spacing:.22em;margin:0;color:var(--amber);
 text-shadow:0 0 10px rgba(255,179,71,.55)}}
.tagline{{color:var(--cyan);font-size:12px;letter-spacing:.08em;text-shadow:0 0 8px rgba(63,243,255,.4)}}
.subtitle{{color:var(--dim);font-size:11px;margin:2px 0 12px}}
#lang{{background:transparent;border:1px solid var(--cyan);color:var(--cyan);border-radius:6px;
 padding:4px 10px;font:inherit;font-size:11px;cursor:pointer}}
#lang:hover{{background:rgba(63,243,255,.12)}}
.stats{{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 14px}}
.stat{{flex:1 1 96px;border:1px solid rgba(63,243,255,.25);border-radius:10px;padding:8px 10px;
 background:linear-gradient(180deg,rgba(63,243,255,.06),transparent)}}
.stat b{{display:block;font-size:20px;color:var(--amber);text-shadow:0 0 8px rgba(255,179,71,.5)}}
.stat span{{font-size:10px;color:var(--dim)}}
.grid{{display:grid;gap:16px}}
@media(min-width:760px){{.grid{{grid-template-columns:minmax(320px,1fr) minmax(320px,1fr)}}}}
.radar-wrap{{border:1px solid rgba(255,179,71,.25);border-radius:14px;padding:10px;
 background:radial-gradient(circle at 50% 45%,rgba(255,138,61,.07),transparent 70%)}}
svg.radar{{width:100%;height:auto;display:block;max-width:460px;margin:0 auto}}
.ring{{fill:none;stroke:rgba(63,243,255,.20)}}
.spoke{{stroke:rgba(63,243,255,.16)}}
.sector-label{{fill:var(--dim);font-size:10px;letter-spacing:.06em}}
@media(prefers-reduced-motion:reduce){{.sweep{{display:none}}}}
.blip{{cursor:pointer}}
.blip-on{{fill:#7CFFB2;filter:drop-shadow(0 0 6px #7CFFB2)}}
.blip-new{{fill:var(--tang);filter:drop-shadow(0 0 8px var(--tang));animation:pulse 1.6s ease-in-out infinite}}
.blip-off{{fill:var(--cyan);opacity:.85;filter:drop-shadow(0 0 5px rgba(63,243,255,.7))}}
@keyframes pulse{{50%{{opacity:.35}}}}
.legend{{display:flex;gap:12px;justify-content:center;font-size:10px;color:var(--dim);margin-top:4px}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:middle}}
h2{{font-size:13px;letter-spacing:.14em;color:var(--amber);text-transform:uppercase;
 border-bottom:1px solid rgba(255,179,71,.25);padding-bottom:6px;margin:4px 0 10px}}
h3.sector-head{{font-size:11px;letter-spacing:.1em;color:var(--cyan);margin:12px 0 6px;text-transform:uppercase}}
.cards{{display:grid;gap:8px}}
@media(min-width:560px){{.cards{{grid-template-columns:1fr 1fr}}}}
.card{{text-align:left;display:grid;grid-template-columns:auto 1fr;gap:4px 8px;align-items:center;
 width:100%;background:rgba(10,26,34,.6);border:1px solid rgba(63,243,255,.22);border-radius:10px;
 padding:10px;color:var(--ink);font:inherit;cursor:pointer;transition:border-color .15s,transform .15s}}
.card:hover{{border-color:var(--amber);transform:translateY(-1px)}}
.card-name{{font-size:12px;color:#eaf6fb}}
.card-benefit{{grid-column:2;font-size:11px;color:var(--dim)}}
.card-verdict{{grid-column:2;font-size:9px;letter-spacing:.12em;color:var(--amber)}}
.led{{width:9px;height:9px;border-radius:50%;box-shadow:0 0 8px currentColor}}
.led-amber{{background:var(--amber);color:var(--amber)}}
.led-cyan{{background:var(--cyan);color:var(--cyan)}}
.led-dim{{background:var(--dim);color:var(--dim)}}
.led-green{{background:#7CFFB2;color:#7CFFB2}}
.muted{{color:var(--dim);font-size:12px}}
footer{{margin-top:18px;color:var(--dim);font-size:10px;text-align:center}}
#modal{{position:fixed;inset:0;background:rgba(2,4,8,.82);display:none;z-index:20;
 align-items:flex-end;justify-content:center;padding:10px}}
@media(min-width:560px){{#modal{{align-items:center}}}}
#modal.open{{display:flex}}
.modal-box{{width:100%;max-width:520px;max-height:88vh;overflow:auto;background:#080f16;
 border:1px solid var(--amber);border-radius:14px;padding:16px;box-shadow:0 0 40px rgba(255,179,71,.25)}}
.modal-box h3{{margin:0 0 4px;color:var(--amber);font-size:15px}}
.modal-box .status{{font-size:10px;letter-spacing:.12em;color:var(--cyan);margin-bottom:10px}}
.modal-box p{{font-size:12px}}
.modal-box .rec{{display:inline-block;font-size:10px;letter-spacing:.12em;padding:3px 8px;border-radius:20px;
 border:1px solid currentColor;margin:6px 0}}
.actions{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.actions button{{flex:1 1 auto;font:inherit;font-size:11px;padding:9px 12px;border-radius:9px;cursor:pointer;
 background:linear-gradient(180deg,rgba(255,179,71,.2),rgba(255,179,71,.06));color:var(--amber);
 border:1px solid var(--amber)}}
.actions button.ghost{{background:transparent;color:var(--cyan);border-color:var(--cyan)}}
.actions button:hover{{filter:brightness(1.25)}}
.copybox{{width:100%;margin-top:10px;background:#05070d;color:var(--cyan);border:1px dashed rgba(63,243,255,.4);
 border-radius:8px;padding:8px;font:inherit;font-size:11px;display:none}}
.copybox.show{{display:block}}
</style>
</head>
<body>
<header>
  <div>
    <h1>{title}</h1>
    <div class="tagline" {_attr_pair({"en": i18n.t("tagline", "en"), "pl": i18n.t("tagline", "pl")})}>{_esc(i18n.t("tagline", lang))}</div>
  </div>
  <button id="lang" {_attr_pair({"en": i18n.t("lang_button", "en"), "pl": i18n.t("lang_button", "pl")})}>{_esc(i18n.t("lang_button", lang))}</button>
</header>
<div class="subtitle" {_attr_pair({"en": i18n.t("subtitle", "en"), "pl": i18n.t("subtitle", "pl")})}>{_esc(i18n.t("subtitle", lang))}</div>

<div class="stats">
  <div class="stat"><b>{on_count}</b><span {_attr_pair({"en": i18n.t("stat_features", "en"), "pl": i18n.t("stat_features", "pl")})}>{_esc(i18n.t("stat_features", lang))}</span></div>
  <div class="stat"><b>{len(available)}</b><span {_attr_pair({"en": i18n.t("stat_available", "en"), "pl": i18n.t("stat_available", "pl")})}>{_esc(i18n.t("stat_available", lang))}</span></div>
  <div class="stat"><b>{horizon.get("new_count", 0)}</b><span {_attr_pair({"en": i18n.t("stat_new", "en"), "pl": i18n.t("stat_new", "pl")})}>{_esc(i18n.t("stat_new", lang))}</span></div>
  <div class="stat"><b>{stats.get("cron_jobs", 0)}</b><span {_attr_pair({"en": i18n.t("stat_jobs", "en"), "pl": i18n.t("stat_jobs", "pl")})}>{_esc(i18n.t("stat_jobs", lang))}</span></div>
  <div class="stat"><b>{stats.get("skills", 0)}</b><span {_attr_pair({"en": i18n.t("stat_skills", "en"), "pl": i18n.t("stat_skills", "pl")})}>{_esc(i18n.t("stat_skills", lang))}</span></div>
</div>

<div class="grid">
  <section class="radar-wrap">
    <h2 {_attr_pair({"en": i18n.t("radar_title", "en"), "pl": i18n.t("radar_title", "pl")})}>{_esc(i18n.t("radar_title", lang))}</h2>
    {_radar(items, sector_list)}
    <div class="legend">
      <span><span class="dot" style="background:#7CFFB2"></span><span {_attr_pair({"en": i18n.t("radar_legend_on", "en"), "pl": i18n.t("radar_legend_on", "pl")})}>{_esc(i18n.t("radar_legend_on", lang))}</span></span>
      <span><span class="dot" style="background:#3ff3ff"></span><span {_attr_pair({"en": i18n.t("radar_legend_off", "en"), "pl": i18n.t("radar_legend_off", "pl")})}>{_esc(i18n.t("radar_legend_off", lang))}</span></span>
      <span><span class="dot" style="background:#ff8a3d"></span><span {_attr_pair({"en": i18n.t("radar_legend_new", "en"), "pl": i18n.t("radar_legend_new", "pl")})}>{_esc(i18n.t("radar_legend_new", lang))}</span></span>
    </div>
  </section>

  <section>
    <h2 {_attr_pair({"en": i18n.t("panel_title", "en"), "pl": i18n.t("panel_title", "pl")})}>{_esc(i18n.t("panel_title", lang))}</h2>
    {"".join(panel)}
    <h2 style="margin-top:18px" {_attr_pair({"en": i18n.t("horizon_title", "en"), "pl": i18n.t("horizon_title", "pl")})}>{_esc(i18n.t("horizon_title", lang))}</h2>
    {horizon_html}
  </section>
</div>

<footer>
  <div {_attr_pair({"en": i18n.t("never_installs", "en"), "pl": i18n.t("never_installs", "pl")})}>{_esc(i18n.t("never_installs", lang))}</div>
  <div {_attr_pair({"en": i18n.t("generated", "en"), "pl": i18n.t("generated", "pl")})}>{_esc(i18n.t("generated", lang))}: {_esc(inventory.get("scanned_at") or "")}</div>
</footer>

<div id="modal" aria-hidden="true">
  <div class="modal-box" role="dialog" aria-modal="true">
    <h3 id="m-name"></h3>
    <div class="status" id="m-status"></div>
    <p><strong data-en="What it gives you" data-pl="Co Ci to daje" id="m-what-label">What it gives you</strong></p>
    <p id="m-benefit"></p>
    <div class="rec" id="m-rec"></div>
    <p class="muted" id="m-hint"></p>
    <div class="actions">
      <button id="m-turn"></button>
      <button class="ghost" id="m-close"></button>
    </div>
    <textarea class="copybox" id="m-copy" readonly></textarea>
  </div>
</div>

<script>
const COCKPIT = {payload};
(function(){{
  const items = {{}}; COCKPIT.items.forEach(function(it){{ items[it.id] = it; }});
  let lang = COCKPIT.lang || "en";
  const S = COCKPIT.strings || {{}};
  function t(key){{ const e = S[key] || {{}}; return e[lang] || e.en || key; }}
  function pair(el, obj){{ if(!obj) return; el.textContent = obj[lang] || obj.en || ""; }}
  function applyLang(){{
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-en]").forEach(function(el){{
      const v = el.getAttribute("data-" + lang) || el.getAttribute("data-en");
      if (v !== null) el.textContent = v;
    }});
    const btn = document.getElementById("lang");
    if (btn) btn.textContent = t("lang_button");
    const mw = document.getElementById("m-what-label");
    if (mw) mw.textContent = t("what_it_gives");
    const mc = document.getElementById("m-close");
    if (mc) mc.textContent = t("close");
    const mt = document.getElementById("m-turn");
    if (mt) mt.textContent = t("turn_on_button");
  }}
  const modal = document.getElementById("modal");
  function openItem(id){{
    const it = items[id]; if(!it) return;
    document.getElementById("m-name").textContent = it.name[lang] || it.name.en;
    document.getElementById("m-status").textContent = t(it.status === "on" ? "status_on" : (it.status === "new" ? "source_catalog" : "status_off"));
    document.getElementById("m-benefit").textContent = it.benefit[lang] || it.benefit.en;
    const rec = document.getElementById("m-rec");
    rec.textContent = t("rec_" + it.verdict) + " — " + (it.reason[lang] || it.reason.en);
    document.getElementById("m-hint").textContent = (it.hint ? (it.hint[lang] || it.hint.en) : "");
    const turn = document.getElementById("m-turn");
    turn.onclick = function(){{ copy(it.prompt, turn); }};
    turn.textContent = t("turn_on_button");
    document.getElementById("m-close").textContent = t("close");
    modal.classList.add("open"); modal.setAttribute("aria-hidden","false");
  }}
  function closeModal(){{ modal.classList.remove("open"); modal.setAttribute("aria-hidden","true"); }}
  function copy(text, button){{
    const box = document.getElementById("m-copy");
    function manual(){{
      box.value = text; box.classList.add("show"); box.focus(); box.select();
      if (button) button.textContent = t("copy_button");
    }}
    if (navigator.clipboard && navigator.clipboard.writeText){{
      navigator.clipboard.writeText(text).then(function(){{
        if (button) button.textContent = t("copied");
      }}, manual);
    }} else {{ manual(); }}
  }}
  document.querySelectorAll("[data-item]").forEach(function(el){{
    el.addEventListener("click", function(){{ openItem(el.getAttribute("data-item")); }});
    el.addEventListener("keydown", function(ev){{ if(ev.key === "Enter" || ev.key === " ") {{ ev.preventDefault(); openItem(el.getAttribute("data-item")); }} }});
  }});
  modal.addEventListener("click", function(ev){{ if(ev.target === modal) closeModal(); }});
  document.addEventListener("keydown", function(ev){{ if(ev.key === "Escape") closeModal(); }});
  document.getElementById("m-close").onclick = closeModal;
  document.getElementById("lang").onclick = function(){{ lang = (lang === "en") ? "pl" : "en"; applyLang(); }};
  applyLang();
}})();
</script>
</body>
</html>
"""

    target = out_path or home.html_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return {"ok": True, "path": str(target), "bytes": len(html.encode("utf-8"))}
