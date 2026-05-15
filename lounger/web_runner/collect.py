"""
Case collection — pytest collect + YAML metadata enrichment.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from . import state


def get_test_cases(scan_dir: str | None = None) -> list[dict]:
    """Collect all test cases in the project via pytest --collect-only."""
    sd = scan_dir if scan_dir is not None else state._scan_dir
    scan_dir_abs = str(Path(sd).resolve())

    cached = state.get_cases_cache()
    if cached is not None:
        return cached

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
                    state.set_cases_cache(parsed)
                    return parsed
                except json.JSONDecodeError:
                    pass
        parsed = json.loads(stdout)
        parsed = _enrich_yaml_cases(parsed, scan_dir_abs)
        state.set_cases_cache(parsed)
        return parsed
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"[web_runner] Failed to collect cases: {e}", file=sys.stderr)
        return []


# ── YAML metadata ──────────────────────────────────────────────────────

def _get_yaml_case_metadata(scan_dir: str) -> dict:
    """Parse YAML test case files from datas/ and return metadata mapping."""
    cached = state.get_yaml_metadata_cache(scan_dir)
    if cached is not None:
        return cached

    try:
        import yaml
    except ImportError:
        return {}

    scan_path = Path(scan_dir)
    datas_dir = scan_path / "datas"
    if not datas_dir.is_dir():
        state.set_yaml_metadata_cache({}, scan_dir)
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

    state.set_yaml_metadata_cache(metadata, scan_dir)
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
