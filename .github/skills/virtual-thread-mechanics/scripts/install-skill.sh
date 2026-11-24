#!/usr/bin/env bash
set -euo pipefail

# install-skill.sh
# Installs virtual-thread-mechanics skill to Antigravity, Claude Code, GitHub Copilot, and/or Gemini CLI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/../SKILL.md" ]]; then
    SKILL_SOURCE="$(cd "${SCRIPT_DIR}/.." && pwd)"
    REPO_ROOT="$(cd "${SKILL_SOURCE}/../../.." && pwd)"
else
    REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
    SKILL_SOURCE="${REPO_ROOT}/.agents/skills/virtual-thread-mechanics"
fi

if [[ ! -d "${SKILL_SOURCE}" ]]; then
    echo "[ERROR] Skill source directory not found: ${SKILL_SOURCE}" >&2
    exit 1
fi

function print_usage() {
    cat <<EOF
Usage: $0 [options]

Options:
  --antigravity   Install to .agents/skills/ (Antigravity workspace)
  --claude        Install to .claude/skills/ (Claude Code)
  --copilot       Install to .github/skills/ (GitHub Copilot)
  --gemini        Install to ~/.gemini/config/skills/ (Local Gemini CLI)
  --all           Install to all supported platforms (Default if no flag specified)
  -h, --help      Show this help message
EOF
}

TARGETS=()

if [[ $# -eq 0 ]]; then
    TARGETS=("antigravity" "claude" "copilot" "gemini")
else
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --antigravity)
                TARGETS+=("antigravity")
                shift
                ;;
            --claude)
                TARGETS+=("claude")
                shift
                ;;
            --copilot)
                TARGETS+=("copilot")
                shift
                ;;
            --gemini)
                TARGETS+=("gemini")
                shift
                ;;
            --all)
                TARGETS=("antigravity" "claude" "copilot" "gemini")
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                echo "[ERROR] Unknown option: $1" >&2
                print_usage
                exit 1
                ;;
        esac
    done
fi

function install_to() {
    local target_dir="$1"
    local name="$2"
    echo "[INFO] Installing virtual-thread-mechanics to ${name} (${target_dir})..."
    local abs_src
    abs_src="$(cd "${SKILL_SOURCE}" && pwd -P)"

    if [[ -d "${target_dir}" ]]; then
        local abs_tgt
        abs_tgt="$(cd "${target_dir}" && pwd -P)"
        if [[ "${abs_src}" == "${abs_tgt}" ]]; then
            echo "       -> Source and destination are identical (${abs_src}). Already in place."
            return 0
        fi
    fi

    if ! mkdir -p "${target_dir}" 2>/dev/null; then
        echo "       [WARN] Permission denied or directory not creatable: ${target_dir}. Skipping."
        return 0
    fi

    if cp -R "${SKILL_SOURCE}/." "${target_dir}/" 2>/dev/null; then
        echo "       -> Done."
    else
        echo "       [WARN] Failed to copy files to ${target_dir}. Skipping."
    fi
}

for t in "${TARGETS[@]}"; do
    case "$t" in
        antigravity)
            install_to "${REPO_ROOT}/.agents/skills/virtual-thread-mechanics" "Antigravity Workspace"
            ;;
        claude)
            install_to "${REPO_ROOT}/.claude/skills/virtual-thread-mechanics" "Claude Code"
            ;;
        copilot)
            install_to "${REPO_ROOT}/.github/skills/virtual-thread-mechanics" "GitHub Copilot"
            ;;
        gemini)
            install_to "${HOME}/.gemini/config/skills/virtual-thread-mechanics" "Local Gemini Config"
            ;;
    esac
done

echo ""
echo "================================================================================"
echo "Skill Installation Complete: virtual-thread-mechanics"
echo "================================================================================"
