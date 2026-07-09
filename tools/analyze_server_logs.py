#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


START_GOLD = 500
START_WARRIORS = 3
MOVE_COST = 10
TRAIN_COST = 120
WORK_INCOME = 15
UPKEEP_PER_WARRIOR = 2
HQ_HEAL_COST = 1000
BASE_HEAL_COST = 500

HQ_HP = [0, 10, 15, 20, 25, 30]
HQ_WORK_CAP = [0, 1, 2, 3, 4, 5]
HQ_TRAIN_HP = [0, 4, 5, 6, 7, 8]
HQ_UPGRADE_COST = [0, 0, 600, 1200, 2400, 3600]
BASE_HP = [0, 6, 12, 18]
BASE_WORK_CAP = [0, 1, 2, 3]
BASE_UPGRADE_COST = [0, 300, 600, 1000]

ECONOMY_BOOM_TURN = 40
ECONOMY_BOOM_ENEMY_BASES = 5
ECONOMY_BOOM_BASE_GAP = 4
EARLY_ECONOMY_TURN = 25
EARLY_ECONOMY_ENEMY_BASES = 3
EARLY_ECONOMY_BASE_GAP = 2
EARLY_ECONOMY_HOME_HOP = 3


@dataclass
class Building:
    side: str
    kind: str
    level: int
    hp: int

    @property
    def work_cap(self) -> int:
        return HQ_WORK_CAP[self.level] if self.kind == "HQ" else BASE_WORK_CAP[self.level]

    @property
    def max_level(self) -> int:
        return 5 if self.kind == "HQ" else 3

    @property
    def max_hp(self) -> int:
        return HQ_HP[self.level] if self.kind == "HQ" else BASE_HP[self.level]

    @property
    def upgrade_cost(self) -> int:
        if self.kind == "HQ":
            return HQ_UPGRADE_COST[self.level + 1]
        return BASE_UPGRADE_COST[self.level + 1]


@dataclass
class Warrior:
    side: str
    region: int
    hp: int


@dataclass
class TurnSnapshot:
    turn: int
    left_gold: int
    right_gold: int
    left_alive: int
    right_alive: int
    left_bases: int
    right_bases: int
    left_hq_level: int
    right_hq_level: int
    left_at_hq: int
    right_at_hq: int
    enemy_at_left_hq: int
    early_economy: bool
    economy_boom: bool
    economy_alert: bool
    economy_boom_hq_ready: bool


@dataclass
class Game:
    path: Path
    n: int
    k: int
    strongholds: list[int]
    adj: list[list[int]]
    buildings: dict[int, Building] = field(default_factory=dict)
    warriors: dict[str, Warrior] = field(default_factory=dict)
    gold: dict[str, int] = field(default_factory=lambda: {"A": START_GOLD, "B": START_GOLD})
    commands: dict[int, dict[str, list[str]]] = field(default_factory=dict)
    result_events: dict[int, list[str]] = field(default_factory=dict)
    snapshots: list[TurnSnapshot] = field(default_factory=list)
    result: str = ""
    end_turn: int = 0
    stats: Counter[str] = field(default_factory=Counter)
    hq_upgrade_turns: dict[str, list[int]] = field(default_factory=lambda: {"A": [], "B": []})
    base_count_by_turn: dict[str, list[tuple[int, int]]] = field(default_factory=lambda: {"A": [], "B": []})

    @property
    def left_hq(self) -> int:
        return 0

    @property
    def right_hq(self) -> int:
        return self.n - 1

    def hq_region(self, side: str) -> int:
        return self.left_hq if side == "A" else self.right_hq


