#!/usr/bin/env python3
"""전쟁터: 봇 변형들의 랜덤 맵 풀리그 + 프록시전 집계 (나도린디 방식).

승=1, 무=0.5로 집계. 변형 간 상호전 + 프록시(econ/turtle/punch) 앵커전.
결과: results/arena/<name>/games.csv + 최종 순위표 stdout.
"""
from __future__ import annotations
import argparse, csv, itertools, pathlib, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "nation-providing" / "testing-tool.py"
PROXY = ROOT / "opponents" / "proxy.py"


def run_game(a_cmd, b_cmd, seed, np_, log):
    cmd = [sys.executable, str(TOOL), "--seed", str(seed), "--NP", str(np_),
           "--KP", str(max(4, int(np_ * 0.16))), "-l", str(log),
           "-a", a_cmd, "-b", b_cmd]
    try:
        r = subprocess.run(cmd, cwd=TOOL.parent, capture_output=True,
                           text=True, timeout=900)
        line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        return line if line.startswith("RESULT") else "RESULT ERR ERR"
    except Exception:
        return "RESULT ERR ERR"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="overnight")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    out = ROOT / "results" / "arena" / args.name
    out.mkdir(parents=True, exist_ok=True)

    bots = {"base55": ROOT / "bots" / "55.py"}
    for f in sorted((ROOT / "bots" / "variants").glob("*.py")):
        bots[f.stem] = f
    proxies = {f"px_{s}": f"{sys.executable} {PROXY} {s}"
               for s in ("econ", "turtle", "punch")}

    def cmd_of(name):
        return proxies.get(name) or f"{sys.executable} {bots[name]}"

    rng = random.Random(7)
    jobs = []
    sizes = [25, 40, 54]
    # 변형 상호전
    for x, y in itertools.combinations(bots, 2):
        for np_ in sizes:
            for _ in range(args.seeds):
                sd = rng.randrange(10000, 99999)
                jobs.append((x, y, sd, np_))
    # 프록시 앵커전 (양 진영)
    for x in bots:
        for p in proxies:
            for np_ in sizes:
                for _ in range(args.seeds):
                    sd = rng.randrange(10000, 99999)
                    jobs.append((x, p, sd, np_))
                    jobs.append((p, x, sd, np_))

    print(f"총 {len(jobs)}판 시작 (workers={args.workers})", flush=True)
    rows = []
    csvf = open(out / "games.csv", "w", newline="", buffering=1)
    cw = csv.DictWriter(csvf, fieldnames=["a", "b", "seed", "np", "result"])
    cw.writeheader()
    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(run_game, cmd_of(a), cmd_of(b), sd, np_,
                          out / f"{a}__{b}__{sd}_{np_}.log"): (a, b, sd, np_)
                for a, b, sd, np_ in jobs}
        done = 0
        for fu in as_completed(futs):
            a, b, sd, np_ = futs[fu]
            res = fu.result()
            row = dict(a=a, b=b, seed=sd, np=np_, result=res)
            rows.append(row); cw.writerow(row)
            done += 1
            if done % 25 == 0:
                print(f"{done}/{len(jobs)}", flush=True)
            # 로그는 용량상 즉시 삭제 (결과만 유지)
            lg = out / f"{a}__{b}__{sd}_{np_}.log"
            if lg.exists():
                lg.unlink()

    csvf.close()

    score = {k: [0.0, 0] for k in bots}
    for r in rows:
        for side, name in (("LEFT", r["a"]), ("RIGHT", r["b"])):
            if name not in score:
                continue
            score[name][1] += 1
            if "DRAW" in r["result"]:
                score[name][0] += 0.5
            elif f"{side}_WIN" in r["result"]:
                score[name][0] += 1.0
    print("\n=== 최종 순위 (승점/판수) ===")
    for k, (s, n) in sorted(score.items(), key=lambda kv: -kv[1][0] / max(1, kv[1][1])):
        print(f"{k:10s} {s:6.1f}/{n} = {s / max(1, n):.3f}")


if __name__ == "__main__":
    main()
