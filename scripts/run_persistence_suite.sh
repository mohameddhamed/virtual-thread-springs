#!/bin/bash
set -euo pipefail

JAVA_EXTRA_OPTS="-Xms2g -Xmx2g -XX:+UseG1GC -Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1"
export JAVA_EXTRA_OPTS

echo "=========================================================="
echo "Starting Persistence Contention Suite: 6 Controlled Trials"
echo "=========================================================="

for trial in 1 2 3; do
  echo ""
  echo "=========================================================="
  echo "  Treatment B (Held Connection): Pool Size 1 — Trial $trial"
  echo "=========================================================="
  BENCHMARK_RUN_SET="java21-orders-persistence-contention" \
  BENCHMARK_CONDITION="orders-held-pool-1" \
  BENCHMARK_TRIAL="trial-$trial" \
  ./run-benchmark.sh --endpoint orders --vus 50 --hold-connection --pool-size 1 --no-build
  sleep 3
done

for trial in 1 2 3; do
  echo ""
  echo "=========================================================="
  echo "  Treatment B (Held Connection): Pool Size 10 — Trial $trial"
  echo "=========================================================="
  BENCHMARK_RUN_SET="java21-orders-persistence-contention" \
  BENCHMARK_CONDITION="orders-held-pool-10" \
  BENCHMARK_TRIAL="trial-$trial" \
  ./run-benchmark.sh --endpoint orders --vus 50 --hold-connection --pool-size 10 --no-build
  sleep 3
done

echo ""
echo "=========================================================="
echo "Persistence Contention Suite Complete! All 6 Trials Done."
echo "=========================================================="
