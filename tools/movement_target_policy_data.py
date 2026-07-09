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
LABELS = ("my_hq", "my_building", "enemy_hq", "enemy_building", "stronghold", "field")


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


def default_roots() -> list[Path]:
    roots: list[Path] = []
    roots.extend(sorted((ROOT / "bots").glob("*_nypc_log")))
    roots.extend(sorted((ROOT / "bots").glob("*_user_log*")))
    archive = ROOT / "bots" / "archive" / "user_logs"
    if archive.exists():
        roots.append(archive)
    return roots


def bucket(value: int, cuts: tuple[int, ...]) -> int:
    for idx, cut in enumerate(cuts):
        if value <= cut:
            return idx
    return len(cuts)


def bounded_delta(value: int) -> int:
    return max(-4, min(4, value))


def bool_int(value: bool) -> int:
    return 1 if value else 0


def iter_enemy_records(paths: list[Path]):
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
            for record in apply_turn_and_collect(path, map_hash, model, "auto"):
                if record.my_side in {"A", "B"} and record.side != record.my_side:
                    yield model, hop, record
        except Exception as exc:  # noqa: BLE001 - keep large batches robust.
            print(f"warning: skipped {path}: {exc}", file=sys.stderr)


def feature_key(model, hop: list[list[int]], record) -> str | None:
    home = 0 if record.my_side == "A" else model.n - 1
    opp = model.n - 1 - home
    src_home = hop[record.src][home]
    dst_home = hop[record.dst][home]
    src_opp = hop[record.src][opp]
    dst_opp = hop[record.dst][opp]
    if max(src_home, dst_home, src_opp, dst_opp) >= 10**8:
        return None
    values = (
        bucket(record.candidate_count, (1, 3, 5, 8, 12, 20)),
        bucket(record.track_candidate_count, (1, 3, 5, 8, 12, 20)),
        min(4, record.track_step),
        bool_int(record.contains_my_hq),
        bool_int(record.contains_my_building),
        bool_int(record.contains_enemy_hq),
        bool_int(record.contains_enemy_building),
        bool_int(record.contains_stronghold),
        bool_int(record.track_contains_my_hq),
        bool_int(record.track_contains_my_building),
        bucket(dst_home, (1, 2, 3, 4, 6, 9)),
        bucket(dst_opp, (1, 2, 3, 4, 6, 9)),
        bounded_delta(dst_home - dst_opp),
        bounded_delta(src_home - dst_home),
        bounded_delta(src_opp - dst_opp),
        bucket(record.turn, (20, 40, 70, 110, 150)),
    )
    return ",".join(str(v) for v in values)


def build(paths: list[Path], min_count: int, min_precision: float, allowed_labels: set[str]) -> dict:
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    for model, hop, record in iter_enemy_records(paths):
        key = feature_key(model, hop, record)
        if key is not None and record.target_type in LABELS:
            stats[key][record.target_type] += 1

    policy = {}
    for key, counts in stats.items():
        total = sum(counts.values())
        if total < min_count:
            continue
        label, top_count = counts.most_common(1)[0]
        precision = top_count / total if total else 0.0
        if precision < min_precision:
            continue
        if label not in allowed_labels:
            continue
        policy[key] = [total, label, top_count, round(precision, 4)]
    return {
        "format": "nypc-move-target-policy-json",
        "version": 1,
        "min_count": min_count,
        "min_precision": min_precision,
        "policy_labels": sorted(allowed_labels),
        "labels": LABELS,
        "policy": policy,
    }


def load_data(path: Path) -> dict:
    data = json.loads(path.read_text())
    if (
        isinstance(data, dict)
        and data.get("format") == "nypc-158-intent-combined-json"
        and isinstance(data.get("target_policy"), dict)
    ):
        return {**data, "policy": data["target_policy"]}
    if not isinstance(data, dict) or data.get("format") != "nypc-move-target-policy-json":
        raise SystemExit(f"unsupported movement target data: {path}")
    policy = data.get("policy")
    if not isinstance(policy, dict):
        raise SystemExit(f"policy missing from {path}")
    return data


def evaluate(paths: list[Path], data: dict) -> Counter[str]:
    policy = data["policy"]
    counts: Counter[str] = Counter()
    for model, hop, record in iter_enemy_records(paths):
        key = feature_key(model, hop, record)
        actual = record.target_type
        counts["records"] += 1
        counts[f"actual_{actual}"] += 1
        if key is None or key not in policy:
            continue
        pred = policy[key][1]
        counts["predicted"] += 1
        counts[f"pred_{pred}"] += 1
        counts[f"actual_{actual}_covered"] += 1
        if pred == actual:
            counts["correct"] += 1
            counts[f"pred_{pred}_correct"] += 1
        if pred != "field":
            counts["actionable"] += 1
            if pred == actual:
                counts["actionable_correct"] += 1
    return counts


def pct(part: int, total: int) -> str:
    return "0.0" if total == 0 else f"{part * 100.0 / total:.1f}"


