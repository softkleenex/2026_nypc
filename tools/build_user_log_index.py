#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from analyze_server_logs import analyze


SUMMARY_RE = re.compile(
    r"중간평가\s*#(\d+)\s*·\s*(.+?)\n"
    r"(?:.*?\n)*?집계 완료\nTier (\d+)\n(\d+)\n(\d+)위\s*/\s*(\d+)팀",
    re.S,
)
OPP_RE = re.compile(
    r"(\d{5,7})\t(.+?)\tTier (\d+)\n(\d+)\n1전 (\d+(?:\.\d+)?)승 \(([\d.]+)%\)"
)


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s).strip()


def parse_ranking(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    meta_match = SUMMARY_RE.search(text)
    if not meta_match:
        raise SystemExit(f"failed to parse ranking header: {path}")
    meta = {
        "eval_no": int(meta_match.group(1)),
        "date": meta_match.group(2).strip(),
        "our_tier": int(meta_match.group(3)),
        "our_rating": int(meta_match.group(4)),
        "our_rank": int(meta_match.group(5)),
        "pool": int(meta_match.group(6)),
    }
    by_id = {}
    by_name = {}
    for match_id, name, tier, rating, wins, pct in OPP_RE.findall(text):
        opp = {
            "opponent_id": match_id,
            "opponent_team": norm(name),
            "opponent_tier": int(tier),
            "opponent_rating": int(rating),
            "site_pct": float(pct),
        }
        by_id[match_id] = opp
        by_name[opp["opponent_team"]] = opp
    return meta, by_id, by_name


def parse_manifest(path: Path):
    with path.open(encoding="utf-8", errors="ignore", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def result_to_outcome(result: str, side: str) -> str:
    if result.startswith("DRAW"):
        return "D"
    if side == "A":
        return "W" if result.startswith("LEFT_WIN") else "L"
    return "W" if result.startswith("RIGHT_WIN") else "L"


def pct_to_outcome(pct: float) -> str:
    if pct == 100.0:
        return "W"
    if pct == 0.0:
        return "L"
    return "D"


def parse_eval_folder(folder: Path):
    m = re.match(r"eval(\d+)_bot(.+?)_\d", folder.name)
    if m:
        return int(m.group(1)), f"bot{m.group(2)}"
    m = re.match(r"eval(\d+)_bot(.+)", folder.name)
    if m:
        return int(m.group(1)), f"bot{m.group(2)}"
    return None, "unknown"


def load_replay_rows(results_dir: Path):
    replay = {}
    for path in sorted(results_dir.glob("145-eval*-*-vs-replay-*/results.csv")):
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                replay[row["source"]] = row
    return replay


def build_rows(log_root: Path, results_dir: Path):
    replay = load_replay_rows(results_dir)
    rows = []
    for folder in sorted(log_root.glob("eval*_bot*")):
        ranking = folder / "ranking.txt"
        manifest = folder / "manifest.tsv"
        if not ranking.exists() or not manifest.exists():
            continue
        eval_no_from_name, our_bot = parse_eval_folder(folder)
        meta, by_id, by_name = parse_ranking(ranking)
        eval_no = eval_no_from_name or meta["eval_no"]
        for item in parse_manifest(manifest):
            rel_file = item["file"]
            if not rel_file:
                continue
            log_path = folder / rel_file
            if not log_path.exists():
                continue
            source = Path(rel_file).name
            match_id = item["match_id"]
            team = norm(item.get("team", ""))
            opp = by_id.get(match_id)
            if opp is None and team:
                opp = by_name.get(team)
            if opp is None:
                stem_id = source.split("_")[0]
                opp = by_id.get(stem_id)
            if opp is None:
                opp = {
                    "opponent_id": "",
                    "opponent_team": team,
                    "opponent_tier": "",
                    "opponent_rating": "",
                    "site_pct": "",
                }
            game = analyze(log_path)
            side = item["side"]
            archived_result = game["result"]
            archived_outcome = result_to_outcome(archived_result, side)
            site_pct = opp["site_pct"]
            site_outcome = pct_to_outcome(site_pct) if site_pct != "" else archived_outcome
            rr = replay.get(source, {})
            rating_diff = ""
            if opp["opponent_rating"] != "":
                rating_diff = meta["our_rating"] - int(opp["opponent_rating"])
            rows.append({
                "eval_no": eval_no,
                "eval_folder": folder.name,
                "our_bot": our_bot,
                "our_tier": meta["our_tier"],
                "our_rating": meta["our_rating"],
                "our_rank": meta["our_rank"],
                "pool": meta["pool"],
                "match_id": match_id,
                "source_log": source,
                "our_side": "LEFT" if side == "A" else "RIGHT",
                "opponent_id": opp["opponent_id"],
                "opponent_team": opp["opponent_team"],
                "opponent_tier": opp["opponent_tier"],
                "opponent_rating": opp["opponent_rating"],
                "rating_diff": rating_diff,
                "site_outcome": site_outcome,
                "archived_outcome": archived_outcome,
                "archived_result": archived_result,
                "archived_turn": game["turn"],
                "replay145_outcome": rr.get("candidate_result", ""),
                "replay145_result": rr.get("result", ""),
                "replay145_turn": rr.get("end_turn", ""),
                "replay145_reason": rr.get("reason", ""),
                "log_path": str(log_path),
                "replay145_log": rr.get("log", ""),
            })
    return rows


def counts(rows, field: str):
    c = defaultdict(lambda: {"W": 0, "L": 0, "D": 0, "": 0})
    for row in rows:
        c[row[field]][row["site_outcome"]] += 1
    return c


def wld(rows, field: str):
    def compact(v: str) -> str:
        return {"WIN": "W", "LOSS": "L", "DRAW": "D"}.get(v, v)
    vals = [compact(row[field]) for row in rows]
    return vals.count("W"), vals.count("L"), vals.count("D")


def write_tsv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "eval_no", "eval_folder", "our_bot", "our_tier", "our_rating", "our_rank",
        "pool", "match_id", "source_log", "our_side", "opponent_id",
        "opponent_team", "opponent_tier", "opponent_rating", "rating_diff",
        "site_outcome", "archived_outcome", "archived_result", "archived_turn",
        "replay145_outcome", "replay145_result", "replay145_turn",
        "replay145_reason", "log_path", "replay145_log",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    by_eval = defaultdict(list)
    by_tier = defaultdict(list)
    for row in rows:
        by_eval[row["eval_no"]].append(row)
        by_tier[row["opponent_tier"]].append(row)

    lines = [
        "# User Log Match Index",
        "",
        "Archived user-evaluation logs matched by opponent tier, submitted bot, result, and log path.",
        "",
        "## Evaluation Summary",
        "",
        "| Eval | Our bot | Rank | Rating | Archived W/L/D | 145 replay W/L/D |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for eval_no in sorted(by_eval):
        group = by_eval[eval_no]
        first = group[0]
        aw, al, ad = wld(group, "site_outcome")
        rw, rl, rd = wld(group, "replay145_outcome")
        lines.append(
            f"| {eval_no} | {first['our_bot']} | {first['our_rank']}/{first['pool']} | "
            f"{first['our_rating']} | {aw}/{al}/{ad} | {rw}/{rl}/{rd} |"
        )

    lines += [
        "",
        "## Opponent Tier Summary",
        "",
        "| Opp tier | Matches | Archived W/L/D | 145 replay W/L/D |",
        "|---:|---:|---:|---:|",
    ]
    for tier in sorted(by_tier, key=lambda x: int(x) if str(x).isdigit() else 999):
        group = by_tier[tier]
        aw, al, ad = wld(group, "site_outcome")
        rw, rl, rd = wld(group, "replay145_outcome")
        lines.append(f"| {tier} | {len(group)} | {aw}/{al}/{ad} | {rw}/{rl}/{rd} |")

    remaining = [r for r in rows if r["replay145_outcome"] not in ("", "WIN")]
    lines += [
        "",
        "## Remaining 145 Replay Risks",
        "",
        "| Eval | Opponent | Tier | Rating | 145 result | Turn | Log |",
        "|---:|---|---:|---:|---|---:|---|",
    ]
    for row in sorted(remaining, key=lambda r: (r["eval_no"], r["source_log"])):
        lines.append(
            f"| {row['eval_no']} | {row['opponent_team']} | {row['opponent_tier']} | "
            f"{row['opponent_rating']} | {row['replay145_result']} | "
            f"{row['replay145_turn']} | `{row['log_path']}` |"
        )
    if not remaining:
        lines.append("| - | - | - | - | - | - | - |")

    fixed = [r for r in rows if r["site_outcome"] in ("L", "D") and r["replay145_outcome"] == "WIN"]
    lines += [
        "",
        "## Previously Bad Results Fixed By 145 Replay",
        "",
        "| Eval | Opponent | Tier | Archived | 145 result | Log |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in sorted(fixed, key=lambda r: (r["eval_no"], r["opponent_tier"], r["opponent_rating"])):
        lines.append(
            f"| {row['eval_no']} | {row['opponent_team']} | {row['opponent_tier']} | "
            f"{row['archived_result']} | {row['replay145_result']} | `{row['log_path']}` |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-root", type=Path, default=Path("bots/archive/user_logs"))
    ap.add_argument("--results-dir", type=Path, default=Path("results/log-replay"))
    ap.add_argument("--tsv", type=Path, default=Path("results/user-log-match-index.tsv"))
    ap.add_argument("--md", type=Path, default=Path("docs/user-log-analysis.md"))
    args = ap.parse_args()

    rows = build_rows(args.log_root, args.results_dir)
    write_tsv(rows, args.tsv)
    write_markdown(rows, args.md)
    print(f"rows={len(rows)}")
    print(f"tsv={args.tsv}")
    print(f"md={args.md}")


if __name__ == "__main__":
    main()
