#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from analyze_server_logs import (
    Game,
    alive_count,
    apply_events,
    base_count,
    calculate_hops,
    hq_level,
    parse_log,
    warriors_at,
)
from build_user_log_index import (
    parse_eval_folder,
    parse_manifest,
    parse_ranking,
    pct_to_outcome,
    result_to_outcome,
)
from extract_log_features import map_hash


ROOT = Path(__file__).resolve().parents[1]
INF = 10**9


def first_at_or_before(values: list[tuple[int, int]], turn_limit: int) -> int:
    last = 0
    for turn, value in values:
        if turn > turn_limit:
            break
        last = value
    return last


def first_turn(values: list[tuple[int, int]], threshold: int) -> int:
    return next((turn for turn, value in values if value >= threshold), 0)


def enemy_near(game: Game, hop: list[list[int]], my_side: str, max_hop: int) -> int:
    enemy = "B" if my_side == "A" else "A"
    home = game.hq_region(my_side)
    return sum(1 for w in game.warriors.values() if w.side == enemy and hop[w.region][home] <= max_hop)


def classify_style(row: dict[str, int | str]) -> str:
    near6 = int(row["enemy_first_near6"])
    alive8 = int(row["enemy_first_alive8"])
    base1 = int(row["enemy_first_base1"])
    base3 = int(row["enemy_first_base3"])
    base5 = int(row["enemy_first_base5"])
    hq2 = int(row["enemy_first_hq2"])
    if near6 and near6 <= 25 and (not base1 or base1 > 35):
        return "early_hq_rush"
    if near6 and near6 <= 60 and alive8 and alive8 <= 60:
        return "delayed_mass"
    if base5 and base5 <= 110:
        return "fast_macro"
    if base3 and base3 <= 60:
        return "early_expand"
    if hq2 and hq2 <= 70:
        return "hq_tech"
    return "balanced"


def analyze_one(path: Path, my_side: str) -> dict[str, int | str]:
    game = parse_log(path)
    hop = calculate_hops(game.adj)
    enemy = "B" if my_side == "A" else "A"
    my_hq = game.hq_region(my_side)
    enemy_hq = game.hq_region(enemy)

    my_bases: list[tuple[int, int]] = []
    enemy_bases: list[tuple[int, int]] = []
    my_alive: list[tuple[int, int]] = []
    enemy_alive: list[tuple[int, int]] = []
    enemy_near3: list[tuple[int, int]] = []
    enemy_near6: list[tuple[int, int]] = []
    my_hq_levels: list[tuple[int, int]] = []
    enemy_hq_levels: list[tuple[int, int]] = []

    my_hq_siege_turn = 0
    enemy_hq_siege_turn = 0

    for turn in sorted(game.commands):
        my_bases.append((turn, base_count(game, my_side)))
        enemy_bases.append((turn, base_count(game, enemy)))
        my_alive.append((turn, alive_count(game, my_side)))
        enemy_alive.append((turn, alive_count(game, enemy)))
        enemy_near3.append((turn, enemy_near(game, hop, my_side, 3)))
        enemy_near6.append((turn, enemy_near(game, hop, my_side, 6)))
        my_hq_levels.append((turn, hq_level(game, my_side)))
        enemy_hq_levels.append((turn, hq_level(game, enemy)))

        for event in game.result_events.get(turn, []):
            parts = event.split()
            if len(parts) >= 4 and parts[0] == "SIEGE":
                side = parts[1]
                region = int(parts[2])
                if side == my_side and region == my_hq and not my_hq_siege_turn:
                    my_hq_siege_turn = turn
                if side == enemy and region == enemy_hq and not enemy_hq_siege_turn:
                    enemy_hq_siege_turn = turn
        apply_events(game, turn)

    row: dict[str, int | str] = {
        "file": path.name,
        "log_path": str(path),
        "map_hash": map_hash(path),
        "our_side": "LEFT" if my_side == "A" else "RIGHT",
        "result": game.result,
        "turn": game.end_turn,
        "my_first_base1": first_turn(my_bases, 1),
        "my_first_base3": first_turn(my_bases, 3),
        "enemy_first_base1": first_turn(enemy_bases, 1),
        "enemy_first_base3": first_turn(enemy_bases, 3),
        "enemy_first_base5": first_turn(enemy_bases, 5),
        "my_first_alive8": first_turn(my_alive, 8),
        "enemy_first_alive8": first_turn(enemy_alive, 8),
        "enemy_first_alive12": first_turn(enemy_alive, 12),
        "enemy_first_near3": first_turn(enemy_near3, 1),
        "enemy_first_near6": first_turn(enemy_near6, 1),
        "my_first_hq2": first_turn(my_hq_levels, 2),
        "enemy_first_hq2": first_turn(enemy_hq_levels, 2),
        "enemy_alive_t20": first_at_or_before(enemy_alive, 20),
        "enemy_alive_t40": first_at_or_before(enemy_alive, 40),
        "enemy_alive_t60": first_at_or_before(enemy_alive, 60),
        "enemy_near6_t40": first_at_or_before(enemy_near6, 40),
        "enemy_near6_t60": first_at_or_before(enemy_near6, 60),
        "final_my_bases": base_count(game, my_side),
        "final_enemy_bases": base_count(game, enemy),
        "final_my_alive": alive_count(game, my_side),
        "final_enemy_alive": alive_count(game, enemy),
        "final_my_hq": hq_level(game, my_side),
        "final_enemy_hq": hq_level(game, enemy),
        "final_my_hq_workers": warriors_at(game, my_side, my_hq),
        "final_enemy_hq_workers": warriors_at(game, enemy, enemy_hq),
        "my_hq_siege_turn": my_hq_siege_turn,
        "enemy_hq_siege_turn": enemy_hq_siege_turn,
        "my_hq_siege_taken": game.stats[f"{my_side}_hq_siege_taken"],
        "enemy_hq_siege_taken": game.stats[f"{enemy}_hq_siege_taken"],
        "my_trains": game.stats[f"{my_side}_trains"],
        "enemy_trains": game.stats[f"{enemy}_trains"],
        "my_paid_moves": game.stats[f"{my_side}_paid_move_cmds"],
        "enemy_paid_moves": game.stats[f"{enemy}_paid_move_cmds"],
    }
    row["style"] = classify_style(row)
    return row


