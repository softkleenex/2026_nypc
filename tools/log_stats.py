#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


def side_of_warrior(wid: str) -> str:
    return wid[0]


def result_side(row: dict[str, str]) -> str:
    side = row.get("bot_side", "LEFT")
    return "A" if side == "LEFT" else "B"


def parse_log(path: Path, my_side: str | None) -> dict[str, int | str]:
    stats: Counter[str] = Counter()
    result = ""
    max_turn = 0
    map_next = False
    n_regions: int | None = None
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split()
        if parts == ["MAP"]:
            map_next = True
            continue
        if map_next:
            if len(parts) >= 1 and parts[0].isdigit():
                n_regions = int(parts[0])
            map_next = False
            continue
        if len(parts) == 2 and parts[0] == "TURN":
            max_turn = max(max_turn, int(parts[1]))
        elif len(parts) >= 3 and parts[0] == "RESULT":
            result = " ".join(parts[1:])
        elif len(parts) >= 2 and parts[0] == "TRAIN":
            for wid in parts[1:]:
                if wid[0] in "AB":
                    stats[f"train_{wid[0]}"] += 1
        elif len(parts) >= 3 and parts[0] == "UPGRADE":
            side = parts[1]
            region = parts[2]
            stats[f"upgrade_{side}"] += 1
            stats[f"upgrade_{side}_{region}"] += 1
        elif len(parts) >= 4 and parts[0] == "DAMAGE":
            cause, wid, damage = parts[1], parts[2], int(parts[3])
            side = side_of_warrior(wid)
            stats[f"damage_events_{side}"] += 1
            stats[f"damage_{side}"] += damage
            stats[f"damage_{cause}_{side}"] += damage
        elif len(parts) >= 4 and parts[0] == "SIEGE":
            side, region, damage = parts[1], parts[2], int(parts[3])
            stats[f"siege_{side}"] += damage
            stats[f"siege_{side}_{region}"] += damage

    if my_side is not None:
        opp_side = "B" if my_side == "A" else "A"
        left_hq = "0"
        right_hq = str(n_regions - 1) if n_regions is not None else ""
        my_hq = left_hq if my_side == "A" else right_hq
        opp_hq = left_hq if opp_side == "A" else right_hq
        return {
            "log": str(path),
            "result": result,
            "turn": max_turn,
            "my_train": stats[f"train_{my_side}"],
            "opp_train": stats[f"train_{opp_side}"],
            "my_upgrades": stats[f"upgrade_{my_side}"],
            "opp_upgrades": stats[f"upgrade_{opp_side}"],
            "my_damage_taken": stats[f"damage_{my_side}"],
            "opp_damage_taken": stats[f"damage_{opp_side}"],
            "my_hq_siege_taken": stats[f"siege_{my_side}_{my_hq}"],
            "opp_hq_siege_taken": stats[f"siege_{opp_side}_{opp_hq}"],
            "my_siege_taken": stats[f"siege_{my_side}"],
            "opp_siege_taken": stats[f"siege_{opp_side}"],
        }

    row: dict[str, int | str] = {"log": str(path), "result": result, "turn": max_turn}
    for key in sorted(stats):
        row[key] = stats[key]
    return row


def parse_from_results(csv_path: Path, mode: str) -> list[dict[str, int | str]]:
    rows = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            if mode != "all" and row["bot_result"].lower() != mode:
                continue
            log = Path(row["log"])
            if not log.exists():
                continue
            stats = parse_log(log, result_side(row))
            stats["seed"] = row["seed"]
            stats["bot_side"] = row["bot_side"]
            stats["bot_result"] = row["bot_result"]
            stats["reason"] = row["reason"]
            rows.append(stats)
    return rows


def write_csv(rows: list[dict[str, int | str]], output: Path | None) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    if output is None:
        writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fields)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        f = output.open("w", newline="")
        writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    if output is not None:
        f.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize NYPC log combat/economy events.")
    parser.add_argument("path", type=Path, help="A log file or results.csv")
    parser.add_argument("--mode", choices=["all", "win", "loss", "draw"], default="all")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.path.suffix == ".csv":
        rows = parse_from_results(args.path, args.mode)
    else:
        rows = [parse_log(args.path, None)]
    write_csv(rows, args.output)


if __name__ == "__main__":
    main()
