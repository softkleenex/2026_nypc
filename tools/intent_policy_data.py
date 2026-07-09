#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from analyze_move_intent import apply_turn_and_collect, read_map
from analyze_server_logs import calculate_hops


ROOT = Path(__file__).resolve().parents[1]
MAX_DATA_BIN = 10 * 1024 * 1024


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


def bucket(value: int, cuts: tuple[int, ...]) -> int:
    for idx, cut in enumerate(cuts):
        if value <= cut:
            return idx
    return len(cuts)


def cand_bucket(value: int) -> int:
    return bucket(value, (1, 3, 5, 8, 12, 20))


def turn_bucket(turn: int) -> int:
    return bucket(turn, (20, 40, 70, 110, 150))


def rel_bucket(value: int) -> int:
    return max(-4, min(4, value))


def feature_key(model, hop: list[list[int]], record) -> str | None:
    if record.my_side not in {"A", "B"} or record.side == record.my_side:
        return None
    home = 0 if record.my_side == "A" else model.n - 1
    opp = model.n - 1 - home
    if home not in model.candidate_targets(record.src, record.dst):
        return None
    src_home = hop[record.src][home]
    dst_home = hop[record.dst][home]
    dst_opp = hop[record.dst][opp]
    if src_home >= 10**8 or dst_home >= 10**8 or dst_opp >= 10**8:
        return None
    advance = src_home - dst_home
    if advance < 0:
        return None
    return ",".join(
        str(v)
        for v in (
            cand_bucket(len(model.candidate_targets(record.src, record.dst))),
            bucket(dst_home, (1, 2, 3, 4, 6, 9)),
            rel_bucket(dst_home - dst_opp),
            min(3, advance),
            turn_bucket(record.turn),
        )
    )


def iter_record_groups(paths: list[Path]):
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
            yield model, hop, apply_turn_and_collect(path, map_hash, model, "auto")
        except Exception as exc:  # noqa: BLE001 - skip imperfect logs in batch mode.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)


def iter_records(paths: list[Path]):
    for model, hop, records in iter_record_groups(paths):
        yield from ((model, hop, r) for r in records)


def build(paths: list[Path], min_count: int, min_precision: float) -> dict:
    stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for model, hop, record in iter_records(paths):
        key = feature_key(model, hop, record)
        if key is None:
            continue
        row = stats[key]
        row[0] += 1
        row[1] += int(record.target_type == "my_hq")
    policy = {}
    for key, (total, hq) in stats.items():
        precision = hq / total if total else 0.0
        if total >= min_count and precision >= min_precision:
            policy[key] = [total, hq, round(precision, 4)]
    return {
        "format": "nypc-158-intent-policy-json",
        "version": 1,
        "min_count": min_count,
        "min_precision": min_precision,
        "policy": policy,
    }


def evaluate(paths: list[Path], data: dict) -> Counter[str]:
    policy = data.get("policy") if isinstance(data, dict) else None
    if not isinstance(policy, dict):
        raise SystemExit("policy missing from data")
    counts: Counter[str] = Counter()
    for model, hop, records in iter_record_groups(paths):
        live_trace: dict[str, tuple[frozenset[int], int, int, int]] = {}
        for record in records:
            if record.my_side not in {"A", "B"} or record.side == record.my_side:
                continue
            counts["enemy_moves"] += 1
            key = feature_key(model, hop, record)
            hot = key in policy if key is not None else False
            counts["hot_moves"] += int(hot)
            counts["hot_actual_hq"] += int(hot and record.target_type == "my_hq")
            home = 0 if record.my_side == "A" else model.n - 1
            cands = frozenset(model.candidate_targets(record.src, record.dst))
            old = live_trace.get(record.wid)
            if old is not None and record.turn - old[2] <= 2:
                merged = old[0] & cands
                steps = old[1] + 1
                hot_steps = old[3] + 1 if hot else 0
                if not merged:
                    merged = cands
                    steps = 1
                    hot_steps = 1 if hot else 0
            else:
                merged = cands
                steps = 1
                hot_steps = 1 if hot else 0
            live_trace[record.wid] = (merged, steps, record.turn, hot_steps)
            route = steps >= 2 and hot_steps >= 2 and len(merged) <= 12 and home in merged
            counts["triggers"] += int(route)
            counts["trigger_actual_hq"] += int(route and record.target_type == "my_hq")
    return counts


def pct(part: int, total: int) -> str:
    return "0.0" if total == 0 else f"{part * 100.0 / total:.1f}"


