# Hermes Cockpit

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

## Files

- `kokpit.html` — the cockpit itself (standalone, offline)
- `FAKTY.md` — a written inventory: what is in use, what is asleep, grouped by domain

## License

MIT.
