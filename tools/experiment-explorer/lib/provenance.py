"""Provenance, cryptographic hash verification, and raw artifact access."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


def find_repo_root() -> Path:
    """Find the root directory of the repository by walking parents."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "docs" / "evidence-freeze").exists():
            return parent
    if (Path.cwd() / "docs" / "evidence-freeze").exists():
        return Path.cwd()
    return current.parents[2]


REPO_ROOT = find_repo_root()


def compute_file_sha256(path: Path | str) -> Optional[str]:
    """Compute the SHA-256 hash of a file on disk."""
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file_integrity(relative_path: str, expected_sha256: Optional[str]) -> dict[str, Any]:
    """Verify physical presence and cryptographic match of a file."""
    p = REPO_ROOT / relative_path
    exists = p.is_file()
    if not exists:
        return {
            "path": relative_path,
            "exists": False,
            "size_bytes": 0,
            "actual_sha256": None,
            "expected_sha256": expected_sha256,
            "match": False,
            "status": "MISSING_FILE",
        }
    actual_sha = compute_file_sha256(p)
    size = p.stat().st_size
    if expected_sha256:
        match = (actual_sha.lower() == expected_sha256.lower())
        status = "VERIFIED" if match else "HASH_MISMATCH"
    else:
        match = True
        status = "UNHASHED_PRESENT"
    return {
        "path": relative_path,
        "exists": True,
        "size_bytes": size,
        "actual_sha256": actual_sha,
        "expected_sha256": expected_sha256,
        "match": match,
        "status": status,
    }


def read_manifest_file(manifest_rel_path: str) -> dict[str, Any]:
    """Read a manifest JSON file with error handling."""
    p = REPO_ROOT / manifest_rel_path
    if not p.is_file():
        return {"error": f"Manifest file not found: {manifest_rel_path}"}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        return {"error": f"Failed to parse manifest: {exc}"}


def get_raw_file_bytes(rel_path: str) -> Optional[bytes]:
    """Read binary or text content of a file for download."""
    p = REPO_ROOT / rel_path
    if not p.is_file():
        return None
    return p.read_bytes()
