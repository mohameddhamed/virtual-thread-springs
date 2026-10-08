#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run-benchmark.sh
# Runs the full benchmark suite with Java Flight Recorder enabled.
# Captures throughput, latency, and thread pinning events.
#
# Usage:
#   ./run-benchmark.sh                  # runs all VU levels (50, 100, 200)
#   ./run-benchmark.sh --vus 100        # runs a single VU level
#   ./run-benchmark.sh --no-jfr         # skip JFR (faster, no pinning data)
# ─────────────────────────────────────────────────────────────────────────────

set -e

# ─── Config ──────────────────────────────────────────────────────────────────
APP_JAR="target/virtual-threads-demo-0.0.1-SNAPSHOT.jar"
BASE_URL="http://localhost:8080"
RESULTS_DIR="results"
JFR_DIR="results/jfr"
STARTUP_WAIT=8   # seconds to wait for Spring Boot to start
VUS_LIST=(50 100 200)
RUN_JFR=true
BUILD_APP=true
LOCK_MODE="reentrant-lock"
VIRTUAL_THREADS_ENABLED="true"
ENDPOINT="mixed"

sha256_file() {
  openssl dgst -sha256 "$1" | awk '{print $2}'
}

# ─── Arg parsing ─────────────────────────────────────────────────────────────
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --vus) VUS_LIST=($2); shift ;;
    --no-jfr) RUN_JFR=false ;;
    --no-build) BUILD_APP=false ;;
    --lock-mode) LOCK_MODE=$2; shift ;;
    --platform) VIRTUAL_THREADS_ENABLED="false" ;;
    --endpoint) ENDPOINT=$2; shift ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
  shift
done

case "$ENDPOINT" in
  mixed|orders|payments|products|cpu|native|native-short) ;;
  *) echo "Invalid endpoint: $ENDPOINT (expected mixed, orders, payments, products, cpu, native, or native-short)"; exit 1 ;;
esac

# ─── Prerequisite checks ─────────────────────────────────────────────────────
if ! command -v k6 &> /dev/null; then
  echo "❌  k6 not found. Install it: https://k6.io/docs/getting-started/installation/"
  exit 1
fi

if [ "$BUILD_APP" = true ]; then
  echo "📦  Building app and native experiment library..."
  ./mvnw package -q -DskipTests
fi

