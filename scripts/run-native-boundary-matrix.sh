#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

JAVA_21="${JAVA_21:-java}"
JAVA_24="${JAVA_24:-/tmp/java24/jdk-24.0.2+12/Contents/Home/bin/java}"
JAVA_25="${JAVA_25:-$HOME/Library/Java/JavaVirtualMachines/openjdk-25/Contents/Home/bin/java}"
RUN_SET="${RUN_SET:-native-boundary-20261008-repeated}"
TRIALS="${TRIALS:-3}"
SCHEDULER_OPTS="-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1 --enable-native-access=ALL-UNNAMED"

if [ ! -x "$JAVA_24" ]; then
  echo "Java 24 executable not found: $JAVA_24" >&2
  exit 1
fi
if [ ! -x "$JAVA_25" ]; then
  echo "Java 25 executable not found: $JAVA_25" >&2
  exit 1
fi

run_condition() {
  local runtime="$1"
  local java_cmd="$2"
  local condition="$3"
  local endpoint="$4"
  local lock_mode="$5"
  local trial

  for trial in $(seq 1 "$TRIALS"); do
    echo
    echo "=== runtime=$runtime condition=$condition trial=$trial/$TRIALS ==="
    BENCHMARK_TRIAL="$trial" \
    BENCHMARK_CONDITION="$condition" \
    BENCHMARK_RUN_SET="$RUN_SET" \
    JAVA_CMD="$java_cmd" \
    JAVA_EXTRA_OPTS="$SCHEDULER_OPTS" \
      ./run-benchmark.sh --no-build --lock-mode "$lock_mode" --endpoint "$endpoint" --vus 10
  done
}

for runtime_spec in \
  "java21|$JAVA_21" \
  "java24|$JAVA_24" \
  "java25|$JAVA_25"; do
  runtime="${runtime_spec%%|*}"
  java_cmd="${runtime_spec#*|}"
  run_condition "$runtime" "$java_cmd" "pure-java-sleep" "payments" "none"
  run_condition "$runtime" "$java_cmd" "blocking-jni" "native" "reentrant-lock"
  run_condition "$runtime" "$java_cmd" "native-short" "native-short" "reentrant-lock"
done

echo
echo "Repeated native-boundary matrix complete: $RUN_SET"
