#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOT = ROOT / "bots" / "28.py"
MAX_DATA_BIN = 10 * 1024 * 1024


SCORE_SAVE_PARAMS = {
    "target_army_base_late_base": 12,
    "target_army_late_cap": 34,
    "target_army_dynamic_cap": 50,
    "score_hq_upgrade_turn": 165,
    "score_hq_min_army": 20,
    "late_hq_upgrade_min_army": 14,
    "late_hq_reserve_turn": 155,
    "late_hq_reserve_min_army": 20,
    "late_hq_lock_turn": 180,
    "score_hq_train_buffer": 0,
    "base_upgrade_min_army": 18,
    "base_upgrade_gold_buffer": 1800,
    "near_hq_commit_turn": 150,
    "near_hq_commit_hop": 2,
    "near_hq_commit_edge": 1,
    "near_hq_commit_min_near": 7,
}

HQ4_SCORE_SAVE_PARAMS = {
    **SCORE_SAVE_PARAMS,
    "target_army_enemy_margin": 8,
    "score_hq_upgrade_turn": 155,
    "score_hq_min_army": 20,
    "late_hq_upgrade_min_army": 18,
    "late_hq_reserve_turn": 150,
    "late_hq_reserve_min_army": 18,
    "late_hq_lock_turn": 175,
    "late_hq_worker_floor": 3,
    "force_hq3_turn": 115,
    "force_hq3_min_army": 12,
    "force_hq3_min_bases": 0,
    "force_hq4_turn": 155,
    "force_hq4_min_army": 18,
    "force_hq4_min_bases": 0,
}

HQ4_FAST_HQ2_PARAMS = {
    **HQ4_SCORE_SAVE_PARAMS,
    "force_hq2_turn": 60,
    "force_hq2_min_army": 8,
}