mkdir -p "$RESULTS_DIR" "$JFR_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
MANIFEST_FILE="$RESULTS_DIR/run-manifest-$TIMESTAMP.json"
RESULT_RECORDS=""
K6_STATUS=0
GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
JAVA_CMD="${JAVA_CMD:-java}"
JAVA_EXTRA_OPTS="${JAVA_EXTRA_OPTS:-}"
TRIAL_ID="${BENCHMARK_TRIAL:-unspecified}"
CONDITION_ID="${BENCHMARK_CONDITION:-$ENDPOINT}"
RUN_SET="${BENCHMARK_RUN_SET:-unspecified}"
JAVA_VERSION=$("$JAVA_CMD" -version 2>&1 | head -n 1 | tr -d '"')
K6_VERSION=$(k6 version 2>/dev/null | head -n 1 || echo "unknown")
OS_NAME=$(uname -srv)
CPU_INFO=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || uname -m)
PROCESSORS=$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo "unknown")
MEMORY=$(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.0f GB", $1/1024/1024/1024}' || echo "unknown")
APP_SHA256=$(sha256_file "$APP_JAR")
NATIVE_LIBRARY=""
NATIVE_LIBRARY_SHA256=""
if [ -f "target/native/libnativeblocking.dylib" ]; then
  NATIVE_LIBRARY="target/native/libnativeblocking.dylib"
elif [ -f "target/native/libnativeblocking.so" ]; then
  NATIVE_LIBRARY="target/native/libnativeblocking.so"
fi
if [ -n "$NATIVE_LIBRARY" ]; then
  NATIVE_LIBRARY_SHA256=$(sha256_file "$NATIVE_LIBRARY")
fi
TIMESTAMP_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$MANIFEST_FILE" <<EOF
{
  "run_id": "$TIMESTAMP",
  "trial_id": "$TRIAL_ID",
  "condition_id": "$CONDITION_ID",
  "run_set": "$RUN_SET",
  "timestamp_utc": "$TIMESTAMP_UTC",
  "timestamp_local": "$(date -Iseconds)",
  "git_commit": "$GIT_COMMIT",
  "application_jar_sha256": "$APP_SHA256",
  "java_command": "$JAVA_CMD",
  "java_vendor_and_version": "$JAVA_VERSION",
  "spring_boot_version": "3.5.12",
  "k6_version": "$K6_VERSION",
  "os": "$OS_NAME",
  "cpu": "$CPU_INFO",
  "logical_processors": "$PROCESSORS",
  "memory": "$MEMORY",
  "execution_mode": "$( [ "$VIRTUAL_THREADS_ENABLED" = "true" ] && echo virtual || echo platform )",
  "virtual_threads_enabled": $VIRTUAL_THREADS_ENABLED,
  "lock_variant": "$LOCK_MODE",
  "endpoint_or_workload": "$ENDPOINT",
  "load_model": "closed",
  "target_vus": "$(IFS=,; echo "${VUS_LIST[*]}")",
  "stage_definition": "15s ramp-up, 30s hold, 10s ramp-down",
  "warmup_rule": "8s application startup plus products health check; k6 ramp-up excluded from steady-state interpretation",
  "measurement_interval": "30s hold stage",
  "timeout": "k6/http default; inspect raw output for timeout samples",
  "connection_pool_size": "Spring Boot/Hikari default; verify from runtime configuration before final thesis use",
  "tomcat_max_threads_or_executor": "Spring Boot virtual-thread request executor",
  "jvm_flags": "-XX:StartFlightRecording=...,settings=profile,dumponexit=true -Djdk.tracePinnedThreads=full",
  "java_extra_options": "$JAVA_EXTRA_OPTS",
  "native_library": "$NATIVE_LIBRARY",
  "native_library_sha256": "$NATIVE_LIBRARY_SHA256",
  "native_enabled": $([ "$ENDPOINT" = "native" ] || [ "$ENDPOINT" = "native-short" ] && echo true || echo false),
  "jfr_enabled": "$RUN_JFR",
  "jfr_configuration": "profile; jdk.tracePinnedThreads=full",
  "telemetry_file": "",
  "telemetry_sha256": "",
  "result_files": [],
  "jfr_file": "",
  "jfr_sha256": "",
  "validity_status": "exploratory",
  "k6_exit_status": $K6_STATUS,
  "exclusion_reason": "",
  "notes": "Repeated process-level run; closed-loop workload. Interpret with the run-set aggregate and reported variability."
}
EOF
echo "🧾  Run manifest initialized: $MANIFEST_FILE"

TELEMETRY_FILE="$RESULTS_DIR/telemetry-$TIMESTAMP.csv"
echo "timestamp,pid,threads,cpu_percent" > "$TELEMETRY_FILE"
capture_telemetry() {
  while kill -0 "$APP_PID" 2>/dev/null; do
    now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    threads=$(ps -M "$APP_PID" 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
    if [ "$threads" = "0" ] && [ -r "/proc/$APP_PID/status" ]; then
      threads=$(awk '/^Threads:/ {print $2}' "/proc/$APP_PID/status")
    fi
    cpu=$(ps -p "$APP_PID" -o %cpu= 2>/dev/null | tr -d ' ')
    printf '%s,%s,%s,%s\n' "$now" "$APP_PID" "${threads:-unknown}" "${cpu:-unknown}" >> "$TELEMETRY_FILE"
    sleep 1
  done
}

# ─── JFR settings ────────────────────────────────────────────────────────────
# jdk.VirtualThreadPinned: emitted every time a VT gets pinned to a Carrier Thread
# threshold=10ms: only log pinning events longer than 10ms (avoids noise)
JFR_OPTS="-Djava.library.path=$PWD/target/native"
if [ "$RUN_JFR" = true ]; then
  JFR_RECORDING="$JFR_DIR/recording-$TIMESTAMP.jfr"
  JFR_OPTS="$JFR_OPTS -XX:StartFlightRecording=filename=$JFR_RECORDING,settings=profile,dumponexit=true \
            -Djdk.tracePinnedThreads=full"
  echo "🎥  JFR recording will be saved to: $JFR_RECORDING"
fi

# ─── Start the app ───────────────────────────────────────────────────────────
echo ""
echo "🚀  Starting Spring Boot app..."
NATIVE_ARGS=()
if [ "$ENDPOINT" = "native" ] || [ "$ENDPOINT" = "native-short" ]; then
  NATIVE_ARGS+=(--demo.native.enabled=true)
fi
$JAVA_CMD $JFR_OPTS $JAVA_EXTRA_OPTS -jar "$APP_JAR" \
  --spring.threads.virtual.enabled="$VIRTUAL_THREADS_ENABLED" \
  --demo.payment.lock-mode="$LOCK_MODE" \
  "${NATIVE_ARGS[@]}" &
APP_PID=$!
cleanup() {
  if [ -n "${TELEMETRY_PID:-}" ] && kill -0 "$TELEMETRY_PID" 2>/dev/null; then
    kill "$TELEMETRY_PID" 2>/dev/null || true
    wait "$TELEMETRY_PID" 2>/dev/null || true
  fi
  if kill -0 "$APP_PID" 2>/dev/null; then
    echo "🛑  Cleaning up app (PID $APP_PID)..."
    kill "$APP_PID" 2>/dev/null || true
    wait "$APP_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM
echo "    PID: $APP_PID"

# Wait for startup
echo "    Waiting ${STARTUP_WAIT}s for startup..."
sleep $STARTUP_WAIT

# Verify the app is up
if ! curl -sf "$BASE_URL/products" > /dev/null; then
  echo "❌  App did not start correctly. Check logs."
  kill $APP_PID 2>/dev/null
  exit 1
fi
echo "    ✅  App is up."
capture_telemetry &
TELEMETRY_PID=$!
echo "    📈  Process telemetry started (PID $TELEMETRY_PID)"

# ─── Run benchmarks ──────────────────────────────────────────────────────────
for VUS in "${VUS_LIST[@]}"; do
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Running load test: ${VUS} concurrent users"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  RESULT_FILE="$RESULTS_DIR/run-${VUS}vus-$TIMESTAMP.json"

  if [ "$ENDPOINT" = "mixed" ]; then
    LOAD_SCRIPT="k6/load-test.js"
  else
    LOAD_SCRIPT="k6/isolated-load-test.js"
  fi
  VUS=$VUS BASE_URL=$BASE_URL ENDPOINT=$ENDPOINT k6 run \
    --out json="$RESULT_FILE" \
    "$LOAD_SCRIPT" || K6_STATUS=$?

  RESULT_SHA256=$(sha256_file "$RESULT_FILE")
  if [ -n "$RESULT_RECORDS" ]; then
    RESULT_RECORDS="$RESULT_RECORDS,"
  fi
  RESULT_RECORDS="$RESULT_RECORDS{\"vus\": $VUS, \"path\": \"$RESULT_FILE\", \"sha256\": \"$RESULT_SHA256\"}"
  echo "    📊  Results saved to: $RESULT_FILE"
done

if kill -0 "$TELEMETRY_PID" 2>/dev/null; then
  kill "$TELEMETRY_PID" 2>/dev/null || true
  wait "$TELEMETRY_PID" 2>/dev/null || true
fi
echo "    📈  Process telemetry saved to: $TELEMETRY_FILE"

TELEMETRY_SHA256=$(sha256_file "$TELEMETRY_FILE")
MANIFEST_TMP=$(mktemp)
sed -e "s#\"telemetry_file\": \"\"#\"telemetry_file\": \"$TELEMETRY_FILE\"#" \
    -e "s#\"telemetry_sha256\": \"\"#\"telemetry_sha256\": \"$TELEMETRY_SHA256\"#" \
    "$MANIFEST_FILE" > "$MANIFEST_TMP"
mv "$MANIFEST_TMP" "$MANIFEST_FILE"

MANIFEST_TMP=$(mktemp)
sed -e "s#\"result_files\": \\[\\]#\"result_files\": [$RESULT_RECORDS]#" \
    -e "s#\"k6_exit_status\": 0#\"k6_exit_status\": $K6_STATUS#" \
    "$MANIFEST_FILE" > "$MANIFEST_TMP"
mv "$MANIFEST_TMP" "$MANIFEST_FILE"

# ─── Stop the app ────────────────────────────────────────────────────────────
echo ""
echo "🛑  Stopping app (PID $APP_PID)..."
kill $APP_PID
wait $APP_PID 2>/dev/null || true
echo "    Done."

# ─── JFR summary ─────────────────────────────────────────────────────────────
if [ "$RUN_JFR" = true ] && [ -f "$JFR_RECORDING" ]; then
  echo ""
  echo "📋  JFR recording saved: $JFR_RECORDING"
  JFR_SHA256=$(sha256_file "$JFR_RECORDING")
  MANIFEST_TMP=$(mktemp)
  sed -e "s#\"jfr_file\": \"\"#\"jfr_file\": \"$JFR_RECORDING\"#" \
      -e "s#\"jfr_sha256\": \"\"#\"jfr_sha256\": \"$JFR_SHA256\"#" \
      "$MANIFEST_FILE" > "$MANIFEST_TMP"
  mv "$MANIFEST_TMP" "$MANIFEST_FILE"
  echo "    SHA-256: $JFR_SHA256"
  echo "    To analyze pinning events, run:"
  echo "    jfr print --events jdk.VirtualThreadPinned $JFR_RECORDING"
  echo ""
  echo "    Or open in JDK Mission Control (JMC) for a visual breakdown."
fi

echo ""
echo "✅  Benchmark run complete. Results are in: $RESULTS_DIR/"
exit "$K6_STATUS"