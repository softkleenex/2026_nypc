#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def summarize_csv(path: Path) -> dict[str, str | int | float]:
    rows = list(csv.DictReader(path.open()))
    played = [r for r in rows if r["bot_result"] != "SKIP"]
    total = len(played)
    skipped = len(rows) - total
    wins = sum(1 for r in played if r["bot_result"] == "WIN")
    losses = sum(1 for r in played if r["bot_result"] == "LOSS")
    draws = sum(1 for r in played if r["bot_result"] == "DRAW")
    wa = sum(1 for r in played if r["reason"] == "WA" or r["returncode"] != "0")
    turns = [int(r["end_turn"]) for r in played if r.get("end_turn")]
    left_ms = [int(r["max_left_ms"]) for r in rows if r.get("max_left_ms")]
    right_ms = [int(r["max_right_ms"]) for r in rows if r.get("max_right_ms")]

    return {
        "name": path.parent.name,
        "csv": str(path),
        "total": total,
        "skipped": skipped,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "wa": wa,
        "win_rate": round(100.0 * wins / total, 2) if total else 0.0,
        "avg_turn": round(sum(turns) / len(turns), 2) if turns else 0.0,
        "max_turn": max(turns) if turns else 0,
        "max_ms": max(left_ms + right_ms) if left_ms or right_ms else 0,
    }


def print_table(rows: list[dict[str, str | int | float]]) -> None:
    fields = ["name", "total", "skipped", "wins", "losses", "draws", "wa", "win_rate", "avg_turn", "max_turn", "max_ms"]
    widths = {f: len(f) for f in fields}
    for row in rows:
        for f in fields:
            widths[f] = max(widths[f], len(str(row[f])))

    print("  ".join(f.ljust(widths[f]) for f in fields))
    print("  ".join("-" * widths[f] for f in fields))
    for row in rows:
        print("  ".join(str(row[f]).ljust(widths[f]) for f in fields))


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize NYPC evaluation CSV files.")
    parser.add_argument("paths", nargs="*", type=Path, help="results.csv files or result directories")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    paths: list[Path] = []
    if args.paths:
        for p in args.paths:
            if p.is_dir():
                paths.extend(sorted(p.glob("*/results.csv")))
                direct = p / "results.csv"
                if direct.exists():
                    paths.append(direct)
            else:
                paths.append(p)
    else:
        paths = sorted(args.results_dir.glob("*/results.csv"))

    summaries = [summarize_csv(p) for p in paths if p.exists()]
    if not summaries:
        print("No results.csv files found.")
        return
    print_table(summaries)


if __name__ == "__main__":
    main()
