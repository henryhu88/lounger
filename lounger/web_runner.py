#!/usr/bin/env python3
"""
lounger web test runner
───────────────────────
Launches a lightweight web service that:
  • Lists all test cases in the project (tree view)
  • Lets you select and execute tests with a single click
  • Streams execution logs in real time via SSE

Usage:
    python -m lounger.web_runner [--port 5000] [--host 0.0.0.0]

Dependencies: stdlib + PyYAML (for datas/ YAML discovery)
"""

from __future__ import annotations

import http.server
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# ═══════════════════════════════════════════════════════════════════════
#  module-level state
# ═══════════════════════════════════════════════════════════════════════

# The project directory being served (set by main())
_scan_dir: str = "."

# Runtime state for active test runs
_active_runs: dict = {}
_runs_lock = threading.Lock()

# Case cache
_cases_cache: list[dict] | None = None
_cases_cache_time: float = 0.0
_cache_ttl: float = 300.0

# YAML metadata cache
_yaml_metadata_cache: dict | None = None
_yaml_metadata_cache_scan_dir: str = ""

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


# ═══════════════════════════════════════════════════════════════════════
#  case collection
# ═══════════════════════════════════════════════════════════════════════

def get_test_cases(scan_dir: str | None = None) -> list[dict]:
    """Collect all test cases in the project via pytest --collect-only."""
    global _cases_cache, _cases_cache_time
    sd = scan_dir if scan_dir is not None else _scan_dir
    scan_dir_abs = str(Path(sd).resolve())
    now = time.time()

    if _cases_cache is not None and (now - _cases_cache_time) < _cache_ttl:
        return _cases_cache

    script = (
        "from lounger.utils.collect import get_test_cases\n"
        "import json, sys\n"
        "cases = get_test_cases(sys.argv[1] if len(sys.argv) > 1 else '.')\n"
        "print(json.dumps(cases, ensure_ascii=False))\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, sd],
            cwd=scan_dir_abs,
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout.strip()
        if not stdout:
            stdout = result.stderr.strip()
        lines = stdout.split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                try:
                    parsed = json.loads(line)
                    parsed = _enrich_yaml_cases(parsed, scan_dir_abs)
                    _cases_cache = parsed
                    _cases_cache_time = now
                    return parsed
                except json.JSONDecodeError:
                    pass
        parsed = json.loads(stdout)
        parsed = _enrich_yaml_cases(parsed, scan_dir_abs)
        _cases_cache = parsed
        _cases_cache_time = now
        return parsed
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"[web_runner] Failed to collect cases: {e}", file=sys.stderr)
        return []


# ═══════════════════════════════════════════════════════════════════════
#  YAML test case metadata
# ═══════════════════════════════════════════════════════════════════════

def _get_yaml_case_metadata(scan_dir: str) -> dict:
    """Parse YAML test case files from datas/ and return metadata mapping.

    Scans the entire datas/ directory recursively — independent of
    test_project config (which controls execution, not visibility).
    """
    global _yaml_metadata_cache, _yaml_metadata_cache_scan_dir
    if _yaml_metadata_cache is not None and _yaml_metadata_cache_scan_dir == scan_dir:
        return _yaml_metadata_cache

    try:
        import yaml
    except ImportError:
        return {}

    scan_path = Path(scan_dir)
    datas_dir = scan_path / "datas"
    if not datas_dir.is_dir():
        _yaml_metadata_cache = {}
        _yaml_metadata_cache_scan_dir = scan_dir
        return {}

    metadata: dict = {}

    for yaml_file in sorted(datas_dir.rglob("*.yaml")):
        if not (yaml_file.stem.startswith("test_") or yaml_file.stem.endswith("_test")):
            continue
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            continue

        if not isinstance(data, list):
            continue

        filename = yaml_file.stem
        rel_path = str(yaml_file.relative_to(scan_path))

        for idx, block in enumerate(data):
            if not isinstance(block, dict) or "teststeps" not in block:
                continue
            steps = block["teststeps"]
            if not isinstance(steps, list) or len(steps) == 0:
                continue

            first_step = steps[0]
            display_name = (
                first_step.get("step")
                or first_step.get("name")
                or f"测试用例 {idx + 1}"
            )
            step_name = first_step.get("name") or "step_1"
            case_id = f"{filename}::case_{idx + 1}_{step_name}"

            metadata[case_id] = {
                "file": rel_path,
                "name": display_name,
                "description": display_name,
            }

    _yaml_metadata_cache = metadata
    _yaml_metadata_cache_scan_dir = scan_dir
    return metadata