def load_rows(log_root: Path) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for folder in sorted(log_root.glob("eval*_bot*")):
        ranking = folder / "ranking.txt"
        manifest = folder / "manifest.tsv"
        if not ranking.exists() or not manifest.exists():
            continue
        eval_no_from_name, our_bot = parse_eval_folder(folder)
        meta, by_id, by_name = parse_ranking(ranking)
        eval_no = eval_no_from_name or meta["eval_no"]
        for item in parse_manifest(manifest):
            rel_file = item.get("file", "")
            if not rel_file:
                continue
            log_path = folder / rel_file
            if not log_path.exists():
                continue
            side = item["side"]
            feature = analyze_one(log_path, side)
            match_id = item["match_id"]
            team = item.get("team", "").strip()
            opp = by_id.get(match_id) or by_name.get(team) or {}
            opp_rating = opp.get("opponent_rating", "")
            site_pct = opp.get("site_pct", "")
            feature.update(
                {
                    "eval_no": eval_no,
                    "eval_folder": folder.name,
                    "our_bot": our_bot,
                    "our_rank": meta["our_rank"],
                    "our_rating": meta["our_rating"],
                    "match_id": match_id,
                    "opponent_team": opp.get("opponent_team", team),
                    "opponent_tier": opp.get("opponent_tier", ""),
                    "opponent_rating": opp_rating,
                    "rating_diff": (
                        meta["our_rating"] - int(opp_rating)
                        if opp_rating != ""
                        else ""
                    ),
                    "site_outcome": pct_to_outcome(float(site_pct)) if site_pct != "" else result_to_outcome(str(feature["result"]), side),
                    "archived_outcome": result_to_outcome(str(feature["result"]), side),
                }
            )
            rows.append(feature)
    return rows


def wld(rows: list[dict[str, int | str]]) -> str:
    counts = Counter(str(row["site_outcome"]) for row in rows)
    return f"{counts['W']}/{counts['L']}/{counts['D']}"


def write_tsv(rows: list[dict[str, int | str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    preferred = [
        "eval_no",
        "our_bot",
        "match_id",
        "opponent_team",
        "opponent_tier",
        "opponent_rating",
        "rating_diff",
        "site_outcome",
        "style",
        "our_side",
        "result",
        "turn",
        "map_hash",
        "log_path",
    ]
    for key in preferred:
        if any(key in row for row in rows):
            fields.append(key)
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict[str, int | str]]) -> None:
    print(f"rows={len(rows)} w/l/d={wld(rows)}")
    for field in ("eval_no", "our_bot", "our_side", "opponent_tier", "style"):
        groups: dict[str, list[dict[str, int | str]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(field, ""))].append(row)
        print(f"\n[{field}]")
        for key, group in sorted(groups.items(), key=lambda kv: (kv[0] == "", kv[0])):
            if not key:
                key = "-"
            print(f"{key}\t{len(group)}\t{wld(group)}")

    loss_rows = [row for row in rows if row["site_outcome"] == "L"]
    print("\n[losses]")
    for row in sorted(loss_rows, key=lambda r: (int(r["eval_no"]), str(r["match_id"]))):
        print(
            f"eval{row['eval_no']} {row['our_bot']} {row['match_id']} "
            f"{row['opponent_team']} T{row['opponent_tier']} "
            f"style={row['style']} side={row['our_side']} "
            f"near6={row['enemy_first_near6']} base3={row['enemy_first_base3']} "
            f"alive8={row['enemy_first_alive8']} hq2={row['enemy_first_hq2']} "
            f"result={row['result']} log={row['log_path']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Match archived user logs with opponent metadata and early style features.")
    parser.add_argument("--log-root", type=Path, default=ROOT / "bots" / "archive" / "user_logs")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "user-style-features.tsv")
    args = parser.parse_args()

    rows = load_rows(args.log_root)
    write_tsv(rows, args.output)
    print_summary(rows)
    print(f"\ntsv={args.output}")


if __name__ == "__main__":
    main()
