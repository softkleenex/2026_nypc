#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

from analyze_server_logs import (
    apply_events,
    base_count,
    calculate_hops,
    hq_level,
    parse_log,
    warriors_at,
)


def map_hash(path: Path) -> str:
    lines = path.read_text(errors="replace").splitlines()
    start = lines.index("MAP") + 1
    end = lines.index("END MAP", start)
    blob = "\n".join(lines[start:end]).encode()
    return hashlib.sha1(blob).hexdigest()[:12]


def first_turn(values: list[tuple[int, int]], threshold: int) -> int:
    return next((turn for turn, value in values if value >= threshold), 0)


def enemy_near_home_count(game, hop: list[list[int]], side: str, max_hop: int) -> int:
    enemy = "B" if side == "A" else "A"
    home = game.hq_region(side)
    return sum(1 for w in game.warriors.values() if w.side == enemy and hop[w.region][home] <= max_hop)


def analyze_feature(path: Path, my_side: str = "A") -> dict[str, int | str]:
    game = parse_log(path)
    hop = calculate_hops(game.adj)
    enemy = "B" if my_side == "A" else "A"

    my_base_by_turn: list[tuple[int, int]] = []
    enemy_base_by_turn: list[tuple[int, int]] = []
    enemy_alive_by_turn: list[tuple[int, int]] = []
    enemy_near3_by_turn: list[tuple[int, int]] = []
    enemy_near6_by_turn: list[tuple[int, int]] = []
    enemy_hq_level_by_turn: list[tuple[int, int]] = []
    my_hq_level_by_turn: list[tuple[int, int]] = []
    my_hq_siege_turn = 0
    enemy_hq_siege_turn = 0

    for turn in sorted(game.commands):
        my_base_by_turn.append((turn, base_count(game, my_side)))
        enemy_base_by_turn.append((turn, base_count(game, enemy)))
        enemy_alive_by_turn.append((turn, sum(1 for w in game.warriors.values() if w.side == enemy)))
        enemy_near3_by_turn.append((turn, enemy_near_home_count(game, hop, my_side, 3)))
        enemy_near6_by_turn.append((turn, enemy_near_home_count(game, hop, my_side, 6)))
        enemy_hq_level_by_turn.append((turn, hq_level(game, enemy)))
        my_hq_level_by_turn.append((turn, hq_level(game, my_side)))

        for event in game.result_events.get(turn, []):
            parts = event.split()
            if len(parts) >= 4 and parts[0] == "SIEGE":
                siege_side = parts[1]
                region = int(parts[2])
                if siege_side == my_side and region == game.hq_region(my_side) and my_hq_siege_turn == 0:
                    my_hq_siege_turn = turn
                if siege_side == enemy and region == game.hq_region(enemy) and enemy_hq_siege_turn == 0:
                    enemy_hq_siege_turn = turn
        apply_events(game, turn)

    my_win = (
        (my_side == "A" and game.result.startswith("LEFT_WIN"))
        or (my_side == "B" and game.result.startswith("RIGHT_WIN"))
    )
    my_loss = (
        (my_side == "A" and game.result.startswith("RIGHT_WIN"))
        or (my_side == "B" and game.result.startswith("LEFT_WIN"))
    )

    return {
        "file": path.name,
        "map_hash": map_hash(path),
        "result": game.result,
        "my_result": "WIN" if my_win else "LOSS" if my_loss else "DRAW",
        "turn": game.end_turn,
        "n": game.n,
        "k": game.k,
        "my_hq_upgrades": ",".join(map(str, game.hq_upgrade_turns[my_side])),
        "enemy_hq_upgrades": ",".join(map(str, game.hq_upgrade_turns[enemy])),
        "my_first_hq2": first_turn(my_hq_level_by_turn, 2),
        "enemy_first_hq2": first_turn(enemy_hq_level_by_turn, 2),
        "my_first_base1": first_turn(my_base_by_turn, 1),
        "my_first_base2": first_turn(my_base_by_turn, 2),
        "my_first_base3": first_turn(my_base_by_turn, 3),
        "enemy_first_base1": first_turn(enemy_base_by_turn, 1),
        "enemy_first_base2": first_turn(enemy_base_by_turn, 2),
        "enemy_first_base3": first_turn(enemy_base_by_turn, 3),
        "enemy_first_base4": first_turn(enemy_base_by_turn, 4),
        "enemy_first_base5": first_turn(enemy_base_by_turn, 5),
        "enemy_first_near3": first_turn(enemy_near3_by_turn, 1),
        "enemy_first_near6": first_turn(enemy_near6_by_turn, 1),
        "enemy_first_alive8": first_turn(enemy_alive_by_turn, 8),
        "my_hq_siege_turn": my_hq_siege_turn,
        "enemy_hq_siege_turn": enemy_hq_siege_turn,
        "final_my_bases": base_count(game, my_side),
        "final_enemy_bases": base_count(game, enemy),
        "final_my_hq": hq_level(game, my_side),
        "final_enemy_hq": hq_level(game, enemy),
        "final_my_hq_workers": warriors_at(game, my_side, game.hq_region(my_side)),
        "final_enemy_hq_workers": warriors_at(game, enemy, game.hq_region(enemy)),
    }


def collect(paths: list[Path]) -> list[Path]:
    logs: list[Path] = []
    for path in paths:
        if path.is_dir():
            logs.extend(sorted(path.glob("*.txt"), key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem))
        else:
            logs.append(path)
    return logs


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract compact NYPC log features for profiling/data.bin design.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--my-side", choices=["A", "B"], default="A")
    args = parser.parse_args()

    rows = [analyze_feature(path, args.my_side) for path in collect(args.paths)]
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