def _enrich_yaml_cases(cases: list[dict], scan_dir: str) -> list[dict]:
    """Re-parent YAML-driven parametrized cases to their actual .yaml source files."""
    metadata = _get_yaml_case_metadata(scan_dir)
    if not metadata:
        return cases

    yaml_pattern = re.compile(r'^test_api\.py::test_api\[(.+?::case_\d+_.+?)\]$')

    for case in cases:
        nodeid = case.get("nodeid", "")
        m = yaml_pattern.match(nodeid)
        if m:
            param_key = m.group(1)
            if param_key in metadata:
                meta = metadata[param_key]
                case["file"] = meta["file"]
                case["name"] = meta["name"]
                if meta.get("description"):
                    case["description"] = meta["description"]

    return cases


# ═══════════════════════════════════════════════════════════════════════
#  tree building
# ═══════════════════════════════════════════════════════════════════════

def _build_case_tree(cases: list[dict], scan_dir: str) -> dict:
    """Build a recursive dir→file→case tree from a flat case list."""
    base = Path(scan_dir).resolve()
    root: dict = {
        "name": base.name,
        "type": "dir",
        "relpath": "",
        "children": [],
        "total_cases": 0,
    }

    for c in cases:
        filepath = c.get("file", "")
        try:
            rel = Path(filepath).resolve().relative_to(base)
        except (ValueError, OSError):
            rel = Path(Path(filepath).name)

        parts = rel.parts
        if not parts:
            continue

        current = root
        for i, part in enumerate(parts[:-1]):
            found = None
            for child in current.get("children", []):
                if child["type"] == "dir" and child["name"] == part:
                    found = child
                    break
            if found is None:
                found = {
                    "name": part,
                    "type": "dir",
                    "relpath": str(Path(*parts[: i + 1])),
                    "children": [],
                    "total_cases": 0,
                }
                current.setdefault("children", []).append(found)
            current = found

        filename = parts[-1]
        file_node = None
        for child in current.get("children", []):
            if child["type"] == "file" and child["name"] == filename:
                file_node = child
                break
        if file_node is None:
            file_node = {
                "name": filename,
                "type": "file",
                "relpath": str(rel),
                "cases": [],
            }
            current.setdefault("children", []).append(file_node)
        file_node.setdefault("cases", []).append(c)

    def _compute_counts(node: dict) -> int:
        if node["type"] == "file":
            node["case_count"] = len(node["cases"])
            node["cases"].sort(key=lambda x: x.get("name", ""))
            return node["case_count"]
        total = 0
        for child in node.get("children", []):
            total += _compute_counts(child)
        node["total_cases"] = total
        return total

    def _sort_tree(node: dict) -> None:
        if "children" in node:
            node["children"].sort(key=lambda x: (0 if x["type"] == "dir" else 1, x["name"].lower()))
            for child in node["children"]:
                _sort_tree(child)

    _compute_counts(root)
    _sort_tree(root)
    return root


# ═══════════════════════════════════════════════════════════════════════
#  test execution (background thread)
# ═══════════════════════════════════════════════════════════════════════

