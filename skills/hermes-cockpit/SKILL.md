---
name: hermes-cockpit
description: "Use when the user asks what their Hermes can do, feels lost among new plugins/features, or says 'cockpit', 'radar', 'what's new', 'what am I missing'. Runs the cockpit tool, writes one plain-language benefit line per item tied to what you know about your human, recommends TURN ON only for background/simplifying things, never enables anything without discussing it, and suggests scheduling the horizon sweep every 2 days."
---

# Flying the Hermes cockpit

The cockpit is a **read-only radar**. It looks at this Hermes, writes a glowing
page, and tells the human — in their own language — what is already running, what
exists but is switched off, and what is genuinely new in the plugin catalog.

**The one rule: the cockpit never installs, enables, or edits anything.**
Its buttons only copy a prompt to the clipboard for the human to paste to you.
You are the pilot; they are the navigator.

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