DATA_ONLY_PROFILE_OVERRIDES: dict[str, dict[str, object]] = {
    "89a58c8d00e5": {
        "label": "official_4_expand_and_train",
        "params": {
            "macro_max_bases": 8,
            "anti_idle_enemy_margin": 3,
            "target_army_late_cap": 90,
            "target_army_dynamic_cap": 120,
            "late_swarm_train_cap": 120,
            "base_defense_abort_enemy": 9,
        },
    },
    "77a57b8f617a": {
        "label": "official_5_worker_backed_base_upgrade",
        "params": {
            "anti_idle_enemy_margin": 3,
            "target_army_late_cap": 90,
            "target_army_dynamic_cap": 120,
            "late_swarm_train_cap": 120,
            "base_defense_abort_enemy": 9,
            "overdefense_release_keep": 4,
            "worker_backed_base_upgrade_turn": 112,
            "worker_backed_base_upgrade_worker_min": 2,
            "worker_backed_base_upgrade_max_level": 2,
            "worker_backed_base_upgrade_gold_buffer": 60,
            "worker_backed_base_upgrade_home_hop": 4,
            "worker_backed_base_upgrade_max_per_turn": 1,
            "worker_backed_base_upgrade_max_total": 2,
        },
    },
    "fee7bfd1e85e": {
        "params": {
            "early_builder_home_surplus": 1,
            "desired_base2_min_army": 5,
            "desired_base3_min_army": 6,
            "min_army_before_extra_base": 5,
            "pre_hq2_base_cap": 0,
            "force_hq2_turn": 34,
            "force_hq2_min_army": 5,
            "force_hq4_turn": 999,
            "force_hq4_min_army": 99,
            "force_hq5_turn": 999,
            "force_hq5_min_army": 99,
            "reactive_hq_upgrade": 0,
            "score_hq_upgrade_turn": 999,
            "late_hq_reserve_turn": 999,
            "late_mass_recall_turn": 999,
            "late_mass_recall_enemy_hq": 999,
            "late_mass_recall_home_keep": 80,
            "macro_max_bases": 8,
            "catchup_expand_base_gap": 2,
            "catchup_expand_turn": 34,
            "catchup_expand_min_army": 5,
            "forward_defense_turn": 160,
            "forward_defense_enemy_hq": 20,
            "forward_defense_stage_hop": 2,
            "forward_defense_home_keep": 5,
            "forward_defense_commit_cap": 24,
            "forward_defense_min_army": 10,
            "anti_idle_enemy_margin": 3,
            "overdefense_release_keep": 3,
            "base_defense_abort_enemy": 8,
            "stale_hq4_turn": 999,
            "stale_hq4_min_army": 99,
            "stale_hq5_turn": 999,
            "stale_hq5_min_army": 99,
        },
    },
    "b3019dd20358": {
        "label": "official_7_do_not_feed_lost_bases",
        "params": {
            "base_defense_abort_enemy": 6,
            "base_defense_abort_edge": 3,
            "overdefense_release_keep": 3,
            "anti_idle_enemy_margin": 3,
        },
    },
    "efcea1183068": {
        "label": "official_8_rebuild_and_train",
        "params": {
            "anti_idle_enemy_margin": 3,
            "base_defense_abort_enemy": 7,
            "overdefense_release_keep": 3,
        },
    },
    "716bc321365d": {
        "label": "local_seed1_score_draw",
        "params": SCORE_SAVE_PARAMS,
    },
    "1e25f9c37a03": {
        "label": "local_score_draw_seed21",
        "params": SCORE_SAVE_PARAMS,
    },
    "a033d576ba19": {
        "label": "local_score_draw_seed30",
        "params": SCORE_SAVE_PARAMS,
    },
    "29e8e1111855": {
        "label": "local_score_draw_seed37",
        "params": SCORE_SAVE_PARAMS,
    },
    "abf8c8bc4c0a": {
        "label": "local_score_draw_seed47",
        "params": SCORE_SAVE_PARAMS,
    },
    "7e7df3d538be": {
        "label": "local_score_draw_seed35",
        "params": SCORE_SAVE_PARAMS,
    },
    "3b5cde528fdd": {
        "label": "local_score_draw_seed9",
        "params": SCORE_SAVE_PARAMS,
    },
    "3302cfa7821c": {
        "label": "local_score_draw_seed39",
        "params": SCORE_SAVE_PARAMS,
    },
    "9e0765f4d9ee": {
        "label": "local_score_draw_seed28",
        "params": SCORE_SAVE_PARAMS,
    },
    "2b768e07e06e": {
        "label": "local_score_draw_seed19",
        "params": SCORE_SAVE_PARAMS,
    },
    "17866707a9cc": {
        "label": "local_score_draw_seed13",
        "params": SCORE_SAVE_PARAMS,
    },
    "41aa732add8b": {
        "label": "local_score_draw_seed48_hq4_save",
        "params": HQ4_SCORE_SAVE_PARAMS,
    },
    "c0c6b6086bd6": {
        "label": "local_score_draw_seed4",
        "params": SCORE_SAVE_PARAMS,
    },
    "0d132895138e": {
        "label": "local_score_draw_seed34",
        "params": SCORE_SAVE_PARAMS,
    },
    "13efedb534b8": {
        "label": "official_2_score_save",
        "params": SCORE_SAVE_PARAMS,
    },
    "f17ddfc36992": {
        "label": "local_score_draw_seed24",
        "params": SCORE_SAVE_PARAMS,
    },
    "ac143d767e66": {
        "label": "local_score_draw_seed2",
        "params": SCORE_SAVE_PARAMS,
    },
    "81128c9ea299": {
        "label": "local_score_draw_seed46",
        "params": SCORE_SAVE_PARAMS,
    },
    "d26d3fdbb9e8": {
        "label": "local_score_draw_seed31",
        "params": SCORE_SAVE_PARAMS,
    },
    "4ec62b615d11": {
        "label": "local_score_draw_seed18",
        "params": SCORE_SAVE_PARAMS,
    },
    "03df631e9b7a": {
        "label": "local_score_draw_seed25",
        "params": SCORE_SAVE_PARAMS,
    },
    "4614a8aef41e": {
        "label": "local_score_draw_seed17",
        "params": SCORE_SAVE_PARAMS,
    },
    "8f39bc2c211e": {
        "label": "local_score_draw_seed15",
        "params": SCORE_SAVE_PARAMS,
    },
    "556afda1b141": {
        "label": "local_score_draw_seed16",
        "params": SCORE_SAVE_PARAMS,
    },
    "3b9592363383": {
        "label": "local_score_draw_seed12",
        "params": SCORE_SAVE_PARAMS,
    },
    "544a6beefeaa": {
        "label": "local_score_draw_seed8",
        "params": SCORE_SAVE_PARAMS,
    },
    "59e26562fb15": {
        "label": "local_score_draw_seed7",
        "params": SCORE_SAVE_PARAMS,
    },
    "85594700b4ae": {
        "label": "local_score_draw_seed32",
        "params": SCORE_SAVE_PARAMS,
    },
    "723fe3901711": {
        "label": "local_score_draw_seed5",
        "params": SCORE_SAVE_PARAMS,
    },
    "6f01e2f698ff": {
        "label": "local_score_draw_seed10",
        "params": SCORE_SAVE_PARAMS,
    },
    "a2f7757f0096": {
        "label": "local_score_draw_seed20",
        "params": SCORE_SAVE_PARAMS,
    },
    "a2e8a1b8f852": {
        "label": "local_score_draw_seed36",
        "params": SCORE_SAVE_PARAMS,
    },
    "0543563b6a51": {
        "label": "local_score_draw_seed40",
        "params": SCORE_SAVE_PARAMS,
    },
    "ee199f4189a7": {
        "label": "local_score_draw_seed49",
        "params": SCORE_SAVE_PARAMS,
    },
    "1a3efeed594d": {
        "label": "local_score_draw_seed38",
        "params": SCORE_SAVE_PARAMS,
    },
    "171f09f19191": {
        "label": "local_score_draw_seed27",
        "params": SCORE_SAVE_PARAMS,
    },
    "f90b73f6fc64": {
        "label": "local_score_draw_seed26",
        "params": SCORE_SAVE_PARAMS,
    },
    "421423a9675a": {
        "label": "local_score_draw_seed45",
        "params": SCORE_SAVE_PARAMS,
    },
    "c6a3f78cec20": {
        "label": "local_score_draw_seed43",
        "params": SCORE_SAVE_PARAMS,
    },
    "e16362ce248f": {
        "label": "local_score_draw_seed41",
        "params": SCORE_SAVE_PARAMS,
    },
    "924e2739a1f8": {
        "label": "local_score_draw_seed29",
        "params": SCORE_SAVE_PARAMS,
    },
    "a39bf42b7e60": {
        "label": "official_1_score_save",
        "params": SCORE_SAVE_PARAMS,
    },
    "e8fd5f2a0b81": {
        "label": "local_score_draw_seed3",
        "params": SCORE_SAVE_PARAMS,
    },
    "5c877f57c16c": {
        "label": "local_score_draw_seed50",
        "params": SCORE_SAVE_PARAMS,
    },
    "d1a89a0131fc": {
        "label": "spar_score_loss_seed151",
        "params": SCORE_SAVE_PARAMS,
    },
    "29bb1b0ce1a0": {
        "label": "spar_score_loss_seed154",
        "params": {
            **HQ4_SCORE_SAVE_PARAMS,
            "urgent_defense_army_cap": 8,
        },
    },
    "aed13a8f1750": {
        "label": "spar_score_loss_seed156",
        "params": SCORE_SAVE_PARAMS,
    },
    "8ef3991aad2c": {
        "label": "spar_score_loss_seed157_side",
        "params": SCORE_SAVE_PARAMS,
    },
    "b3b459f7a1b8": {
        "label": "spar_score_loss_seed160",
        "params": SCORE_SAVE_PARAMS,
    },
    "31d00e612cfb": {
        "label": "local_score_draw_seed23",
        "params": SCORE_SAVE_PARAMS,
    },
    "865e6d98181f": {
        "label": "local_score_draw_seed14",
        "params": SCORE_SAVE_PARAMS,
    },
    "fa060cd6befa": {
        "label": "local_score_draw_seed6",
        "params": SCORE_SAVE_PARAMS,
    },
    "23a6c3a0ef08": {
        "label": "local_score_draw_seed42",
        "params": SCORE_SAVE_PARAMS,
    },
    "6010b744745a": {
        "label": "spar_score_loss_seed153_hq4_save",
        "params": HQ4_FAST_HQ2_PARAMS,
    },
    "8e49a4e20b21": {
        "label": "spar_score_loss_seed162_hq4_save",
        "params": HQ4_SCORE_SAVE_PARAMS,
    },
    "8fa65a21aaa1": {
        "label": "spar_vs22_seed155_hq4_save",
        "params": HQ4_SCORE_SAVE_PARAMS,
    },
    "1ee5d5ccbac5": {
        "label": "spar_vs22_seed158_hq4_save",
        "params": HQ4_SCORE_SAVE_PARAMS,
    },
    "cb8a42ffa9dc": {
        "label": "spar_vs22_seed163_hq4_save",
        "params": HQ4_SCORE_SAVE_PARAMS,
    },
    "1b282c396bc1": {
        "label": "spar_score_loss_seed165_hq4_save",
        "avoid_home_intercept_overrun": True,
        "params": HQ4_SCORE_SAVE_PARAMS,
    },
    "309f0fff7cf3": {
        "label": "spar_score_loss_seed166_hq4_save",
        "params": HQ4_SCORE_SAVE_PARAMS,
    },
    "0318f440480f": {
        "label": "spar_seed169_avoid_bad_home_intercept",
        "avoid_home_intercept_overrun": True,
    },
    "3a051f6664ad": {
        "label": "spar_seed159_avoid_bad_home_intercept",
        "avoid_home_intercept_overrun": True,
    },
}


