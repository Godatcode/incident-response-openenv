#!/usr/bin/env bash
# Pre-validation script for Incident Response OpenEnv submission.
# Usage: ./validate-submission.sh <base_url>
#   e.g. ./validate-submission.sh http://localhost:8000

set -euo pipefail

BASE="${1:-http://localhost:8000}"
PASS=0
FAIL=0

ok()   { echo "[PASS] $*"; PASS=$((PASS+1)); }
fail() { echo "[FAIL] $*"; FAIL=$((FAIL+1)); }

# ---------- 1. Health ----------
echo "--- /health ---"
resp=$(curl -sf "$BASE/health") || { fail "/health unreachable"; echo "Aborting: server not running at $BASE"; exit 1; }
echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('status')=='ok', d" \
  && ok "/health returns {status: ok}" \
  || fail "/health bad response: $resp"

# ---------- 2. Tasks ----------
echo "--- /tasks ---"
resp=$(curl -sf "$BASE/tasks")
echo "$resp" | python3 -c "
import sys, json
d = json.load(sys.stdin)
tasks = d.get('tasks', [])
required = {'easy_oom_outage', 'medium_bad_deploy', 'hard_phantom'}
missing = required - set(tasks)
assert not missing, f'Missing tasks: {missing}'
print('tasks:', tasks)
" && ok "/tasks lists all three tasks" || fail "/tasks missing required tasks: $resp"

# ---------- 3. /reset — empty JSON body, no query params ----------
echo "--- /reset (empty JSON body {}) ---"
resp=$(curl -sf -X POST -d '{}' "$BASE/reset")
echo "$resp" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'active_alerts' in d, 'missing active_alerts'
assert 'service_statuses' in d, 'missing service_statuses'
assert 'step_number' in d, 'missing step_number'
assert 'max_steps' in d, 'missing max_steps'
assert d['max_steps'] == 10, f'expected easy task max_steps=10, got {d[\"max_steps\"]}'
print('easy task, max_steps:', d['max_steps'])
" && ok "/reset {} defaults to easy_oom_outage" || fail "/reset {} wrong response: $resp"

# ---------- 4. /reset — JSON body with task_name ----------
echo "--- /reset (JSON body task_name) ---"
resp=$(curl -sf -X POST -H 'Content-Type: application/json' -d '{"task_name":"medium_bad_deploy"}' "$BASE/reset")
echo "$resp" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['max_steps'] == 15, f'expected medium max_steps=15, got {d[\"max_steps\"]}'
print('medium task, max_steps:', d['max_steps'])
" && ok "/reset with task_name in JSON body works" || fail "/reset JSON body: $resp"

# ---------- 5. /reset — query param (backward compat) ----------
echo "--- /reset (query param) ---"
resp=$(curl -sf -X POST "$BASE/reset?task_name=hard_phantom")
echo "$resp" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['max_steps'] == 20, f'expected hard max_steps=20, got {d[\"max_steps\"]}'
print('hard task, max_steps:', d['max_steps'])
" && ok "/reset query param works" || fail "/reset query param: $resp"

# ---------- 6. /step ----------
echo "--- /step ---"
# First reset to easy
curl -sf -X POST -d '{}' "$BASE/reset" > /dev/null
resp=$(curl -sf -X POST -H 'Content-Type: application/json' \
  -d '{"action_type":"check_logs","target_service":"user-service"}' "$BASE/step")
echo "$resp" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'observation' in d, 'missing observation'
assert 'reward' in d, 'missing reward'
assert 'done' in d, 'missing done'
assert 'info' in d, 'missing info'
r = d['reward']
val = r['value'] if isinstance(r, dict) else float(r)
assert 0.0 <= val <= 1.0, f'reward out of [0,1]: {val}'
print('reward:', val, 'done:', d['done'])
" && ok "/step returns valid (observation, reward, done, info)" || fail "/step bad response: $resp"

# ---------- 7. [END] log format ----------
echo "--- inference.py [END] log format ---"
grep -q 'score={score:.2f}' inference.py \
  && ok "inference.py [END] line contains score= field" \
  || fail "inference.py [END] line missing score= field"

# Verify full format: [END] success=... steps=... score=... rewards=...
grep -qE '\[END\].*success=.*steps=.*score=.*rewards=' inference.py \
  && ok "inference.py [END] format matches required pattern" \
  || fail "inference.py [END] format mismatch — expected: [END] success=... steps=... score=... rewards=..."

# ---------- Summary ----------
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && echo "ALL CHECKS PASSED" && exit 0 || exit 1