def _execute_tests(run_id: str, nodeids: list[str]) -> None:
    """Run pytest in a subprocess, push lines into the run queue."""
    cwd = str(Path(_scan_dir).resolve())
    tmpdir = Path(cwd) / "collected_cases"
    tmpdir.mkdir(parents=True, exist_ok=True)
    target_file = tmpdir / f"_web_run_{run_id}.json"

    target_payload = [{"nodeid": nid} for nid in nodeids]
    target_file.write_text(json.dumps(target_payload, indent=2), encoding="utf-8")

    cmd = [
        sys.executable, "-m", "pytest",
        "--run-json", str(target_file),
        "-v", "-s",
        "--tb=short",
        "--color=yes",
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd,
            env=env,
        )
    except FileNotFoundError:
        with _runs_lock:
            _active_runs[run_id]["status"] = "error"
            _active_runs[run_id]["error"] = "pytest not found"
        return

    with _runs_lock:
        _active_runs[run_id]["_process"] = proc

    log_queue = _active_runs[run_id]["queue"]

    for raw_line in iter(proc.stdout.readline, ""):
        clean = _strip_ansi(raw_line)
        log_queue.put(clean)
        with _runs_lock:
            _active_runs[run_id]["logs"].append(clean)

    proc.wait()

    summary = f"\n── 执行完成 (exit code: {proc.returncode}) ──\n"
    log_queue.put(summary)
    with _runs_lock:
        _active_runs[run_id]["logs"].append(summary)
        _active_runs[run_id]["status"] = "completed"
        _active_runs[run_id]["exit_code"] = proc.returncode

    try:
        target_file.unlink()
    except OSError:
        pass


# ═══════════════════════════════════════════════════════════════════════
#  HTTP request handler
# ═══════════════════════════════════════════════════════════════════════

_HTML_PAGE: Optional[str] = None


def _load_html() -> str:
    """Load the HTML page (lazy, once)."""
    global _HTML_PAGE
    if _HTML_PAGE is None:
        _HTML_PAGE = _FALLBACK_HTML
    return _HTML_PAGE


class _RequestHandler(http.server.BaseHTTPRequestHandler):
    """Single handler for all routes."""

    def log_message(self, format, *args):
        if self.path.startswith("/api/stream"):
            return
        super().log_message(format, *args)

    # ── routing ──

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            self._serve_html()
        elif path == "/api/cases":
            self._serve_json(get_test_cases())
        elif path == "/api/tree":
            cases = get_test_cases()
            tree = _build_case_tree(cases, _scan_dir)
            self._serve_json({"tree": tree, "flat": cases})
        elif path == "/api/runs":
            self._serve_runs()
        elif path.startswith("/api/stream/"):
            self._serve_stream(path.split("/")[-1])
        else:
            self._serve_404()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/run":
            self._handle_run()
        elif path == "/api/run-all":
            self._handle_run_all()
        elif path == "/api/refresh":
            self._serve_refresh()
        else:
            self._serve_404()

    # ── handlers ──

    def _serve_html(self):
        html = _load_html()
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_json(self, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_runs(self):
        with _runs_lock:
            runs = {}
            for rid, info in _active_runs.items():
                runs[rid] = {
                    "status": info["status"],
                    "nodeids": info["nodeids"],
                    "log_count": len(info["logs"]),
                    "exit_code": info.get("exit_code"),
                }
        self._serve_json(runs)

    def _serve_refresh(self):
        global _cases_cache, _cases_cache_time, _yaml_metadata_cache, _yaml_metadata_cache_scan_dir
        _cases_cache = None
        _cases_cache_time = 0.0
        _yaml_metadata_cache = None
        _yaml_metadata_cache_scan_dir = ""
        cases = get_test_cases()
        self._serve_json({"refreshed": True, "count": len(cases)})

    def _serve_404(self):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found")

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw)

    def _handle_run(self):
        body = self._read_body()
        nodeids = body.get("nodeids", [])
        if not nodeids:
            self._serve_json({"error": "No test cases selected"})
            return

        run_id = uuid.uuid4().hex[:8]
        log_queue: queue.Queue = queue.Queue()

        with _runs_lock:
            _active_runs[run_id] = {
                "queue": log_queue,
                "status": "running",
                "logs": [],
                "nodeids": nodeids,
                "exit_code": None,
            }

        t = threading.Thread(target=_execute_tests, args=(run_id, nodeids), daemon=True)
        t.start()
        self._serve_json({"run_id": run_id, "count": len(nodeids)})

    def _handle_run_all(self):
        cases = get_test_cases()
        all_nodeids = [c["nodeid"] for c in cases if c.get("nodeid")]
        if not all_nodeids:
            self._serve_json({"error": "No test cases found"})
            return
        self._start_run(all_nodeids)

    def _start_run(self, nodeids: list[str]):
        run_id = uuid.uuid4().hex[:8]
        log_queue: queue.Queue = queue.Queue()

        with _runs_lock:
            _active_runs[run_id] = {
                "queue": log_queue,
                "status": "running",
                "logs": [],
                "nodeids": nodeids,
                "exit_code": None,
            }

        t = threading.Thread(target=_execute_tests, args=(run_id, nodeids), daemon=True)
        t.start()
        self._serve_json({"run_id": run_id, "count": len(nodeids)})

    # ── SSE streaming ──

    def _serve_stream(self, run_id: str):
        with _runs_lock:
            run_info = _active_runs.get(run_id)

        if run_info is None:
            self._serve_404()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        log_queue = run_info["queue"]
        sent_count = 0

        with _runs_lock:
            existing = list(run_info["logs"])

        for line in existing[sent_count:]:
            self._sse_event({"line": line})
            sent_count += 1

        while True:
            try:
                line = log_queue.get(timeout=1)
                self._sse_event({"line": line})
                sent_count += 1
            except queue.Empty:
                with _runs_lock:
                    status = run_info["status"]
                if status in ("completed", "error"):
                    self._sse_event({
                        "line": "",
                        "done": True,
                        "exit_code": run_info.get("exit_code", -1),
                        "status": status,
                    })
                    break
                self._sse_event({"heartbeat": True})

    def _sse_event(self, data: dict):
        payload = json.dumps(data, ensure_ascii=False)
        self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
        self.wfile.flush()


