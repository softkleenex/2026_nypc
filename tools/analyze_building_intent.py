#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

from analyze_move_intent import MapModel, read_map, side_from_file
from analyze_server_logs import HQ_TRAIN_HP, Warrior, apply_upgrade, hq_level, parse_log


def collect(paths: list[Path]) -> list[Path]:
    logs: list[Path] = []
    for path in paths:
        if path.is_dir():
            logs.extend(sorted(p for p in path.rglob("*") if p.is_file() and p.suffix in {".txt", ".log"}))
        elif path.is_file():
            logs.append(path)
    return logs


def update_active_targets(game, turn: int, active_targets: dict[str, int], traces: dict[str, tuple[int, frozenset[int], int]]) -> None:
    for commands in game.commands[turn].values():
        for command in commands:
            parts = command.split()
            if len(parts) == 3 and parts[0] == "MOVE" and parts[1] in game.warriors:
                wid = parts[1]
                target = int(parts[2])
                if active_targets.get(wid) != target:
                    traces.pop(wid, None)
                active_targets[wid] = target


def owned_candidates(game, candidates: frozenset[int], side: str, include_hq: bool) -> frozenset[int]:
    out = []
    for region in candidates:
        building = game.buildings.get(region)
        if building is None or building.side != side:
            continue
        if not include_hq and building.kind == "HQ":
            continue
        out.append(region)
    return frozenset(out)


def analyze_one(path: Path, map_hash: str, model: MapModel, include_hq: bool) -> Counter[str]:
    game = parse_log(path)
    my_side = side_from_file(path)
    if my_side not in {"A", "B"}:
        return Counter()
    active_targets: dict[str, int] = {}
    traces: dict[str, tuple[int, frozenset[int], int]] = {}
    counts: Counter[str] = Counter(logs=1)

    for turn in sorted(game.commands):
        update_active_targets(game, turn, active_targets, traces)
        for event in game.result_events.get(turn, []):
            parts = event.split()
            if not parts:
                continue
            if parts[0] == "UPGRADE" and len(parts) >= 3:
                apply_upgrade(game, parts[1], int(parts[2]))
                continue
            if parts[0] == "TRAIN" and len(parts) >= 2:
                for wid in parts[1:]:
                    side = wid[0]
                    level = hq_level(game, side) or 1
                    game.warriors[wid] = Warrior(side, game.hq_region(side), HQ_TRAIN_HP[level])
                continue
            if parts[0] == "MOVE" and len(parts) == 3:
                wid = parts[1]
                dst = int(parts[2])
                warrior = game.warriors.get(wid)
                if warrior is None:
                    continue
                src = warrior.region
                actual = active_targets.get(wid)
                if wid[0] != my_side and actual is not None and src != dst:
                    counts["enemy_moves"] += 1
                    cands = frozenset(model.candidate_targets(src, dst))
                    old = traces.get(wid)
                    if old is not None and old[0] == actual:
                        merged = old[1] & cands
                        steps = old[2] + 1
                        if not merged:
                            merged = cands
                            steps = 1
                    else:
                        merged = cands
                        steps = 1
                    traces[wid] = (actual, merged, steps)
                    owned = owned_candidates(game, merged, my_side, include_hq)
                    actual_owned = actual in owned
                    actual_base = False
                    actual_building = game.buildings.get(actual)
                    if actual_building is not None and actual_building.side == my_side:
                        actual_base = include_hq or actual_building.kind != "HQ"
                    for step_min in (1, 2, 3):
                        if steps < step_min:
                            continue
                        for cap in (1, 2, 3, 5, 8):
                            if len(merged) <= cap and owned:
                                key = f"s{step_min}_c{cap}"
                                counts[f"{key}_triggers"] += 1
                                counts[f"{key}_actual_owned"] += int(actual_owned)
                                counts[f"{key}_actual_base"] += int(actual_base)
                                counts[f"{key}_owned_count_sum"] += len(owned)
                                if len(owned) == 1:
                                    counts[f"{key}_single"] += 1
                                    counts[f"{key}_single_actual"] += int(actual_owned)
                if warrior is not None:
                    warrior.region = dst
                if active_targets.get(wid) == dst:
                    active_targets.pop(wid, None)
                    traces.pop(wid, None)
                continue
            if parts[0] == "DAMAGE" and len(parts) == 4:
                wid = parts[2]
                warrior = game.warriors.get(wid)
                if warrior is not None:
                    warrior.hp -= int(parts[3])
                continue
            if parts[0] == "SIEGE" and len(parts) == 4:
                region = int(parts[2])
                building = game.buildings.get(region)
                if building is not None:
                    building.hp -= int(parts[3])

        for wid in [wid for wid, warrior in game.warriors.items() if warrior.hp <= 0]:
            del game.warriors[wid]
            active_targets.pop(wid, None)
            traces.pop(wid, None)
        for region in [region for region, building in game.buildings.items() if building.hp <= 0]:
            del game.buildings[region]

    return counts


def pct(part: int, total: int) -> str:
    return "0.0" if total == 0 else f"{part * 100.0 / total:.1f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze whether movement traces identify incoming attacks on our buildings.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--include-hq", action="store_true")
    args = parser.parse_args()

    total: Counter[str] = Counter()
    cache = {}
    for path in collect(args.paths):
        try:
            map_hash, model = read_map(path)
            if map_hash not in cache:
                cache[map_hash] = model
            total.update(analyze_one(path, map_hash, cache[map_hash], args.include_hq))
        except Exception as exc:  # noqa: BLE001 - keep batch running.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)

    rows = [("logs", total["logs"]), ("enemy_moves", total["enemy_moves"])]
    for step_min in (1, 2, 3):
        for cap in (1, 2, 3, 5, 8):
            key = f"s{step_min}_c{cap}"
            n = total[f"{key}_triggers"]
            if n == 0:
                continue
            rows.append((f"{key}_triggers", str(n)))
            rows.append((f"{key}_actual_owned", f"{total[f'{key}_actual_owned']} ({pct(total[f'{key}_actual_owned'], n)}%)"))
            rows.append((f"{key}_actual_base", f"{total[f'{key}_actual_base']} ({pct(total[f'{key}_actual_base'], n)}%)"))
            rows.append((f"{key}_avg_owned_candidates", f"{total[f'{key}_owned_count_sum'] / n:.2f}"))
            single = total[f"{key}_single"]
            rows.append((f"{key}_single", f"{single} ({pct(single, n)}%)"))
            rows.append((f"{key}_single_actual", f"{total[f'{key}_single_actual']} ({pct(total[f'{key}_single_actual'], single)}%)"))

    writer = csv.writer(sys.stdout)
    writer.writerow(["metric", "value"])
    writer.writerows(rows)


if __name__ == "__main__":
    main()
