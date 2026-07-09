#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "nation-providing"
TESTING_TOOL = TOOL_DIR / "testing-tool.py"
DEFAULT_BOT = ROOT / "bots" / "current.py"
SAMPLE = TOOL_DIR / "sample-code.py"


@dataclass(frozen=True)
class MatchSpec:
    seed: int
    bot_side: str
    left_cmd: str
    right_cmd: str
    log_path: Path


def sample_cmd(name: str) -> str:
    return f"{sys.executable} {SAMPLE} {name}"


def bot_cmd(path: Path) -> str:
    return f"{sys.executable} {path}"


def parse_log(log_path: Path) -> dict[str, int | str]:
    info: dict[str, int | str] = {
        "end_turn": 0,
        "max_left_ms": 0,
        "max_right_ms": 0,
        "min_left_tokens": 999,
        "min_right_tokens": 999,
    }
    if not log_path.exists():
        return info

    for line in log_path.read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "END" and parts[1] == "TURN":
            info["end_turn"] = max(int(info["end_turn"]), int(parts[2]))
        elif len(parts) >= 7 and parts[0] == "TIME":
            left_ms = int(parts[2])
            left_tokens = int(parts[3])
            right_ms = int(parts[5])
            right_tokens = int(parts[6])
            info["max_left_ms"] = max(int(info["max_left_ms"]), left_ms)
            info["max_right_ms"] = max(int(info["max_right_ms"]), right_ms)
            info["min_left_tokens"] = min(int(info["min_left_tokens"]), left_tokens)
            info["min_right_tokens"] = min(int(info["min_right_tokens"]), right_tokens)

    if info["min_left_tokens"] == 999:
        info["min_left_tokens"] = 0
    if info["min_right_tokens"] == 999:
        info["min_right_tokens"] = 0
    return info


def run_match(spec: MatchSpec, timeout_s: int) -> dict[str, int | str]:
    spec.log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(TESTING_TOOL),
        "--seed",
        str(spec.seed),
        "-l",
        str(spec.log_path),
        "-a",
        spec.left_cmd,
        "-b",
        spec.right_cmd,
    ]

    started = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=TOOL_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
    )
    elapsed_ms = round((time.monotonic() - started) * 1000)

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    result = stdout.splitlines()[-1] if stdout else "NO_RESULT"
    if result == "NO_RESULT" and "Error generating map:" in stderr:
        outcome = "SKIP"
        reason = "MAP_ERROR"
        bot_result = "SKIP"
    else:
        parts = result.split()
        outcome = parts[1] if len(parts) >= 2 and parts[0] == "RESULT" else "UNKNOWN"
        reason = parts[2] if len(parts) >= 3 and parts[0] == "RESULT" else "UNKNOWN"

        if spec.bot_side == "LEFT":
            bot_result = "WIN" if outcome == "LEFT_WIN" else ("DRAW" if outcome == "DRAW" else "LOSS")
        else:
            bot_result = "WIN" if outcome == "RIGHT_WIN" else ("DRAW" if outcome == "DRAW" else "LOSS")

    row: dict[str, int | str] = {
        "seed": spec.seed,
        "bot_side": spec.bot_side,
        "bot_result": bot_result,
        "outcome": outcome,
        "reason": reason,
        "returncode": proc.returncode,
        "elapsed_ms": elapsed_ms,
        "result": result,
        "log": str(spec.log_path),
        "stderr": stderr,
    }
    row.update(parse_log(spec.log_path))
    return row


def build_specs(args: argparse.Namespace, run_dir: Path) -> list[MatchSpec]:
    bot = args.bot.resolve()
    opponent = args.opponent or sample_cmd("P2")
    specs: list[MatchSpec] = []
    sides = ["LEFT", "RIGHT"] if args.side == "both" else [args.side.upper()]

    for seed in range(args.start, args.start + args.count):
        for side in sides:
            if side == "LEFT":
                left_cmd = bot_cmd(bot)
                right_cmd = opponent
            else:
                left_cmd = args.left_opponent or sample_cmd("P1")
                right_cmd = bot_cmd(bot)
            log_path = run_dir / "logs" / f"seed_{seed}_{side.lower()}.log"
            specs.append(MatchSpec(seed, side, left_cmd, right_cmd, log_path))
    return specs


def summarize(rows: list[dict[str, int | str]]) -> dict[str, int | float]:
    played = [r for r in rows if r["bot_result"] != "SKIP"]
    total = len(played)
    skipped = len(rows) - total
    wins = sum(1 for r in played if r["bot_result"] == "WIN")
    losses = sum(1 for r in played if r["bot_result"] == "LOSS")
    draws = sum(1 for r in played if r["bot_result"] == "DRAW")
    wa = sum(1 for r in played if r["reason"] == "WA" or r["returncode"] != 0)
    avg_turn = round(sum(int(r["end_turn"]) for r in played) / total, 2) if total else 0
    return {
        "total": total,
        "skipped": skipped,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "wa": wa,
        "win_rate": round(100.0 * wins / total, 2) if total else 0,
        "avg_end_turn": avg_turn,
    }


def write_csv(path: Path, rows: list[dict[str, int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "seed",
        "bot_side",
        "bot_result",
        "outcome",
        "reason",
        "end_turn",
        "max_left_ms",
        "max_right_ms",
        "min_left_tokens",
        "min_right_tokens",
        "returncode",
        "elapsed_ms",
        "result",
        "log",
        "stderr",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NYPC bot matches over many seeds.")
    parser.add_argument("--bot", type=Path, default=DEFAULT_BOT)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--side", choices=["left", "right", "both"], default="left")
    parser.add_argument("--opponent", help="Opponent command when bot is LEFT")
    parser.add_argument("--left-opponent", help="Opponent command when bot is RIGHT")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--name", default=time.strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    run_dir = args.results_dir / args.name
    rows = []
    for spec in build_specs(args, run_dir):
        row = run_match(spec, args.timeout)
        rows.append(row)
        if not args.quiet:
            print(
                f"seed={row['seed']} side={row['bot_side']} "
                f"{row['bot_result']} {row['result']} turn={row['end_turn']}"
            )

    csv_path = run_dir / "results.csv"
    write_csv(csv_path, rows)
    summary = summarize(rows)

    print()
    print(
        "summary "
        f"total={summary['total']} wins={summary['wins']} losses={summary['losses']} "
        f"draws={summary['draws']} wa={summary['wa']} skipped={summary['skipped']} "
        f"win_rate={summary['win_rate']} avg_end_turn={summary['avg_end_turn']}"
    )
    print(f"csv={csv_path}")
    print(f"logs={run_dir / 'logs'}")


if __name__ == "__main__":
    main()