# ═══════════════════════════════════════════════════════════════════════
#  server
# ═══════════════════════════════════════════════════════════════════════

class _ThreadingHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main(host: str = "0.0.0.0", port: int = 5000, scan_dir: str = "."):
    """Start the lounger web test runner.

    Args:
        host: Bind address.
        port: Port number.
        scan_dir: Project root directory (where config/config.yaml lives).
    """
    global _scan_dir
    _scan_dir = str(Path(scan_dir).resolve())

    server = _ThreadingHTTPServer((host, port), _RequestHandler)
    print(f"🚀 lounger web runner → http://{host}:{port}")
    print(f"   Project: {_scan_dir}")
    print(f"   Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down.")
        server.shutdown()


def cli_main():
    """CLI entry point with argparse.

    Auto-detects the project root from the calling script.  When invoked
    from a project launcher like ``myapi/web_runner.py``, the project
    root is the directory containing that launcher.  When invoked directly
    via ``python -m lounger.web_runner``, falls back to the current
    directory.
    """
    import argparse
    parser = argparse.ArgumentParser(description="lounger web test runner")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--project", default=None, help="Project root directory (default: auto-detect)")
    args = parser.parse_args()

    if args.project is None:
        # Detect caller location to derive project root.
        import inspect
        stack = inspect.stack()
        caller_file = Path(inspect.getframeinfo(stack[1][0]).filename).resolve()
        this_file = Path(__file__).resolve()

        if caller_file == this_file:
            # Called directly (python -m lounger.web_runner) — use CWD
            args.project = "."
        else:
            # Called from a launcher script (console entry-point or
            # project launcher like myapi/web_runner.py).
            # If caller is a .py file inside a project directory, use
            # its parent as the project root; otherwise fall back to CWD.
            caller_dir = caller_file.parent
            if caller_file.suffix == ".py" and (caller_dir / "config" / "config.yaml").exists():
                args.project = str(caller_dir)
            else:
                args.project = "."

    main(host=args.host, port=args.port, scan_dir=args.project)


