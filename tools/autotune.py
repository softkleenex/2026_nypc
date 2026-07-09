#!/usr/bin/env python3
"""STYLES['econ'] 파라미터 자동 탐색 (좌표하강 힐클라이밍).

이건 "3~6개 변형을 손으로 만들어 테스트"가 아니라, 실제 탐색 루프다:
매 라운드 현재 최선 후보의 각 파라미터를 무작위로 흔든 변이 M개를 만들어
전부 실제 게임(evaluate.py, 양 진영 무작위 맵)으로 현재 최선과 겨루게 하고,
승패비가 임계를 넘는 변이만 채택한다. 채택된 변이가 다음 라운드의 기준이 된다.

턴당 100ms 중 15ms만 쓰는 계산 여유를 활용해, 사람이 감으로 고른 상수 대신
탐색으로 찾은 상수를 쓰는 것이 목표.
"""
from __future__ import annotations
import random, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "bots" / "57.py"

# 탐색 대상 파라미터: (이름, 최소, 최대, 정수 여부, 변이폭)
PARAM_SPACE = {
    "push_army": (10, 40, 1, 4),
    "push_turn": (110, 170, 1, 10),
    "garrison": (0, 5, 1, 1),
    "wave": (4, 14, 1, 2),
    "target_bases": (6, 14, 1, 2),
    "threat_min": (1, 5, 1, 1),
    "threat_hops": (1, 3, 1, 1),
}

ECON_RE = re.compile(
    r'"econ":\s*dict\(\s*'
    r'push_army=(\d+),\s*push_turn=(\d+),\s*hq_push_lv=(\d+),\s*garrison=(\d+),\s*wave=(\d+),\s*'
    r'hq_cap=(\d+),\s*target_bases=(\d+),\s*expand_parallel=(\d+),\s*half_ratio=([\d.]+),\s*'
    r'repair_turn=(\d+),\s*threat_hops=(\d+),\s*threat_min=(\d+),\s*\),',
    re.S,
)


def read_econ(src: str) -> dict:
    m = ECON_RE.search(src)
    if not m:
        raise SystemExit("econ 블록 패턴이 안 맞음 -- 정규식 갱신 필요")
    keys = ["push_army", "push_turn", "hq_push_lv", "garrison", "wave", "hq_cap",
            "target_bases", "expand_parallel", "half_ratio", "repair_turn",
            "threat_hops", "threat_min"]
    vals = m.groups()
    out = {}
    for k, v in zip(keys, vals):
        out[k] = float(v) if k == "half_ratio" else int(v)
    return out


def write_econ(src: str, params: dict) -> str:
    new_block = (
        '"econ": dict(\n'
        f'        push_army={params["push_army"]}, push_turn={params["push_turn"]}, '
        f'hq_push_lv={params["hq_push_lv"]}, garrison={params["garrison"]}, wave={params["wave"]},\n'
        f'        hq_cap={params["hq_cap"]}, target_bases={params["target_bases"]}, '
        f'expand_parallel={params["expand_parallel"]}, half_ratio={params["half_ratio"]},\n'
        f'        repair_turn={params["repair_turn"]}, threat_hops={params["threat_hops"]}, '
        f'threat_min={params["threat_min"]},\n    ),'
    )
    return ECON_RE.sub(new_block, src, count=1)


def mutate(base_params: dict, rng: random.Random) -> dict:
    p = dict(base_params)
    k = rng.choice(list(PARAM_SPACE.keys()))
    lo, hi, is_int, step = PARAM_SPACE[k]
    delta = rng.choice([-step, step, -step * 2, step * 2])
    p[k] = max(lo, min(hi, p[k] + delta))
    return p


def play(cand_path: pathlib.Path, base_path: pathlib.Path, n: int, seed0: int) -> tuple[int, int, int]:
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "evaluate.py"),
         "--bot", str(cand_path),
         "--opponent", f"{sys.executable} {base_path}",
         "--left-opponent", f"{sys.executable} {base_path}",
         "--side", "both", "--start", str(seed0), "--count", str(n),
         "--timeout", "60", "--name", f"autotune-{cand_path.stem}", "--quiet"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    out = r.stdout
    m = re.search(r"wins=(\d+) losses=(\d+) draws=(\d+)", out)
    if not m:
        return 0, 0, n * 2
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def main():
    rng = random.Random(20260706)
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    variants_per_round = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    games_per_test = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    base_src = BASE.read_text()
    best_params = read_econ(base_src)
    best_path = BASE
    seed_ctr = 5000

    print(f"시작 파라미터: {best_params}")
    for rnd in range(1, rounds + 1):
        print(f"\n=== 라운드 {rnd}/{rounds} ===")
        candidates = [mutate(best_params, rng) for _ in range(variants_per_round)]
        results = []
        for i, params in enumerate(candidates):
            cand_src = write_econ(base_src, params)
            cand_path = ROOT / "bots" / "variants" / f"tune_r{rnd}_{i}.py"
            cand_path.parent.mkdir(exist_ok=True)
            cand_path.write_text(cand_src)
            w, l, d = play(cand_path, best_path, games_per_test, seed_ctr)
            seed_ctr += games_per_test + 5
            ratio = w / max(1, l)
            print(f"  변이{i} {params}: {w}승{l}패{d}무 (비율 {ratio:.2f})")
            results.append((ratio, w, l, params, cand_path))

        results.sort(key=lambda r: -r[0])
        top_ratio, top_w, top_l, top_params, top_path = results[0]
        # 채택 기준: 승패 합 12판 이상 + 승패비 1.3 이상 (노이즈 배제)
        if top_ratio >= 1.3 and (top_w + top_l) >= 12:
            print(f"  -> 채택: {top_params} (비율 {top_ratio:.2f})")
            best_params = top_params
            base_src = write_econ(base_src, best_params)
            best_path = top_path
        else:
            print(f"  -> 이번 라운드 개선 없음 (최고 비율 {top_ratio:.2f}, 기준 1.3 미달)")

    print(f"\n=== 최종 파라미터 ===\n{best_params}")
    final_path = ROOT / "bots" / "58.py"
    final_path.write_text(base_src)
    print(f"저장: {final_path}")


if __name__ == "__main__":
    main()
