from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
from pathlib import Path
import subprocess
import sys


REFERENCE_COMMIT = "12ddbcc66b0f1b3679c3f87ab1598cd538fdaa47"
PYTHON_VERSION = (3, 11, 15)
LOCKFILE = Path("requirements/meta-fwd-001.lock.txt")

# Dependency closure of the first META_FWD_001 signal path. These files existed
# at registration and are frozen byte-for-byte to REFERENCE_COMMIT. New audit,
# reporting and settlement modules may be added without changing this set.
FROZEN_SOURCE_PATHS = (
    "src/metaalpha/forward_meta.py",
    "src/metaalpha/data_sources.py",
    "src/metaalpha/hybrid_model.py",
    "src/metaalpha/market_baseline.py",
    "src/metaalpha/meta_branch.py",
    "src/metaalpha/calendar_cycle.py",
    "src/metaalpha/liuyao_hash.py",
    "src/metaalpha/meihua.py",
    "src/metaalpha/pipeline.py",
    "src/metaalpha/qimen_market.py",
    "src/metaalpha/qimen_v1.py",
    "src/metaalpha/symbolic_state.py",
    "src/metaalpha/bazi_ziping.py",
    "src/metaalpha/calendar_features.py",
    "src/metaalpha/controls.py",
    "src/metaalpha/ganzhi.py",
    "src/metaalpha/labels.py",
    "src/metaalpha/natal_transit.py",
    "src/metaalpha/validation.py",
    "src/metaalpha/zpzt_route_v3.py",
    "src/metaalpha/zpzt_route_v4.py",
    "src/metaalpha/zpzt_state.py",
    "src/metaalpha/zpzt_strength.py",
    "src/metaalpha/zpzt_structure_v4.py",
    "src/metaalpha/zpzt_use_v2.py",
)


def _git_show(repo_root: Path, ref: str, path: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace").strip() or f"git show failed: {path}")
    return proc.stdout


def source_freeze_report(repo_root: Path) -> dict[str, object]:
    failures: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for rel in FROZEN_SOURCE_PATHS:
        current_path = repo_root / rel
        if not current_path.exists():
            failures[rel] = "missing from current checkout"
            continue
        try:
            frozen = _git_show(repo_root, REFERENCE_COMMIT, rel)
        except Exception as exc:
            failures[rel] = f"missing/unreadable at reference commit: {exc}"
            continue
        current = current_path.read_bytes()
        hashes[rel] = hashlib.sha256(current).hexdigest()
        if current != frozen:
            failures[rel] = "current bytes differ from frozen registration commit"
    return {
        "reference_commit": REFERENCE_COMMIT,
        "frozen_source_count": len(FROZEN_SOURCE_PATHS),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "current_sha256": hashes,
    }


def _parse_lockfile(path: Path) -> dict[str, str]:
    expected: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"lockfile entry is not exact: {line}")
        name, version = line.split("==", 1)
        expected[name.strip()] = version.strip()
    return expected


def runtime_freeze_report(repo_root: Path) -> dict[str, object]:
    failures: dict[str, str] = {}
    current_python = tuple(sys.version_info[:3])
    if current_python != PYTHON_VERSION:
        failures["python"] = f"expected {'.'.join(map(str, PYTHON_VERSION))}, got {'.'.join(map(str, current_python))}"

    lock_path = repo_root / LOCKFILE
    if not lock_path.exists():
        failures["lockfile"] = f"missing {LOCKFILE.as_posix()}"
        expected = {}
    else:
        try:
            expected = _parse_lockfile(lock_path)
        except Exception as exc:
            failures["lockfile"] = str(exc)
            expected = {}

    installed: dict[str, str] = {}
    for name, wanted in expected.items():
        try:
            actual = metadata.version(name)
        except metadata.PackageNotFoundError:
            failures[f"package:{name}"] = f"expected {wanted}, package not installed"
            continue
        installed[name] = actual
        if actual != wanted:
            failures[f"package:{name}"] = f"expected {wanted}, got {actual}"

    return {
        "python_expected": ".".join(map(str, PYTHON_VERSION)),
        "python_actual": ".".join(map(str, current_python)),
        "lockfile": LOCKFILE.as_posix(),
        "locked_package_count": len(expected),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "installed_versions": installed,
    }


def verify_all(repo_root: Path) -> dict[str, object]:
    source = source_freeze_report(repo_root)
    runtime = runtime_freeze_report(repo_root)
    status = "PASS" if source["status"] == "PASS" and runtime["status"] == "PASS" else "FAIL"
    return {
        "family_id": "META_FWD_001",
        "status": status,
        "source": source,
        "runtime": runtime,
        "note": "Predictive source and runtime are frozen to the first eligible META_FWD_001 run; audit/settlement code is outside the frozen predictor closure.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify frozen META_FWD_001 predictive source/runtime")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    report = verify_all(args.repo_root.resolve())
    import json
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