# ═══════════════════════════════════════════════════════════════════════
#  fallback HTML
# ═══════════════════════════════════════════════════════════════════════

_FALLBACK_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>lounger Test Runner</title>
<style>
:root {
  --bg: #1e1e2e; --surface: #282840; --border: #3a3a5c;
  --text: #cdd6f4; --muted: #6c7086; --accent: #89b4fa;
  --green: #a6e3a1; --red: #f38ba8; --yellow: #f9e2af;
  --radius: 8px; --indent: 18px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg); color: var(--text); height: 100vh; display: flex; }
/* ── sidebar ── */
.sidebar { width: 420px; min-width: 320px; background: var(--surface);
  border-right: 1px solid var(--border); display: flex; flex-direction: column; }
.sidebar-header { padding: 16px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 10px; }
.sidebar-header h1 { font-size: 18px; font-weight: 600; }
.logo { font-size: 24px; }
.toolbar { padding: 10px 16px; display: flex; gap: 8px; flex-wrap: wrap;
  border-bottom: 1px solid var(--border); }
.toolbar input { flex: 1; min-width: 120px; padding: 6px 10px;
  background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius);
  color: var(--text); font-size: 13px; outline: none; }
.toolbar input:focus { border-color: var(--accent); }
.btn { padding: 6px 14px; border: none; border-radius: var(--radius);
  cursor: pointer; font-size: 13px; font-weight: 500; transition: opacity .15s; }
.btn:hover { opacity: 0.85; }
.btn-accent { background: var(--accent); color: var(--bg); }
.btn-green { background: var(--green); color: var(--bg); }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
.case-list { flex: 1; overflow-x: hidden; overflow-y: auto; padding: 4px 0; }
/* ── tree nodes ── */
.tree-node { display: flex; align-items: center; gap: 6px; cursor: pointer;
  user-select: none; font-size: 13px; border-left: 3px solid transparent;
  min-height: 30px; padding-right: 10px; }
.tree-node:hover { background: rgba(255,255,255,.04); }
.tree-node.tree-dir { color: var(--accent); font-weight: 500; }
.tree-node.tree-file { color: var(--text); }
.tree-node.tree-case { color: var(--muted); }
.tree-node.tree-case.selected { background: rgba(137,180,250,.08); border-left-color: var(--accent); }
.tree-toggle { width: 16px; height: 16px; display: inline-flex; align-items: center;
  justify-content: center; font-size: 10px; flex-shrink: 0;
  transition: transform .15s; color: var(--muted); }
.tree-node.open > .tree-toggle { transform: rotate(90deg); }
.tree-toggle.leaf { visibility: hidden; }
.tree-icon { width: 16px; text-align: center; flex-shrink: 0; font-size: 14px; }
.tree-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-label .count { color: var(--muted); font-size: 11px; margin-left: 4px; }
.tree-children { display: none; }
.tree-children.show { display: block; }
.tree-node input[type=checkbox] { accent-color: var(--accent); flex-shrink: 0; }
.run-btn { padding: 2px 8px; font-size: 11px; background: var(--accent);
  color: var(--bg); border: none; border-radius: 4px; cursor: pointer; opacity: 0;
  flex-shrink: 0; }
.tree-node:hover .run-btn { opacity: 1; }
.empty-state { padding: 40px 20px; text-align: center; color: var(--muted); }
/* ── main ── */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.main-header { padding: 12px 20px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 12px; font-size: 14px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }
.status-dot.running { background: var(--yellow); animation: pulse 1s infinite; }
.status-dot.done { background: var(--green); }
.status-dot.error { background: var(--red); }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }
.log-container { flex: 1; overflow-y: auto; padding: 16px 20px;
  background: #11111b; font-family: "SF Mono", "Fira Code", monospace;
  font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-all; }
