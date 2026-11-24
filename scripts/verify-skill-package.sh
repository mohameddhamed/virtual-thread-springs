#!/usr/bin/env bash
set -euo pipefail

# verify-skill-package.sh
# Verifies the virtual-thread-mechanics skill:
# 1. Runs all 4 minimal Java reproductions on JDK 21 and validates exit code 0 + invariant assertions.
# 2. Validates internal Markdown link targets across skill documentation.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILL_DIR="${REPO_ROOT}/.agents/skills/virtual-thread-mechanics"
EXAMPLES_DIR="${SKILL_DIR}/examples"

echo "================================================================================"
echo "Virtual Thread Mechanics: Skill Package Verification Suite"
echo "================================================================================"
echo "[INFO] Java Runtime:"
java -version
echo ""

# --- 1. Verify Java Examples ---
echo "--------------------------------------------------------------------------------"
echo "Step 1: Executing Minimal Reproductions (Single-Carrier Isolation Invariants)"
echo "--------------------------------------------------------------------------------"

EXAMPLES=(
    "MinimalCarrierStarvation.java"
    "MinimalJniCarrierCapture.java"
    "MinimalPoolQueueShift.java"
    "MinimalAqsTailDispersion.java"
)

FAILED_EXAMPLES=0

for ex in "${EXAMPLES[@]}"; do
    ex_path="${EXAMPLES_DIR}/${ex}"
    if [[ ! -f "${ex_path}" ]]; then
        echo "[FAIL] Missing example file: ${ex_path}"
        FAILED_EXAMPLES=$((FAILED_EXAMPLES + 1))
        continue
    fi
    echo ""
    echo "[RUN] Executing: ${ex}..."
    if java "${ex_path}"; then
        echo "[PASS] ${ex} completed with exit code 0."
    else
        echo "[FAIL] ${ex} failed!"
        FAILED_EXAMPLES=$((FAILED_EXAMPLES + 1))
    fi
done

if [[ ${FAILED_EXAMPLES} -ne 0 ]]; then
    echo ""
    echo "[ERROR] ${FAILED_EXAMPLES} example(s) failed execution."
    exit 1
fi

echo ""
echo "[SUCCESS] All 4 minimal reproductions passed with exit code 0."

# --- 2. Validate Markdown Links ---
echo ""
echo "--------------------------------------------------------------------------------"
echo "Step 2: Validating Internal Markdown Links & References"
echo "--------------------------------------------------------------------------------"

python3 - << 'PY_EOF'
import re
import sys
from pathlib import Path

repo_root = Path.cwd()
skill_dir = repo_root / ".agents" / "skills" / "virtual-thread-mechanics"
docs_dir = repo_root / "docs"

files_to_check = [
    skill_dir / "SKILL.md",
    skill_dir / "references" / "symptom-to-mechanism-map.md",
    skill_dir / "references" / "invariant-ledger.md",
    skill_dir / "references" / "maintainer-issue-template.md",
    docs_dir / "KNOWLEDGE_DISTILLATION.md",
]

link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
failed = 0
checked_links = 0

for file_path in files_to_check:
    if not file_path.exists():
        print(f"[FAIL] File not found: {file_path}")
        failed += 1
        continue

    content = file_path.read_text(encoding="utf-8")
    matches = link_pattern.findall(content)
    file_dir = file_path.parent

    for label, target in matches:
        target_clean = target.strip()
        # Ignore external http/https/mailto links
        if target_clean.startswith(("http://", "https://", "mailto:")):
            continue

        # Handle file:// URLs or relative paths
        clean_path = target_clean
        if clean_path.startswith("file://"):
            clean_path = clean_path[len("file://"):]
        # Remove hash anchors
        if "#" in clean_path:
            clean_path = clean_path.split("#")[0]

        if not clean_path:
            continue

        checked_links += 1
        # Resolve target
        if clean_path.startswith("/"):
            # Check absolute path or path relative to skill_dir or repo_root
            resolved = Path(clean_path)
            if not resolved.exists():
                # Try relative to skill_dir
                resolved_skill = skill_dir / clean_path.lstrip("/")
                # Try relative to repo_root
                resolved_repo = repo_root / clean_path.lstrip("/")
                if resolved_skill.exists():
                    resolved = resolved_skill
                elif resolved_repo.exists():
                    resolved = resolved_repo
        else:
            resolved = (file_dir / clean_path).resolve()
            if not resolved.exists():
                # Also check relative to skill_dir
                resolved_skill = (skill_dir / clean_path).resolve()
                if resolved_skill.exists():
                    resolved = resolved_skill

        if not resolved.exists():
            print(f"[FAIL] Broken link in {file_path.relative_to(repo_root)}: '{label}' -> '{target}' (resolved as {resolved})")
            failed += 1
        else:
            print(f"[OK] Link verified in {file_path.name}: '{label}' -> {resolved.name}")

print(f"\n[INFO] Validated {checked_links} local links across {len(files_to_check)} documents.")
if failed > 0:
    print(f"[ERROR] Found {failed} broken link(s).")
    sys.exit(1)
else:
    print("[SUCCESS] All internal Markdown links are valid.")
PY_EOF

echo ""
echo "================================================================================"
echo "Skill Package Verification Complete: ALL CHECKS PASSED (Exit Code: 0)"
echo "================================================================================"