def cmd_build(args: argparse.Namespace) -> None:
    payload = build(args.paths, args.min_count, args.min_precision)
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    if len(raw) > MAX_DATA_BIN:
        raise SystemExit(f"data.bin too large: {len(raw)} > {MAX_DATA_BIN}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(f"wrote {args.output} ({len(raw)} bytes, keys={len(payload['policy'])})")


def cmd_eval(args: argparse.Namespace) -> None:
    data = json.loads(args.data.read_text())
    counts = evaluate(args.paths, data)
    rows = [
        ("enemy_moves", counts["enemy_moves"]),
        ("hot_moves", f"{counts['hot_moves']} ({pct(counts['hot_moves'], counts['enemy_moves'])}%)"),
        ("hot_actual_hq", f"{counts['hot_actual_hq']} ({pct(counts['hot_actual_hq'], counts['hot_moves'])}%)"),
        ("triggers", str(counts["triggers"])),
        ("trigger_actual_hq", f"{counts['trigger_actual_hq']} ({pct(counts['trigger_actual_hq'], counts['triggers'])}%)"),
    ]
    writer = sys.stdout
    writer.write("metric,value\n")
    for key, value in rows:
        writer.write(f"{key},{value}\n")


def trace_rows(paths: list[Path], data: dict) -> list[dict[str, int | str]]:
    policy = data.get("policy") if isinstance(data, dict) else None
    if not isinstance(policy, dict):
        raise SystemExit("policy missing from data")
    rows: list[dict[str, int | str]] = []
    for model, hop, records in iter_record_groups(paths):
        live_trace: dict[str, tuple[frozenset[int], int, int, int]] = {}
        for record in records:
            if record.my_side not in {"A", "B"} or record.side == record.my_side:
                continue
            key = feature_key(model, hop, record)
            hot = key in policy if key is not None else False
            home = 0 if record.my_side == "A" else model.n - 1
            cands = frozenset(model.candidate_targets(record.src, record.dst))
            old = live_trace.get(record.wid)
            if old is not None and record.turn - old[2] <= 2:
                merged = old[0] & cands
                steps = old[1] + 1
                hot_steps = old[3] + 1 if hot else 0
                if not merged:
                    merged = cands
                    steps = 1
                    hot_steps = 1 if hot else 0
            else:
                merged = cands
                steps = 1
                hot_steps = 1 if hot else 0
            live_trace[record.wid] = (merged, steps, record.turn, hot_steps)
            route = steps >= 2 and hot_steps >= 2 and len(merged) <= 12 and home in merged
            if not route:
                continue
            rows.append(
                {
                    "file": Path(record.file).name,
                    "turn": record.turn,
                    "my_side": record.my_side,
                    "wid": record.wid,
                    "src": record.src,
                    "dst": record.dst,
                    "actual_target": record.actual_target,
                    "target_type": record.target_type,
                    "steps": steps,
                    "hot_steps": hot_steps,
                    "candidate_count": len(merged),
                    "correct_hq": int(record.target_type == "my_hq"),
                    "key": key or "",
                }
            )
    return rows


def cmd_trace(args: argparse.Namespace) -> None:
    data = json.loads(args.data.read_text())
    rows = trace_rows(args.paths, data)
    fields = [
        "file", "turn", "my_side", "wid", "src", "dst", "actual_target",
        "target_type", "steps", "hot_steps", "candidate_count", "correct_hq",
        "key",
    ]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {args.output} rows={len(rows)}")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def cmd_crossval(args: argparse.Namespace) -> None:
    folders = [
        path for path in sorted(args.root.glob("eval*_bot*"))
        if (path / "matches").is_dir()
    ]
    if len(folders) < 2:
        raise SystemExit(f"need at least two eval folders under {args.root}")
    rows = []
    for heldout in folders:
        train = [folder / "matches" for folder in folders if folder != heldout]
        data = build(train, args.min_count, args.min_precision)
        counts = evaluate([heldout / "matches"], data)
        row = {
            "heldout": heldout.name,
            "keys": len(data["policy"]),
            "enemy_moves": counts["enemy_moves"],
            "hot_moves": counts["hot_moves"],
            "hot_precision_pct": pct(counts["hot_actual_hq"], counts["hot_moves"]),
            "triggers": counts["triggers"],
            "trigger_precision_pct": pct(counts["trigger_actual_hq"], counts["triggers"]),
        }
        rows.append(row)
    fields = list(rows[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.output}")
    for row in rows:
        print(
            f"{row['heldout']}: hot={row['hot_moves']}/{row['enemy_moves']} "
            f"hot_precision={row['hot_precision_pct']} triggers={row['triggers']} "
            f"trigger_precision={row['trigger_precision_pct']} keys={row['keys']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/evaluate generic movement-intent policy data.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_p = sub.add_parser("build")
    build_p.add_argument("paths", nargs="+", type=Path)
    build_p.add_argument("--output", type=Path, default=ROOT / "bots" / "158_data.bin")
    build_p.add_argument("--min-count", type=int, default=20)
    build_p.add_argument("--min-precision", type=float, default=0.85)
    build_p.set_defaults(func=cmd_build)

    eval_p = sub.add_parser("eval")
    eval_p.add_argument("paths", nargs="+", type=Path)
    eval_p.add_argument("--data", type=Path, required=True)
    eval_p.set_defaults(func=cmd_eval)

    trace_p = sub.add_parser("trace")
    trace_p.add_argument("paths", nargs="+", type=Path)
    trace_p.add_argument("--data", type=Path, required=True)
    trace_p.add_argument("--output", type=Path)
    trace_p.set_defaults(func=cmd_trace)

    cross_p = sub.add_parser("crossval")
    cross_p.add_argument("--root", type=Path, default=ROOT / "bots" / "archive" / "user_logs")
    cross_p.add_argument("--output", type=Path, default=ROOT / "results" / "intent-policy-crossval.tsv")
    cross_p.add_argument("--min-count", type=int, default=20)
    cross_p.add_argument("--min-precision", type=float, default=0.85)
    cross_p.set_defaults(func=cmd_crossval)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
