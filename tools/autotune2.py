#!/usr/bin/env python3
"""넓은 무작위 탐색 (좌표하강이 아니라 전체 공간 랜덤 샘플링).

60.py(gate=20 챔피언) 기준, STYLES['econ']을 넓은 범위에서 무작위로 여러 개
뽑아 econ 프록시(비대칭 상대, 아직 승률 여유 있음)와 직접 대결시킨다.
"""
from __future__ import annotations
import random, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "bots" / "60.py"
OPP = f"{sys.executable} {ROOT / 'opponents' / 'proxy.py'} econ"

PARAM_RANGES = {
    "push_army": (14, 36),
    "push_turn": (110, 165),
    "garrison": (0, 4),
    "wave": (5, 12),
    "target_bases": (7, 13),
    "threat_min": (1, 4),
    "threat_hops": (1, 3),
}

ECON_RE = re.compile(
    r'"econ":\s*dict\(\s*'
    r'push_army=(\d+),\s*push_turn=(\d+),\s*hq_push_lv=(\d+),\s*garrison=(\d+),\s*wave=(\d+),\s*'
    r'hq_cap=(\d+),\s*target_bases=(\d+),\s*expand_parallel=(\d+),\s*half_ratio=([\d.]+),\s*'
    r'repair_turn=(\d+),\s*threat_hops=(\d+),\s*threat_min=(\d+),\s*\),',
    re.S,
)
KEYS = ["push_army", "push_turn", "hq_push_lv", "garrison", "wave", "hq_cap",
        "target_bases", "expand_parallel", "half_ratio", "repair_turn",
        "threat_hops", "threat_min"]


def read_econ(src):
    m = ECON_RE.search(src)
    return {k: (float(v) if k == "half_ratio" else int(v)) for k, v in zip(KEYS, m.groups())}


def write_econ(src, params):
    block = (
        '"econ": dict(\n'
        f'        push_army={params["push_army"]}, push_turn={params["push_turn"]}, '
        f'hq_push_lv={params["hq_push_lv"]}, garrison={params["garrison"]}, wave={params["wave"]},\n'
        f'        hq_cap={params["hq_cap"]}, target_bases={params["target_bases"]}, '
        f'expand_parallel={params["expand_parallel"]}, half_ratio={params["half_ratio"]},\n'
        f'        repair_turn={params["repair_turn"]}, threat_hops={params["threat_hops"]}, '
        f'threat_min={params["threat_min"]},\n    ),'
    )
    return ECON_RE.sub(block, src, count=1)


def random_config(base, rng):
    p = dict(base)
    for k, (lo, hi) in PARAM_RANGES.items():
        p[k] = rng.randint(lo, hi)
    return p


def play_head_to_head(cand_path, base_path, n, seed0):
    # 직접대결 -- 같은 시드에서 후보/기준이 동시에 겨루므로 시드 난이도
    # 편향이 자동 상쇄된다 (프록시 별도비교는 시드범위 편향 위험 -- 실측됨).
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "evaluate.py"),
         "--bot", str(cand_path),
         "--opponent", f"{sys.executable} {base_path}",
         "--left-opponent", f"{sys.executable} {base_path}",
         "--side", "both", "--start", str(seed0), "--count", str(n),
         "--timeout", "60", "--name", f"at2-{cand_path.stem}", "--quiet"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    m = re.search(r"wins=(\d+) losses=(\d+) draws=(\d+)", r.stdout)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, n * 2)


def main():
    rng = random.Random(777)
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    games = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    base_src = BASE.read_text()
    base_params = read_econ(base_src)
    best = (1.0, base_params, BASE)
    for i in range(trials):
        params = random_config(base_params, rng)
        cand_src = write_econ(base_src, params)
        cand_path = ROOT / "bots" / "variants" / f"wide_{i}.py"
        cand_path.parent.mkdir(exist_ok=True)
        cand_path.write_text(cand_src)
        # 매 변이마다 새 시드 블록 사용 (변이 간에는 달라도 되지만, 후보 vs
        # 기준은 반드시 같은 시드에서 -- 직접대결이라 이미 보장됨)
        w, l, d = play_head_to_head(cand_path, BASE, games, 9500 + i * (games + 5))
        ratio = w / max(1, l)
        flag = ""
        if ratio > best[0] and (w + l) >= 10:
            best = (ratio, params, cand_path)
            flag = " <- 신기록"
        print(f"[{i}] {params}: {w}승{l}패{d}무 (비율 {ratio:.2f}){flag}")

    print(f"\n최종 최선: 비율 {best[0]:.2f}")
    print(best[1])
    print(f"경로: {best[2]}")


if __name__ == "__main__":
    main()
