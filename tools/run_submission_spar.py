#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "nation-providing"
TESTING_TOOL = TOOL_DIR / "testing-tool.py"
DEFAULT_SUBMISSIONS = ROOT / "bots"
DEFAULT_OUTPUT_DIR = ROOT / "bots"


@dataclass(frozen=True)
class MatchSpec:
    slot: str
    opponent: Path
    seed: int
    candidate_side: str
    left_cmd: str
    right_cmd: str
    log_path: Path


def py_cmd(path: Path) -> str:
    return f"{sys.executable} {path.resolve()}"


def default_candidate() -> Path:
    bots = sorted((p for p in DEFAULT_SUBMISSIONS.glob("*.py") if p.stem.isdigit()), key=submission_number)
    if not bots:
        raise SystemExit(f"No numeric bot files found in {DEFAULT_SUBMISSIONS}")
    return bots[-1]


def submission_number(path: Path) -> int:
    try:
        return int(path.stem)
    except ValueError as exc:
        raise SystemExit(f"Submission filename must be numeric like 3.py: {path}") from exc


def discover_submissions(path: Path, latest: int, candidate: Path | None = None) -> list[Path]:
    candidate_path = candidate.resolve() if candidate is not None else None
    bots = sorted(
        (
            p
            for p in path.glob("*.py")
            if p.stem.isdigit() and (candidate_path is None or p.resolve() != candidate_path)
        ),
        key=submission_number,
    )
    if latest <= 0:
        return bots
    if len(bots) < latest:
        raise SystemExit(f"Need {latest} numeric submission files in {path}, found {len(bots)}")
    return bots[-latest:]


def pair_log_stem(candidate: Path, opponent: Path) -> str:
    return f"{candidate.stem}_{opponent.stem}log"


def pair_log_dir(output_dir: Path, candidate: Path, opponent: Path) -> Path:
    return output_dir / pair_log_stem(candidate, opponent)


def parse_log(log_path: Path) -> dict[str, int]:
    info = {
        "end_turn": 0,
        "max_left_ms": 0,
        "max_right_ms": 0,
    }
    if not log_path.exists():
        return info
    for line in log_path.read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "END" and parts[1] == "TURN" and parts[2].isdigit():
            info["end_turn"] = max(info["end_turn"], int(parts[2]))
        elif len(parts) >= 7 and parts[0] == "TIME" and parts[4] == "RIGHT":
            info["max_left_ms"] = max(info["max_left_ms"], int(parts[2]))
            info["max_right_ms"] = max(info["max_right_ms"], int(parts[5]))
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
    parts = result.split()
    outcome = parts[1] if len(parts) >= 2 and parts[0] == "RESULT" else "UNKNOWN"
    reason = parts[2] if len(parts) >= 3 and parts[0] == "RESULT" else "UNKNOWN"
    if spec.candidate_side == "LEFT":
        candidate_result = "WIN" if outcome == "LEFT_WIN" else "DRAW" if outcome == "DRAW" else "LOSS"
    else:
        candidate_result = "WIN" if outcome == "RIGHT_WIN" else "DRAW" if outcome == "DRAW" else "LOSS"

    row: dict[str, int | str] = {
        "slot": spec.slot,
        "opponent": spec.opponent.name,
        "seed": spec.seed,
        "candidate_side": spec.candidate_side,
        "candidate_result": candidate_result,
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


def build_specs(args: argparse.Namespace, opponents: list[Path]) -> list[MatchSpec]:
    specs: list[MatchSpec] = []
    candidate_cmd = py_cmd(args.candidate)
    sides = ["LEFT", "RIGHT"] if args.side == "both" else [args.side.upper()]
    for idx, opponent in enumerate(opponents, start=1):
        slot = f"log{idx}"
        opponent_cmd = py_cmd(opponent)
        out_dir = pair_log_dir(args.output_dir, args.candidate, opponent)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        log_index = 1
        for seed in range(args.start, args.start + args.count):
            for side in sides:
                if side == "LEFT":
                    left_cmd = candidate_cmd
                    right_cmd = opponent_cmd
                else:
                    left_cmd = opponent_cmd
                    right_cmd = candidate_cmd
                log_path = out_dir / f"{log_index}.txt"
                specs.append(MatchSpec(slot, opponent, seed, side, left_cmd, right_cmd, log_path))
                log_index += 1
    return specs


def write_rows(path: Path, rows: list[dict[str, int | str]]) -> None:
    fields = [
        "slot",
        "opponent",
        "seed",
        "candidate_side",
        "candidate_result",
        "outcome",
        "reason",
        "end_turn",
        "max_left_ms",
        "max_right_ms",
        "returncode",
        "elapsed_ms",
        "result",
        "log",
        "stderr",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, int | str]]) -> list[dict[str, int | float | str]]:
    out = []
    slots = sorted({str(r["slot"]) for r in rows})
    for slot in slots:
        part = [r for r in rows if r["slot"] == slot]
        total = len(part)
        wins = sum(1 for r in part if r["candidate_result"] == "WIN")
        losses = sum(1 for r in part if r["candidate_result"] == "LOSS")
        draws = sum(1 for r in part if r["candidate_result"] == "DRAW")
        wa = sum(1 for r in part if r["reason"] == "WA" or r["returncode"] != 0)
        avg_turn = round(sum(int(r["end_turn"]) for r in part) / total, 2) if total else 0
        out.append(
            {
                "slot": slot,
                "opponent": str(part[0]["opponent"]) if part else "",
                "total": total,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "wa": wa,
                "win_rate": round(100.0 * wins / total, 2) if total else 0,
                "avg_turn": avg_turn,
            }
        )
    return out