def print_eval(counts: Counter[str]) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["metric", "value"])
    writer.writerow(["records", counts["records"]])
    writer.writerow(["predicted", f"{counts['predicted']} ({pct(counts['predicted'], counts['records'])}%)"])
    writer.writerow(["correct", f"{counts['correct']} ({pct(counts['correct'], counts['predicted'])}%)"])
    writer.writerow(["actionable", f"{counts['actionable']} ({pct(counts['actionable'], counts['predicted'])}%)"])
    writer.writerow([
        "actionable_correct",
        f"{counts['actionable_correct']} ({pct(counts['actionable_correct'], counts['actionable'])}%)",
    ])
    for label in LABELS:
        actual = counts[f"actual_{label}"]
        pred = counts[f"pred_{label}"]
        writer.writerow([f"actual_{label}", actual])
        writer.writerow([f"actual_{label}_covered", f"{counts[f'actual_{label}_covered']} ({pct(counts[f'actual_{label}_covered'], actual)}%)"])
        writer.writerow([f"pred_{label}", pred])
        writer.writerow([f"pred_{label}_correct", f"{counts[f'pred_{label}_correct']} ({pct(counts[f'pred_{label}_correct'], pred)}%)"])


def parse_allowed_labels(args: argparse.Namespace) -> set[str]:
    if args.labels:
        allowed_labels = set(args.labels.split(","))
    else:
        allowed_labels = set(LABELS if getattr(args, "include_field", False) else LABELS[:-1])
    bad = allowed_labels - set(LABELS)
    if bad:
        raise SystemExit(f"unknown labels: {', '.join(sorted(bad))}")
    return allowed_labels


def cmd_build(args: argparse.Namespace) -> None:
    roots = args.paths or default_roots()
    data = build(roots, args.min_count, args.min_precision, parse_allowed_labels(args))
    raw = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_DATA_BIN:
        raise SystemExit(f"data.bin too large: {len(raw)} > {MAX_DATA_BIN}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(f"wrote {args.output} ({len(raw)} bytes, keys={len(data['policy'])})")


def cmd_eval(args: argparse.Namespace) -> None:
    data = load_data(args.data)
    print_eval(evaluate(args.paths, data))


def cmd_crossval(args: argparse.Namespace) -> None:
    folders = [
        path for path in sorted(args.root.glob("eval*_bot*"))
        if (path / "matches").is_dir()
    ]
    if len(folders) < 2:
        raise SystemExit(f"need at least two eval folders under {args.root}")
    rows = []
    allowed_labels = parse_allowed_labels(args)
    for heldout in folders:
        train = [folder / "matches" for folder in folders if folder != heldout]
        data = build(train, args.min_count, args.min_precision, allowed_labels)
        counts = evaluate([heldout / "matches"], data)
        predicted = counts["predicted"]
        actionable = counts["actionable"]
        row = {
            "heldout": heldout.name,
            "keys": len(data["policy"]),
            "records": counts["records"],
            "predicted": predicted,
            "coverage_pct": pct(predicted, counts["records"]),
            "correct": counts["correct"],
            "precision_pct": pct(counts["correct"], predicted),
            "actionable": actionable,
            "actionable_precision_pct": pct(counts["actionable_correct"], actionable),
        }
        for label in LABELS:
            pred = counts[f"pred_{label}"]
            row[f"pred_{label}"] = pred
            row[f"pred_{label}_precision_pct"] = pct(counts[f"pred_{label}_correct"], pred)
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
            f"{row['heldout']}: predicted={row['predicted']}/{row['records']} "
            f"precision={row['precision_pct']} keys={row['keys']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/evaluate generic movement target-type policy data.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_p = sub.add_parser("build")
    build_p.add_argument("paths", nargs="*", type=Path)
    build_p.add_argument("--output", type=Path, default=ROOT / "results" / "movement-target-policy-data.bin")
    build_p.add_argument("--min-count", type=int, default=30)
    build_p.add_argument("--min-precision", type=float, default=0.9)
    build_p.add_argument("--include-field", action="store_true")
    build_p.add_argument("--labels", help="Comma-separated predicted labels to keep, e.g. my_hq,my_building.")
    build_p.set_defaults(func=cmd_build)

    eval_p = sub.add_parser("eval")
    eval_p.add_argument("paths", nargs="+", type=Path)
    eval_p.add_argument("--data", type=Path, required=True)
    eval_p.set_defaults(func=cmd_eval)

    cross_p = sub.add_parser("crossval")
    cross_p.add_argument("--root", type=Path, default=ROOT / "bots" / "archive" / "user_logs")
    cross_p.add_argument("--output", type=Path, default=ROOT / "results" / "movement-target-policy-crossval.tsv")
    cross_p.add_argument("--min-count", type=int, default=20)
    cross_p.add_argument("--min-precision", type=float, default=0.9)
    cross_p.add_argument("--include-field", action="store_true")
    cross_p.add_argument("--labels", help="Comma-separated predicted labels to keep, e.g. my_hq,enemy_hq.")
    cross_p.set_defaults(func=cmd_crossval)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
