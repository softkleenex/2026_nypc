#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALUATE = ROOT / "tools" / "evaluate.py"


PROXY = ROOT / "opponents" / "proxy.py"


def proxy_cmd(style: str) -> str:
    return f"{sys.executable} {PROXY} {style}"


# pool 이름 -> (bot이 LEFT일 때 상대 커맨드, bot이 RIGHT일 때 LEFT 상대 커맨드)
# proxy-* 풀은 공식 샘플 AI 4~8번의 매크로 스타일을 모사한 벤치마크다.
# 캘리브레이션(2026-07-02): 서버 3승5패였던 25.py 기준
#   proxy-econ 0W 8L 2D / proxy-turtle 0W 4L 6D / proxy-rush 8W 0L 2D
POOLS: dict[str, tuple[str | None, str | None]] = {
    "sample": (None, None),
    "proxy-econ": (proxy_cmd("econ"), proxy_cmd("econ")),
    "proxy-turtle": (proxy_cmd("turtle"), proxy_cmd("turtle")),
    "proxy-rush": (proxy_cmd("rush"), proxy_cmd("rush")),
    "proxy-punch": (proxy_cmd("punch"), proxy_cmd("punch")),
}


def load_results(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def summarize(rows: list[dict[str, str]]) -> dict[str, int | float | str]:
    played = [r for r in rows if r["bot_result"] != "SKIP"]
    total = len(played)
    wins = sum(1 for r in played if r["bot_result"] == "WIN")
    losses = sum(1 for r in played if r["bot_result"] == "LOSS")
    draws = sum(1 for r in played if r["bot_result"] == "DRAW")
    wa = sum(1 for r in played if r["reason"] == "WA" or r["returncode"] != "0")
    avg_turn = round(sum(int(r["end_turn"]) for r in played) / total, 2) if total else 0
    max_turn = max((int(r["end_turn"]) for r in played), default=0)
    max_ms = max(
        (max(int(r["max_left_ms"]), int(r["max_right_ms"])) for r in played),
        default=0,
    )
    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "wa": wa,
        "win_rate": round(100.0 * wins / total, 2) if total else 0,
        "avg_turn": avg_turn,
        "max_turn": max_turn,
        "max_ms": max_ms,
    }


def run_pool(args: argparse.Namespace, pool: str, run_root: Path) -> dict[str, int | float | str]:
    opponent, left_opponent = POOLS[pool]
    cmd = [
        sys.executable,
        str(EVALUATE),
        "--bot",
        str(args.bot),
        "--start",
        str(args.start),
        "--count",
        str(args.count),
        "--side",
        args.side,
        "--name",
        pool,
        "--results-dir",
        str(run_root),
        "--timeout",
        str(args.timeout),
        "--quiet",
    ]
    if opponent is not None:
        cmd.extend(["--opponent", opponent])
    if left_opponent is not None:
        cmd.extend(["--left-opponent", left_opponent])

    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    row = summarize(load_results(run_root / pool / "results.csv"))
    row["pool"] = pool
    return row


def write_summary(path: Path, rows: list[dict[str, int | float | str]]) -> None:
    fields = ["pool", "total", "wins", "losses", "draws", "wa", "win_rate", "avg_turn", "max_turn", "max_ms"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NYPC bot against the maintained opponent pool.")
    parser.add_argument("--bot", type=Path, default=ROOT / "bots" / "current.py")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--side", choices=["left", "right", "both"], default="both")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--name", default=time.strftime("pool-%Y%m%d-%H%M%S"))
    parser.add_argument("--pools", nargs="+", choices=sorted(POOLS), default=list(POOLS))
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    run_root = args.results_dir / args.name
    run_root.mkdir(parents=True, exist_ok=True)

    rows = []
    for pool in args.pools:
        row = run_pool(args, pool, run_root)
        rows.append(row)
        print(
            f"{pool}: total={row['total']} wins={row['wins']} losses={row['losses']} "
            f"draws={row['draws']} wa={row['wa']} win_rate={row['win_rate']} avg_turn={row['avg_turn']}"
        )

    summary_path = run_root / "pool-summary.csv"
    write_summary(summary_path, rows)
    print(f"summary={summary_path}")


if __name__ == "__main__":
    main()
