#!/usr/bin/env python3
"""유저 중간평가 로그 폴더 분석 -- 대전기록/상대ID/상대점수 위주.

입력: 유저 로그 폴더 (게임 로그 <대전ID>_<A|B>.txt 여러 개 + 순위 요약 텍스트
파일 1개, 보통 '무제.txt'). 순위 요약 파일은 사이트에서 그대로 복사한
"중간평가 #N ... 대전 ID / 상대 팀 / 상대 퍼포먼스 / 결과" 표 형식을 가정.

출력: 상대 레이팅 차이 순으로 정렬한 대전 표 (승패/우리측/턴/타입) +
업셋패/아까운무/체급승 하이라이트.

사용:
    python3 tools/analyze_user_eval.py bots/62_user_log
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_server_logs import analyze  # noqa: E402

SUMMARY_RE = re.compile(
    r"중간평가\s*#(\d+)\s*·\s*(.+)\n"
    r"(?:.*\n)*?집계 완료\nTier (\d+)\n(\d+)\n(\d+)위\s*/\s*(\d+)팀"
)
OPP_RE = re.compile(
    r"(\d{5,7})\t(.+?)\tTier (\d+)\n(\d+)\n1전 (\d+(?:\.\d+)?)승 \(([\d.]+)%\)"
)


def find_summary_file(folder: Path) -> Path | None:
    for p in sorted(folder.glob("*.txt")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "중간평가" in text and "대전 ID" in text:
            return p
    return None


def parse_summary(text: str):
    m = SUMMARY_RE.search(text)
    meta = None
    if m:
        meta = dict(
            eval_no=int(m.group(1)), date=m.group(2).strip(),
            tier=int(m.group(3)), rating=int(m.group(4)),
            rank=int(m.group(5)), pool=int(m.group(6)),
        )
    opponents = {}
    for id_, name, tier, rating, wins, pct in OPP_RE.findall(text):
        opponents[id_] = dict(name=name.strip(), tier=int(tier),
                               rating=int(rating), pct=float(pct))
    return meta, opponents


def infer_side(result: str, pct: float) -> str:
    if pct == 100:
        return "LEFT" if "LEFT_WIN" in result else "RIGHT"
    if pct == 0:
        return "RIGHT" if "LEFT_WIN" in result else "LEFT"
    return "DRAW"


def outcome_label(pct: float) -> str:
    if pct == 100:
        return "승"
    if pct == 0:
        return "패"
    return "무"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", type=Path)
    args = ap.parse_args()
    folder = args.folder

    summary_path = find_summary_file(folder)
    if summary_path is None:
        raise SystemExit(f"순위 요약 파일을 찾지 못함 (폴더 내 .txt 중 '중간평가' 포함 파일 없음): {folder}")
    meta, opponents = parse_summary(summary_path.read_text(encoding="utf-8", errors="ignore"))
    if meta is None:
        print("[경고] 헤더(레이팅/순위) 파싱 실패 -- 형식이 바뀌었을 수 있음", file=sys.stderr)
    if not opponents:
        raise SystemExit("상대 목록 파싱 실패 -- OPP_RE 정규식이 이 배치 형식과 안 맞음")

    logs = sorted(p for p in folder.glob("*.txt") if p != summary_path)
    rows = []
    unmatched = []
    seen_ids = set()
    for log in logs:
        fid = log.stem.split("_")[0].strip()
        opp = opponents.get(fid)
        if opp is None:
            unmatched.append(log.name)
            continue
        game = analyze(log)
        side = infer_side(game["result"], opp["pct"])
        rows.append(dict(
            file=log.name, id=fid, name=opp["name"], tier=opp["tier"],
            rating=opp["rating"], diff=(meta["rating"] - opp["rating"]) if meta else None,
            pct=opp["pct"], outcome=outcome_label(opp["pct"]), side=side,
            result=game["result"], turn=game["turn"],
        ))
        if fid in seen_ids:
            print(f"[경고] 대전ID 중복: {fid} ({log.name}) -- 파일명 손상 의심(공백/자르림), 수동 확인 필요", file=sys.stderr)
        seen_ids.add(fid)

    missing = set(opponents) - seen_ids
    if missing:
        print(f"[경고] 요약엔 있는데 로그 파일이 없는 대전ID: {sorted(missing)}", file=sys.stderr)
    if unmatched:
        print(f"[경고] 로그는 있는데 요약에 없는 파일: {unmatched}", file=sys.stderr)

    rows.sort(key=lambda r: (r["diff"] if r["diff"] is not None else 0))

    if meta:
        print(f"=== 중간평가 #{meta['eval_no']} ({meta['date']}) ===")
        print(f"Tier {meta['tier']} · {meta['rating']}점 · {meta['rank']}위/{meta['pool']}팀\n")

    w = sum(1 for r in rows if r["pct"] == 100)
    l = sum(1 for r in rows if r["pct"] == 0)
    d = sum(1 for r in rows if 0 < r["pct"] < 100)
    print(f"전적: {w}승 {l}패 {d}무 (총 {len(rows)}전)\n")

    print(f"{'상대':14s} {'Tier':4s} {'레이팅':6s} {'차이':6s} {'결과':4s} {'우리측':6s} {'타입':22s} {'턴':4s} {'대전ID':8s}")
    for r in rows:
        diff_s = f"{r['diff']:+d}" if r["diff"] is not None else "?"
        print(f"{r['name']:14s} T{r['tier']:<3d} {r['rating']:<6d} {diff_s:6s} "
              f"{r['outcome']:4s} {r['side']:6s} {r['result']:22s} {r['turn']:>4} {r['id']:8s}")

    def tag(r):
        return f"{r['name']}({r['diff']:+d})"

    upsets = [r for r in rows if r["pct"] == 0 and r["diff"] is not None and r["diff"] > 0]
    missed = [r for r in rows if 0 < r["pct"] < 100 and r["diff"] is not None and r["diff"] > 0]
    quality_wins = [r for r in rows if r["pct"] == 100 and r["diff"] is not None and r["diff"] < 0]
    print()
    if upsets:
        print("⚠️  업셋 패배 (레이팅 아래인데 짐): " + ", ".join(tag(r) for r in upsets))
    if missed:
        print("🟡 아까운 무승부 (레이팅 아래인데 못 이김): " + ", ".join(tag(r) for r in missed))
    if quality_wins:
        print("✅ 체급 이상 승리 (레이팅 위인데 이김): " + ", ".join(tag(r) for r in quality_wins))


if __name__ == "__main__":
    main()