def parse_log(path: Path) -> Game:
    lines = path.read_text(errors="replace").splitlines()
    i = 0
    while i < len(lines) and lines[i] != "MAP":
        i += 1
    if i >= len(lines):
        raise ValueError(f"MAP block not found: {path}")
    i += 1
    n, k = map(int, lines[i].split()[:2])
    i += 1
    i += 1
    i += 1
    strong_parts = lines[i].split()
    strongholds = [int(v) for v in strong_parts[1:]] if strong_parts and strong_parts[0] == "STRONGHOLDS" else [int(v) for v in strong_parts]
    i += 1
    adj: list[list[int]] = []
    for _ in range(n):
        parts = [int(v) for v in lines[i].split()]
        adj.append(parts[1:])
        i += 1
    if lines[i] != "END MAP":
        raise ValueError(f"END MAP not found where expected: {path}")
    i += 1

    game = Game(path=path, n=n, k=k, strongholds=strongholds, adj=adj)
    game.buildings[game.left_hq] = Building("A", "HQ", 1, HQ_HP[1])
    game.buildings[game.right_hq] = Building("B", "HQ", 1, HQ_HP[1])
    for num in range(1, START_WARRIORS + 1):
        game.warriors[f"A{num}"] = Warrior("A", game.left_hq, HQ_TRAIN_HP[1])
        game.warriors[f"B{num}"] = Warrior("B", game.right_hq, HQ_TRAIN_HP[1])

    while i < len(lines):
        parts = lines[i].split()
        if len(parts) >= 3 and parts[0] == "RESULT":
            game.result = " ".join(parts[1:])
            break
        if len(parts) != 2 or parts[0] != "TURN":
            i += 1
            continue
        turn = int(parts[1])
        game.end_turn = max(game.end_turn, turn)
        i += 1

        turn_commands = {"LEFT": [], "RIGHT": []}
        for side_word in ("LEFT", "RIGHT"):
            if i >= len(lines) or lines[i] != f"COMMAND {side_word} START":
                raise ValueError(f"command block start mismatch at turn {turn}: {path}")
            i += 1
            while i < len(lines) and lines[i] != f"COMMAND {side_word} END":
                turn_commands[side_word].append(lines[i])
                i += 1
            i += 1
        game.commands[turn] = turn_commands

        if i < len(lines) and lines[i].startswith("RESULT "):
            game.result = " ".join(lines[i].split()[1:])
            game.commands.pop(turn, None)
            break

        if i >= len(lines) or lines[i] != f"TURN {turn} RESULT":
            raise ValueError(f"turn result mismatch at turn {turn}: {path}")
        i += 1
        if i < len(lines) and lines[i].startswith("TIME "):
            i += 1
        events: list[str] = []
        while i < len(lines) and lines[i] != f"END TURN {turn}":
            events.append(lines[i])
            i += 1
        game.result_events[turn] = events
        if i < len(lines) and lines[i] == f"END TURN {turn}":
            i += 1

    return game


def calculate_hops(adj: list[list[int]]) -> list[list[int]]:
    n = len(adj)
    inf = 10**9
    hop = [[inf] * n for _ in range(n)]
    for start in range(n):
        hop[start][start] = 0
        q = [start]
        for u in q:
            for v in adj[u]:
                if hop[start][v] == inf:
                    hop[start][v] = hop[start][u] + 1
                    q.append(v)
    return hop


def side_from_word(word: str) -> str:
    return "A" if word == "LEFT" else "B"


def word_from_side(side: str) -> str:
    return "LEFT" if side == "A" else "RIGHT"


def alive_count(game: Game, side: str) -> int:
    return sum(1 for w in game.warriors.values() if w.side == side)


def base_count(game: Game, side: str) -> int:
    return sum(1 for b in game.buildings.values() if b.side == side and b.kind == "BASE")


def hq_level(game: Game, side: str) -> int:
    b = game.buildings.get(game.hq_region(side))
    return b.level if b is not None and b.side == side and b.kind == "HQ" else 0


def warriors_at(game: Game, side: str, region: int) -> int:
    return sum(1 for w in game.warriors.values() if w.side == side and w.region == region)


def command_cost(game: Game, side: str, command: str) -> tuple[int, str]:
    parts = command.split()
    if not parts:
        return 0, "none"
    if parts[0] == "TRAIN":
        return TRAIN_COST * int(parts[1]), "train"
    if parts[0] == "MOVE":
        target = int(parts[2])
        b = game.buildings.get(target)
        return (0, "free_move") if b is not None and b.side == side else (MOVE_COST, "paid_move")
    if parts[0] == "UPGRADE":
        region = int(parts[1])
        b = game.buildings.get(region)
        if b is None:
            return BASE_UPGRADE_COST[1], "base_build"
        if b.side != side:
            return 0, "invalid_upgrade"
        if b.level < b.max_level:
            return b.upgrade_cost, "hq_upgrade" if b.kind == "HQ" else "base_upgrade"
        return (HQ_HEAL_COST if b.kind == "HQ" else BASE_HEAL_COST), "heal"
    return 0, "none"


def apply_upgrade(game: Game, side: str, region: int) -> None:
    b = game.buildings.get(region)
    if b is None:
        game.buildings[region] = Building(side, "BASE", 1, BASE_HP[1])
        return
    if b.side != side:
        return
    if b.level < b.max_level:
        b.level += 1
    b.hp = b.max_hp