def write_summary(path: Path, rows: list[dict[str, int | float | str]]) -> None:
    fields = ["slot", "opponent", "total", "wins", "losses", "draws", "wa", "win_rate", "avg_turn"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_pair_logs(
    candidate: Path,
    output_dir: Path,
    run_name: str,
    rows: list[dict[str, int | str]],
    summary_rows: list[dict[str, int | float | str]],
) -> None:
    for summary in summary_rows:
        slot = str(summary["slot"])
        opponent = str(summary["opponent"])
        opponent_path = Path(opponent)
        log_dir = pair_log_dir(output_dir, candidate, opponent_path)
        pair_path = output_dir / f"{pair_log_stem(candidate, opponent_path)}.txt"
        non_draws = [r for r in rows if r["slot"] == slot and r["candidate_result"] != "DRAW"]

        lines = [
            f"candidate: {candidate.name}",
            f"opponent: {opponent}",
            f"run: {run_name}",
            f"log_dir: {log_dir}",
            "",
            f"total: {summary['total']}",
            f"wins: {summary['wins']}",
            f"losses: {summary['losses']}",
            f"draws: {summary['draws']}",
            f"wa: {summary['wa']}",
            f"win_rate: {summary['win_rate']}",
            f"avg_turn: {summary['avg_turn']}",
            "",
            "non_draws:",
        ]
        if non_draws:
            for row in non_draws:
                lines.append(
                    f"- seed={row['seed']} side={row['candidate_side']} "
                    f"{row['candidate_result']} {row['result']} log={row['log']}"
                )
        else:
            lines.append("- none")
        lines.append("")
        pair_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the current candidate against the latest saved submission snapshots."
    )
    parser.add_argument("--candidate", type=Path, default=default_candidate())
    parser.add_argument("--submissions-dir", type=Path, default=DEFAULT_SUBMISSIONS)
    parser.add_argument("--latest", type=int, default=2)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--side", choices=["left", "right", "both"], default="both")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--name", default=time.strftime("submission-spar-%Y%m%d-%H%M%S"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.candidate = args.candidate.resolve()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    opponents = discover_submissions(args.submissions_dir, args.latest, args.candidate)
    if not opponents:
        raise SystemExit(f"No .py submissions found in {args.submissions_dir}")

    print("opponents=" + ",".join(opponent.name for opponent in opponents))
    specs = build_specs(args, opponents)
    rows = []
    for spec in specs:
        row = run_match(spec, args.timeout)
        rows.append(row)
        print(
            f"{row['slot']} {row['opponent']} seed={row['seed']} "
            f"side={row['candidate_side']} {row['candidate_result']} {row['result']}"
        )

    summary_rows = summarize(rows)
    write_pair_logs(args.candidate, args.output_dir, args.name, rows, summary_rows)
    for row in summary_rows:
        log_dir = pair_log_dir(args.output_dir, args.candidate, Path(str(row["opponent"])))
        summary_path = args.output_dir / f"{pair_log_stem(args.candidate, Path(str(row['opponent'])))}.txt"
        print(
            f"{row['slot']}: opponent={row['opponent']} total={row['total']} "
            f"wins={row['wins']} losses={row['losses']} draws={row['draws']} "
            f"wa={row['wa']} win_rate={row['win_rate']} avg_turn={row['avg_turn']}"
        )
        print(f"logs={log_dir}")
        print(f"summary={summary_path}")


if __name__ == "__main__":
    main()
