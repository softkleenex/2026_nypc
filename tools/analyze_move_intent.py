#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import math
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from analyze_server_logs import (
    BASE_HP,
    HQ_TRAIN_HP,
    Warrior,
    apply_upgrade,
    hq_level,
    parse_log,
)


INF = 10**18


@dataclass
class MapModel:
    n: int
    xs: list[int]
    ys: list[int]
    strongholds: set[int]
    adj: list[list[int]]
    dist_to_target: list[list[int]] = field(init=False)
    candidate_cache: dict[tuple[int, int], tuple[int, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.dist_to_target = [self._dijkstra(target) for target in range(self.n)]

    def edge_cost(self, u: int, v: int) -> int:
        return math.ceil(math.hypot(self.xs[u] - self.xs[v], self.ys[u] - self.ys[v]))

    def _dijkstra(self, target: int) -> list[int]:
        dist = [INF] * self.n
        dist[target] = 0
        pq = [(0, target)]
        while pq:
            cur, u = heapq.heappop(pq)
            if cur != dist[u]:
                continue
            for v in self.adj[u]:
                nd = cur + self.edge_cost(u, v)
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist

    def next_step(self, src: int, target: int) -> int | None:
        if src == target:
            return None
        dist = self.dist_to_target[target]
        best: tuple[int, int] | None = None
        for nb in self.adj[src]:
            total = self.edge_cost(src, nb) + dist[nb]
            key = (total, nb)
            if best is None or key < best:
                best = key
        return None if best is None else best[1]

    def candidate_targets(self, src: int, observed_next: int) -> tuple[int, ...]:
        key = (src, observed_next)
        cached = self.candidate_cache.get(key)
        if cached is not None:
            return cached
        candidates = tuple(
            target
            for target in range(self.n)
            if target != src and self.next_step(src, target) == observed_next
        )
        self.candidate_cache[key] = candidates
        return candidates


@dataclass
class MoveRecord:
    file: str
    map_hash: str
    turn: int
    my_side: str
    wid: str
    side: str
    src: int
    dst: int
    actual_target: int
    candidate_count: int
    contains_actual: bool
    target_type: str
    contains_my_hq: bool
    contains_my_building: bool
    contains_enemy_hq: bool
    contains_enemy_building: bool
    contains_stronghold: bool
    track_step: int
    track_candidate_count: int
    track_contains_actual: bool
    track_contains_my_hq: bool
    track_contains_my_building: bool
    first_candidates: str


def read_map(path: Path) -> tuple[str, MapModel]:
    lines = path.read_text(errors="replace").splitlines()
    start = lines.index("MAP") + 1
    n, _k = map(int, lines[start].split()[:2])
    xs = [int(v) for v in lines[start + 1].split()]
    ys = [int(v) for v in lines[start + 2].split()]
    strong_parts = lines[start + 3].split()
    if strong_parts and strong_parts[0] == "STRONGHOLDS":
        strongholds = {int(v) for v in strong_parts[1:]}
    else:
        strongholds = {int(v) for v in strong_parts}

    adj: list[list[int]] = []
    idx = start + 4
    for _ in range(n):
        parts = [int(v) for v in lines[idx].split()]
        adj.append(parts[1:])
        idx += 1
    end = lines.index("END MAP", start)
    blob = "\n".join(lines[start:end]).encode()
    map_hash = hashlib.sha1(blob).hexdigest()[:12]
    return map_hash, MapModel(n=n, xs=xs, ys=ys, strongholds=strongholds, adj=adj)


def side_from_file(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_A"):
        return "A"
    if stem.endswith("_B"):
        return "B"
    return ""


def classify_target(game, model: MapModel, my_side: str, target: int) -> str:
    enemy = "B" if my_side == "A" else "A"
    if target == game.hq_region(my_side):
        return "my_hq"
    if target == game.hq_region(enemy):
        return "enemy_hq"
    building = game.buildings.get(target)
    if building is not None:
        if building.side == my_side:
            return "my_building"
        if building.side == enemy:
            return "enemy_building"
    if target in model.strongholds:
        return "stronghold"
    return "field"


def contains_owned_building(game, candidates: tuple[int, ...], side: str) -> bool:
    return any(
        (building := game.buildings.get(target)) is not None and building.side == side
        for target in candidates
    )


def update_active_targets(
    game,
    turn: int,
    active_targets: dict[str, int],
    candidate_trace: dict[str, tuple[int, frozenset[int], int]],
) -> None:
    for commands in game.commands[turn].values():
        for command in commands:
            parts = command.split()
            if len(parts) == 3 and parts[0] == "MOVE":
                wid = parts[1]
                if wid in game.warriors:
                    target = int(parts[2])
                    if active_targets.get(wid) != target:
                        candidate_trace.pop(wid, None)
                    active_targets[wid] = target


def apply_turn_and_collect(
    path: Path,
    map_hash: str,
    model: MapModel,
    perspective: str,
) -> list[MoveRecord]:
    game = parse_log(path)
    my_side = side_from_file(path) if perspective == "auto" else perspective
    active_targets: dict[str, int] = {}
    candidate_trace: dict[str, tuple[int, frozenset[int], int]] = {}
    records: list[MoveRecord] = []

    for turn in sorted(game.commands):
        update_active_targets(game, turn, active_targets, candidate_trace)
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
                actual_target = active_targets.get(wid)
                if actual_target is not None and src != dst:
                    candidates = model.candidate_targets(src, dst)
                    candidate_set = frozenset(candidates)
                    prev_trace = candidate_trace.get(wid)
                    if prev_trace is not None and prev_trace[0] == actual_target:
                        track_set = prev_trace[1] & candidate_set
                        track_step = prev_trace[2] + 1
                    else:
                        track_set = candidate_set
                        track_step = 1
                    candidate_trace[wid] = (actual_target, track_set, track_step)
                    target_type = classify_target(game, model, my_side, actual_target) if my_side else ""
                    enemy = "B" if my_side == "A" else "A"
                    records.append(
                        MoveRecord(
                            file=str(path),
                            map_hash=map_hash,
                            turn=turn,
                            my_side=my_side,
                            wid=wid,
                            side=wid[0],
                            src=src,
                            dst=dst,
                            actual_target=actual_target,
                            candidate_count=len(candidates),
                            contains_actual=actual_target in candidates,
                            target_type=target_type,
                            contains_my_hq=bool(my_side) and game.hq_region(my_side) in candidates,
                            contains_my_building=bool(my_side) and contains_owned_building(game, candidates, my_side),
                            contains_enemy_hq=bool(my_side) and game.hq_region(enemy) in candidates,
                            contains_enemy_building=bool(my_side) and contains_owned_building(game, candidates, enemy),
                            contains_stronghold=any(target in model.strongholds for target in candidates),
                            track_step=track_step,
                            track_candidate_count=len(track_set),
                            track_contains_actual=actual_target in track_set,
                            track_contains_my_hq=bool(my_side) and game.hq_region(my_side) in track_set,
                            track_contains_my_building=bool(my_side) and contains_owned_building(game, tuple(track_set), my_side),
                            first_candidates=",".join(str(target) for target in candidates[:12]),
                        )
                    )
                warrior.region = dst
                if active_targets.get(wid) == dst:
                    del active_targets[wid]
                    candidate_trace.pop(wid, None)
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

        dead = [wid for wid, warrior in game.warriors.items() if warrior.hp <= 0]
        for wid in dead:
            del game.warriors[wid]
            active_targets.pop(wid, None)
            candidate_trace.pop(wid, None)
        destroyed = [region for region, building in game.buildings.items() if building.hp <= 0]
        for region in destroyed:
            del game.buildings[region]

    return records


def collect(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_dir():
            out.extend(sorted(path.rglob("*.txt")))
        else:
            out.append(path)
    return out


def bucket_size(size: int) -> str:
    if size <= 1:
        return "size_1"
    if size <= 3:
        return "size_2_3"
    if size <= 5:
        return "size_4_5"
    if size <= 10:
        return "size_6_10"
    if size <= 20:
        return "size_11_20"
    return "size_21_plus"


def pct(part: int, total: int) -> str:
    return "0.0" if total == 0 else f"{part * 100.0 / total:.1f}"


def summarize(records: list[MoveRecord]) -> list[tuple[str, str]]:
    counts: Counter[str] = Counter()
    sizes: list[int] = []
    for record in records:
        counts["known_moves"] += 1
        counts[bucket_size(record.candidate_count)] += 1
        counts["contains_actual"] += int(record.contains_actual)
        counts["track_contains_actual"] += int(record.track_contains_actual)
        sizes.append(record.candidate_count)
        if record.my_side and record.side != record.my_side:
            counts["enemy_moves"] += 1
            counts[f"enemy_actual_{record.target_type}"] += 1
            counts["enemy_contains_my_hq"] += int(record.contains_my_hq)
            counts["enemy_contains_my_building"] += int(record.contains_my_building)
            for step_limit in (2, 3):
                if record.track_step >= step_limit:
                    counts[f"enemy_track{step_limit}_moves"] += 1
                    counts[f"enemy_track{step_limit}_contains_my_hq"] += int(record.track_contains_my_hq)
                    counts[f"enemy_track{step_limit}_contains_my_building"] += int(record.track_contains_my_building)
                    if record.track_contains_my_hq:
                        counts[f"track{step_limit}_my_hq_candidate_actual_{record.target_type}"] += 1
                    if record.track_contains_my_hq and record.track_candidate_count <= 5:
                        counts[f"track{step_limit}_my_hq_tight"] += 1
                        counts[f"track{step_limit}_my_hq_tight_actual_{record.target_type}"] += 1
            if record.contains_my_hq:
                counts[f"my_hq_candidate_actual_{record.target_type}"] += 1
            if record.contains_my_building:
                counts[f"my_building_candidate_actual_{record.target_type}"] += 1

    total = counts["known_moves"]
    enemy = counts["enemy_moves"]
    rows = [
        ("known_moves", str(total)),
        ("target_in_candidates", f"{counts['contains_actual']} ({pct(counts['contains_actual'], total)}%)"),
        ("track_target_in_candidates", f"{counts['track_contains_actual']} ({pct(counts['track_contains_actual'], total)}%)"),
        ("avg_candidate_count", f"{statistics.mean(sizes):.2f}" if sizes else "0.00"),
        ("median_candidate_count", f"{statistics.median(sizes):.1f}" if sizes else "0.0"),
        ("max_candidate_count", str(max(sizes) if sizes else 0)),
    ]
    for key in ("size_1", "size_2_3", "size_4_5", "size_6_10", "size_11_20", "size_21_plus"):
        rows.append((key, f"{counts[key]} ({pct(counts[key], total)}%)"))
    rows.extend(
        [
            ("enemy_moves_with_perspective", str(enemy)),
            ("enemy_step_compatible_with_my_hq", f"{counts['enemy_contains_my_hq']} ({pct(counts['enemy_contains_my_hq'], enemy)}%)"),
            (
                "enemy_step_compatible_with_my_building",
                f"{counts['enemy_contains_my_building']} ({pct(counts['enemy_contains_my_building'], enemy)}%)",
            ),
        ]
    )
    for key in (
        "enemy_actual_my_hq",
        "enemy_actual_my_building",
        "enemy_actual_enemy_hq",
        "enemy_actual_enemy_building",
        "enemy_actual_stronghold",
        "enemy_actual_field",
    ):
        rows.append((key, f"{counts[key]} ({pct(counts[key], enemy)}%)"))
    hq_candidate = counts["enemy_contains_my_hq"]
    for key in (
        "my_hq_candidate_actual_my_hq",
        "my_hq_candidate_actual_my_building",
        "my_hq_candidate_actual_enemy_hq",
        "my_hq_candidate_actual_enemy_building",
        "my_hq_candidate_actual_stronghold",
        "my_hq_candidate_actual_field",
    ):
        rows.append((key, f"{counts[key]} ({pct(counts[key], hq_candidate)}%)"))
    for step_limit in (2, 3):
        track_total = counts[f"enemy_track{step_limit}_moves"]
        track_hq = counts[f"enemy_track{step_limit}_contains_my_hq"]
        track_tight = counts[f"track{step_limit}_my_hq_tight"]
        rows.extend(
            [
                (f"enemy_track{step_limit}_moves", str(track_total)),
                (
                    f"track{step_limit}_compatible_with_my_hq",
                    f"{track_hq} ({pct(track_hq, track_total)}%)",
                ),
                (
                    f"track{step_limit}_hq_actual_my_hq",
                    f"{counts[f'track{step_limit}_my_hq_candidate_actual_my_hq']} ({pct(counts[f'track{step_limit}_my_hq_candidate_actual_my_hq'], track_hq)}%)",
                ),
                (
                    f"track{step_limit}_hq_tight_count_le5",
                    f"{track_tight} ({pct(track_tight, track_hq)}%)",
                ),
                (
                    f"track{step_limit}_hq_tight_actual_my_hq",
                    f"{counts[f'track{step_limit}_my_hq_tight_actual_my_hq']} ({pct(counts[f'track{step_limit}_my_hq_tight_actual_my_hq'], track_tight)}%)",
                ),
            ]
        )
    return rows


def write_details(path: Path, records: list[MoveRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [field.name for field in MoveRecord.__dataclass_fields__.values()]
    with path.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure how well observed one-step movement predicts true MOVE targets in NYPC logs."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--perspective", choices=["auto", "A", "B", ""], default="auto")
    parser.add_argument("--out", type=Path, help="Optional TSV of per-move records.")
    args = parser.parse_args()

    map_cache: dict[str, MapModel] = {}
    records: list[MoveRecord] = []
    for path in collect(args.paths):
        try:
            map_hash, model = read_map(path)
            if map_hash not in map_cache:
                map_cache[map_hash] = model
            records.extend(apply_turn_and_collect(path, map_hash, map_cache[map_hash], args.perspective))
        except Exception as exc:  # noqa: BLE001 - keep batch analysis moving over imperfect logs.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)

    if args.out is not None:
        write_details(args.out, records)

    writer = csv.writer(sys.stdout)
    writer.writerow(["metric", "value"])
    writer.writerows(summarize(records))


if __name__ == "__main__":
    main()
