---
name: hermes-cockpit
description: "Use when the user asks what their Hermes can do, feels lost among new plugins/features, or says 'cockpit', 'radar', 'what's new', 'what am I missing', or wants to rename/personalise the radar's sectors. Runs the cockpit tool, writes one plain-language benefit line per item tied to what you know about your human, recommends TURN ON only for background/simplifying things, never enables anything without discussing it, offers the optional custom-sector layout (set_sectors), and suggests scheduling the horizon sweep every 2 days."
---

# Flying the Hermes cockpit

The cockpit is a **read-only radar**. It looks at this Hermes, writes a glowing
page, and tells the human — in their own language — what is already running, what
exists but is switched off, and what is genuinely new in the plugin catalog.

**The one rule: the cockpit never installs, enables, or edits anything.**
Its buttons only copy a prompt to the clipboard for the human to paste to you.
You are the pilot; they are the navigator.

The single exception is the radar's own layout: `set_sectors` writes the optional
`<HERMES_HOME>/cockpit/sectors.yaml`, and only when the human asks for it. It
never touches their Hermes config, plugins, or anything else.

## The loop (do this, in order)

1. **Sweep.** Call the tool:
   ```
   cockpit(action="summary")
   ```
   You get back: the inventory (counts, names), the list of capabilities that are
   off, the new catalog entries, and a briefing written for *you*.

2. **Write personal lines.** For each item you actually want to speak about, write
   ONE short sentence in the human's language, tied to what you know about them
   ("you keep asking me to remember things between chats" → memory). Key them by
   the item id the briefing gave you (`core:memory`, `catalog:<name>`, …).

3. **Render.**
   ```
   cockpit(action="render", lang="en", notes={"core:memory": "…", "core:cron": "…"})
   ```
   Returns `{"path": "<HERMES_HOME>/cockpit/cockpit.html"}`. Hand the human the path
   (or open it for them if your platform can send files).

4. **Talk, don't act.** Say what you recommend and why, then *ask*. Never turn
   something on because the page said TURN ON.

## How to read the recommendations

- **TURN ON** — background or simplifying: it works for them without a new account
  and removes work. Safe to suggest first.
- **MAYBE LATER** — worth having, but needs an API key, an account, or a decision.
  Name the cost out loud.
- **NOT NOW** — heavy, experimental, or a duplicate of something already running.

When the tool has no personal line from you, it falls back to the catalog's own
description — accurate but impersonal. Always prefer your own sentence.

## Personalising the radar (offer it, don't force it)

The radar ships with five sectors (*Conversation, Memory, Time & initiative,
Creativity, Hands in the world*). Many people want their own words — "Talking",
"My studio", "Making" — and want a given tool to sit under the sector it belongs
to *for them*. **Offer this once you have rendered the page and they have seen
it**; do not impose it.

Read the current layout first:

```
cockpit(action="sectors")
```

Then, once they agree on the words and the placement, write it:

```
cockpit(action="set_sectors",
        sectors=[{"id": "conversation", "label": "Talking"},
                 {"id": "studio",      "label": "My studio"},
                 {"id": "hands",       "label": "Doing"}],
        assign={"core:image_gen": "studio"},
        catalog_category_map={"media": "studio"})
```

Rules to respect and to tell the human:

- **2 to 8 sectors.** Fewer or more is rejected (nothing is written).
- **Labels are optional and at most 32 characters.** Reuse an existing sector id
  (`conversation`, `memory`, `time`, `creativity`, `hands`) to keep its default
  label; give any id you like to invent a new one.
- **`assign` maps an item to a sector**: a capability id like `core:image_gen`,
  or a catalog plugin like `catalog:<name>`. An unknown sector id is rejected by
  `set_sectors`.
- **`catalog_category_map`** (optional) routes whole catalog categories, e.g.
  `media: studio`.
- If the file is later missing or broken, the tool silently falls back to the
  five defaults and says so — it never crashes. Invalid entries are ignored with
  a warning that appears in the `summary`.

Prefer `set_sectors` over asking the human to hand-edit YAML: it validates the
input and writes the file atomically.

## Keep the horizon fresh (suggest this, don't create it)

The `horizon` action diffs the public catalog against
`<HERMES_HOME>/cockpit/seen.json`. To catch new plugins without anyone asking,
suggest a job every 2 days — **offer the exact command; let the human say yes**:

```bash
hermes cron create "every 2d" \
  "Run the cockpit horizon sweep and tell me only if something genuinely new and useful appeared: cockpit(action='horizon'). If new_count is 0, reply with just [SILENT]." \
  --name "Cockpit horizon" --deliver origin
```

Do **not** create the cron job yourself. Do not enable it yourself. Present it.

## Privacy and safety

- Everything is local except one call: the public catalog JSON
  (`https://hermes-agent.nousresearch.com/docs/api/plugin-catalog.json`). No
  secrets, no `.env`, no auth files are ever read.
- The inventory reports counts and names of mechanisms, never their contents.
- Offline? The last snapshot is reused; the page says so. Nothing breaks.

## Actions cheat-sheet

| action    | what it returns |
|-----------|-----------------|
| `scan`    | raw inventory JSON only |
| `horizon` | catalog diff: new / updated / removed since last sweep |
| `summary` | the briefing you write your personal lines from |
| `render`  | writes `cockpit.html`, returns its path |
| `all`     | scan + horizon + render + summary in one call (also what `/cockpit` does) |
| `sectors` | the radar's current sectors + assignments |
| `set_sectors` | validates + writes the custom `sectors.yaml` (2–8 sectors) |