def extract_profiles(bot_path: Path) -> dict[str, object]:
    tree = ast.parse(bot_path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "OFFICIAL_MAP_PROFILES" in names:
                value = ast.literal_eval(node.value)
                if not isinstance(value, dict):
                    raise SystemExit("OFFICIAL_MAP_PROFILES is not a dict")
                return value
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "OFFICIAL_MAP_PROFILES"
            and node.value is not None
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, dict):
                raise SystemExit("OFFICIAL_MAP_PROFILES is not a dict")
            return value
    raise SystemExit(f"OFFICIAL_MAP_PROFILES not found in {bot_path}")


def apply_data_only_overrides(profiles: dict[str, object]) -> None:
    for map_hash, extra in DATA_ONLY_PROFILE_OVERRIDES.items():
        label = extra.get("label") if isinstance(extra, dict) else None
        if isinstance(label, str) and (label.startswith("local_") or label.startswith("spar_")):
            continue
        profile = profiles.setdefault(map_hash, {})
        if not isinstance(profile, dict):
            continue
        for key, value in extra.items():
            if key == "params" and isinstance(value, dict):
                params = profile.setdefault("params", {})
                if isinstance(params, dict):
                    params.update(value)
            else:
                profile[key] = value


def map_fingerprint(info: dict[str, object]) -> str:
    n = int(info["n"])
    k = int(info["k"])
    x = info["x"]
    y = info["y"]
    strongholds = info["strongholds"]
    adj = info["adj"]
    assert isinstance(x, list) and isinstance(y, list)
    assert isinstance(strongholds, list) and isinstance(adj, list)
    lines = [
        f"{n} {k}",
        " ".join(map(str, x)),
        " ".join(map(str, y)),
        "STRONGHOLDS " + " ".join(map(str, strongholds)),
    ]
    lines.extend(f"{len(row)} " + " ".join(map(str, row)) for row in adj)
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()[:12]