.log-line { }
.log-line.pass { color: var(--green); }
.log-line.fail { color: var(--red); }
.log-line.warn { color: var(--yellow); }
.log-line.summary { color: var(--accent); font-weight: bold; }
.log-placeholder { color: var(--muted); text-align: center; padding: 60px 20px; }
.log-placeholder .icon { font-size: 48px; margin-bottom: 12px; }
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <span class="logo">🧪</span>
    <h1>lounger Test Runner</h1>
  </div>
  <div style="padding:8px 16px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
    <span id="caseStats" style="font-size:12px;color:var(--muted)">📊 加载中...</span>
    <button class="btn btn-outline" onclick="refreshCases()" style="font-size:12px">🔄 刷新用例列表</button>
  </div>
  <div class="toolbar">
    <input type="text" id="search" placeholder="搜索用例名称..." oninput="filterCases()">
    <button class="btn btn-outline" onclick="selectAll()">全选</button>
    <button class="btn btn-outline" onclick="deselectAll()">取消</button>
  </div>
  <div class="toolbar">
    <button class="btn btn-green" onclick="runSelected()" style="flex:1">▶ 执行选中</button>
    <button class="btn btn-accent" onclick="runAll()" style="flex:1">▶▶ 执行全部</button>
  </div>
  <div class="case-list" id="caseList">
    <div class="empty-state">⏳ 正在收集用例...</div>
  </div>
</div>

<div class="main">
  <div class="main-header">
    <span class="status-dot" id="statusDot"></span>
    <span id="statusText">就绪</span>
    <span style="flex:1"></span>
    <button class="btn btn-outline" onclick="clearLogs()" id="clearBtn" style="display:none">清空日志</button>
  </div>
  <div class="log-container" id="logContainer">
    <div class="log-placeholder">
      <div class="icon">📋</div>
      <div>选择左侧用例，点击「执行」开始</div>
    </div>
  </div>
</div>

<script>
// ── state ──
let allCases = [];
let caseTree = null;
let selectedIds = new Set();
let currentRunId = null;
let eventSource = null;

// ── fetch cases ──
async function loadCases() {
  try {
    const [casesResp, treeResp] = await Promise.all([
      fetch('/api/cases'),
      fetch('/api/tree')
    ]);
    allCases = await casesResp.json();
    const treeData = await treeResp.json();
    caseTree = treeData.tree;
    renderTree();
  } catch(e) {
    document.getElementById('caseList').innerHTML =
      '<div class="empty-state">❌ 加载失败: ' + e.message + '</div>';
  }
}

function updateStats() {
  const stats = document.getElementById('caseStats');
  if (!allCases.length) {
    stats.textContent = '📭 未发现用例';
    return;
  }
  const yaml = allCases.filter(c => c.file && c.file.endsWith('.yaml')).length;
  const pytest = allCases.length - yaml;
  stats.innerHTML = '📊 共 <b>' + allCases.length + '</b> 用例 &nbsp;|&nbsp; pytest: <b>' + pytest + '</b> &nbsp;|&nbsp; YAML: <b>' + yaml + '</b>';
}

function renderTree() {
  const container = document.getElementById('caseList');
  if (!allCases.length) {
    container.innerHTML = '<div class="empty-state">📭 未发现测试用例<br><small>请确认 config/config.yaml 配置正确</small></div>';
    updateStats();
    return;
  }
  let html = '';
  if (caseTree && caseTree.children) {
    for (const child of caseTree.children) {
      html += renderNode(child, 0);
    }
  }
  container.innerHTML = html;
  updateStats();
}

