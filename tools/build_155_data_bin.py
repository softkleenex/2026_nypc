#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_data_bin import build_map_plan, map_fingerprint, parse_log_map


ROOT = Path(__file__).resolve().parents[1]
MAX_DATA_BIN = 10 * 1024 * 1024


def default_roots() -> list[Path]:
    roots: list[Path] = []
    roots.extend(sorted((ROOT / "bots").glob("*_nypc_log")))
    roots.extend(sorted((ROOT / "bots").glob("*_user_log*")))
    archive = ROOT / "bots" / "archive" / "user_logs"
    if archive.exists():
        roots.append(archive)
    return roots


def collect_logs(paths: list[Path]) -> list[Path]:
    logs: list[Path] = []
    for path in paths:
        if path.is_dir():
            logs.extend(
                sorted(
                    p for p in path.rglob("*")
                    if p.is_file() and p.suffix in {".txt", ".log"}
                )
            )
        elif path.is_file():
            logs.append(path)
    return logs


def build_profiles(logs: list[Path]) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for path in logs:
        info = parse_log_map(path)
        if info is None:
            continue
        key = map_fingerprint(info)
        if key not in profiles:
            profiles[key] = {"plan": build_map_plan(info)}
            counts[key] = 0
        counts[key] += 1
    for key, count in counts.items():
        profiles[key]["observed"] = count
    return profiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Build data.bin map profiles for bots/155.py.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "bots" / "155_data.bin")
    args = parser.parse_args()

    roots = args.paths or default_roots()
    profiles = build_profiles(collect_logs(roots))
    payload = {
        "format": "nypc-155-profile-json",
        "version": 1,
        "profiles": profiles,
    }
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_DATA_BIN:
        raise SystemExit(f"data.bin too large: {len(raw)} > {MAX_DATA_BIN}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(f"wrote {args.output} ({len(raw)} bytes, profiles={len(profiles)})")


if __name__ == "__main__":
    main()