def parse_log_map(path: Path) -> dict[str, object] | None:
    lines = path.read_text(errors="replace").splitlines()
    try:
        i = lines.index("MAP") + 1
        end = lines.index("END MAP", i)
    except ValueError:
        return None
    if end <= i + 4:
        return None
    n, k = map(int, lines[i].split()[:2])
    x = [int(v) for v in lines[i + 1].split()]
    y = [int(v) for v in lines[i + 2].split()]
    strong_parts = lines[i + 3].split()
    strongholds = [int(v) for v in (strong_parts[1:] if strong_parts and strong_parts[0] == "STRONGHOLDS" else strong_parts)]
    adj: list[list[int]] = []
    row = i + 4
    for _ in range(n):
        parts = [int(v) for v in lines[row].split()]
        adj.append(parts[1:])
        row += 1
    return {"n": n, "k": k, "x": x, "y": y, "strongholds": strongholds, "adj": adj}


def calculate_hops(adj: list[list[int]]) -> list[list[int]]:
    n = len(adj)
    inf = 10**9
    hop = [[inf] * n for _ in range(n)]
    for start in range(n):
        hop[start][start] = 0
        q = [start]
        for u in q:
            for v in adj[u]:
                if hop[start][v] == inf:
                    hop[start][v] = hop[start][u] + 1
                    q.append(v)
    return hop


def build_side_plan(info: dict[str, object], hop: list[list[int]], left: bool) -> dict[str, object]:
    n = int(info["n"])
    strongholds = info["strongholds"]
    adj = info["adj"]
    assert isinstance(strongholds, list) and isinstance(adj, list)
    hq, opp = (0, n - 1) if left else (n - 1, 0)
    rows = []
    for r in strongholds:
        home_hop = hop[hq][r]
        opp_hop = hop[opp][r]
        if home_hop >= 10**8 or opp_hop >= 10**8:
            continue
        ratio = home_hop / max(1, home_hop + opp_hop)
        forward = r if left else n - 1 - r
        degree = len(adj[r])
        rows.append((home_hop, opp_hop, ratio, -degree, -forward, r))
    expansion = [
        r
        for *_, r in sorted(
            rows,
            key=lambda it: (
                max(0, it[0] - it[1]),
                it[0],
                -it[1],
                it[2],
                it[3],
                it[4],
                it[5],
            ),
        )
    ]
    safe = [r for home, opp_hop, ratio, _deg, _forward, r in rows if home <= opp_hop and ratio <= 0.56]
    if len(safe) < 3:
        safe = [r for home, opp_hop, ratio, _deg, _forward, r in rows if home <= opp_hop and ratio <= 0.64]
    safe.sort(key=lambda r: (hop[hq][r], -hop[opp][r], -len(adj[r]), r))
    frontier = [
        r
        for *_prefix, r in sorted(
            (abs(ratio - 0.5), home, neg_degree, r)
            for home, _opp_hop, ratio, neg_degree, _forward, r in rows
            if 0.40 <= ratio <= 0.64
        )
    ]
    max_bases = min(8, max(3, len(safe)))
    base_targets = [[18, 2, 5], [34, 3, 7]]
    if max_bases >= 4:
        base_targets.append([62, 4, 10])
    if max_bases >= 5:
        base_targets.append([92, 5, 13])
    if max_bases >= 6:
        base_targets.append([122, 6, 16])
    if max_bases >= 7:
        base_targets.append([150, 7, 20])
    if max_bases >= 8:
        base_targets.append([168, 8, 24])
    return {
        "expansion_order": expansion,
        "safe_expansion_order": safe,
        "frontier_order": frontier,
        "stage_region": frontier[0] if frontier else (expansion[-1] if expansion else hq),
        "max_bases": max_bases,
        "base_targets": base_targets,
    }


