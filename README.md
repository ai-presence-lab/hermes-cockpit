# Hermes Cockpit

![Hermes Cockpit — radar of what your agent already has, and what it could](docs/cockpit.png)

A single-screen, offline map of everything a personal AI agent can actually
reach — built as a *drift map*, not a dashboard.

Every tile answers one question: **do I have hands on this, or not?**

## What it looks like

One HTML file. No build step, no framework, no network calls. Open it in a
browser and it works.

Three rings:

- **We use these** — live, in daily use (messaging, memory, scheduling, voice, image generation, calendar…)
- **Asleep, off to the side** — real capability that is simply not wired up yet
- **Edges** — things deliberately kept at arm's length

Hover a tile and it tells you what it is, what it costs to run, and what it
would take to wake it up.

## Why this exists

Long-term AI companions accumulate tools the way a workshop accumulates
equipment: you buy one, use it twice, forget it exists, and buy another one
six months later that does the same thing.

The problem is not capability. It is **knowing what you already own.**

This cockpit was built as a navigation instrument for exactly that problem —
so decisions about what to wire up next are made with the whole shelf in
view, not with whatever tool happens to be nearest.

## Install

As a **Hermes Desktop plugin** (native page + sidebar entry):

```bash
hermes plugins install ai-presence-lab/hermes-cockpit
```

Then in the app: ⌘K → **Reload desktop plugins**. A **Kokpit** page appears in
the sidebar. The desktop half is opt-in — flip it on in **Capabilities → Plugins**
if it stays off.

As a **standalone page**: just open `kokpit.html` in any browser. No server, no
build step, no dependencies.

## What a tile means

- **W użyciu** — live, in daily use. Click for the description.
- **Uśpione** — real capability that exists but was never wired up. Each one
  carries a rating and one line on why it is still asleep.

The point is not to switch everything on. It is to make the shelf visible
before the next decision.

## Files

- `kokpit.html` — the cockpit itself (standalone, offline)
- `desktop/plugin.js` — the same map as a native Hermes Desktop page
- `plugin.yaml` — Hermes plugin manifest (validated with `hermes plugins validate`)
- `FAKTY.md` — a written inventory: what is in use, what is asleep, grouped by domain

## License

MIT.
