#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from analyze_move_intent import apply_turn_and_collect, read_map


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


def load_profiles(path: Path) -> dict:
    data = json.loads(path.read_text())
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise SystemExit(f"profiles missing from {path}")
    return profiles


def flip_region(n: int, side: str, region: int) -> int:
    return n - 1 - region if side == "B" else region


def hot_edges_for(profiles: dict, map_hash: str, my_side: str) -> set[tuple[int, int]]:
    profile = profiles.get(map_hash)
    if not isinstance(profile, dict):
        return set()
    side_key = "right" if my_side == "B" else "left"
    side = profile.get(side_key)
    edges = side.get("hq_edges") if isinstance(side, dict) else None
    if not isinstance(edges, dict):
        return set()
    out: set[tuple[int, int]] = set()
    for key in edges:
        parts = key.split(",")
        if len(parts) != 2:
            continue
        try:
            out.add((int(parts[0]), int(parts[1])))
        except ValueError:
            continue
    return out


def pct(part: int, total: int) -> str:
    return "0.0" if total == 0 else f"{part * 100.0 / total:.1f}"


def evaluate(logs: list[Path], profiles: dict) -> Counter[str]:
    counts: Counter[str] = Counter()
    map_cache = {}
    for path in logs:
        try:
            map_hash, model = read_map(path)
            if map_hash not in map_cache:
                map_cache[map_hash] = model
            model = map_cache[map_hash]
            records = apply_turn_and_collect(path, map_hash, model, "auto")
        except Exception as exc:  # noqa: BLE001 - batch evaluator should skip malformed files.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)
            continue

        live_trace: dict[str, tuple[frozenset[int], int, int, int]] = {}
        counts["logs"] += 1
        for record in records:
            if record.my_side not in {"A", "B"} or record.side == record.my_side:
                continue
            counts["enemy_moves"] += 1
            cands = frozenset(model.candidate_targets(record.src, record.dst))
            old = live_trace.get(record.wid)
            src = flip_region(model.n, record.my_side, record.src)
            dst = flip_region(model.n, record.my_side, record.dst)
            edge_hot = (src, dst) in hot_edges_for(profiles, map_hash, record.my_side)
            counts["hot_edge_moves"] += int(edge_hot)
            counts["hot_edge_actual_hq"] += int(edge_hot and record.target_type == "my_hq")
            counts["hot_edge_contains_hq"] += int(edge_hot and record.contains_my_hq)

            if old is not None and record.turn - old[2] <= 2:
                merged = old[0] & cands
                steps = old[1] + 1
                hot_steps = old[3] + 1 if edge_hot else 0
                if not merged:
                    merged = cands
                    steps = 1
                    hot_steps = 1 if edge_hot else 0
            else:
                merged = cands
                steps = 1
                hot_steps = 1 if edge_hot else 0
            live_trace[record.wid] = (merged, steps, record.turn, hot_steps)

            tight_route = steps >= 2 and len(merged) <= 5 and record.my_side == "A" and 0 in merged
            if record.my_side == "B":
                tight_route = steps >= 2 and len(merged) <= 5 and model.n - 1 in merged
            data_route = steps >= 2 and hot_steps >= 2 and len(merged) <= 12
            if record.my_side == "A":
                data_route = data_route and 0 in merged
            else:
                data_route = data_route and model.n - 1 in merged

            if tight_route:
                counts["tight_triggers"] += 1
                counts["tight_actual_hq"] += int(record.target_type == "my_hq")
            if data_route:
                counts["data_triggers"] += 1
                counts["data_actual_hq"] += int(record.target_type == "my_hq")
            if data_route and not tight_route:
                counts["data_extra_triggers"] += 1
                counts["data_extra_actual_hq"] += int(record.target_type == "my_hq")

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate movement-intent data.bin precision on logs.")
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--data", type=Path, default=Path("bots/156_data.bin"))
    args = parser.parse_args()

    counts = evaluate(collect_logs(args.logs), load_profiles(args.data))
    rows = [
        ("logs", counts["logs"]),
        ("enemy_moves", counts["enemy_moves"]),
        ("hot_edge_moves", f"{counts['hot_edge_moves']} ({pct(counts['hot_edge_moves'], counts['enemy_moves'])}%)"),
        ("hot_edge_actual_hq", f"{counts['hot_edge_actual_hq']} ({pct(counts['hot_edge_actual_hq'], counts['hot_edge_moves'])}%)"),
        ("hot_edge_contains_hq", f"{counts['hot_edge_contains_hq']} ({pct(counts['hot_edge_contains_hq'], counts['hot_edge_moves'])}%)"),
        ("tight_triggers", str(counts["tight_triggers"])),
        ("tight_actual_hq", f"{counts['tight_actual_hq']} ({pct(counts['tight_actual_hq'], counts['tight_triggers'])}%)"),
        ("data_triggers", str(counts["data_triggers"])),
        ("data_actual_hq", f"{counts['data_actual_hq']} ({pct(counts['data_actual_hq'], counts['data_triggers'])}%)"),
        ("data_extra_triggers", str(counts["data_extra_triggers"])),
        ("data_extra_actual_hq", f"{counts['data_extra_actual_hq']} ({pct(counts['data_extra_actual_hq'], counts['data_extra_triggers'])}%)"),
    ]
    writer = csv.writer(sys.stdout)
    writer.writerow(["metric", "value"])
    writer.writerows(rows)


if __name__ == "__main__":
    main()