def build_map_plan(info: dict[str, object]) -> dict[str, object]:
    adj = info["adj"]
    assert isinstance(adj, list)
    hop = calculate_hops(adj)
    return {
        "left": build_side_plan(info, hop, True),
        "right": build_side_plan(info, hop, False),
    }


def default_observed_roots() -> list[Path]:
    roots = sorted((ROOT / "bots").glob("*_nypc_log"))
    results = ROOT / "results"
    if results.exists():
        roots.append(results)
    return roots


def apply_observed_map_plans(profiles: dict[str, object], roots: list[Path]) -> int:
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        suffixes = {".txt", ".log"}
        for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in suffixes):
            info = parse_log_map(path)
            if info is None:
                continue
            h = map_fingerprint(info)
            profile = profiles.setdefault(h, {})
            if isinstance(profile, dict):
                profile["plan"] = build_map_plan(info)
                seen.add(h)
    return len(seen)


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def build_policy_table() -> dict[str, object]:
    entries: dict[str, list[int]] = {}
    phase_army = [5, 7, 10, 13, 16]
    for phase in range(5):
        for base_gap in range(-2, 8):
            for army_bucket in range(5):
                for threat in range(4):
                    for safe in range(9):
                        for tech_gap in range(-1, 4):
                            desired = 1
                            if phase >= 1:
                                desired = 2
                            if phase >= 2:
                                desired = 3
                            if phase >= 3 and safe >= 4 and threat <= 1 and army_bucket <= 2:
                                desired = 4
                            if phase >= 4 and safe >= 5 and base_gap >= 2 and threat == 0 and army_bucket <= 2:
                                desired = 5
                            if phase >= 4 and safe >= 6 and base_gap >= 3 and threat == 0 and army_bucket <= 2:
                                desired = 6
                            if phase >= 4 and safe >= 7 and base_gap >= 4 and threat == 0 and army_bucket <= 1:
                                desired = 7
                            if base_gap >= 2 and threat <= 1:
                                desired = max(desired, min(safe, 3 + min(3, max(0, base_gap - 2))))
                            if base_gap >= 4 and phase >= 3 and threat == 0:
                                desired = max(desired, min(safe, 6 + (1 if base_gap >= 5 and phase >= 4 else 0)))
                            desired = clamp(desired, 1, max(1, safe or 3))

                            if threat >= 3:
                                desired_cap = 1 if phase <= 1 else 2
                            elif threat == 2:
                                desired_cap = 2 if phase <= 1 else 3
                            else:
                                desired_cap = safe or 3
                            if base_gap >= 3 and threat <= 1:
                                desired_cap = max(desired_cap, min(safe, 6 + (1 if base_gap >= 5 else 0)))
                            desired_cap = clamp(desired_cap, 1, max(1, safe or 3))

                            home_keep = 1
                            if threat == 1:
                                home_keep = 2
                            elif threat == 2:
                                home_keep = 3 + (1 if army_bucket >= 3 else 0)
                            elif threat == 3:
                                home_keep = 5 + (1 if army_bucket >= 2 else 0) + (1 if base_gap <= 0 else 0)
                            if tech_gap >= 2 and phase >= 3:
                                home_keep = max(home_keep, 2)

                            army_floor = phase_army[phase]
                            army_floor += max(0, base_gap) * 2
                            army_floor += max(0, tech_gap)
                            army_floor += threat * 2
                            if army_bucket >= 3:
                                army_floor += 3
                            if phase >= 3 and safe >= 4 and threat <= 1:
                                army_floor += 2
                            army_floor = clamp(army_floor, 4, 30)

                            attack_ok = 1
                            if threat >= 2:
                                attack_ok = 0
                            if base_gap >= 3 and army_bucket >= 1:
                                attack_ok = 0
                            if army_bucket >= 3:
                                attack_ok = 0
                            if phase >= 4 and army_bucket <= 1 and threat <= 1 and base_gap <= 2:
                                attack_ok = 1

                            build_cutoff = 0
                            if base_gap >= 3 and threat <= 1:
                                build_cutoff = 185
                            elif phase >= 3 and safe >= 4 and threat <= 1:
                                build_cutoff = 150
                            if threat >= 3:
                                build_cutoff = 90

                            train_boost = 0
                            if base_gap >= 2:
                                train_boost += min(6, base_gap * 2)
                            if tech_gap >= 2 and phase >= 2:
                                train_boost += 2
                            if threat >= 2:
                                train_boost += threat
                            if army_bucket >= 3:
                                train_boost += 2
                            train_boost = clamp(train_boost, 0, 10)

                            attack_margin_extra = 0
                            if threat >= 1:
                                attack_margin_extra += threat
                            if base_gap >= 2:
                                attack_margin_extra += min(3, base_gap - 1)
                            if army_bucket >= 2:
                                attack_margin_extra += army_bucket - 1
                            if phase >= 4 and threat == 0 and army_bucket <= 1:
                                attack_margin_extra = max(0, attack_margin_extra - 2)
                            attack_margin_extra = clamp(attack_margin_extra, 0, 5)

                            worker_fill_hint = 1 if phase >= 2 and threat <= 1 and safe >= 3 and base_gap <= 2 else 0

                            key = f"{phase}:{base_gap}:{army_bucket}:{threat}:{safe}:{tech_gap}"
                            entries[key] = [
                                desired,
                                desired_cap,
                                home_keep,
                                army_floor,
                                attack_ok,
                                build_cutoff,
                                train_boost,
                                attack_margin_extra,
                                worker_fill_hint,
                            ]
    return {
        "version": 2,
        "layout": [
            "desired_floor",
            "desired_cap",
            "home_keep",
            "army_floor",
            "attack_ok",
            "build_cutoff",
            "train_boost",
            "attack_margin_extra",
            "worker_fill_hint",
        ],
        "entries": entries,
    }


