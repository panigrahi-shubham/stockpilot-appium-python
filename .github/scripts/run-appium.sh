#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts
apk="${STOCKPILOT_CI_APK:?Set STOCKPILOT_CI_APK to the verified APK}"
mapfile -t emulators < <(adb devices | tr -d '\r' | awk '$1 ~ /^emulator-[0-9]+$/ && $2 == "device" { print $1 }')
if [[ ${#emulators[@]} != 1 ]]; then
  echo "Expected exactly one booted Android emulator." >&2
  exit 1
fi
serial="${emulators[0]}"

# The demo sign-in flow requires Android to validate its default network.
python - "$serial" <<'PY'
import re
import subprocess
import sys
import time

serial = sys.argv[1]
for _ in range(30):
    state = subprocess.check_output(
        ["adb", "-s", serial, "shell", "dumpsys", "connectivity"],
        text=True,
        timeout=10,
    )
    active = re.search(r"^Active default network:\s*(\d+)", state, re.M)
    networks = state.partition("Current Networks:")[2].split("Network Requests:", 1)[0]
    if active:
        row = next(
            (line for line in networks.splitlines()
             if f"NetworkAgentInfo{{network{{{active[1]}}}" in line),
            "",
        )
        capabilities = re.search(r"Capabilities:\s*([A-Z_&]+)", row)
        if capabilities and {"INTERNET", "VALIDATED"} <= set(capabilities[1].split("&")):
            break
    time.sleep(3)
else:
    sys.exit("Android's active network did not validate. Check emulator DNS and routing.")
PY

adb -s "$serial" install -r "$apk"
appium --address 127.0.0.1 --port 4723 --log-level warn \
  > artifacts/appium-server.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT

ready=false
for _ in {1..30}; do
  if curl --fail --silent --max-time 2 http://127.0.0.1:4723/status \
     | python -c 'import json, sys; sys.exit(0 if json.loads(sys.stdin.read() or "{}").get("value", {}).get("ready") else 1)'; then
    ready=true
    break
  fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    break
  fi
  sleep 2
done
if [[ "$ready" != true ]]; then
  echo "Appium did not become ready. See artifacts/appium-server.log." >&2
  exit 1
fi

case "${TEST_SUITE:-smoke}" in
  smoke) selection=(-m smoke) ;;
  regression) selection=() ;;
  *) echo "Unsupported TEST_SUITE" >&2; exit 1 ;;
esac

python -m pytest -v --tb=short --device "$serial" --appium-url http://127.0.0.1:4723 \
  --junitxml=artifacts/appium-results.xml "${selection[@]}"
