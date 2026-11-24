#!/usr/bin/env bash
set -euo pipefail

# scripts/fetch_raw_evidence.sh
# Automated retrieval and SHA-256 verification of the raw benchmark evidence corpus.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results"
CHECKSUMS_FILE="${RESULTS_DIR}/SHA256SUMS"
ARCHIVE_NAME="virtual-threads-raw-evidence.tar.gz"
REMOTE_URL="${RAW_EVIDENCE_URL:-https://zenodo.org/record/placeholder/files/${ARCHIVE_NAME}}"

echo "==> Verifying raw benchmark evidence in ${RESULTS_DIR}..."

if [ ! -f "${CHECKSUMS_FILE}" ]; then
  echo "Error: ${CHECKSUMS_FILE} not found." >&2
  exit 1
fi

# Check if evidence is already unpacked and valid
if command -v sha256sum >/dev/null 2>&1; then
  CHECK_CMD="sha256sum -c"
elif command -v shasum >/dev/null 2>&1; then
  CHECK_CMD="shasum -a 256 -c"
else
  CHECK_CMD="python3 -c '
import sys, hashlib
all_ok = True
for line in open(sys.argv[1]):
    line = line.strip()
    if not line: continue
    exp, fn = line.split(None, 1)
    try:
        act = hashlib.sha256(open(fn, \"rb\").read()).hexdigest()
        if act != exp:
            print(f\"FAIL {fn}\")
            all_ok = False
        else:
            print(f\"{fn}: OK\")
    except Exception as e:
        print(f\"MISSING {fn}: {e}\")
        all_ok = False
sys.exit(0 if all_ok else 1)
' "
fi

cd "${RESULTS_DIR}"
echo "==> Running SHA-256 verification against ${CHECKSUMS_FILE}..."
if eval "${CHECK_CMD} SHA256SUMS" > /dev/null 2>&1; then
  echo "==> All 543 raw benchmark evidence artifacts verified successfully."
  exit 0
fi

echo "==> Local files missing or mismatched. Attempting archive retrieval..."
if [ -f "${REPO_ROOT}/${ARCHIVE_NAME}" ]; then
  echo "==> Unpacking local ${ARCHIVE_NAME}..."
  tar -xzf "${REPO_ROOT}/${ARCHIVE_NAME}" -C "${RESULTS_DIR}"
else
  echo "==> Fetching from remote URL: ${REMOTE_URL}..."
  if command -v curl >/dev/null 2>&1; then
    curl -fSL "${REMOTE_URL}" -o "${REPO_ROOT}/${ARCHIVE_NAME}"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "${REPO_ROOT}/${ARCHIVE_NAME}" "${REMOTE_URL}"
  else
    echo "Error: Neither curl nor wget found." >&2
    exit 1
  fi
  tar -xzf "${REPO_ROOT}/${ARCHIVE_NAME}" -C "${RESULTS_DIR}"
fi

echo "==> Re-running SHA-256 verification..."
eval "${CHECK_CMD} SHA256SUMS"
echo "==> Verification completed successfully."
