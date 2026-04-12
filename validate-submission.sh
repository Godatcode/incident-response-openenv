#!/usr/bin/env bash
# Runtime validation helper aligned with the OpenEnv server contract.

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

echo "--- openenv runtime validation ---"
python3 - <<'PY' "$BASE_URL"
import json
import sys

from openenv.cli._validation import validate_running_environment

base_url = sys.argv[1]
report = validate_running_environment(base_url)
print(json.dumps(report, indent=2))
if not report.get("passed", False):
    raise SystemExit(1)
PY

echo "--- task catalog ---"
TASKS_JSON="$(curl -sf "$BASE_URL/tasks")"
python3 - <<'PY' "$TASKS_JSON"
import json
import sys

payload = json.loads(sys.argv[1])
required = {"easy_oom_outage", "medium_bad_deploy", "hard_phantom"}
tasks = set(payload.get("tasks", []))
missing = sorted(required - tasks)
if missing:
    raise SystemExit(f"Missing tasks: {missing}")
print(json.dumps(payload, indent=2))
PY

echo "--- inference contract smoke check ---"
python3 - <<'PY'
from pathlib import Path

text = Path("inference.py").read_text()
required_snippets = [
    "[START] task=",
    "[STEP] step=",
    "[END] success=",
    "LOCAL_IMAGE_NAME",
    "HF_TOKEN",
]
missing = [snippet for snippet in required_snippets if snippet not in text]
if missing:
    raise SystemExit(f"inference.py is missing required contract snippets: {missing}")
print("inference.py contract markers present")
PY

echo "ALL CHECKS PASSED"