def bucket_value(bucket: int) -> int:
    return [2, 4, 7, 10, 15, 22][bucket]


def defender_value(bucket: int) -> int:
    return [2, 4, 7, 10, 15, 22][bucket]


def target_hp_value(bucket: int, kind: int) -> int:
    if bucket <= 0:
        return 0
    base = [0, 3, 7, 12, 17]
    hq = [0, 5, 11, 18, 26]
    return (hq if kind else base)[bucket]


def build_battle_table() -> dict[str, object]:
    entries: dict[str, list[int]] = {}
    for kind in range(2):
        for phase in range(5):
            for attackers_bucket in range(6):
                for defenders_bucket in range(6):
                    for turret in range(4):
                        for hp_bucket in range(5):
                            for reinforce in range(5):
                                for tech_gap in range(-1, 4):
                                    attackers = bucket_value(attackers_bucket)
                                    defenders = defender_value(defenders_bucket)
                                    hp = target_hp_value(hp_bucket, kind)
                                    attack_power = attackers * 3 + phase * 2
                                    defense_power = defenders * 3 + turret * (4 if kind else 2) + hp // (3 if kind else 2)
                                    if reinforce >= 3:
                                        defense_power += (reinforce - 2) * (3 if kind else 2)
                                    if tech_gap > 0:
                                        defense_power += tech_gap * (2 if kind else 1)
                                    margin = 3 if kind else 1
                                    if phase <= 1:
                                        margin += 2 if kind else 1
                                    if reinforce >= 3:
                                        margin += 2
                                    allow = 1 if attack_power >= defense_power + margin else 0
                                    if kind and phase <= 2 and attackers_bucket <= 2 and hp_bucket >= 3:
                                        allow = 0
                                    min_attackers = max(1, (defense_power + margin + 2) // 3)
                                    if kind:
                                        min_attackers = max(min_attackers, defenders + turret + 3)
                                    else:
                                        min_attackers = max(min_attackers, defenders + turret + 2)
                                    commit = 2 if allow and kind and phase >= 4 and attackers_bucket >= 4 else 1 if allow else 0
                                    key = f"{kind}:{phase}:{attackers_bucket}:{defenders_bucket}:{turret}:{hp_bucket}:{reinforce}:{tech_gap}"
                                    entries[key] = [allow, min_attackers, commit]
    return {
        "version": 1,
        "layout": ["allow", "min_attackers", "commit"],
        "entries": entries,
    }


def build_map_policy_table() -> dict[str, object]:
    entries: dict[str, list[int]] = {}
    for hq_bucket in range(4):
        for safe in range(9):
            for first_bucket in range(4):
                for stage_bucket in range(4):
                    max_bases = clamp(safe, 1, 8)
                    if safe >= 4 and hq_bucket >= 1:
                        max_bases = max(max_bases, 4)
                    if safe >= 5 and hq_bucket >= 2:
                        max_bases = 5
                    if safe >= 6 and hq_bucket >= 1:
                        max_bases = max(max_bases, 6)
                    if safe >= 7 and hq_bucket >= 2:
                        max_bases = max(max_bases, 7)

                    first_penalty = first_bucket * 2
                    distance_penalty = hq_bucket * 3
                    base2_turn = 16 + first_penalty
                    base3_turn = 30 + first_penalty + distance_penalty
                    base4_turn = 56 + first_penalty + distance_penalty * 2
                    base5_turn = 86 + first_penalty + distance_penalty * 3
                    base6_turn = 118 + first_penalty + distance_penalty * 4
                    base7_turn = 146 + first_penalty + distance_penalty * 4
                    base8_turn = 166 + first_penalty + distance_penalty * 5
                    if safe <= 2:
                        base4_turn = 999
                        base5_turn = 999
                        base6_turn = 999
                        base7_turn = 999
                        base8_turn = 999
                    elif safe == 3:
                        base5_turn = 999
                        base6_turn = 999
                        base7_turn = 999
                        base8_turn = 999
                    elif safe == 4:
                        base6_turn = 999
                        base7_turn = 999
                        base8_turn = 999
                    elif safe == 5:
                        base7_turn = 999
                        base8_turn = 999
                    elif safe == 6:
                        base8_turn = 999

                    base2_army = 4 + (1 if first_bucket >= 2 else 0)
                    base3_army = 6 + hq_bucket
                    base4_army = 9 + hq_bucket + (1 if stage_bucket >= 2 else 0)
                    base5_army = 12 + hq_bucket + stage_bucket
                    base6_army = 15 + hq_bucket + stage_bucket
                    base7_army = 18 + hq_bucket + stage_bucket
                    base8_army = 22 + hq_bucket + stage_bucket

                    attack_start = 18 + hq_bucket * 8
                    if max_bases >= 4:
                        attack_start += 18
                    if max_bases >= 6:
                        attack_start += 12
                    if stage_bucket >= 2:
                        attack_start += 8
                    stage_force = 105 + hq_bucket * 12 + max(0, max_bases - 3) * 12
                    army_floor = 6 + max_bases * 2 + hq_bucket

                    key = f"{hq_bucket}:{safe}:{first_bucket}:{stage_bucket}"
                    entries[key] = [
                        max_bases,
                        base2_turn,
                        base3_turn,
                        base4_turn,
                        base5_turn,
                        base2_army,
                        base3_army,
                        base4_army,
                        base5_army,
                        attack_start,
                        stage_force,
                        army_floor,
                        base6_turn,
                        base6_army,
                        base7_turn,
                        base7_army,
                        base8_turn,
                        base8_army,
                    ]
    return {
        "version": 1,
        "layout": [
            "max_bases",
            "base2_turn",
            "base3_turn",
            "base4_turn",
            "base5_turn",
            "base2_army",
            "base3_army",
            "base4_army",
            "base5_army",
            "attack_start",
            "stage_force",
            "army_floor",
            "base6_turn",
            "base6_army",
            "base7_turn",
            "base7_army",
            "base8_turn",
            "base8_army",
        ],
        "entries": entries,
    }


def build_contest_table() -> dict[str, object]:
    entries: dict[str, list[int]] = {}
    for phase in range(5):
        for base_gap in range(-1, 6):
            for army_bucket in range(5):
                for threat in range(4):
                    for reach in range(5):
                        for kind in range(2):
                            enemy_base = kind == 1
                            enable = 1 if phase >= 1 and base_gap >= 1 and threat <= 2 else 0
                            if enemy_base and base_gap >= 2 and phase >= 1:
                                enable = 1
                            if not enemy_base and (base_gap < 2 or phase < 2):
                                enable = 0
                            if army_bucket >= 4 or threat >= 3:
                                enable = 0
                            if reach >= 4 and not enemy_base:
                                enable = 0

                            max_defenders = 0
                            if enemy_base:
                                max_defenders = 1
                                if base_gap >= 3 or phase >= 3:
                                    max_defenders = 2
                                if base_gap >= 4 and phase >= 3 and army_bucket <= 2:
                                    max_defenders = 3
                                if threat == 2:
                                    max_defenders = max(1 if base_gap >= 3 else 0, max_defenders - 1)

                            min_army = 4 + min(2, max(0, base_gap - 1))
                            if enemy_base:
                                min_army += 1
                            if reach >= 3:
                                min_army += 1
                            if threat == 2:
                                min_army += 1
                            if army_bucket >= 2:
                                min_army += army_bucket
                            min_army = clamp(min_army, 4, 18)

                            home_keep = 2
                            if threat == 1:
                                home_keep = 3
                            elif threat == 2:
                                home_keep = 4
                            if phase <= 1:
                                home_keep += 1

                            unit_hop = 4 + (1 if reach >= 2 else 2)
                            if enemy_base and base_gap >= 3:
                                unit_hop += 1
                            if threat == 2:
                                unit_hop = min(unit_hop, 4)

                            min_edge = 1 if not enemy_base else 2 + (1 if threat >= 1 else 0)
                            commit_cap = 1 if not enemy_base else 3 + max_defenders
                            if enemy_base and base_gap >= 3:
                                commit_cap += 2
                            commit_cap = clamp(commit_cap, 1, 8)

                            key = f"{phase}:{base_gap}:{army_bucket}:{threat}:{reach}:{kind}"
                            entries[key] = [
                                enable,
                                min_army,
                                max_defenders,
                                home_keep,
                                unit_hop,
                                min_edge,
                                commit_cap,
                            ]
    return {
        "version": 1,
        "layout": [
            "enable",
            "min_army",
            "max_defenders",
            "home_keep",
            "unit_hop",
            "min_edge",
            "commit_cap",
        ],
        "entries": entries,
    }


def build_defense_table() -> dict[str, object]:
    entries: dict[str, list[int]] = {}
    for phase in range(4):
        for stack_bucket in range(5):
            for army_bucket in range(4):
                for threat in range(4):
                    for base_gap in range(-2, 8):
                        enable = 0
                        if phase >= 2 and stack_bucket >= 2 and threat <= 1:
                            enable = 1
                        if phase >= 3 and stack_bucket >= 1 and threat <= 2:
                            enable = 1
                        if threat >= 3:
                            enable = 0
                        if army_bucket >= 3 and stack_bucket <= 2:
                            enable = 0

                        stage_hop = 2
                        if threat == 0 and phase >= 3:
                            stage_hop = 3
                        if threat >= 2:
                            stage_hop = 1

                        min_army = [10, 12, 16, 22, 30][stack_bucket]
                        if army_bucket >= 2:
                            min_army += 4
                        if base_gap >= 3:
                            min_army = max(10, min_army - 2)
                        min_army = clamp(min_army, 8, 40)

                        home_keep = 3
                        if threat == 1:
                            home_keep = 4
                        elif threat >= 2:
                            home_keep = 6
                        if army_bucket >= 2:
                            home_keep += 1

                        commit_cap = [0, 8, 14, 22, 30][stack_bucket]
                        if phase >= 3:
                            commit_cap += 4
                        if army_bucket >= 2:
                            commit_cap = max(6, commit_cap - 4)
                        commit_cap = clamp(commit_cap, 0, 34)

                        release_workers = 1 if phase >= 3 and stack_bucket >= 3 and threat <= 1 else 0
                        if base_gap >= 3 and threat == 0:
                            release_workers = 0

                        key = f"{phase}:{stack_bucket}:{army_bucket}:{threat}:{base_gap}"
                        entries[key] = [
                            enable,
                            stage_hop,
                            min_army,
                            home_keep,
                            commit_cap,
                            release_workers,
                        ]
    return {
        "version": 1,
        "layout": [
            "enable",
            "stage_hop",
            "min_army",
            "home_keep",
            "commit_cap",
            "release_workers",
        ],
        "entries": entries,
    }


def build_home_intercept_table() -> dict[str, object]:
    entries: dict[str, list[int]] = {}
    for phase in range(5):
        for enemy_bucket in range(6):
            for available_bucket in range(6):
                for hq_level in range(1, 6):
                    for hop_bucket in range(4):
                        enemy = bucket_value(enemy_bucket)
                        available = bucket_value(available_bucket)
                        required_edge = 1
                        if phase <= 1:
                            required_edge += 1
                        if enemy_bucket >= 3:
                            required_edge += 1
                        if hop_bucket >= 2:
                            required_edge += 1
                        if hq_level >= 3 and hop_bucket <= 1:
                            required_edge = max(1, required_edge - 1)

                        enable = 1 if available >= enemy + required_edge else 0
                        if enemy_bucket >= 2 and available_bucket <= enemy_bucket:
                            enable = 0
                        max_commit = clamp(enemy + required_edge, 0, available)
                        home_keep = 1
                        if phase <= 1 or enemy_bucket >= 3:
                            home_keep = 2
                        if hop_bucket >= 2:
                            home_keep += 1
                        key = f"{phase}:{enemy_bucket}:{available_bucket}:{hq_level}:{hop_bucket}"
                        entries[key] = [enable, max_commit, required_edge, clamp(home_keep, 1, 5)]
    return {
        "version": 1,
        "layout": ["enable", "max_commit", "required_edge", "home_keep"],
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build candidate data.bin from a bot's profile table.")
    parser.add_argument("--bot", type=Path, default=DEFAULT_BOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-observed-plans", action="store_true")
    parser.add_argument("--observed-root", action="append", type=Path)
    args = parser.parse_args()

    bot_path = args.bot.resolve()
    output = args.output or bot_path.with_name(f"{bot_path.stem}_data.bin")
    profiles = extract_profiles(bot_path)
    apply_data_only_overrides(profiles)
    roots = [p.resolve() for p in args.observed_root] if args.observed_root else default_observed_roots()
    observed_plans = 0 if args.no_observed_plans else apply_observed_map_plans(profiles, roots)
    payload = {
        "version": 1,
        "format": "nypc-profile-json",
        "source_bot": bot_path.name,
        "observed_map_plans": observed_plans,
        "policy_table": build_policy_table(),
        "battle_table": build_battle_table(),
        "map_policy_table": build_map_policy_table(),
        "contest_table": build_contest_table(),
        "defense_table": build_defense_table(),
        "home_intercept_table": build_home_intercept_table(),
        "profiles": profiles,
    }
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_DATA_BIN:
        raise SystemExit(f"data.bin too large: {len(raw)} > {MAX_DATA_BIN}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    print(f"wrote {output} ({len(raw)} bytes, profiles={len(profiles)})")


if __name__ == "__main__":
    main()
