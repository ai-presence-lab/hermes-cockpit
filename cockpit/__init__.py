"""hermes-cockpit internals (stdlib-only, import-safe).

Modules:
  home         — resolve HERMES_HOME, read config read-only, cockpit state paths
  inventory    — the radar's raw facts (counts and names, never contents)
  capabilities — the curated, generic map of Hermes capabilities
  horizon      — fetch + diff the public plugin catalog
  recommend    — deterministic TURN ON / MAYBE LATER / NOT NOW fallback
  render       — write the single self-contained HTML page
  api          — the one entry point the tool and the tests call
"""

from __future__ import annotations

__all__ = ["api", "capabilities", "home", "horizon", "inventory", "recommend", "render"]
