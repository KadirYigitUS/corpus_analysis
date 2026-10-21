"""End-to-End Playwright Test Bridge for Corpus Analysis SPA."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import pytest

PW_DIR = Path(__file__).resolve().parent / "pw"
RESULTS_JSON = (
    Path(__file__).resolve().parent.parent
    / "results"
    / "playwright"
    / "results.json"
)
NODE_MODULES_FALLBACK = "/home/ben/miniconda3/lib/node_modules"
NODE_BIN_FALLBACK = "/home/ben/miniconda3/bin/node"

EXPECTED_TESTS = [
    "suite_shell::shell_brand_and_initial_load",
    "suite_shell::shell_theme_toggle_persists_across_reload",
    "suite_shell::shell_language_toggle_loads_i18n_and_updates_labels",
    "suite_shell::shell_scope_and_matrix_selectors_update_state",
    "suite_shell::shell_rss_gauge_within_bounds",
    "suite_shell::shell_modals_and_help_drawer",
    "suite_tabs_01_04::tab01_inventory_grid_search_sort_and_schema",
    "suite_tabs_01_04::tab02_alignment_kpis_chapters_ner_and_pair_switch",
    "suite_tabs_01_04::tab03_nda_parallel_tokens_svg_links_and_dictionary_drawer",
    "suite_tabs_01_04::tab04_pos_profiles_pair_delta_and_group_comparison",
    "suite_tabs_05_08::tab05_dependency_tree_svg_conll_and_download",
    "suite_tabs_05_08::tab06_kwic_modes_spans_sort_punct_compare_and_invalid_regex",
    "suite_tabs_05_08::tab07_batch_dispersion_and_correlation_grids",
    "suite_tabs_05_08::tab08_lexical_diversity_table_and_mattr_trajectory",
    "suite_tabs_09_11::tab09_collocation_6_metrics_min_freq_and_graphcoll",
    "suite_tabs_09_11::tab10_tfidf_keywords_propn_toggle_and_bundle_download",
    "suite_tabs_09_11::tab11_explorer_quick_search_and_clipboard_copy",
    "suite_tabs_09_11::crosscutting_random_order_tab_navigation",
]


def _resolve_node() -> str | None:
    node = shutil.which("node")
    if node:
        return node
    if Path(NODE_BIN_FALLBACK).is_file():
        return NODE_BIN_FALLBACK
    return None


def _check_playwright(node_bin: str, env: dict[str, str]) -> tuple[bool, str]:
    probe = (
        "const { chromium } = require('playwright');"
        "(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});"
        "await b.close();})()"
    )
    proc = subprocess.run(
        [node_bin, "-e", probe],
        env=env,
        capture_output=True,
        text=True,
        timeout=25,
    )
    return proc.returncode == 0, proc.stderr.strip()


@pytest.fixture(scope="module")
def live_server() -> Any:
    """Start SPA Flask server on an ephemeral socket port in a child process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    env = os.environ.copy()
    env["CORPUS_CACHE_POLICY"] = "keep"
    root_dir = str(Path(__file__).resolve().parents[3])
    env["PYTHONPATH"] = f"{root_dir}:{env.get('PYTHONPATH', '')}"
    srv_code = (
        "from werkzeug.serving import make_server; "
        "from SPA.app import create_app; "
        f"make_server('127.0.0.1', {port}, create_app(), threaded=True).serve_forever()"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", srv_code],
        cwd=root_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    base_url = f"http://127.0.0.1:{port}"
    for _ in range(80):
        try:
            with urllib.request.urlopen(f"{base_url}/favicon.ico", timeout=1) as r:
                if r.status in (200, 204):
                    break
        except Exception:
            time.sleep(0.1)

    yield base_url
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="module")
def playwright_suite_run(live_server: str) -> dict[str, Any]:
    """Execute Node Playwright runner once against live_server and parse results.json."""
    node_bin = _resolve_node()
    if not node_bin:
        pytest.skip("Node.js binary not found on PATH or miniconda3 fallback")

    env = os.environ.copy()
    existing_np = env.get("NODE_PATH", "")
    env["NODE_PATH"] = (
        f"{NODE_MODULES_FALLBACK}:{existing_np}"
        if existing_np
        else NODE_MODULES_FALLBACK
    )
    env["BASE_URL"] = live_server

    ok, err = _check_playwright(node_bin, env)
    if not ok:
        pytest.skip(f"Playwright Chromium unavailable: {err}")

    if RESULTS_JSON.exists():
        RESULTS_JSON.unlink()

    runner_js = PW_DIR / "run_all.js"
    proc = subprocess.run(
        [node_bin, str(runner_js)],
        cwd=str(PW_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if not RESULTS_JSON.exists():
        pytest.fail(
            f"Playwright runner did not write results.json (rc={proc.returncode}):\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    data = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    data["_returncode"] = proc.returncode
    data["_stdout"] = proc.stdout
    data["_stderr"] = proc.stderr
    return data


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.parametrize("test_id", EXPECTED_TESTS)
def test_playwright_suite(playwright_suite_run: dict[str, Any], test_id: str) -> None:
    """Assert each individual Playwright E2E test case passed with zero errors."""
    tests_by_id = {t["id"]: t for t in playwright_suite_run.get("tests", [])}
    assert test_id in tests_by_id, f"Test {test_id} missing from results.json"
    entry = tests_by_id[test_id]
    if entry["status"] != "passed":
        pytest.fail(
            f"Playwright test {test_id} failed ({entry.get('duration_ms')}ms):\n"
            f"{entry.get('error')}\nArtifacts: {entry.get('artifacts')}"
        )


@pytest.mark.e2e
@pytest.mark.playwright
def test_playwright_runner_zero_exit(playwright_suite_run: dict[str, Any]) -> None:
    """Assert the overall Node runner exited with returncode 0 and 0 failed tests."""
    assert playwright_suite_run["_returncode"] == 0, (
        f"Runner exited non-zero ({playwright_suite_run['_returncode']}):\n"
        f"{playwright_suite_run['_stderr']}"
    )
    assert playwright_suite_run.get("failed", 0) == 0