function renderNode(node, depth) {
  const indent = depth * 18;
  let html = '';

  if (node.type === 'dir') {
    const hasKids = node.children && node.children.length > 0;
    html += '<div class="tree-node tree-dir open" onclick="toggleTreeNode(this)" style="padding-left:' + indent + 'px">';
    html += '<span class="tree-toggle' + (hasKids ? '' : ' leaf') + '">▶</span>';
    html += '<span class="tree-icon">📁</span>';
    html += '<span class="tree-label" title="' + esc(node.relpath || node.name) + '">' + esc(node.name);
    html += ' <span class="count">(' + node.total_cases + ')</span></span>';
    html += '</div>';
    if (hasKids) {
      html += '<div class="tree-children show">';
      for (const child of node.children) {
        html += renderNode(child, depth + 1);
      }
      html += '</div>';
    }
  } else if (node.type === 'file') {
    const hasCases = node.cases && node.cases.length > 0;
    html += '<div class="tree-node tree-file open" onclick="toggleTreeNode(this)" style="padding-left:' + indent + 'px">';
    html += '<span class="tree-toggle' + (hasCases ? '' : ' leaf') + '">▶</span>';
    html += '<span class="tree-icon">📄</span>';
    html += '<span class="tree-label" title="' + esc(node.relpath || node.name) + '">' + esc(node.name);
    if (hasCases) html += ' <span class="count">(' + node.case_count + ')</span>';
    html += '</span></div>';
    if (hasCases) {
      html += '<div class="tree-children show">';
      for (const c of node.cases) {
        html += renderCaseNode(c, depth + 1);
      }
      html += '</div>';
    }
  }
  return html;
}

function renderCaseNode(c, depth) {
  const indent = depth * 18;
  const sel = selectedIds.has(c.nodeid) ? ' selected' : '';
  const checked = selectedIds.has(c.nodeid) ? ' checked' : '';
  const desc = c.description ? c.description.trim() : '';
  const titleParts = [c.name];
  if (c.nodeid) titleParts.push(c.nodeid);
  if (desc) titleParts.push(desc);
  const tooltip = titleParts.join('\n');

  let html = '';
  html += '<div class="tree-node tree-case' + sel + '" onclick="toggleCase(\'' + esc(c.nodeid) + '\', event)" style="padding-left:' + indent + 'px">';
  html += '<span class="tree-toggle leaf">▶</span>';
  html += '<input type="checkbox" ' + checked + ' onclick="event.stopPropagation(); toggleCase(\'' + esc(c.nodeid) + '\', event)">';
  html += '<span class="tree-label" title="' + esc(tooltip) + '">🧪 ' + esc(c.name) + '</span>';
  html += '<button class="run-btn" onclick="event.stopPropagation(); runSingle(\'' + esc(c.nodeid) + '\')">▶</button>';
  html += '</div>';
  return html;
}

function toggleTreeNode(el) {
  el.classList.toggle('open');
  const children = el.nextElementSibling;
  if (children && children.classList.contains('tree-children')) {
    children.classList.toggle('show');
  }
}

function toggleCase(nodeid, ev) {
  if (selectedIds.has(nodeid)) {
    selectedIds.delete(nodeid);
  } else {
    selectedIds.add(nodeid);
  }
  const row = ev.target.closest('.tree-node');
  if (row) {
    const cb = row.querySelector('input[type=checkbox]');
    if (cb) cb.checked = selectedIds.has(nodeid);
    row.classList.toggle('selected', selectedIds.has(nodeid));
  }
}

function selectAll() {
  for (const c of allCases) selectedIds.add(c.nodeid);
  renderTree();
}
function deselectAll() {
  selectedIds.clear();
  renderTree();
}

