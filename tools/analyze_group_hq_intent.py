#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from analyze_move_intent import apply_turn_and_collect, read_map
from analyze_server_logs import (
    apply_events,
    alive_count,
    base_count,
    calculate_hops,
    hq_level,
    parse_log,
)
from movement_target_policy_data import feature_key as target_policy_key


ROOT = Path(__file__).resolve().parents[1]


def has_map_block(path: Path) -> bool:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return False
    return "\nMAP\n" in f"\n{text}"


def collect_logs(paths: list[Path]) -> list[Path]:
    logs: list[Path] = []
    for path in paths:
        if path.is_dir():
            logs.extend(
                sorted(
                    p for p in path.rglob("*")
                    if p.is_file() and p.suffix in {".txt", ".log"} and has_map_block(p)
                )
            )
        elif path.is_file() and has_map_block(path):
            logs.append(path)
    return logs


def load_my_hq_target_policy(path: Path | None) -> set[str]:
    if path is None:
        return set()
    data = json.loads(path.read_text())
    policy = data.get("target_policy") if isinstance(data.get("target_policy"), dict) else data.get("policy", {})
    if not isinstance(policy, dict):
        return set()
    return {
        key for key, value in policy.items()
        if isinstance(value, list) and len(value) >= 2 and value[1] == "my_hq"
    }


def state_snapshots(path: Path, my_side: str) -> dict[int, dict[str, int]]:
    game = parse_log(path)
    hop = calculate_hops(game.adj)
    foe = "B" if my_side == "A" else "A"
    home = game.hq_region(my_side)
    out: dict[int, dict[str, int]] = {}
    for turn in sorted(game.commands):
        out[turn] = {
            "my_bases": base_count(game, my_side),
            "foe_bases": base_count(game, foe),
            "my_alive": alive_count(game, my_side),
            "foe_alive": alive_count(game, foe),
            "my_hq_lv": hq_level(game, my_side),
            "foe_near3": sum(
                1 for warrior in game.warriors.values()
                if warrior.side == foe and hop[warrior.region][home] <= 3
            ),
        }
        apply_events(game, turn)
    return out


def analyze(paths: list[Path], data_path: Path | None) -> list[dict[str, int | str]]:
    target_policy = load_my_hq_target_policy(data_path)
    rows: list[dict[str, int | str]] = []
    map_cache = {}
    hop_cache = {}
    for path in collect_logs(paths):
        try:
            map_hash, model = read_map(path)
            if map_hash not in map_cache:
                map_cache[map_hash] = model
                hop_cache[map_hash] = calculate_hops(model.adj)
            model = map_cache[map_hash]
            hop = hop_cache[map_hash]
            records = apply_turn_and_collect(path, map_hash, model, "auto")
            my_side = next((record.my_side for record in records if record.my_side in {"A", "B"}), "")
            states = state_snapshots(path, my_side) if my_side else {}
        except Exception as exc:  # noqa: BLE001 - keep large batches robust.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)
            continue

        live_trace: dict[str, tuple[frozenset[int], int, int]] = {}
        turn_rows: dict[tuple[int, str], Counter[str]] = defaultdict(Counter)
        for record in records:
            if record.my_side not in {"A", "B"} or record.side == record.my_side:
                continue
            home = 0 if record.my_side == "A" else model.n - 1
            cands = frozenset(model.candidate_targets(record.src, record.dst))
            old = live_trace.get(record.wid)
            if old is not None and record.turn - old[2] <= 2:
                merged = old[0] & cands
                steps = old[1] + 1
                if not merged:
                    merged = cands
                    steps = 1
            else:
                merged = cands
                steps = 1
            live_trace[record.wid] = (merged, steps, record.turn)

            key = target_policy_key(model, hop, record)
            policy_hit = key in target_policy if key is not None else False
            group = turn_rows[(record.turn, record.my_side)]
            group["enemy_moves"] += 1
            group["actual_hq_moves"] += int(record.target_type == "my_hq")
            group["actual_building_moves"] += int(record.target_type == "my_building")
            group["step_hq_support"] += int(home in cands)
            group["trace_hq_support"] += int(steps >= 2 and len(merged) <= 12 and home in merged)
            group["target_policy_hq_support"] += int(policy_hit)
            group["policy_trace_hq_support"] += int(policy_hit and home in merged)

        for (turn, side), counts in sorted(turn_rows.items()):
            row: dict[str, int | str] = {
                "file": path.name,
                "log_path": str(path),
                "map_hash": map_hash,
                "turn": turn,
                "my_side": side,
                "enemy_moves": counts["enemy_moves"],
                "actual_hq_moves": counts["actual_hq_moves"],
                "actual_building_moves": counts["actual_building_moves"],
                "step_hq_support": counts["step_hq_support"],
                "trace_hq_support": counts["trace_hq_support"],
                "target_policy_hq_support": counts["target_policy_hq_support"],
                "policy_trace_hq_support": counts["policy_trace_hq_support"],
            }
            row.update(states.get(turn, {}))
            rows.append(row)
    return rows


def pct(part: int, total: int) -> str:
    return "0.0" if total == 0 else f"{part * 100.0 / total:.1f}"


def summarize(rows: list[dict[str, int | str]]) -> list[list[str]]:
    out = [["signal", "threshold", "pred_turns", "correct_turns", "precision_pct", "actual_hq_turns", "recall_pct"]]
    actual_turns = sum(1 for row in rows if int(row["actual_hq_moves"]) > 0)
    for signal in (
        "step_hq_support",
        "trace_hq_support",
        "target_policy_hq_support",
        "policy_trace_hq_support",
    ):
        max_value = max((int(row[signal]) for row in rows), default=0)
        for threshold in range(1, min(12, max_value) + 1):
            pred = [row for row in rows if int(row[signal]) >= threshold]
            correct = sum(1 for row in pred if int(row["actual_hq_moves"]) > 0)
            detected_actual = sum(
                1 for row in rows
                if int(row["actual_hq_moves"]) > 0 and int(row[signal]) >= threshold
            )
            out.append(
                [
                    signal,
                    str(threshold),
                    str(len(pred)),
                    str(correct),
                    pct(correct, len(pred)),
                    str(actual_turns),
                    pct(detected_actual, actual_turns),
                ]
            )
    return out


def write_rows(path: Path, rows: list[dict[str, int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "file", "log_path", "map_hash", "turn", "my_side", "enemy_moves",
        "actual_hq_moves", "actual_building_moves", "step_hq_support",
        "trace_hq_support", "target_policy_hq_support", "policy_trace_hq_support",
        "my_bases", "foe_bases", "my_alive", "foe_alive", "my_hq_lv", "foe_near3",
    ]
    with path.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze same-turn grouped enemy movement support for HQ intent.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    rows = analyze(args.paths, args.data)
    if args.output:
        write_rows(args.output, rows)
    summary = summarize(rows)
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_output.open("w", newline="") as fp:
            csv.writer(fp).writerows(summary)
    else:
        csv.writer(sys.stdout).writerows(summary)


if __name__ == "__main__":
    main()
