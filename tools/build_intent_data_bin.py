#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from analyze_move_intent import apply_turn_and_collect, read_map


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


def flip_region(n: int, side: str, region: int) -> int:
    return n - 1 - region if side == "B" else region


def build_profiles(logs: list[Path], min_count: int, min_precision: float) -> dict[str, dict]:
    stats: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    observed: dict[str, int] = defaultdict(int)
    map_sizes: dict[str, int] = {}
    map_cache = {}

    for path in logs:
        try:
            map_hash, model = read_map(path)
            if map_hash not in map_cache:
                map_cache[map_hash] = model
            model = map_cache[map_hash]
            records = apply_turn_and_collect(path, map_hash, model, "auto")
        except Exception:
            continue
        observed[map_hash] += 1
        map_sizes[map_hash] = model.n
        for record in records:
            if record.my_side not in {"A", "B"} or record.side == record.my_side:
                continue
            side_key = "right" if record.my_side == "B" else "left"
            src = flip_region(model.n, record.my_side, record.src)
            dst = flip_region(model.n, record.my_side, record.dst)
            key = (map_hash, side_key, f"{src},{dst}")
            row = stats[key]
            row[0] += 1
            row[1] += int(record.target_type == "my_hq")
            row[2] += int(record.contains_my_hq)
            row[3] += record.candidate_count

    profiles: dict[str, dict] = {}
    for (map_hash, side_key, edge), (total, hq, hq_compatible, cand_sum) in stats.items():
        if total < min_count:
            continue
        precision = hq / total if total else 0.0
        if precision < min_precision:
            continue
        profile = profiles.setdefault(
            map_hash,
            {"n": map_sizes.get(map_hash, 0), "observed_logs": observed.get(map_hash, 0)},
        )
        side = profile.setdefault(side_key, {})
        edges = side.setdefault("hq_edges", {})
        edges[edge] = [
            total,
            hq,
            hq_compatible,
            round(cand_sum / total, 2),
        ]
    return profiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Build movement-intent data.bin profiles from logs.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "bots" / "156_data.bin")
    parser.add_argument("--min-count", type=int, default=3)
    parser.add_argument("--min-precision", type=float, default=0.75)
    args = parser.parse_args()

    roots = args.paths or default_roots()
    profiles = build_profiles(collect_logs(roots), args.min_count, args.min_precision)
    payload = {
        "format": "nypc-156-intent-json",
        "version": 1,
        "min_count": args.min_count,
        "min_precision": args.min_precision,
        "profiles": profiles,
    }
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_DATA_BIN:
        raise SystemExit(f"data.bin too large: {len(raw)} > {MAX_DATA_BIN}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    edge_count = sum(
        len(side.get("hq_edges", {}))
        for profile in profiles.values()
        for side in (profile.get("left", {}), profile.get("right", {}))
        if isinstance(side, dict)
    )
    print(f"wrote {args.output} ({len(raw)} bytes, profiles={len(profiles)}, edges={edge_count})")


if __name__ == "__main__":
    main()
