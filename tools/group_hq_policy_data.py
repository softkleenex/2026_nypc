#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from analyze_group_hq_intent import analyze, collect_logs


ROOT = Path(__file__).resolve().parents[1]
MAX_DATA_BIN = 10 * 1024 * 1024


def bucket(value: int, cuts: tuple[int, ...]) -> int:
    for idx, cut in enumerate(cuts):
        if value <= cut:
            return idx
    return len(cuts)


def clamp_delta(value: int) -> int:
    if value <= -5:
        return -3
    if value <= -2:
        return -2
    if value < 2:
        return 0
    if value < 5:
        return 2
    return 3


def int_field(row: dict[str, int | str], key: str) -> int:
    value = row.get(key, 0)
    if value == "":
        return 0
    return int(value)


def feature_key(row: dict[str, int | str]) -> str | None:
    trace = int_field(row, "trace_hq_support")
    target = int_field(row, "target_policy_hq_support")
    if trace <= 0 and target <= 0:
        return None
    vals = (
        bucket(trace, (0, 1, 2, 3, 6, 10)),
        bucket(target, (0, 1, 3, 6, 10)),
    )
    return ",".join(str(v) for v in vals)


def rows_for(paths: list[Path], target_data: Path | None) -> list[dict[str, int | str]]:
    return analyze(paths, target_data)


def build(paths: list[Path], target_data: Path | None, min_count: int, min_precision: float) -> dict:
    stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in rows_for(paths, target_data):
        key = feature_key(row)
        if key is None:
            continue
        stats[key][0] += 1
        stats[key][1] += int(int_field(row, "actual_hq_moves") > 0)
    policy = {}
    for key, (total, hq_turns) in stats.items():
        precision = hq_turns / total if total else 0.0
        if total >= min_count and precision >= min_precision:
            policy[key] = [total, hq_turns, round(precision, 4)]
    return {
        "format": "nypc-group-hq-policy-json",
        "version": 1,
        "min_count": min_count,
        "min_precision": min_precision,
        "policy": policy,
    }


def evaluate(paths: list[Path], target_data: Path | None, data: dict) -> Counter[str]:
    policy = data.get("policy") if isinstance(data, dict) else None
    if not isinstance(policy, dict):
        raise SystemExit("policy missing from data")
    counts: Counter[str] = Counter()
    for row in rows_for(paths, target_data):
        actual = int_field(row, "actual_hq_moves") > 0
        counts["turns"] += 1
        counts["actual_hq_turns"] += int(actual)
        key = feature_key(row)
        pred = key in policy if key is not None else False
        counts["pred_turns"] += int(pred)
        counts["correct_turns"] += int(pred and actual)
        counts["false_turns"] += int(pred and not actual)
        counts["target_policy_turns"] += int(int_field(row, "target_policy_hq_support") > 0)
        counts["trace3_turns"] += int(int_field(row, "trace_hq_support") >= 3)
    return counts


def pct(part: int, total: int) -> str:
    return "0.0" if total == 0 else f"{part * 100.0 / total:.1f}"


def load_data(path: Path) -> dict:
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get("format") != "nypc-group-hq-policy-json":
        raise SystemExit(f"unsupported group HQ policy data: {path}")
    return data


def write_payload(path: Path, payload: dict) -> None:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    if len(raw) > MAX_DATA_BIN:
        raise SystemExit(f"data.bin too large: {len(raw)} > {MAX_DATA_BIN}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    print(f"wrote {path} ({len(raw)} bytes, keys={len(payload['policy'])})")


def print_eval(counts: Counter[str]) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["metric", "value"])
    writer.writerow(["turns", counts["turns"]])
    writer.writerow(["actual_hq_turns", counts["actual_hq_turns"]])
    writer.writerow(["pred_turns", f"{counts['pred_turns']} ({pct(counts['pred_turns'], counts['turns'])}%)"])
    writer.writerow(["correct_turns", f"{counts['correct_turns']} ({pct(counts['correct_turns'], counts['pred_turns'])}%)"])
    writer.writerow(["recall", f"{counts['correct_turns']} ({pct(counts['correct_turns'], counts['actual_hq_turns'])}%)"])
    writer.writerow(["false_turns", counts["false_turns"]])
    writer.writerow(["target_policy_turns", counts["target_policy_turns"]])
    writer.writerow(["trace3_turns", counts["trace3_turns"]])


def cmd_build(args: argparse.Namespace) -> None:
    payload = build(args.paths, args.target_data, args.min_count, args.min_precision)
    write_payload(args.output, payload)


def cmd_eval(args: argparse.Namespace) -> None:
    print_eval(evaluate(args.paths, args.target_data, load_data(args.data)))


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
        payload = build(train, args.target_data, args.min_count, args.min_precision)
        counts = evaluate([heldout / "matches"], args.target_data, payload)
        row = {
            "heldout": heldout.name,
            "keys": len(payload["policy"]),
            "turns": counts["turns"],
            "actual_hq_turns": counts["actual_hq_turns"],
            "pred_turns": counts["pred_turns"],
            "coverage_pct": pct(counts["pred_turns"], counts["turns"]),
            "correct_turns": counts["correct_turns"],
            "precision_pct": pct(counts["correct_turns"], counts["pred_turns"]),
            "recall_pct": pct(counts["correct_turns"], counts["actual_hq_turns"]),
            "false_turns": counts["false_turns"],
        }
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.output}")
    for row in rows:
        print(
            f"{row['heldout']}: pred={row['pred_turns']} "
            f"precision={row['precision_pct']} recall={row['recall_pct']} keys={row['keys']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/evaluate grouped HQ movement policy data.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_p = sub.add_parser("build")
    build_p.add_argument("paths", nargs="*", type=Path)
    build_p.add_argument("--target-data", type=Path, default=ROOT / "bots" / "180_data.bin")
    build_p.add_argument("--output", type=Path, default=ROOT / "results" / "group-hq-policy-data.bin")
    build_p.add_argument("--min-count", type=int, default=12)
    build_p.add_argument("--min-precision", type=float, default=0.95)
    build_p.set_defaults(func=cmd_build)

    eval_p = sub.add_parser("eval")
    eval_p.add_argument("paths", nargs="+", type=Path)
    eval_p.add_argument("--target-data", type=Path, default=ROOT / "bots" / "180_data.bin")
    eval_p.add_argument("--data", type=Path, required=True)
    eval_p.set_defaults(func=cmd_eval)

    cross_p = sub.add_parser("crossval")
    cross_p.add_argument("--root", type=Path, default=ROOT / "bots" / "archive" / "user_logs")
    cross_p.add_argument("--target-data", type=Path, default=ROOT / "bots" / "180_data.bin")
    cross_p.add_argument("--output", type=Path, default=ROOT / "results" / "group-hq-policy-crossval.tsv")
    cross_p.add_argument("--min-count", type=int, default=12)
    cross_p.add_argument("--min-precision", type=float, default=0.95)
    cross_p.set_defaults(func=cmd_crossval)

    args = parser.parse_args()
    if getattr(args, "paths", None) == []:
        args.paths = [ROOT / "bots" / "archive" / "user_logs"]
    args.func(args)


if __name__ == "__main__":
    main()
