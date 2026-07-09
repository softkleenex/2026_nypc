#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from analyze_move_intent import MoveRecord, apply_turn_and_collect, read_map
from analyze_server_logs import calculate_hops
from intent_policy_data import feature_key as intent_feature_key
from movement_target_policy_data import feature_key as target_feature_key


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Seq:
    file: str
    wid: str
    start_turn: int
    end_turn: int
    near3_turn: int
    near1_turn: int
    arrival_turn: int
    tight_turn: int
    combined_turn: int
    target_turn: int
    steps: int


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


def flip_region(n: int, side: str, region: int) -> int:
    return n - 1 - region if side == "B" else region


def hot_edges_for(data: dict, map_hash: str, my_side: str, n: int) -> set[tuple[int, int]]:
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        return set()
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
            src, dst = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if 0 <= src < n and 0 <= dst < n:
            out.add((src, dst))
    return out


def analyze_records(path: Path, data: dict) -> list[Seq]:
    map_hash, model = read_map(path)
    hop = calculate_hops(model.adj)
    records = [
        r for r in apply_turn_and_collect(path, map_hash, model, "auto")
        if r.my_side in {"A", "B"} and r.side != r.my_side
    ]
    policy = data.get("policy") if isinstance(data.get("policy"), dict) else {}
    target_policy = data.get("target_policy") if isinstance(data.get("target_policy"), dict) else {}
    seqs: list[Seq] = []
    active: dict[str, dict] = {}
    for record in records:
        home = 0 if record.my_side == "A" else model.n - 1
        hot_edges = hot_edges_for(data, map_hash, record.my_side, model.n)
        edge = (
            flip_region(model.n, record.my_side, record.src),
            flip_region(model.n, record.my_side, record.dst),
        )
        cands = frozenset(model.candidate_targets(record.src, record.dst))
        intent_key = intent_feature_key(model, hop, record)
        target_key = target_feature_key(model, hop, record)
        edge_hot = edge in hot_edges or (intent_key is not None and intent_key in policy)
        target_hot = (
            target_key in target_policy
            and isinstance(target_policy[target_key], list)
            and len(target_policy[target_key]) >= 2
            and target_policy[target_key][1] == "my_hq"
        )
        state = active.get(record.wid)
        if record.track_step == 1 or state is None or state["actual_target"] != record.actual_target:
            state = {
                "file": Path(record.file).name,
                "wid": record.wid,
                "actual_target": record.actual_target,
                "target_type": record.target_type,
                "start_turn": record.turn,
                "end_turn": record.turn,
                "near3_turn": 0,
                "near1_turn": 0,
                "arrival_turn": 0,
                "tight_turn": 0,
                "combined_turn": 0,
                "target_turn": 0,
                "hot_steps": 0,
                "steps": 0,
            }
            active[record.wid] = state
        state["end_turn"] = record.turn
        state["steps"] = max(state["steps"], record.track_step)
        if edge_hot:
            state["hot_steps"] += 1
        else:
            state["hot_steps"] = 0
        if record.track_step >= 2 and record.track_candidate_count <= 5 and record.track_contains_my_hq:
            state["tight_turn"] = state["tight_turn"] or record.turn
        if (
            record.track_step >= 2
            and state["hot_steps"] >= 2
            and record.track_candidate_count <= 12
            and record.track_contains_my_hq
        ):
            state["combined_turn"] = state["combined_turn"] or record.turn
        if target_hot:
            state["target_turn"] = state["target_turn"] or record.turn
        if hop[record.dst][home] <= 3:
            state["near3_turn"] = state["near3_turn"] or record.turn
        if hop[record.dst][home] <= 1:
            state["near1_turn"] = state["near1_turn"] or record.turn
        if record.dst == home:
            state["arrival_turn"] = state["arrival_turn"] or record.turn

    for state in active.values():
        if state["target_type"] != "my_hq":
            continue
        seqs.append(
            Seq(
                file=state["file"],
                wid=state["wid"],
                start_turn=state["start_turn"],
                end_turn=state["end_turn"],
                near3_turn=state["near3_turn"],
                near1_turn=state["near1_turn"],
                arrival_turn=state["arrival_turn"],
                tight_turn=state["tight_turn"],
                combined_turn=state["combined_turn"],
                target_turn=state["target_turn"],
                steps=state["steps"],
            )
        )
    return seqs


def summarize(seqs: list[Seq]) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for method in ("tight", "combined", "target"):
        counts: Counter[str] = Counter()
        leads: list[int] = []
        for seq in seqs:
            detect = getattr(seq, f"{method}_turn")
            if not detect:
                continue
            counts["detected"] += 1
            if seq.near1_turn:
                lead = seq.near1_turn - detect
                leads.append(lead)
                counts["lead_ge_1"] += int(lead >= 1)
                counts["lead_ge_2"] += int(lead >= 2)
                counts["lead_ge_3"] += int(lead >= 3)
        rows.append(
            {
                "method": method,
                "total_hq_sequences": len(seqs),
                "detected": counts["detected"],
                "lead_ge_1": counts["lead_ge_1"],
                "lead_ge_2": counts["lead_ge_2"],
                "lead_ge_3": counts["lead_ge_3"],
                "min_lead": min(leads) if leads else "",
                "median_lead": sorted(leads)[len(leads) // 2] if leads else "",
                "max_lead": max(leads) if leads else "",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure lead time of HQ-intent signals before enemies reach our HQ.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--data", type=Path, default=ROOT / "bots" / "172_data.bin")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.data.read_text())
    seqs: list[Seq] = []
    for path in collect_logs(args.paths):
        try:
            seqs.extend(analyze_records(path, data))
        except Exception as exc:  # noqa: BLE001 - batch mode should continue.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)

    rows = summarize(seqs)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
