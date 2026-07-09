#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "nation-providing"
TESTING_TOOL = TOOL_DIR / "testing-tool.py"
REPLAY_BOT = ROOT / "tools" / "replay_log_bot.py"
DEFAULT_CANDIDATE = ROOT / "bots" / "current.py"


@dataclass(frozen=True)
class ReplaySpec:
    source_log: Path
    replay_side: str
    candidate_side: str
    map_path: Path
    log_path: Path
    left_cmd: str
    right_cmd: str


def extract_map(source: Path, output: Path) -> None:
    lines = source.read_text(errors="replace").splitlines()
    try:
        start = lines.index("MAP") + 1
        end = lines.index("END MAP")
    except ValueError as exc:
        raise SystemExit(f"MAP block not found in {source}") from exc
    map_lines = []
    for line in lines[start:end]:
        if line.startswith("STRONGHOLDS "):
            map_lines.append(line.removeprefix("STRONGHOLDS "))
        else:
            map_lines.append(line)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(map_lines) + "\n")


def py_cmd(path: Path, *args: str) -> str:
    parts = [sys.executable, str(path.resolve()), *args]
    return " ".join(shlex.quote(str(p)) for p in parts)


def parse_log(log_path: Path) -> dict[str, int]:
    info = {"end_turn": 0, "max_left_ms": 0, "max_right_ms": 0}
    if not log_path.exists():
        return info
    for line in log_path.read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "END" and parts[1] == "TURN":
            info["end_turn"] = max(info["end_turn"], int(parts[2]))
        elif len(parts) >= 7 and parts[0] == "TIME":
            info["max_left_ms"] = max(info["max_left_ms"], int(parts[2]))
            info["max_right_ms"] = max(info["max_right_ms"], int(parts[5]))
    return info


def collect_logs(paths: list[Path]) -> list[Path]:
    logs: list[Path] = []
    for path in paths:
        if path.is_dir():
            logs.extend(sorted(p for p in path.glob("*.txt") if p.is_file()))
        else:
            logs.append(path)
    return logs


def build_spec(args: argparse.Namespace, source_log: Path, run_dir: Path) -> ReplaySpec:
    replay_side = args.replay_side.upper()
    candidate_side = "LEFT" if replay_side == "RIGHT" else "RIGHT"
    stem = source_log.stem.replace(" ", "_")
    map_path = run_dir / "maps" / f"{stem}.txt"
    out_log = run_dir / "logs" / f"{stem}_{candidate_side.lower()}_vs_replay_{replay_side.lower()}.log"
    extract_map(source_log, map_path)

    replay_cmd = py_cmd(REPLAY_BOT, str(source_log.resolve()), "--side", replay_side)
    candidate_cmd = py_cmd(args.candidate)
    if candidate_side == "LEFT":
        left_cmd = candidate_cmd
        right_cmd = replay_cmd
    else:
        left_cmd = replay_cmd
        right_cmd = candidate_cmd

    return ReplaySpec(
        source_log=source_log,
        replay_side=replay_side,
        candidate_side=candidate_side,
        map_path=map_path,
        log_path=out_log,
        left_cmd=left_cmd,
        right_cmd=right_cmd,
    )


def run_spec(spec: ReplaySpec, timeout_s: int) -> dict[str, int | str]:
    spec.log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(TESTING_TOOL),
        "-i",
        str(spec.map_path),
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
    parts = result.split()
    outcome = parts[1] if len(parts) >= 2 and parts[0] == "RESULT" else "UNKNOWN"
    reason = parts[2] if len(parts) >= 3 and parts[0] == "RESULT" else "UNKNOWN"
    if spec.candidate_side == "LEFT":
        candidate_result = "WIN" if outcome == "LEFT_WIN" else "DRAW" if outcome == "DRAW" else "LOSS"
    else:
        candidate_result = "WIN" if outcome == "RIGHT_WIN" else "DRAW" if outcome == "DRAW" else "LOSS"

    row: dict[str, int | str] = {
        "source": spec.source_log.name,
        "candidate_side": spec.candidate_side,
        "replay_side": spec.replay_side,
        "candidate_result": candidate_result,
        "outcome": outcome,
        "reason": reason,
        "returncode": proc.returncode,
        "elapsed_ms": elapsed_ms,
        "result": result,
        "map": str(spec.map_path),
        "log": str(spec.log_path),
        "stderr": stderr,
    }
    row.update(parse_log(spec.log_path))
    return row


def write_rows(path: Path, rows: list[dict[str, int | str]]) -> None:
    fields = [
        "source",
        "candidate_side",
        "replay_side",
        "candidate_result",
        "outcome",
        "reason",
        "end_turn",
        "max_left_ms",
        "max_right_ms",
        "returncode",
        "elapsed_ms",
        "result",
        "map",
        "log",
        "stderr",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run current candidate against one replayed side from server logs.")
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--replay-side", choices=["left", "right"], default="right")
    parser.add_argument("--name", default=time.strftime("log-replay-%Y%m%d-%H%M%S"))
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results" / "log-replay")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    run_dir = args.results_dir / args.name
    rows = []
    for source_log in collect_logs(args.logs):
        spec = build_spec(args, source_log, run_dir)
        row = run_spec(spec, args.timeout)
        rows.append(row)
        print(
            f"{row['source']} candidate={row['candidate_side']} replay={row['replay_side']} "
            f"{row['candidate_result']} {row['result']} turn={row['end_turn']}"
        )
    write_rows(run_dir / "results.csv", rows)
    wins = sum(1 for r in rows if r["candidate_result"] == "WIN")
    losses = sum(1 for r in rows if r["candidate_result"] == "LOSS")
    draws = sum(1 for r in rows if r["candidate_result"] == "DRAW")
    wa = sum(1 for r in rows if r["reason"] == "WA" or r["returncode"] != 0)
    print(f"summary total={len(rows)} wins={wins} losses={losses} draws={draws} wa={wa}")
    print(f"csv={run_dir / 'results.csv'}")


if __name__ == "__main__":
    main()
