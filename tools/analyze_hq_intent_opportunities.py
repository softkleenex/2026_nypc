#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from analyze_move_intent import apply_turn_and_collect, read_map
from analyze_server_logs import (
    HQ_UPGRADE_COST,
    apply_events,
    alive_count,
    base_count,
    calculate_hops,
    hq_level,
    parse_log,
    warriors_at,
)
from movement_target_policy_data import feature_key


ROOT = Path(__file__).resolve().parents[1]


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


def has_map_block(path: Path) -> bool:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return False
    return "\nMAP\n" in f"\n{text}"


def start_snapshots(path: Path, my_side: str) -> dict[int, dict[str, int]]:
    game = parse_log(path)
    hop = calculate_hops(game.adj)
    foe = "B" if my_side == "A" else "A"
    my_hq = game.hq_region(my_side)
    out: dict[int, dict[str, int]] = {}
    for turn in sorted(game.commands):
        hq_lv = hq_level(game, my_side)
        cost = HQ_UPGRADE_COST[hq_lv + 1] if 0 < hq_lv < 5 else 1000
        out[turn] = {
            "gold": game.gold[my_side],
            "my_alive": alive_count(game, my_side),
            "foe_alive": alive_count(game, foe),
            "my_bases": base_count(game, my_side),
            "foe_bases": base_count(game, foe),
            "hq_lv": hq_lv,
            "hq_hp": game.buildings.get(my_hq).hp if game.buildings.get(my_hq) else 0,
            "hq_workers": warriors_at(game, my_side, my_hq),
            "foe_near1": sum(1 for w in game.warriors.values() if w.side == foe and hop[w.region][my_hq] <= 1),
            "foe_near3": sum(1 for w in game.warriors.values() if w.side == foe and hop[w.region][my_hq] <= 3),
            "hq_upgrade_cost": cost,
            "can_hq_upgrade": int(game.gold[my_side] >= cost and hq_lv < 5),
        }
        apply_events(game, turn)
    return out


def command_summary(path: Path, my_side: str) -> dict[int, dict[str, str | int]]:
    game = parse_log(path)
    side_word = "LEFT" if my_side == "A" else "RIGHT"
    my_hq = game.hq_region(my_side)
    out: dict[int, dict[str, str | int]] = {}
    for turn, sides in game.commands.items():
        commands = sides.get(side_word, [])
        train = 0
        hq_upgrade = 0
        moves_from_hq = 0
        moves_to_hq = 0
        for command in commands:
            parts = command.split()
            if not parts:
                continue
            if parts[0] == "TRAIN":
                train += int(parts[1])
            elif parts[0] == "UPGRADE" and len(parts) == 2 and int(parts[1]) == my_hq:
                hq_upgrade += 1
            elif parts[0] == "MOVE" and len(parts) == 3:
                target = int(parts[2])
                if target == my_hq:
                    moves_to_hq += 1
                # The log command block has target only, not source. Use result
                # state snapshots for source-side questions.
        out[turn] = {
            "train_cmd": train,
            "hq_upgrade_cmd": hq_upgrade,
            "move_to_hq_cmds": moves_to_hq,
            "command_text": ";".join(commands[:8]),
        }
    return out


def target_hits(path: Path, data: dict) -> list[dict[str, int | str]]:
    map_hash, model = read_map(path)
    hop = calculate_hops(model.adj)
    policy = data.get("target_policy") if isinstance(data.get("target_policy"), dict) else data.get("policy", {})
    rows: list[dict[str, int | str]] = []
    for record in apply_turn_and_collect(path, map_hash, model, "auto"):
        if record.my_side not in {"A", "B"} or record.side == record.my_side:
            continue
        key = feature_key(model, hop, record)
        value = policy.get(key) if isinstance(policy, dict) else None
        if isinstance(value, list) and len(value) >= 2 and value[1] == "my_hq":
            rows.append(
                {
                    "file": Path(record.file).name,
                    "detect_turn": record.turn,
                    "action_turn": record.turn + 1,
                    "my_side": record.my_side,
                    "wid": record.wid,
                    "actual_target": record.actual_target,
                    "target_type": record.target_type,
                }
            )
    return rows


def analyze(path: Path, data: dict) -> list[dict[str, int | str]]:
    map_hash, _model = read_map(path)
    records = apply_turn_and_collect(path, map_hash, _model, "auto")
    my_side = next((r.my_side for r in records if r.my_side in {"A", "B"}), "")
    if not my_side:
        return []
    snaps = start_snapshots(path, my_side)
    commands = command_summary(path, my_side)
    rows = []
    grouped: Counter[int] = Counter()
    for hit in target_hits(path, data):
        if hit["target_type"] == "my_hq":
            grouped[int(hit["detect_turn"])] += 1
    for detect_turn, n_hits in sorted(grouped.items()):
        action_turn = detect_turn + 1
        row: dict[str, int | str] = {
            "file": path.name,
            "detect_turn": detect_turn,
            "action_turn": action_turn,
            "target_hits": n_hits,
        }
        row.update(snaps.get(action_turn, {}))
        row.update(commands.get(action_turn, {}))
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect possible actions after target-policy my-HQ intent signals.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--data", type=Path, default=ROOT / "bots" / "172_data.bin")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.data.read_text())
    rows: list[dict[str, int | str]] = []
    for path in collect_logs(args.paths):
        try:
            rows.extend(analyze(path, data))
        except Exception as exc:  # noqa: BLE001 - batch mode should continue.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
