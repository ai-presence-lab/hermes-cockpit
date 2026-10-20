# Submitting `hermes-cockpit` to the official plugin catalog

> **Draft — not yet submitted.** This file is a checklist for the authors
> (Agata Śliwińska × Drift). Nothing here has been pushed or opened as a PR.

The catalog is a **human-reviewed** directory in
[`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent). Being
listed *is* the trust signal: users install a catalog plugin by name, at the exact
commit a maintainer read. The canonical rules live in
[`plugin-catalog/README.md`](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/README.md);
the step-by-step guide is at
[Submitting to the Plugin Catalog](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission).

## Before opening the PR

1. **Publish the repository publicly.** `repo` must be an `https://` URL anyone can
   clone (GitHub or GitLab). Everything in this folder is the plugin root — push it
   as-is (the tree must contain `plugin.yaml` and `__init__.py` at the top level).

2. **Pick the commit to pin.** A full **40-character** SHA. Branches, tags and short
   SHAs are rejected by the loader. The pinned release should be **at least 2 weeks
   old** at pin time (supply-chain maturity policy).

   ```bash
   git log -1 --format=%H
   ```

3. **Run the exact CI check** against that checkout and fix every failure:

   ```bash
   hermes plugins validate /path/to/hermes-cockpit-plugin --install-deps
   ```

   Expected on this tree: all checks ✓, `security scan — safe`, and
   `declared tools — matches registrations` (the manifest declares `provides_tools:
   [cockpit]`, which is exactly what `register()` registers). Then read the
   *warnings* too — a reviewer will.

4. **Declare capabilities honestly.** At the pinned commit the plugin registers:
   - tools: `cockpit`
   - hooks: none
   - middleware: none
   - env vars required: none
   - an in-session slash command `/cockpit` and a bundled skill
     `hermes-cockpit:hermes-cockpit` (these are not part of the catalog
     `capabilities:` block, but mention them in the PR description).

5. **No self-updating code.** This plugin never fetches or replaces its own files.
   It fetches *data* — the public catalog JSON — and writes only inside
   `<HERMES_HOME>/cockpit/`. That is not an update mechanism; say so in the PR.

## The entry file

Add **one** file, `plugin-catalog/hermes-cockpit.yaml`, to a fork of
`NousResearch/hermes-agent`, then open a PR. Fill the `sha` with the real pin and
quote `version`:

```yaml
name: hermes-cockpit
repo: https://github.com/<owner>/hermes-cockpit-plugin
sha: <40-hex-commit-sha>            # MANDATORY exact pin
description: >-
  A retro-futuristic cockpit for any Hermes: a radar of what is already enabled,
  a panel of features and catalog plugins that exist but are not switched on, and
  an "on the horizon" list of new catalog plugins since the last sweep — each with
  a plain-language benefit and a TURN ON / MAYBE LATER / NOT NOW recommendation.
  Read-only: it never installs or enables anything itself.
maintainer: Agata Śliwińska × Drift
tier: community                     # official | community
category: general                   # desktop | memory | platform | web | tools | voice | automation | models | general
requires_hermes: ">=0.21"
version: "1.0.0"                    # quoted human label for the sha
docs_url: ""                        # optional
platforms: []                       # empty = all platforms
readme: true                        # render the README at the pinned sha
capabilities:
  provides_tools:
    - cockpit
  provides_hooks: []
  provides_middleware: []
  requires_env: []
```

## PR description — what to disclose

Say what the plugin does, which Hermes surfaces it uses, and everything the
catalog rules ask authors to disclose:

- **Surfaces used:** one tool (`ctx.register_tool`), one in-session slash command
  (`ctx.register_command`), one bundled skill (`ctx.register_skill`). No hooks, no
  middleware, no core patching, no monkey-patching.
- **Network:** exactly one call — a read-only `GET` of the public plugin catalog
  JSON (`https://hermes-agent.nousresearch.com/docs/api/plugin-catalog.json`).
  Nothing about the user is sent. It can be overridden via
  `HERMES_COCKPIT_CATALOG_URL` or the `catalog_url` argument (used by the tests).
- **Writes:** only inside `<HERMES_HOME>/cockpit/` (`seen.json`,
  `catalog-cache.json`, `cockpit.html`).
- **Reads:** the user's own config and home, read-only, filtered to an allowlist of
  keys. It **never** reads `.env`, `auth.json`, or any credential file.
- **No install/enable:** the page's buttons only copy a prompt to the clipboard.
- **Screenshots:** add one of the radar at desktop width and one at 390 px (mobile),
  per the guide's UI rule.
- **Attribution:** the manifest and README credit `Agata Śliwińska × Drift`; MIT.

## After the PR

- The catalog CI job clones the repo at the pinned SHA and runs
  `hermes plugins validate`. Wait for it to go green.
- A maintainer reviews the pinned tree and merges, asks for changes, or declines.
- To ship an update later, open a **new PR that bumps only the `sha`** — reviewers
  look at the upstream commit range being adopted.
