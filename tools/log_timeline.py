#!/usr/bin/env python3
"""테스트 툴 로그를 재생해 양측 상태(병력/기지/HQ HP/침공 병력)를 턴별로 요약한다.

사용법: python3 tools/log_timeline.py <log> [--every 10]

무승부/패배 게임에서 "어느 시점에 무엇이 밀렸는지"를 보기 위한 도구.
"""
from __future__ import annotations

import argparse
import math

HQ_HP = {1: 10, 2: 15, 3: 20, 4: 25, 5: 30}
HQ_WHP = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8}
BASE_HP = {1: 6, 2: 12, 3: 18}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--every", type=int, default=10)
    args = ap.parse_args()

    lines = open(args.log, errors="replace").read().splitlines()
    i = 0
    while not lines[i].startswith("MAP"):
        i += 1
    n, _k = map(int, lines[i + 1].split())
    xs = list(map(int, lines[i + 2].split()))
    ys = list(map(int, lines[i + 3].split()))

    # 진영별 상태
    warriors: dict[str, list] = {}  # id -> [region, hp]
    buildings: dict[int, list] = {0: ["A", "HQ", 1, 10], n - 1: ["B", "HQ", 1, 10]}
    for s, hq in (("A", 0), ("B", n - 1)):
        for j in range(1, 4):
            warriors[f"{s}{j}"] = [hq, 4]

    hq_of = {"A": 0, "B": n - 1}

    def dist(u: int, v: int) -> float:
        return math.hypot(xs[u] - xs[v], ys[u] - ys[v])

    def summary(turn: int) -> str:
        out = []
        for s in "AB":
            alive = [w for w in warriors.values() if False]
        parts = [f"T{turn:3d}"]
        for s in "AB":
            my = [(wid, w) for wid, w in warriors.items() if wid[0] == s]
            bases = [b for b in buildings.values() if b[0] == s and b[1] == "BASE"]
            hq = buildings.get(hq_of[s])
            hq_txt = f"HQ L{hq[2]} {hq[3]}hp" if hq is not None and hq[0] == s else "HQ DEAD"
            # 상대 본부가 내 본부보다 가까운 지역에 있는 병력 = 침공 병력
            inv = sum(
                1 for _, w in my
                if dist(w[0], hq_of["B" if s == "A" else "A"]) < dist(w[0], hq_of[s])
            )
            parts.append(
                f"{s}: {len(my):2d}army({inv:2d}fwd) {len(bases)}bases "
                f"L{sum(b[2] for b in bases)} {hq_txt}"
            )
        return " | ".join(parts)

    turn = 0
    in_result = False
    cur_cmd_side = None
    my_side_letter = {"LEFT": "A", "RIGHT": "B"}
    print(summary(0))
    for line in lines:
        t = line.split()
        if not t:
            continue
        if t[0] == "TURN" and len(t) >= 3 and t[2] == "RESULT":
            in_result = True
            turn = int(t[1])
            continue
        if t[0] == "END" and len(t) >= 3 and t[1] == "TURN":
            in_result = False
            if turn % args.every == 0:
                print(summary(turn))
            continue
        if not in_result:
            # 명령 블록에서 UPGRADE만 상태에 반영 (결과 블록에 없음)
            if t[0] == "COMMAND" and len(t) >= 3:
                cur_cmd_side = my_side_letter.get(t[1])
            elif t[0] == "UPGRADE" and len(t) == 2 and cur_cmd_side:
                r = int(t[1])
                b = buildings.get(r)
                if b is None:
                    buildings[r] = [cur_cmd_side, "BASE", 1, 6]
                elif b[1] == "HQ":
                    if b[2] < 5:
                        b[2] += 1
                    b[3] = HQ_HP[b[2]]
                else:
                    if b[2] < 3:
                        b[2] += 1
                    b[3] = BASE_HP[b[2]]
            continue
        # 결과 블록
        if t[0] == "TRAIN" and len(t) >= 2 and not t[1].isdigit():
            # 양측이 같은 턴에 훈련하면 "TRAIN A4 B4"처럼 한 줄에 여러 ID가 온다
            for wid in t[1:]:
                hq = buildings.get(hq_of[wid[0]])
                warriors[wid] = [hq_of[wid[0]], HQ_WHP[hq[2]] if hq else 4]
        elif t[0] == "MOVE" and len(t) == 3:
            if t[1] in warriors:
                warriors[t[1]][0] = int(t[2])
        elif t[0] == "DAMAGE" and len(t) == 4:
            wid = t[2]
            if wid in warriors:
                warriors[wid][1] -= int(t[3])
                if warriors[wid][1] <= 0:
                    del warriors[wid]
        elif t[0] == "SIEGE" and len(t) == 4:
            r = int(t[2])
            if r in buildings:
                buildings[r][3] -= int(t[3])
                if buildings[r][3] <= 0:
                    del buildings[r]
    print(summary(turn))
    for line in lines[-3:]:
        if line.startswith("RESULT"):
            print(line)


if __name__ == "__main__":
    main()