def apply_events(game: Game, turn: int) -> None:
    for side_word, commands in game.commands[turn].items():
        side = side_from_word(side_word)
        for command in commands:
            cost, kind = command_cost(game, side, command)
            game.gold[side] -= cost
            game.stats[f"{side}_{kind}_cmds"] += 1
            game.stats[f"{side}_{kind}_cost"] += cost
            parts = command.split()
            if len(parts) >= 2 and parts[0] == "UPGRADE":
                region = int(parts[1])
                if region == game.hq_region(side):
                    game.stats[f"{side}_hq_upgrade_commands"] += 1
            elif len(parts) >= 2 and parts[0] == "TRAIN":
                game.stats[f"{side}_train_commands"] += int(parts[1])

    for event in game.result_events[turn]:
        parts = event.split()
        if not parts:
            continue
        if parts[0] == "UPGRADE":
            side = parts[1]
            region = int(parts[2])
            before = game.buildings.get(region)
            was_hq = before is not None and before.kind == "HQ"
            apply_upgrade(game, side, region)
            game.stats[f"{side}_upgrades"] += 1
            if region == game.hq_region(side) and was_hq:
                game.hq_upgrade_turns[side].append(turn)
        elif parts[0] == "TRAIN":
            for wid in parts[1:]:
                side = wid[0]
                level = hq_level(game, side) or 1
                game.warriors[wid] = Warrior(side, game.hq_region(side), HQ_TRAIN_HP[level])
                game.stats[f"{side}_trains"] += 1
        elif parts[0] == "MOVE":
            wid = parts[1]
            region = int(parts[2])
            if wid in game.warriors:
                game.warriors[wid].region = region
        elif parts[0] == "DAMAGE":
            wid = parts[2]
            damage = int(parts[3])
            if wid in game.warriors:
                game.warriors[wid].hp -= damage
                game.stats[f"{wid[0]}_damage_taken"] += damage
        elif parts[0] == "SIEGE":
            side = parts[1]
            region = int(parts[2])
            damage = int(parts[3])
            b = game.buildings.get(region)
            if b is not None:
                b.hp -= damage
                game.stats[f"{side}_siege_taken"] += damage
                if region == game.hq_region(side):
                    game.stats[f"{side}_hq_siege_taken"] += damage
                    if f"{side}_first_hq_siege_turn" not in game.stats:
                        game.stats[f"{side}_first_hq_siege_turn"] = turn

    dead = [wid for wid, w in game.warriors.items() if w.hp <= 0]
    for wid in dead:
        del game.warriors[wid]
    destroyed = [region for region, b in game.buildings.items() if b.hp <= 0]
    for region in destroyed:
        del game.buildings[region]

    for side in ("A", "B"):
        income = 0
        for region, b in game.buildings.items():
            if b.side != side:
                continue
            workers = warriors_at(game, side, region)
            income += WORK_INCOME * min(workers, b.work_cap)
        game.gold[side] += income
        game.gold[side] = max(0, game.gold[side] - UPKEEP_PER_WARRIOR * alive_count(game, side))


def take_snapshot(game: Game, turn: int, hop: list[list[int]]) -> None:
    left_bases = base_count(game, "A")
    right_bases = base_count(game, "B")
    right_regions = [r for r, b in game.buildings.items() if b.side == "B" and b.kind == "BASE"]
    enemy_home_hop = min(
        (
            hop[w.region][game.left_hq]
            for w in game.warriors.values()
            if w.side == "B" and w.region != game.right_hq
        ),
        default=10**9,
    )
    economy_boom = (
        turn >= ECONOMY_BOOM_TURN
        and len(right_regions) >= ECONOMY_BOOM_ENEMY_BASES
        and len(right_regions) >= left_bases + ECONOMY_BOOM_BASE_GAP
        and enemy_home_hop > 3
        and warriors_at(game, "B", game.left_hq) == 0
    )
    early_economy = (
        turn >= EARLY_ECONOMY_TURN
        and len(right_regions) >= EARLY_ECONOMY_ENEMY_BASES
        and len(right_regions) >= left_bases + EARLY_ECONOMY_BASE_GAP
        and enemy_home_hop > EARLY_ECONOMY_HOME_HOP
        and warriors_at(game, "B", game.left_hq) == 0
    )
    economy_alert = early_economy or economy_boom
    left_at_hq = warriors_at(game, "A", game.left_hq)
    left_level = hq_level(game, "A")
    game.snapshots.append(
        TurnSnapshot(
            turn=turn,
            left_gold=game.gold["A"],
            right_gold=game.gold["B"],
            left_alive=alive_count(game, "A"),
            right_alive=alive_count(game, "B"),
            left_bases=left_bases,
            right_bases=right_bases,
            left_hq_level=left_level,
            right_hq_level=hq_level(game, "B"),
            left_at_hq=left_at_hq,
            right_at_hq=warriors_at(game, "B", game.right_hq),
            enemy_at_left_hq=warriors_at(game, "B", game.left_hq),
            early_economy=early_economy,
            economy_boom=economy_boom,
            economy_alert=economy_alert,
            economy_boom_hq_ready=(
                economy_alert
                and left_level == 1
                and left_bases >= 1
                and alive_count(game, "A") >= 6
                and left_at_hq > 0
                and game.gold["A"] >= HQ_UPGRADE_COST[2]
            ),
        )
    )


