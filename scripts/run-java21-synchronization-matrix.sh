#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

RUN_SET="${RUN_SET:-java21-synchronization-20261008-repeated}"
TRIALS="${TRIALS:-3}"
JAVA_CMD="${JAVA_CMD:-java}"

run_condition() {
  local condition="$1"
  local lock_mode="$2"
  local platform_flag="$3"
  local trial

  for trial in $(seq 1 "$TRIALS"); do
    echo
    echo "=== condition=$condition trial=$trial/$TRIALS ==="
    BENCHMARK_TRIAL="$trial" \
    BENCHMARK_CONDITION="$condition" \
    BENCHMARK_RUN_SET="$RUN_SET" \
    JAVA_CMD="$JAVA_CMD" \
      ./run-benchmark.sh --no-build --lock-mode "$lock_mode" --endpoint payments --vus 10 $platform_flag
  done
}

run_condition "synchronized" "synchronized" ""
run_condition "reentrant-lock" "reentrant-lock" ""
run_condition "no-lock-diagnostic" "none" ""
run_condition "platform-synchronized" "synchronized" "--platform"

echo
echo "Java 21 synchronization matrix complete: $RUN_SET"
