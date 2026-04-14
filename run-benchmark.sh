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

# ─── Arg parsing ─────────────────────────────────────────────────────────────
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --vus) VUS_LIST=($2); shift ;;
    --no-jfr) RUN_JFR=false ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
  shift
done

# ─── Prerequisite checks ─────────────────────────────────────────────────────
if ! command -v k6 &> /dev/null; then
  echo "❌  k6 not found. Install it: https://k6.io/docs/getting-started/installation/"
  exit 1
fi

if [ ! -f "$APP_JAR" ]; then
  echo "📦  Building app..."
  ./mvnw clean package -q -DskipTests
fi

mkdir -p "$RESULTS_DIR" "$JFR_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# ─── JFR settings ────────────────────────────────────────────────────────────
# jdk.VirtualThreadPinned: emitted every time a VT gets pinned to a Carrier Thread
# threshold=10ms: only log pinning events longer than 10ms (avoids noise)
JFR_OPTS=""
if [ "$RUN_JFR" = true ]; then
  JFR_RECORDING="$JFR_DIR/recording-$TIMESTAMP.jfr"
  JFR_OPTS="-XX:StartFlightRecording=filename=$JFR_RECORDING,settings=profile,dumponexit=true \
            -Djdk.tracePinnedThreads=full"
  echo "🎥  JFR recording will be saved to: $JFR_RECORDING"
fi

# ─── Start the app ───────────────────────────────────────────────────────────
echo ""
echo "🚀  Starting Spring Boot app..."
java $JFR_OPTS -jar "$APP_JAR" &
APP_PID=$!
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

# ─── Run benchmarks ──────────────────────────────────────────────────────────
for VUS in "${VUS_LIST[@]}"; do
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Running load test: ${VUS} concurrent users"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  RESULT_FILE="$RESULTS_DIR/run-${VUS}vus-$TIMESTAMP.json"

  VUS=$VUS BASE_URL=$BASE_URL k6 run \
    --out json="$RESULT_FILE" \
    k6/load-test.js

  echo "    📊  Results saved to: $RESULT_FILE"
done

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
  echo "    To analyze pinning events, run:"
  echo "    jfr print --events jdk.VirtualThreadPinned $JFR_RECORDING"
  echo ""
  echo "    Or open in JDK Mission Control (JMC) for a visual breakdown."
fi

echo ""
echo "✅  Benchmark run complete. Results are in: $RESULTS_DIR/"