function filterCases() {
  const q = document.getElementById('search').value.toLowerCase();
  const container = document.getElementById('caseList');
  const allRows = container.querySelectorAll('.tree-node');
  const allGroups = container.querySelectorAll('.tree-children');

  allRows.forEach(row => {
    if (row.classList.contains('tree-case')) {
      const label = (row.querySelector('.tree-label')?.textContent || '').toLowerCase();
      row.style.display = (!q || label.includes(q)) ? '' : 'none';
    }
  });

  allGroups.forEach(group => {
    let hasVisible = false;
    group.querySelectorAll(':scope > .tree-node').forEach(r => {
      if (r.style.display !== 'none') hasVisible = true;
    });
    group.querySelectorAll('.tree-children').forEach(n => {
      n.querySelectorAll(':scope > .tree-node').forEach(r => {
        if (r.style.display !== 'none') hasVisible = true;
      });
    });

    if (hasVisible) {
      group.style.display = 'block';
      group.classList.add('show');
      const header = group.previousElementSibling;
      if (header && header.classList.contains('tree-node')) {
        header.classList.add('open');
        header.style.display = '';
      }
    } else if (q) {
      group.style.display = 'none';
      group.classList.remove('show');
    } else {
      group.style.display = '';
      group.classList.add('show');
      const header = group.previousElementSibling;
      if (header && header.classList.contains('tree-node')) {
        header.classList.add('open');
        header.style.display = '';
      }
    }
  });

  if (q) {
    allRows.forEach(row => {
      if (!row.classList.contains('tree-case')) {
        const next = row.nextElementSibling;
        if (next && next.classList.contains('tree-children')) {
          let anyVis = false;
          next.querySelectorAll('.tree-node.tree-case').forEach(cs => {
            if (cs.style.display !== 'none') anyVis = true;
          });
          row.style.display = anyVis ? '' : 'none';
        }
      }
    });
  } else {
    allRows.forEach(row => { row.style.display = ''; });
  }
}

// ── execution ──
async function runSelected() {
  if (selectedIds.size === 0) { alert('请先选择测试用例'); return; }
  await startRun([...selectedIds]);
}

async function runAll() {
  if (!allCases.length) return;
  await startRun(allCases.map(c => c.nodeid));
}

async function runSingle(nodeid) {
  await startRun([nodeid]);
}

async function startRun(nodeids) {
  if (eventSource) { eventSource.close(); eventSource = null; }

  const resp = await fetch('/api/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({nodeids})
  });
  const data = await resp.json();
  if (data.error) { alert(data.error); return; }

  currentRunId = data.run_id;
  document.getElementById('statusDot').className = 'status-dot running';
  document.getElementById('statusText').textContent = '运行中 (' + data.count + ' 用例)';
  document.getElementById('clearBtn').style.display = '';
  clearLogs();

  eventSource = new EventSource('/api/stream/' + data.run_id);
  const logEl = document.getElementById('logContainer');

  eventSource.onmessage = function(ev) {
    const msg = JSON.parse(ev.data);
    if (msg.heartbeat) return;
    if (msg.line) {
      const div = document.createElement('div');
      div.className = 'log-line';
      if (msg.line.includes('PASSED')) div.classList.add('pass');
      else if (msg.line.includes('FAILED') || msg.line.includes('ERROR')) div.classList.add('fail');
      else if (msg.line.includes('WARNING') || msg.line.includes('skipped')) div.classList.add('warn');
      else if (msg.line.startsWith('──')) div.classList.add('summary');
      div.textContent = msg.line;
      logEl.appendChild(div);
      logEl.scrollTop = logEl.scrollHeight;
    }
    if (msg.done) {
      eventSource.close();
      eventSource = null;
      document.getElementById('statusDot').className = 'status-dot ' +
        (msg.exit_code === 0 ? 'done' : 'error');
      document.getElementById('statusText').textContent =
        msg.exit_code === 0 ? '全部通过 ✅' : '执行失败 ❌ (exit ' + msg.exit_code + ')';
      loadCases();
    }
  };

  eventSource.onerror = function() {
    if (eventSource && eventSource.readyState === EventSource.CLOSED) {
      eventSource = null;
    }
  };
}

function clearLogs() {
  document.getElementById('logContainer').innerHTML = '';
}

async function refreshCases() {
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = '⏳ 刷新中...';
  try {
    await fetch('/api/refresh', {method: 'POST'});
    await loadCases();
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 刷新用例列表';
  }
}

// ── utils ──
function esc(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }

// ── init ──
loadCases();
</script>
</body>
</html>"""


if __name__ == "__main__":
    cli_main()
