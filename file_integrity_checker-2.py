#!/usr/bin/env python3
"""
File Integrity Checker — SHA-256
Author: Muskan Sain

Create a baseline of files and later verify that their contents have not changed.
The baseline JSON is excluded automatically when it is stored inside the scanned folder.
Symbolic links are skipped to avoid following files outside the selected folder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALGORITHM = "sha256"
BASELINE_VERSION = 1
DEFAULT_BASELINE = ".file_integrity_baseline.json"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file, reading it in bounded-size chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def collect_files(root: Path, baseline_path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Hash regular files under root; skip symlinks and the baseline itself."""
    root = root.resolve()
    baseline_abs = baseline_path.resolve()
    records: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for current, dirs, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(
            d for d in dirs
            if not (current_path / d).is_symlink()
        )
        for filename in sorted(filenames):
            path = current_path / filename
            if path.is_symlink() or path.resolve() == baseline_abs:
                continue
            try:
                if not path.is_file():
                    continue
                relative = path.relative_to(root).as_posix()
                records[relative] = {
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            except (OSError, PermissionError) as exc:
                errors.append(f"{path}: {exc}")
    return records, errors


def create_baseline(target: Path, baseline: Path) -> dict[str, Any]:
    """Create or replace a SHA-256 baseline for target directory."""
    target = target.expanduser().resolve()
    baseline = baseline.expanduser().resolve()
    if not target.exists() or not target.is_dir():
        raise ValueError(f"Target directory does not exist or is not a directory: {target}")
    if _is_within(baseline, target) is False and baseline.exists() and baseline.is_dir():
        raise ValueError("Baseline path must be a file, not a directory.")

    files, errors = collect_files(target, baseline)
    data = {
        "project": "File Integrity Checker",
        "author": "Muskan Sain",
        "version": BASELINE_VERSION,
        "algorithm": ALGORITHM.upper(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "root_directory": str(target),
        "file_count": len(files),
        "files": files,
    }
    baseline.parent.mkdir(parents=True, exist_ok=True)
    temporary = baseline.with_suffix(baseline.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(baseline)
    if errors:
        print("Warning: some files could not be read:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
    return data


def load_baseline(baseline: Path) -> dict[str, Any]:
    """Load and validate a baseline JSON file."""
    try:
        data = json.loads(baseline.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Baseline not found: {baseline}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Baseline is not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or data.get("algorithm") != "SHA256":
        raise ValueError("Unsupported or invalid baseline format (expected SHA256).")
    if data.get("version") != BASELINE_VERSION or not isinstance(data.get("files"), dict):
        raise ValueError("Unsupported or invalid baseline version.")
    for name, record in data["files"].items():
        if not isinstance(name, str) or not isinstance(record, dict):
            raise ValueError("Invalid file entry in baseline.")
        digest = record.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"Invalid SHA-256 digest for {name!r}.")
    return data


def verify_files(target: Path, baseline: Path) -> dict[str, Any]:
    """Compare current file hashes with the saved baseline."""
    target = target.expanduser().resolve()
    baseline = baseline.expanduser().resolve()
    if not target.exists() or not target.is_dir():
        raise ValueError(f"Target directory does not exist or is not a directory: {target}")
    saved = load_baseline(baseline)
    expected = saved["files"]
    current, errors = collect_files(target, baseline)

    expected_names = set(expected)
    current_names = set(current)
    added = sorted(current_names - expected_names)
    missing = sorted(expected_names - current_names)
    modified = sorted(
        name for name in (current_names & expected_names)
        if current[name]["sha256"] != expected[name]["sha256"]
    )
    unchanged = sorted(
        name for name in (current_names & expected_names)
        if current[name]["sha256"] == expected[name]["sha256"]
    )
    return {
        "added": added,
        "missing": missing,
        "modified": modified,
        "unchanged": unchanged,
        "errors": errors,
        "is_clean": not (added or missing or modified or errors),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create and verify SHA-256 file integrity baselines."
    )
    parser.add_argument("command", choices=("baseline", "verify"), help="Operation to perform")
    parser.add_argument("folder", nargs="?", default=".", help="Folder to scan (default: current folder)")
    parser.add_argument(
        "--baseline", default=None,
        help=f"Baseline JSON path (default: FOLDER/{DEFAULT_BASELINE})"
    )
    args = parser.parse_args(argv)

    target = Path(args.folder)
    baseline = Path(args.baseline) if args.baseline else target / DEFAULT_BASELINE
    try:
        if args.command == "baseline":
            result = create_baseline(target, baseline)
            print(f"Baseline created: {baseline.resolve()}")
            print(f"Files recorded: {result['file_count']}")
            print(f"Hash algorithm: SHA-256")
            return 0

        result = verify_files(target, baseline)
        print("FILE INTEGRITY VERIFICATION")
        print(f"Unchanged: {len(result['unchanged'])}")
        print(f"Modified:  {len(result['modified'])}")
        print(f"Added:     {len(result['added'])}")
        print(f"Missing:   {len(result['missing'])}")
        for label in ("modified", "added", "missing"):
            for name in result[label]:
                print(f"{label.upper()}: {name}")
        for error in result["errors"]:
            print(f"READ ERROR: {error}")
        if result["is_clean"]:
            print("RESULT: PASS — no changes detected.")
            return 0
        print("RESULT: WARNING — changes or read errors detected.")
        return 1
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
