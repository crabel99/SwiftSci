#!/bin/bash
# Read-only telemetry. Run as your ordinary Mac user, not through sudo.
set -euo pipefail
umask 077
if [[ "${1:-}" == --help ]]; then
  echo 'Capture two minutes of Apple CPU frequency, QoS, forced-idle and thermal telemetry around the existing fixed native loop.'
  echo 'Run as your ordinary Mac user. Only powermetrics receives administrator access. No settings are changed.'
  exit 0
fi
if [[ "$EUID" -eq 0 ]]; then echo 'Run this script without sudo; only the hardware profiler needs it.' >&2; exit 1; fi
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
TASK_CAPTURE="$(mktemp -d "$TASK_DIR/frequency-capture.XXXXXX")"
echo 'Apple hardware telemetry requires your local administrator authentication.'
echo 'The fixed compute probe runs as your ordinary user with the E-core scheduling policy.'
echo "Results: $TASK_CAPTURE"
sudo -v
sudo -n /usr/bin/powermetrics --samplers cpu_power,sfi,thermal --show-cpu-qos \
  --sample-rate 200 --sample-count 600 --format plist \
  > "$TASK_CAPTURE/power.plist" 2> "$TASK_CAPTURE/power.stderr" &
TASK_TELEMETRY_PID=$!
# The profiler requests 600 samples over 120 seconds. No external hard timeout is claimed.
trap 'wait "$TASK_TELEMETRY_PID" || true' EXIT
/usr/bin/python3 \
  "$TASK_DIR/frequency-workload.py" "$TASK_CAPTURE/native" > "$TASK_CAPTURE/native.log" 2>&1
wait "$TASK_TELEMETRY_PID"
trap - EXIT
/usr/bin/python3 "$TASK_DIR/validate-frequency-capture.py" "$TASK_CAPTURE"
echo "Capture artifacts saved: $TASK_CAPTURE"
echo 'Hardware-frequency and forced-idle correlation still require review.'
