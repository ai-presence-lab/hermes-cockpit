"""Tests for hermes-cockpit.

Runnable two ways:
    /opt/hermes/.venv/bin/python tests/test_cockpit.py
    /opt/hermes/.venv/bin/pytest tests/test_cockpit.py

Everything runs against a throwaway HERMES_HOME under the system temp dir, so
nothing here touches a real Hermes install.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))


def _load_plugin_module():
    spec = importlib.util.spec_from_file_location(
        "hermes_cockpit_plugin",
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(PLUGIN_DIR)]
    sys.modules["hermes_cockpit_plugin"] = module
    spec.loader.exec_module(module)
    return module


def _make_home() -> Path:
    root = Path(tempfile.mkdtemp(prefix="cockpit-test-home-"))
    (root / "plugins").mkdir(parents=True, exist_ok=True)
    (root / "cron").mkdir(parents=True, exist_ok=True)
    (root / "skills" / "alpha").mkdir(parents=True, exist_ok=True)
    (root / "skills" / "beta").mkdir(parents=True, exist_ok=True)
    (root / "skills" / "alpha" / "SKILL.md").write_text("# alpha\n", encoding="utf-8")
    (root / "skills" / "beta" / "SKILL.md").write_text("# beta\n", encoding="utf-8")
    (root / "plugins" / "demo-plugin").mkdir(parents=True, exist_ok=True)
    (root / "plugins" / "demo-plugin" / "plugin.yaml").write_text(
        "name: demo-plugin\nversion: 1.0.0\ndescription: demo\n", encoding="utf-8"
    )
    (root / "config.yaml").write_text(
        "plugins:\n"
        "  enabled:\n"
        "    - hermes-cockpit\n"
        "platforms:\n"
        "  telegram:\n"
        "    enabled: true\n"
        "memory:\n"
        "  provider: local\n"
        "mcp_servers:\n"
        "  files:\n"
        "    command: echo\n"
        "platform_toolsets:\n"
        "  telegram:\n"
        "    - web\n"
        "    - terminal\n",
        encoding="utf-8",
    )
    (root / "cron" / "jobs.json").write_text(
        json.dumps({"jobs": [{"id": "a", "enabled": True}, {"id": "b", "enabled": False}]}),
        encoding="utf-8",
    )
    return root


def _fake_catalog(path: Path, names) -> str:
    entries = [
        {
            "name": n,
            "description": f"{n} does a useful thing. It keeps working in the background.",
            "category": "automation",
            "tier": "official" if i == 0 else "community",
            "version": "1.0.0",
            "repo": f"https://example.invalid/{n}",
            "docs_url": "",
            "platforms": [],
            "capabilities": {"provides_tools": ["x"], "provides_hooks": [], "requires_env": []},
            "sha": f"sha-{n}",
        }
        for i, n in enumerate(names)
    ]
    path.write_text(json.dumps({"generated_at": "2026-01-01T00:00:00Z", "entries": entries, "removed": []}), encoding="utf-8")
    return path.resolve().as_uri()


def test_scan_and_detection() -> None:
    home = _make_home()
    os.environ["HERMES_HOME"] = str(home)
    try:
        from cockpit import capabilities, inventory

        inv = inventory.scan()
        assert inv["stats"]["cron_jobs"] == 2, inv["stats"]
        assert inv["stats"]["skills"] == 2, inv["stats"]
        assert inv["stats"]["mcp_servers"] == 1, inv["stats"]
        assert "telegram" in inv["platforms"], inv["platforms"]
        assert inv["memory"]["provider"] == "local", inv["memory"]
        assert inv["plugins"]["enabled"] == ["hermes-cockpit"], inv["plugins"]
        assert "demo-plugin" in inv["plugins"]["installed"], inv["plugins"]

        from cockpit import home as home_mod

        cfg = home_mod.load_config()
        caps = {c["id"]: c for c in capabilities.detect_all(cfg, inv)}
        assert caps["core:memory"]["on"] is True, caps["core:memory"]
        assert caps["core:cron"]["on"] is True, caps["core:cron"]
        assert caps["core:mcp"]["on"] is True, caps["core:mcp"]
        assert caps["core:platforms"]["on"] is True, caps["core:platforms"]
        assert caps["core:web"]["on"] is True, caps["core:web"]
        assert caps["core:image_gen"]["on"] is False, caps["core:image_gen"]
        print("ok  test_scan_and_detection")
    finally:
        os.environ.pop("HERMES_HOME", None)
        shutil.rmtree(home, ignore_errors=True)


def test_horizon_diff() -> None:
    home = _make_home()
    os.environ["HERMES_HOME"] = str(home)
    try:
        from cockpit import horizon

        cat = home / "cat.json"
        url = _fake_catalog(cat, ["one", "two"])

        first = horizon.horizon(url=url)
        assert first["baseline"] is True, first
        assert first["new_count"] == 0, first
        assert (home / "cockpit" / "seen.json").is_file(), "seen.json not written"

        second = horizon.horizon(url=url)
        assert second["baseline"] is False, second
        assert second["new_count"] == 0, second
        assert second["seen_count"] == 2, second

        url2 = _fake_catalog(cat, ["one", "two", "three"])
        third = horizon.horizon(url=url2)
        assert third["new_count"] == 1, third
        assert third["new"][0]["name"] == "three", third["new"]
        print("ok  test_horizon_diff")
    finally:
        os.environ.pop("HERMES_HOME", None)
        shutil.rmtree(home, ignore_errors=True)


def test_render_and_js() -> None:
    home = _make_home()
    os.environ["HERMES_HOME"] = str(home)
    try:
        from cockpit import capabilities, horizon, inventory, recommend, render
        from cockpit import home as home_mod

        cat = home / "cat.json"
        url = _fake_catalog(cat, ["one", "two"])
        horizon.horizon(url=url)
        url2 = _fake_catalog(cat, ["one", "two", "three"])
        hz = horizon.horizon(url=url2)

        inv = inventory.scan()
        cfg = home_mod.load_config()
        items = recommend.build_items(capabilities.detect_all(cfg, inv), hz, {"core:memory": "Remembers your projects."})
        out = render.render_html(items, inv, hz, lang="en")
        path = Path(out["path"])
        assert path.is_file(), out
        html = path.read_text(encoding="utf-8")
        assert "<!doctype html>" in html.lower(), "no doctype"
        assert "HERMES COCKPIT" in html
        assert 'class="radar"' in html
        assert "You navigate. Your agent pilots." in html
        assert "Remembers your projects." in html
        for sector in ("Conversation", "Memory", "Time &amp; initiative", "Creativity", "Hands in the world"):
            assert sector in html, f"missing sector {sector}"

        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        js_path = home / "cockpit.js"
        js_path.write_text(script, encoding="utf-8")
        node = shutil.which("node")
        if node:
            proc = subprocess.run([node, "--check", str(js_path)], capture_output=True, text=True)
            assert proc.returncode == 0, f"node --check failed: {proc.stderr}"
            print("ok  test_render_and_js (node --check passed)")
        else:
            assert "const COCKPIT" in script
            print("ok  test_render_and_js (node not installed; structural check only)")
    finally:
        os.environ.pop("HERMES_HOME", None)
        shutil.rmtree(home, ignore_errors=True)


def test_tool_handler_end_to_end() -> None:
    home = _make_home()
    os.environ["HERMES_HOME"] = str(home)
    try:
        module = _load_plugin_module()
        cat = home / "cat.json"
        url = _fake_catalog(cat, ["one", "two"])
        raw = module.cockpit_handler({"action": "all", "lang": "pl", "catalog_url": url})
        data = json.loads(raw)
        assert data["ok"] is True, data
        assert data["render"]["path"].endswith("cockpit.html"), data["render"]
        assert Path(data["render"]["path"]).is_file()
        assert data["inventory"]["stats"]["skills"] == 2
        assert "summary" in data and "COCKPIT BRIEFING" in data["summary"]
        # slash command path
        reply = module._slash_handler("")
        assert "Cockpit ready" in reply, reply
        print("ok  test_tool_handler_end_to_end")
    finally:
        os.environ.pop("HERMES_HOME", None)
        shutil.rmtree(home, ignore_errors=True)


def test_no_secret_reads() -> None:
    """A .env sitting in the home must never be read."""
    home = _make_home()
    os.environ["HERMES_HOME"] = str(home)
    try:
        secret = "SUPERSECRETVALUE123"
        (home / ".env").write_text(f"MY_API_KEY={secret}\n", encoding="utf-8")
        module = _load_plugin_module()
        cat = home / "cat.json"
        url = _fake_catalog(cat, ["one"])
        raw = module.cockpit_handler({"action": "all", "catalog_url": url})
        assert secret not in raw, "secret value leaked into tool output"
        assert secret not in Path(json.loads(raw)["render"]["path"]).read_text(encoding="utf-8")
        print("ok  test_no_secret_reads")
    finally:
        os.environ.pop("HERMES_HOME", None)
        shutil.rmtree(home, ignore_errors=True)


def main() -> int:
    tests = [
        test_scan_and_detection,
        test_horizon_diff,
        test_render_and_js,
        test_tool_handler_end_to_end,
        test_no_secret_reads,
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
        except Exception as exc:  # pragma: no cover
            failures += 1
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