def analyze(path: Path) -> dict[str, int | str]:
    game = parse_log(path)
    hop = calculate_hops(game.adj)
    for turn in sorted(game.commands):
        take_snapshot(game, turn, hop)
        apply_events(game, turn)
        game.base_count_by_turn["A"].append((turn, base_count(game, "A")))
        game.base_count_by_turn["B"].append((turn, base_count(game, "B")))

    row: dict[str, int | str] = {
        "file": path.name,
        "result": game.result,
        "turn": game.end_turn,
        "n": game.n,
        "left_trains": game.stats["A_trains"],
        "right_trains": game.stats["B_trains"],
        "left_paid_moves": game.stats["A_paid_move_cmds"],
        "right_paid_moves": game.stats["B_paid_move_cmds"],
        "left_paid_move_cost": game.stats["A_paid_move_cost"],
        "right_paid_move_cost": game.stats["B_paid_move_cost"],
        "left_train_cost": game.stats["A_train_cost"],
        "right_train_cost": game.stats["B_train_cost"],
        "left_hq_upgrade_cmds": game.stats["A_hq_upgrade_commands"],
        "left_hq_upgrades": len(game.hq_upgrade_turns["A"]),
        "right_hq_upgrades": len(game.hq_upgrade_turns["B"]),
        "left_final_hq": hq_level(game, "A"),
        "right_final_hq": hq_level(game, "B"),
        "left_max_bases": max((v for _, v in game.base_count_by_turn["A"]), default=0),
        "right_max_bases": max((v for _, v in game.base_count_by_turn["B"]), default=0),
        "left_final_alive": alive_count(game, "A"),
        "right_final_alive": alive_count(game, "B"),
        "left_max_alive": max((s.left_alive for s in game.snapshots), default=0),
        "right_max_alive": max((s.right_alive for s in game.snapshots), default=0),
        "left_hq_siege_taken": game.stats["A_hq_siege_taken"],
        "right_hq_siege_taken": game.stats["B_hq_siege_taken"],
        "left_first_hq_siege_turn": game.stats.get("A_first_hq_siege_turn", 0),
        "right_first_hq_siege_turn": game.stats.get("B_first_hq_siege_turn", 0),
        "first_right_5_bases_turn": next((t for t, c in game.base_count_by_turn["B"] if c >= 5), 0),
        "first_right_3_bases_turn": next((t for t, c in game.base_count_by_turn["B"] if c >= 3), 0),
        "first_right_4_bases_turn": next((t for t, c in game.base_count_by_turn["B"] if c >= 4), 0),
        "first_left_2_bases_turn": next((t for t, c in game.base_count_by_turn["A"] if c >= 2), 0),
        "first_left_3_bases_turn": next((t for t, c in game.base_count_by_turn["A"] if c >= 3), 0),
        "first_left_early_economy_turn": next((s.turn for s in game.snapshots if s.early_economy), 0),
        "first_left_economy_boom_turn": next((s.turn for s in game.snapshots if s.economy_boom), 0),
        "first_left_economy_alert_hq_ready_turn": next((s.turn for s in game.snapshots if s.economy_boom_hq_ready), 0),
        "left_min_hq_workers_after_alert": min((s.left_at_hq for s in game.snapshots if s.economy_alert), default=0),
        "left_max_gold_after_alert": max((s.left_gold for s in game.snapshots if s.economy_alert), default=0),
        "left_max_alive_after_alert": max((s.left_alive for s in game.snapshots if s.economy_alert), default=0),
    }
    for side, prefix in (("A", "left"), ("B", "right")):
        turns = game.hq_upgrade_turns[side]
        row[f"{prefix}_hq_upgrade_turns"] = ",".join(str(t) for t in turns)
    return row


def write_csv(rows: list[dict[str, int | str]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize NYPC server logs with economy/HQ timing.")
    parser.add_argument("paths", nargs="+", type=Path, help="Log files or directories containing .txt logs.")
    args = parser.parse_args()

    logs: list[Path] = []
    for path in args.paths:
        if path.is_dir():
            logs.extend(sorted(p for p in path.glob("*.txt") if p.is_file()))
        else:
            logs.append(path)
    write_csv([analyze(path) for path in logs])


if __name__ == "__main__":
    main()
