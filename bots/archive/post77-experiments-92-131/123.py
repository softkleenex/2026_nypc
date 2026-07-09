#!/usr/bin/env python3
"""NYPC 2026 Code Battle bot."""
from __future__ import annotations

import heapq
import math
import sys

MOVE_COST = 10
TRAIN_COST = 120
WORK_INCOME = 15
UPKEEP = 2

# level -> (upgrade_cost, warrior_hp, max_hp, turret, train_cap, work_cap)
HQ_LV = {
    1: (0, 4, 10, 1, 1, 1),
    2: (600, 5, 15, 2, 1, 2),
    3: (1200, 6, 20, 2, 2, 3),
    4: (2400, 7, 25, 3, 2, 4),
    5: (3600, 8, 30, 3, 3, 5),
}
HQ_REPAIR_COST = 1000
# level -> (cost, max_hp, turret, work_cap)
BASE_LV = {
    1: (300, 6, 1, 1),
    2: (600, 12, 1, 2),
    3: (1000, 18, 2, 3),
}
BASE_REPAIR_COST = 500

STYLES = {
    "econ": dict(
        push_army=24, push_turn=150, hq_push_lv=4, garrison=2, wave=8,
        hq_cap=5, target_bases=10, expand_parallel=2, half_ratio=1.0,
        repair_turn=184, threat_hops=2, threat_min=3,
    ),
    "turtle": dict(
        push_army=40, push_turn=168, hq_push_lv=5, garrison=4, wave=10,
        hq_cap=5, target_bases=8, expand_parallel=2, half_ratio=0.95,
        repair_turn=176, threat_hops=3, threat_min=2,
    ),
    "rush": dict(
        push_army=7, push_turn=45, hq_push_lv=1, garrison=1, wave=4,
        hq_cap=2, target_bases=2, expand_parallel=1, half_ratio=0.7,
        repair_turn=188, threat_hops=2, threat_min=4,
    ),
}


def readln() -> str:
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return line.rstrip("\n")


class Bot:
    def __init__(self, style: str) -> None:
        self.p = STYLES[style]
        self.turn = 0
        self.attacking = False
        # warriors: id_str -> [region, hp, moving, move_target]
        self.mine: dict[str, list] = {}
        self.enemy: dict[str, list] = {}
        # buildings: region -> [side_char, is_hq, level, hp]
        self.buildings: dict[int, list] = {}
        self.gold = 500

    # ---------- init ----------

    def read_init(self) -> None:
        t = readln().split()
        self.side = "A" if t[1] == "LEFT" else "B"
        self.foe = "B" if self.side == "A" else "A"
        t = readln().split()
        self.N, self.K = int(t[0]), int(t[1])
        self.x = [int(v) for v in readln().split()]
        self.y = [int(v) for v in readln().split()]
        self.strongholds = sorted(int(v) for v in readln().split())
        self.adj: list[list[int]] = []
        for _ in range(self.N):
            t = [int(v) for v in readln().split()]
            self.adj.append(sorted(t[1:1 + t[0]]))
        # 미러 정규화: RIGHT면 내부적으로 지역을 뒤집어 항상 LEFT 시점.
        # 점대칭+x오름차순 넘버링이라 뒤집힌 맵 배열은 원본과 동일하다.
        self.flip = self.side == "B"
        self.my_hq = 0
        self.opp_hq = self.N - 1

        for i in range(1, 4):
            self.mine[f"{self.side}{i}"] = [self.my_hq, 4, False, self.my_hq]
            self.enemy[f"{self.foe}{i}"] = [self.opp_hq, 4, False, self.opp_hq]
        self.buildings[self.my_hq] = [self.side, True, 1, 10]
        self.buildings[self.opp_hq] = [self.foe, True, 1, 10]

        self.dist = [self._dijkstra(s) for s in range(self.N)]
        self.hops = [self._bfs(s) for s in range(self.N)]
        self.unknown_map = True
        self.mp = dict(chip=True)  # 칩은 지고/비길 때만 발동하는 안전 규칙
        print("OK", flush=True)

    def _sim_fight(self, my_hps, en_hps, my_turret=0, en_turret=0,
                   en_bldg_hp=0, my_bldg_hp=0):
        """한 구역 1턴 전투 결과 예측 (룰 §7). 반환: (내 생존수, 적 생존수,
        내가 넣은 공성, 적이 넣은 공성). 공격 횟수는 시작 시점 고정."""
        mine = sorted(my_hps); enemy = sorted(en_hps)
        my_atk = len(mine) + (my_turret if my_bldg_hp > 0 else 0)
        en_atk = len(enemy) + (en_turret if en_bldg_hp > 0 else 0)
        my_siege = en_siege = 0
        for _ in range(my_atk):
            if enemy and enemy[0] > 0:
                enemy[0] -= 1
                if enemy[0] == 0: enemy.pop(0)
                enemy.sort()
            elif en_bldg_hp - my_siege > 0:
                my_siege += 1
        for _ in range(en_atk):
            if mine and mine[0] > 0:
                mine[0] -= 1
                if mine[0] == 0: mine.pop(0)
                mine.sort()
            elif my_bldg_hp - en_siege > 0:
                en_siege += 1
        return len(mine), len(enemy), my_siege, en_siege

    def _tr(self, r: int) -> int:
        return self.N - 1 - r if self.flip else r

    def _dijkstra(self, src: int) -> list[float]:
        dist = [math.inf] * self.N
        dist[src] = 0.0
        pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v in self.adj[u]:
                w = math.ceil(math.hypot(self.x[u] - self.x[v], self.y[u] - self.y[v]))
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist

    def _bfs(self, src: int) -> list[int]:
        hops = [-1] * self.N
        hops[src] = 0
        q = [src]
        for u in q:
            for v in self.adj[u]:
                if hops[v] < 0:
                    hops[v] = hops[u] + 1
                    q.append(v)
        return hops

    def route_steps(self, src: int, target: int) -> int:
        steps = 0
        cur = src
        while cur != target and steps <= self.N:
            best_v = -1
            best_score = math.inf
            for v in self.adj[cur]:
                score = math.ceil(math.hypot(self.x[cur] - self.x[v],
                                             self.y[cur] - self.y[v])) + self.dist[target][v]
                if (score < best_score
                        or (score == best_score
                            and (best_v < 0
                                 or (v > best_v if self.flip else v < best_v)))):
                    best_score = score
                    best_v = v
            if best_v < 0 or self.dist[target][best_v] == math.inf:
                return 10**9
            cur = best_v
            steps += 1
        return steps if cur == target else 10**9

    # ---------- helpers ----------

    def my_at(self, r: int) -> list[str]:
        return [w for w, s in self.mine.items() if s[0] == r]

    def enemy_count_at(self, r: int) -> int:
        return sum(1 for s in self.enemy.values() if s[0] == r)

    def work_cap(self, b: list) -> int:
        return HQ_LV[b[2]][5] if b[1] else BASE_LV[b[2]][3]

    def my_buildings(self) -> list[tuple[int, list]]:
        return [(r, b) for r, b in self.buildings.items() if b[0] == self.side]

    # ---------- planning ----------

    def plan(self) -> list[str]:
        p = self.p
        cmds: list[str] = []
        alive = len(self.mine)
        reserve = UPKEEP * alive + 30
        gold = self.gold
        upgraded: set[int] = set()
        planned_builds: set[int] = set()

        def can_upgrade_region(r: int) -> bool:
            if r in upgraded:
                return False
            if not self.my_at(r) or self.enemy_count_at(r):
                return False
            b = self.buildings.get(r)
            return b is None or b[0] == self.side

        def do_upgrade(r: int, cost: int) -> None:
            nonlocal gold
            cmds.append(f"UPGRADE {self._tr(r)}")
            upgraded.add(r)
            gold -= cost

        # ---------- 위협 평가 (지출 우선순위가 여기 의존) ----------
        enemy_forward: dict[int, int] = {}
        for s in self.enemy.values():
            if self.dist[self.my_hq][s[0]] < self.dist[self.opp_hq][s[0]]:
                enemy_forward[s[0]] = enemy_forward.get(s[0], 0) + 1
        invaders = 0
        for r, n in enemy_forward.items():
            b = self.buildings.get(r)
            if b is not None and b[0] == self.foe:
                n = max(0, n - self.work_cap(b))
            invaders += n
        invaded = invaders >= 8    # 침공(웨이브 규모): 소개 + 본부 농성
        raided = invaders >= 3     # 소규모 습격: 병력으로 요격
        # 조기 강습 요새화 (미지맵): T30~70 창의 병력 우위 강습 대응.
        # 노동자 소개/경제 큐가 이 플래그를 쓰므로 여기(상단)서 계산한다.
        early_fortress = (getattr(self, "unknown_map", False)
                          and self.turn < 70
                          and len(self.enemy) >= len(self.mine) + 3
                          and invaders >= 3)
        # 지속 침공 동결 카운터: 적이 우리 반경에 대군을 상시 주둔시키고
        # 매크로에서도 크게 앞서면, 농성은 천천히 죽는 확정 패배다.
        # 그때 적의 집은 비어 있는 경우가 많으므로 카운터 레이스로 전환한다.
        self.inv_streak = getattr(self, "inv_streak", 0)
        self.inv_streak = self.inv_streak + 1 if invaders >= 6 else 0
        n_my_bases = sum(1 for _, b in self.my_buildings() if not b[1])
        n_en_bases = sum(1 for b in self.buildings.values()
                         if b[0] == self.foe and not b[1])
        self._desp_latch = getattr(self, "_desp_latch", False) or (
            getattr(self, "unknown_map", False)
            and self.inv_streak >= 15 and self.turn >= 80
            and n_en_bases >= n_my_bases + 3)
        if self._desp_latch:
            def race_steps(pool: dict[str, list], target: int,
                           blockers: dict[str, list]) -> int:
                best = 10**9
                for s in pool.values():
                    block_delay = 1 if any(x[0] == s[0] for x in blockers.values()) else 0
                    if s[2]:
                        first = s[3]
                        steps = self.route_steps(s[0], first)
                        if steps < 10**9 and first != target:
                            steps += self.route_steps(first, target)
                    else:
                        steps = self.route_steps(s[0], target)
                    best = min(best, block_delay + steps)
                return best

            my_race = race_steps(self.mine, self.opp_hq, self.enemy)
            enemy_race = race_steps(self.enemy, self.my_hq, self.mine)
            desperate = my_race <= enemy_race + 1
        else:
            desperate = False
        def enemy_pressure_at(origin: int, k: int) -> int:
            by_region: dict[int, int] = {}
            recent_enemy_step = getattr(self, "_enemy_step", {})
            for wid, s in self.enemy.items():
                h = self.hops[origin][s[0]]
                projected = False
                step = recent_enemy_step.get(wid)
                if self.turn >= 140 and step is not None:
                    old_r, new_r = step
                    projected = (
                        new_r == s[0] and 0 <= h <= k + 1
                        and self.dist[origin][new_r] < self.dist[origin][old_r]
                    )
                if 0 <= h <= k or projected:
                    by_region[s[0]] = by_region.get(s[0], 0) + 1
            pressure = 0
            for r, n in by_region.items():
                b = self.buildings.get(r)
                if b is not None and b[0] == self.foe:
                    n = max(0, n - self.work_cap(b))
                pressure += n
            return pressure

        def enemy_pressure_near(k: int) -> int:
            return enemy_pressure_at(self.my_hq, k)

        near_enemy = enemy_pressure_near(p["threat_hops"])
        # 초반 러시 감지: 개막 직후 적 전사가 내 쪽 절반 가까이 들어오면
        # 확장을 멈추고 집을 지킨다.
        rush_alert = self.turn < 30 and any(
            self.dist[self.my_hq][s[0]] < 0.45 * self.dist[self.my_hq][self.opp_hq]
            for s in self.enemy.values()
        )
        # 올인 러시 감지:
        # T8까지 적 총병력 5+는 전병력 러시의 텔이다. 감지 시 기지 건설을
        # 멈추고 전액 훈련한다.
        _adv = sum(
            1 for w in self.enemy.values()
            if self.dist[self.opp_hq][w[0]] > 0.35 * self.dist[self.my_hq][self.opp_hq]
        )
        _early_mass = len(self.enemy) >= 5 and self.turn <= 8
        allin_alert = (getattr(self, "unknown_map", False)
                       and self.turn <= 14
                       and ((_adv >= 4 or _early_mass) and self.turn <= 8
                            or getattr(self, "_allin_seen", False)))
        if allin_alert:
            self._allin_seen = True
            rush_alert = True
        # 집 근처에 적이 있는 동안은 테크보다 병력이다. 압박 중 HQ 테크
        # 저축이 훈련을 잠그면 수비가 늦어진다. 집에서 조용히 매스를 모으는
        # 상대는 침공 전에 총병력 열세로만 보이므로 미리 전시경제로 전환한다.
        outmassed = self.turn < 140 and len(self.enemy) >= len(self.mine) + 5
        under_pressure = raided or near_enemy >= 1 or outmassed

        # 런타임 상대 분류: 100턴까지 침공하지 않으면서 총병력이 앞서는
        # 상대는 병력 동행과 외곽 견제로 대응한다.
        if getattr(self, "unknown_map", False) and 95 <= self.turn <= 105:
            self._tv = getattr(self, "_tv", 0) + (
                1 if invaders < 3 and len(self.enemy) > len(self.mine) else 0)
        if (getattr(self, "unknown_map", False) and self.turn == 105
                and getattr(self, "_tv", 0) >= 6):
            # 거북이/경제형: 매스 동행(parity) + 외곽 경제 레이드(raid).
            # 상호 L5 풀피 요새 무승부의 해법은 상대의 L5/수리 자금줄을
            # 끊는 것이다.
            self.mp = dict(self.mp, parity=True, raid=True)

        # 종반 칩: 턴제한 판정은 본부 HP만 본다. 지고 있으면
        # 잃을 게 없으니 공성으로 1이라도 깎으러 가고, 동점이면 병력 우위가
        # 있을 때만 간다 (확정 무승부를 요새 돌격으로 패배로 바꾸지 않기).
        my_hq_b = self.buildings.get(self.my_hq)
        their_hq_b = self.buildings.get(self.opp_hq)
        endgame_chip = False
        if (self.mp.get("chip") and self.turn >= 180 and my_hq_b is not None
                and their_hq_b is not None and their_hq_b[0] == self.foe):
            if their_hq_b[3] > my_hq_b[3]:
                endgame_chip = True
            elif their_hq_b[3] == my_hq_b[3]:
                endgame_chip = len(self.mine) >= len(self.enemy) + 4

        # ---------- 경제 목표 큐 ----------
        # 우선순위 순서로 실행하고, 못 사는 저축 목표를 만나면 이후 지출과
        # 훈련을 그 금액만큼 막아서 골드를 모은다 (훈련이 저축을 먹는 교착 방지).
        hq = self.buildings.get(self.my_hq)
        n_bases = sum(1 for _, b in self.my_buildings() if not b[1])
        saving_for = 0  # 훈련 전에 남겨둘 저축액

        # 0) 종반/비상 본부 수리·회복 (업그레이드는 즉시 만피) -- 항상 최우선
        if hq is not None and can_upgrade_region(self.my_hq):
            max_hp = HQ_LV[hq[2]][2]
            cost = HQ_LV[hq[2] + 1][0] if hq[2] < 5 else HQ_REPAIR_COST
            urgent = hq[3] <= max(4, int(max_hp * 0.4)) and gold >= cost + 200
            endgame = self.turn >= p["repair_turn"] and hq[3] < max_hp and gold >= cost
            # 막판 골드 컨버전: 골드를 쥐고 낮은 HQ 레벨로 판정에 가지 않는다.
            convert = (getattr(self, "unknown_map", False) and self.turn >= 185
                       and hq[2] < 5 and gold >= cost)
            # 본부 긴급 방어 (미지맵): 적 3기+ 본부 인접 시 즉시 업글 = 만피
            # 회복으로 적 집결 직후의 공성 누적을 끊는다.
            hq_siege_soon = (getattr(self, "unknown_map", False)
                             and (hq[2] < 5 or hq[3] < max_hp) and gold >= cost
                             and enemy_pressure_near(1) >= 3)
            if urgent or endgame or convert or hq_siege_soon:
                do_upgrade(self.my_hq, cost)

        # 빠른 확장 곡선: 기지 3개 -> 5개 -> 최대,
        # HQ 레벨 3 -> 5, 기지 레벨 2 -> 3.
        t = self.turn
        # 기지 L2는 노동 슬롯을 2배로 늘리므로 일찍 간다.
        if getattr(self, "unknown_map", False):
            # 불리한 장기전의 공통 선행조건은 중반 기지 열세다.
            base_target = min(p["target_bases"] + 4,
                              4 if t < 30 else (6 if t < 55 else (8 if t < 85 else 99)))
        else:
            base_target = min(p["target_bases"], 3 if t < 25 else (5 if t < 45 else 99))
        hq_cap = p["hq_cap"]
        hq_target = min(hq_cap, 1 if t < 45 else (3 if t < 100 else 5))
        # HQ L1 서킷브레이커 조건을 여기서 먼저 계산해둔다 (아래 anti-greed가
        # hq_target을 짓누르기 전에, 우리 자신이 이미 L1에 갇혀 있는 상황은
        # anti-greed 대상에서 빼야 한다 -- 안 그러면 "다같이 L1에 머물자"는
        # anti-greed 처방이 서킷브레이커가 풀려던 바로 그 함정을 재고정한다).
        _hq_stuck = (getattr(self, "unknown_map", False) and t >= 80
                     and hq is not None and hq[2] == 1)
        # 훈련한도는 HQ레벨에만 달려있고 L2는 한도를 안 올려준다.
        # 이미 물량에서 밀리고 있을 때만 훈련한도 병목을 뚫는다.
        need_train_cap = (getattr(self, "unknown_map", False) and t >= 70
                          and len(self.enemy) >= len(self.mine) + 8)
        if need_train_cap:
            hq_target = max(hq_target, min(hq_cap, 3))
        # anti-greed HQ 게이트: 상대가 HQ L1 고정으로 순수 확장/물량에 올인하면
        # 격차가 중반부터 계속 벌어진다. 한번 켜지면 상대가 HQ를 올리거나
        # 우리가 따라잡을 때까지 유지한다.
        their_hq_lv1 = (their_hq_b is not None and their_hq_b[0] == self.foe
                        and their_hq_b[2] <= 1)
        self._antigreed_latch = getattr(self, "_antigreed_latch", False)
        early_greed = (40 <= t < 60 and (
            n_en_bases >= n_my_bases + 2
            or (t < 50 and n_en_bases >= n_my_bases + 1
                and len(self.enemy) >= len(self.mine) + 2)
        ))
        mid_greed = (60 <= t <= 150 and (
            n_en_bases >= n_my_bases + 2
            or len(self.enemy) >= len(self.mine) + 3
        ))
        if (getattr(self, "unknown_map", False) and invaders < 3
                and their_hq_lv1 and not _hq_stuck
                and (early_greed or mid_greed)):
            self._antigreed_latch = True
        elif not their_hq_lv1 or len(self.mine) >= len(self.enemy) or t > 150:
            self._antigreed_latch = False
        if self._antigreed_latch and not (_hq_stuck or need_train_cap):
            hq_target = 1
        # 기지 L3는 슬롯 +1의 ROI가 낮으므로 중후반 잉여 골드로만 올린다.
        if getattr(self, "unknown_map", False):
            base_lv_target = 1 if t < 40 else (2 if t < 90 else 3)
        else:
            base_lv_target = 1 if t < 40 else 2

        # 1) 거점 기지 건설: 도착한 전사가 있으면 짓고, 확장이 실제로 진행
        #    중일 때만 저축한다. 경합 등으로 클레임 불가능한 목표를 위한 300
        #    저축은 큐 1순위라 HQ 테크를 영원히 차단한다 (경합맵에서 HQ 1렙
        #    동결로 200턴을 보내는 버그의 원인).
        def force_near(pool: dict, r: int, k: int) -> int:
            return sum(1 for s in pool.values() if 0 <= self.hops[r][s[0]] <= k)

        heading_now = {s[3] for s in self.mine.values() if s[2]}
        expandable = any(
            r not in self.buildings
            and self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r] * p["half_ratio"]
            and (
                r in heading_now
                or force_near(self.enemy, r, 2) == 0
                or force_near(self.mine, r, 2) >= force_near(self.enemy, r, 2) + 2
            )
            for r in self.strongholds
        )
        if allin_alert:
            expandable = False  # 올인 러시 중 기지 300골드는 수비 훈련 2.5명이다
        if n_bases < base_target and expandable:
            build_order = (sorted(self.strongholds, key=lambda r: self.dist[self.my_hq][r])
                           if getattr(self, "unknown_map", False) else self.strongholds)
            for r in build_order:
                if r in self.buildings or r in upgraded:
                    continue
                if self.my_at(r) and not self.enemy_count_at(r):
                    if gold >= BASE_LV[1][0] + reserve:
                        do_upgrade(r, BASE_LV[1][0])
                        planned_builds.add(r)
                        n_bases += 1
                        if n_bases >= base_target:
                            break
            if n_bases < base_target:
                saving_for = BASE_LV[1][0]

        # 2) 본부 레벨업. 공세/압박 중에는 잉여로만 올린다. 적이 본부를 점거해
        #    업글이 불법인 동안 그 비용을 저축하면 (훈련까지 잠겨) 교착이 된다.
        hq_race = (
            getattr(self, "unknown_map", False) and self.turn >= 110
            and invaders < 3 and not desperate
            and my_hq_b is not None and their_hq_b is not None
            and their_hq_b[0] == self.foe and their_hq_b[2] >= my_hq_b[2]
        )
        # HQ L1 서킷브레이커: near_enemy>=1 하나로도 under_pressure가 걸려서
        # 저축 예약(elif)이 게임 내내 한 번도 실행 안 될 수 있다 -- 즉시구매만
        # 으로는 훈련이 여유 골드를 계속 먹어치워 600골드가 안 모인다. T80
        # 넘도록 여전히 L1이면 위협 여부와 무관하게 HQ를 최우선 저축 대상으로
        # 강제한다.
        # 확장 저축 중에도 여유 골드가 크면 HQ 직접 구매를 허용한다.
        _hq_bypass = (getattr(self, "unknown_map", False) and saving_for > 0)
        if (saving_for == 0 or _hq_bypass) and hq is not None and hq[2] < hq_target:
            cost = HQ_LV[hq[2] + 1][0]
            # 확장이 위협으로 이미 멈춘 상태면 그 저축(300)을 지킬 필요가
            # 없다 -- 패딩을 유지하면 HQ가 L1(훈련한도 1/턴)에 갇혀 저강도
            # 지속압박에 서서히 갈리는 함정이 생긴다.
            # hq_race(상대가 이미 앞서서 따라잡기 중)일 때도 패딩을 지킬
            # 필요가 없다 -- 턴제한 판정은 HQ HP만 보므로 레이스 중에까지
            # 여유금 300을 더 요구하면 따라잡기가 늦어진다.
            _extra = 300 if (_hq_bypass and not under_pressure
                             and not _hq_stuck and not hq_race) else 0
            if can_upgrade_region(self.my_hq) and gold >= cost + reserve + _extra:
                do_upgrade(self.my_hq, cost)
            elif _hq_bypass and _hq_stuck and can_upgrade_region(self.my_hq):
                saving_for = max(saving_for, cost)
            elif (saving_for == 0
                  and (not (self.attacking or under_pressure)
                       or hq_race or _hq_stuck or need_train_cap)
                  and can_upgrade_region(self.my_hq)):
                saving_for = cost

        # 3) 기지 레벨업 (본부에서 가까운 순, 앞선 저축 목표가 없을 때만)
        hq_upgrade_blocked = (
            hq is not None and hq[2] < hq_target and can_upgrade_region(self.my_hq)
            and self.turn < 100 and len(self.enemy) >= len(self.mine) + 4
            and (self.attacking or under_pressure)
            and not (hq_race or _hq_stuck or need_train_cap)
        )
        if saving_for == 0 and not hq_upgrade_blocked:
            for r, b in sorted(self.my_buildings(), key=lambda rb: self.dist[self.my_hq][rb[0]]):
                if b[1] or not can_upgrade_region(r):
                    continue
                if b[2] >= base_lv_target:
                    if (b[2] == 3 and b[3] < BASE_LV[3][1]
                            and gold >= BASE_REPAIR_COST + reserve):
                        do_upgrade(r, BASE_REPAIR_COST)
                    continue
                cost = BASE_LV[b[2] + 1][0]
                if gold >= cost + reserve:
                    do_upgrade(r, cost)
                elif not (self.attacking or under_pressure):
                    saving_for = cost
                    break

        # 같은 턴 HQ 업그레이드/수리 예정이면 종반 HP 판정도 그 회복을 반영한다.
        if (self.mp.get("chip") and self.turn >= 180 and my_hq_b is not None
                and their_hq_b is not None and their_hq_b[0] == self.foe):
            my_hq_score_hp = my_hq_b[3]
            if self.my_hq in upgraded:
                my_hq_score_lv = my_hq_b[2] + (1 if my_hq_b[2] < 5 else 0)
                my_hq_score_hp = HQ_LV[my_hq_score_lv][2]
            endgame_chip = (
                their_hq_b[3] > my_hq_score_hp
                or (their_hq_b[3] == my_hq_score_hp
                    and len(self.mine) >= len(self.enemy) + 4)
            )

        # ---------- 이동 ----------
        movable = [w for w, s in self.mine.items() if not s[2]]
        movable.sort(key=lambda w: int(w[1:]))
        assigned: set[str] = set()
        moves: list[tuple[str, int]] = []

        def move_to(w: str, target: int) -> None:
            nonlocal gold
            s = self.mine[w]
            assigned.add(w)
            if s[0] == target:
                return
            b = self.buildings.get(target)
            free = (b is not None and b[0] == self.side) or target in planned_builds
            cost = 0 if free else MOVE_COST
            if gold - cost < 0 or self.dist[s[0]][target] == math.inf:
                assigned.discard(w)
                return
            gold -= cost
            moves.append((w, target))
            s[2], s[3] = True, target

        # 노동자: 각 건물 노동 한도만큼 현지 전사 고정.
        # 침공 중에는 적이 3홉 이내인 기지의 노동자를 소개해 병력에 합류시킨다
        # (흩어진 노동자는 진격로의 공짜 킬이고, 기지는 300골드면 다시 짓는다).
        def enemy_within(r: int, k: int) -> bool:
            return any(0 <= self.hops[r][s[0]] <= k for s in self.enemy.values())

        worker_slots = 0
        deficits: list[tuple[int, int]] = []  # (region, 부족 인원)
        for r, b in self.my_buildings():
            cap = self.work_cap(b)
            if (invaded or early_fortress) and r != self.my_hq and enemy_within(r, 3):
                continue  # 고정하지 않음 -> 아래에서 자유 병력으로 회군
            if endgame_chip and self.turn >= 188 and r != self.my_hq:
                continue  # 종반 칩: 기지는 점수가 아니다. 노동자도 공성 투입.
            here = [w for w in self.my_at(r) if w in movable and w not in assigned]
            for w in here[:cap]:
                assigned.add(w)
            heading_here = sum(1 for s in self.mine.values() if s[2] and s[3] == r)
            # 실제 채워진 인원만 반영 (빈 슬롯까지 "소모됨"으로 잡으면
            # army_size가 과소평가되어 push_army/big_idle 발동이 지연된다)
            worker_slots += min(cap, len(here[:cap]) + heading_here)
            lack = cap - len(here[:cap]) - heading_here
            if lack > 0:
                deficits.append((r, lack))

        # 오늘 지은 기지의 건설자는 그 자리에 노동자로 고정한다. 짓자마자 떠나면
        # 기지가 무노동(수입 0)이 되고 다른 전사가 왕복하는 낭비가 생긴다.
        for r in planned_builds:
            here = [w for w in self.my_at(r) if w in movable and w not in assigned]
            kept = here[:1]
            for w in kept:
                assigned.add(w)
            worker_slots += len(kept)

        # 위협 감지: 본부 근처 적 병력 -> 자유 병력 귀환
        # 압박 내성: 소수 캠퍼가 회군 트리거를 영구 점화하면 경제가 굳는다.
        # 소수 캠퍼는 요격(defend_at) 담당이고, 전군 회군은 진짜 웨이브부터.
        ring_pressure = False
        if getattr(self, "unknown_map", False):
            near1 = enemy_pressure_near(1)
            # 링 압박 = 전방 상시 주둔형. 전군회군이 영구 점화되면
            # 경제 동결 + 기지 단조 감소로 이어진다.
            # 전군 회군 대신 비례 대응: 수비대만 차출, 경제/확장은 계속.
            threatened = near1 >= 3 or invaded or rush_alert or early_fortress
            ring_pressure = (near_enemy >= 5 and not threatened)
        else:
            threatened = near_enemy >= p["threat_min"] or invaded or rush_alert
        if desperate:
            threatened = False  # 농성 해제: 지키는 게임은 이미 졌다

        # 확장: 미점유 거점(내 반경)으로 가장 가까운 자유 전사 파견.
        # 턴 50 이후에는 적이 근처에 없는 거점이면 상대 반경까지 탐욕 확장한다
        # (수비적 상대에게서 맵 전체 경제를 가져오는 것이 미러전의 승부처).
        # 경합 거점은 국지 우세가 있을 때만 클레임한다. 확장병 1명을 적 스택
        # 옆에 보내면 공짜 킬 -> 빈 슬롯 -> 재훈련 -> 재파견 골드 쳇바퀴가 돌아
        # 본부 업글 저축이 영영 안 모이고, 반대로 경합지를 전부 양보하면
        # 상대가 경제로 앞선다. 힘이 있으면 먹는다.

        expansion_ok = (not threatened
                        or (getattr(self, "unknown_map", False) and invaders <= 4
                            and not rush_alert and self.turn >= 30))
        if expansion_ok and n_bases < base_target:
            heading = {s[3] for s in self.mine.values() if s[2]}

            def claimable(r: int) -> bool:
                foes = force_near(self.enemy, r, 2)
                return foes == 0 or force_near(self.mine, r, 2) >= foes + 2

            targets = [
                r for r in self.strongholds
                if r not in self.buildings and r not in planned_builds and r not in heading
                and claimable(r)
                and (
                    self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r] * p["half_ratio"]
                    or (self.turn >= 50 and force_near(self.enemy, r, 3) == 0)
                )
            ]
            if getattr(self, "unknown_map", False):
                targets.sort(key=lambda r: (self.dist[self.my_hq][r],
                                            self.dist[self.opp_hq][r]))
            else:
                targets.sort(key=lambda r: self.dist[self.my_hq][r])
            # 첫 2턴은 1명만 내보낸다. 개막 러시가 오면 남은 병력으로 막아야 한다.
            _pwin = 50 if getattr(self, "unknown_map", False) else 30
            parallel = 1 if self.turn < 3 else (3 if self.turn < _pwin else p["expand_parallel"])
            n_claims = min(parallel, base_target - n_bases)
            for r in targets[:n_claims]:
                free = [w for w in movable if w not in assigned]
                if not free:
                    break
                w = min(free, key=lambda w: self.dist[self.mine[w][0]][r])
                move_to(w, r)

        # 골드를 기다리며 미건설 거점 위에 서 있는 확장병은 자리를 지킨다.
        # 결원 충원이나 집결 이동이 이들을 빼가면 클레임이 무효가 된다.
        if n_bases < p["target_bases"]:
            for r in self.strongholds:
                if r in self.buildings or r in planned_builds:
                    continue
                for w in [w for w in movable
                          if w not in assigned and self.mine[w][0] == r][:1]:
                    assigned.add(w)

        # 노동자 충원: 부족한 건물에 가까운 자유 전사 파견 (아군 건물이라 이동 무료).
        # 공세 중에도 계속 채운다 -- 장기 소모전은 지속 수입이 큰 쪽이 이긴다.
        deficits.sort(key=lambda d: self.dist[self.my_hq][d[0]])
        if not threatened:
            for r, lack in deficits:
                for _ in range(lack):
                    free = [w for w in movable if w not in assigned]
                    if not free:
                        break
                    w = min(free, key=lambda w: self.dist[self.mine[w][0]][r])
                    move_to(w, r)

        # 군대: 집결 -> 병력·테크·수적 우위가 갖춰지면 총공세.
        # 수비자는 포탑+지형 이점이 있으므로 수적 우위 없는 푸시는 헌납이다.
        # 다만 종반까지 우위가 안 오면 턴제한 HP 비교를 위해 강제로 나간다.
        _pt = p["push_turn"] - (15 if (getattr(self, "unknown_map", False)
                                       and self.N >= 73) else 0)
        army_size = max(0, alive - worker_slots)
        hq_lv = hq[2] if hq is not None else 1
        enemy_alive = len(self.enemy)
        advantage = alive >= enemy_alive + 8
        big_idle = (getattr(self, "unknown_map", False)
                    and army_size >= int(p["push_army"] * 1.5)
                    and len(self.mine) >= len(self.enemy)
                    and hq_lv >= p["hq_push_lv"] and self.turn >= 100)
        normal_attack = (
            (army_size >= p["push_army"] and hq_lv >= p["hq_push_lv"] and advantage)
            or (self.turn >= _pt and advantage)
            or (self.turn >= _pt + 25 and army_size >= p["wave"])
            or endgame_chip or desperate or big_idle
        )
        raid_attack = (self.mp.get("raid") and 110 <= self.turn < 175
                       and invaders < 3 and army_size >= p["wave"])
        if normal_attack or raid_attack:
            self.attacking = True
            self._raid_attack = raid_attack and not normal_attack
        elif self.attacking and invaded:
            self.attacking = False  # 재정비는 본진 침공 시에만. 총병력 열세
            self._raid_attack = False
        elif self.attacking and getattr(self, "_raid_attack", False) and self.turn >= 175:
            # raid는 시간 제한이 있는 견제다. 정규 공세 조건 없이 종반까지
            # 공격 상태가 새면 본부 HP 판정 구간의 병력 운용이 꼬인다.
            self.attacking = False
            self._raid_attack = False
        # 집결지는 내 반경 안의 최전방 건물로 제한 (적진 깊숙한 확장 기지에
        # 병력을 모아두면 각개격파당한다)
        my_regions = [
            r for r, _ in self.my_buildings()
            if self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r]
        ]
        if getattr(self, "unknown_map", False):
            staging = min(
                my_regions,
                key=lambda r: (self.dist[self.opp_hq][r], self.dist[self.my_hq][r]),
                default=self.my_hq,
            )
        else:
            staging = min(my_regions, key=lambda r: self.dist[self.opp_hq][r], default=self.my_hq)

        # 소규모 습격 요격 지점: 적이 2홉 이내에 붙은 내 건물 중 가장 위험한 곳.
        # 방어를 둘로 쪼개면 대등한 상대 앞에서는 주력방어가 약해진다.
        defend_at = None
        if (raided or near_enemy >= 1) and not invaded:
            cands = [
                (enemy_pressure_at(r, 2), r)
                for r, _ in self.my_buildings()
            ]
            cands = [c for c in cands if c[0] > 0]
            if cands:
                if getattr(self, "unknown_map", False):
                    defend_at = max(cands, key=lambda c: (
                        c[0], -self.dist[self.my_hq][c[1]]))[1]
                else:
                    defend_at = max(cands)[1]

        _defend_b = self.buildings.get(defend_at) if defend_at is not None else None
        _defend_intact = _defend_b is None or _defend_b[3] >= (
            HQ_LV[_defend_b[2]][2] if _defend_b[1] else BASE_LV[_defend_b[2]][1])
        if (getattr(self, "unknown_map", False)
                and (defend_at is None or (n_bases < 4 and _defend_intact))
                and (not threatened or invaders <= 6) and not self.attacking
                and n_bases < 5 and invaders <= 6 and self.turn >= 30):
            contested = [
                r for r in self.strongholds
                if r not in self.buildings
                and self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r]
                and 0 < force_near(self.enemy, r, 2) <= 3
            ]
            if contested:
                defend_at = min(contested, key=lambda r: self.dist[self.my_hq][r])

        hq_holders = sum(1 for w in assigned if self.mine[w][0] == self.my_hq)
        free = [w for w in movable if w not in assigned]

        # 수비 핀 피더 (미지맵): 본부 옆에 집결한 적 스택을 1기 투입으로 동결
        if (getattr(self, "unknown_map", False) and self.turn >= 140
                and not desperate):
            import collections as _c
            _stacks = _c.Counter(
                w[0] for w in self.enemy.values()
                if 0 <= self.hops[self.my_hq][w[0]] <= 1 and w[0] != self.my_hq
            )
            if _stacks:
                _pin_r, _pin_n = max(_stacks.items(), key=lambda kv: kv[1])
                _feeding = any((w[2] and w[3] == _pin_r) or w[0] == _pin_r
                               for w in self.mine.values())
                self._fed = getattr(self, "_fed", 0)
                if _pin_n >= 4 and not _feeding and free and self._fed < 15:
                    _f = min(free, key=lambda w: self.dist[self.mine[w][0]][_pin_r])
                    move_to(_f, _pin_r)
                    if _f in assigned:
                        self._fed += 1
                    free = [w for w in free if w not in assigned]
        staging_ready = sum(1 for w in free if self.mine[w][0] == staging)
        _halfwave = max(3, p["wave"] // 2) if getattr(self, "unknown_map", False) else 0
        release = self.attacking and not threatened and (
            staging_ready >= p["wave"]
            or (self.turn >= _pt + 20 and staging_ready >= _halfwave)
        )
        # 공격 목표: 적 본부 직행 대신 호위가 얇은 적 건물부터 부순다.
        # 경제를 먼저 죽이면 적의 훈련이 말라 소모전이 저절로 무너진다.
        # 적 기지가 없어지면 자연히 목표가 본부가 된다.
        enemy_bldgs = [r for r, b in self.buildings.items() if b[0] == self.foe]
        # 끈질긴 목표: 지난 턴 목표가 아직 서 있으면 유지한다. 매턴 재계산은
        # 웨이브를 여러 목표로 분산시켜 공성 공백을 만든다.
        if getattr(self, "wave_target", None) in enemy_bldgs:
            attack_at = self.wave_target
        elif enemy_bldgs:
            attack_at = min(
                enemy_bldgs,
                key=lambda r: (
                    sum(1 for s in self.enemy.values() if 0 <= self.hops[r][s[0]] <= 2) * 30
                    + self.dist[staging][r] * 0.02
                    + (10 if r == self.opp_hq else 0)
                ),
            )
        else:
            attack_at = self.opp_hq
        if self.turn >= 182:
            attack_at = self.opp_hq  # 턴제한 판정은 본부 HP만 본다
        self.wave_target = attack_at

        # ---------- 견제 부대 선발 (본대 배정 전) ----------
        _hq_squad = set()
        if (getattr(self, "unknown_map", False) and self.turn >= 60
                and self.turn < 182  # 턴제한 판정은 본부 HP만 봄 -- 종반엔
                # 견제부대(최대 5+2기)를 흩어두지 않고 본대 압박에 합류
                and not threatened and not early_fortress
                and not (outmassed and self.turn >= 120)
                and not desperate
                and army_size >= p["wave"]):
            _en_bases = [r for r, b in self.buildings.items()
                         if b[0] == self.foe and not b[1]]
            if _en_bases:
                _ht = getattr(self, "_harass_t", None)
                if _ht not in _en_bases:  # 끈질긴 목표 (파괴 전 재선정 금지)
                    _ht = min(_en_bases, key=lambda r: (
                        force_near(self.enemy, r, 1) * 20
                        + self.dist[self.opp_hq][r] * -0.01))  # 호위 얇고 외곽
                    self._harass_t = _ht
                for w in sorted(free, key=lambda w: self.dist[self.mine[w][0]][_ht])[:5]:
                    _hq_squad.add(w)
                    move_to(w, _ht)
                free = [w for w in free if w not in assigned]
                # 병력이 아주 여유로울 때만 2번째 목표에 소수만 얹는다.
                _en_bases2 = [r for r in _en_bases if r != _ht]
                if _en_bases2 and army_size >= p["wave"] * 3:
                    _ht2 = getattr(self, "_harass_t2", None)
                    if _ht2 not in _en_bases2:
                        _ht2 = min(_en_bases2, key=lambda r: (
                            force_near(self.enemy, r, 1) * 20
                            + self.dist[self.opp_hq][r] * -0.01))
                        self._harass_t2 = _ht2
                    for w in sorted(free, key=lambda w: self.dist[self.mine[w][0]][_ht2])[:2]:
                        _hq_squad.add(w)
                        move_to(w, _ht2)
                    free = [w for w in free if w not in assigned]

        _ring_def = 0
        _ring_need = invaders + 2 if ring_pressure else 0
        for w in free:
            s = self.mine[w]
            if ring_pressure and _ring_def < _ring_need:
                _ring_def += 1
                move_to(w, defend_at if defend_at is not None else self.my_hq)
            elif threatened:
                # 적진 깊숙한 병력에게 회군은 자살이다. 내 반경 병력만
                # 회군하고, 깊은 병력은 하던 공세를 계속한다.
                if self.dist[self.my_hq][s[0]] <= self.dist[self.opp_hq][s[0]]:
                    move_to(w, self.my_hq)
                else:
                    move_to(w, getattr(self, "wave_target", self.opp_hq))
            elif defend_at is not None and not self.attacking:
                move_to(w, defend_at)
            elif hq_holders < p["garrison"] and s[0] == self.my_hq and not self.attacking:
                assigned.add(w)
                hq_holders += 1
            elif (getattr(self, "unknown_map", False) and self.attacking
                  and self.turn >= _pt + 10 and attack_at == self.opp_hq
                  and s[0] in self.adj[self.opp_hq]):
                # 관문 웨이브 게이트: 도착 즉시 한 명씩 돌입시키면 상대 본부
                # 수비(터렛+상시 훈련)에 각개격파당한다. 웨이브가 찰 때까지
                # 관문에서 뭉치고, 종반에는 무조건 진입한다.
                _gate_n = sum(1 for x in self.mine.values()
                             if x[0] in self.adj[self.opp_hq]
                             and (not x[2] or x[3] == self.opp_hq))
                if _gate_n >= 35 or self.turn >= 195:
                    move_to(w, self.opp_hq)
                else:
                    assigned.add(w)  # 관문 축적 -- 각개격파 방지
            elif (getattr(self, "unknown_map", False) and self.attacking
                  and s[0] == attack_at):
                assigned.add(w)  # 목표 도달 병력 고정 -- 회군 명령이 공성을 끊지 않게 한다.
            elif s[0] == staging and release:
                if (getattr(self, "unknown_map", False) and self.turn >= _pt + 10
                        and attack_at == self.opp_hq):
                    gates = sorted(self.adj[self.opp_hq],
                                   key=lambda r: self.dist[staging][r])[:3]
                    move_to(w, gates[int(w[1:]) % len(gates)])
                else:
                    move_to(w, attack_at)
            else:
                move_to(w, staging)

        # ---------- 훈련 ----------
        # 빈 노동 슬롯이 있으면 훈련은 경제 투자(120골드 -> 15/턴)이므로 저축보다
        # 우선한다. 슬롯이 다 찼으면 군대 훈련이라 저축 목표 위의 잉여로만 한다.
        # 위협/공세 중에는 항상 최대 훈련.
        open_slots = 0
        for r, b in self.my_buildings():
            stationed = sum(1 for s in self.mine.values() if s[0] == r)
            heading_here = sum(1 for s in self.mine.values() if s[2] and s[3] == r)
            open_slots += max(0, self.work_cap(b) - stationed - heading_here)
        train_n = 0
        if hq is not None:
            lv = hq[2] + (1 if self.my_hq in upgraded and hq[2] < 5 else 0)
            cap = HQ_LV[lv][4]
            # 병력 열세면 저축보다 훈련한다.
            behind = self.mp.get("parity", False) and len(self.mine) < len(self.enemy)
            hold = 0 if (threatened or self.attacking or open_slots > 0
                         or under_pressure or behind) else saving_for
            if ((hq_race or _hq_stuck or need_train_cap) and saving_for > 0
                    and not behind and not threatened):
                hold = saving_for
            # 종반 보급 보증: 남은 턴의 식비를 훈련이 먹으면 굶주림 연쇄로
            # 군대가 굶주림으로 융해된다.
            supply_fund = 0
            if self.turn >= 160:
                supply_fund = min(1000, alive * (200 - self.turn))
            # 대군의 역설 방지 (미지맵): 병력 +12 우위면 훈련 정지 -> 테크.
            # 큰 병력 우위에서도 유지비와 훈련비가 HQ 저축을 질식시킬 수 있다.
            if (getattr(self, "unknown_map", False)
                    and len(self.mine) >= len(self.enemy) + 12
                    and hq is not None and hq[2] < hq_target
                    and not self.attacking):
                cap = 0  # 공세 중엔 정상 훈련 (마무리 물량 유지)
                # anti-greed가 hq_target=1로 눌러놓은 상태에서는 HQ를 안 살
                # 것이므로 훈련만 막고 골드를 놀리는 건 순손해다.
            afford = (gold - reserve - hold - supply_fund) // TRAIN_COST
            # 저축 잠금 중에도 수입이 크면 1기/턴은 뽑는다. 훈련 완전
            # 동결은 웨이브 소형화의 근본 원인이다.
            if (getattr(self, "unknown_map", False) and afford < 1 and hold > 0
                    and getattr(self, "_last_income", 0) >= 180
                    and gold - reserve - supply_fund >= TRAIN_COST):
                afford = 1
            train_n = max(0, min(cap, afford))

        # ---------- 커맨드 확정 + 골드 반영 ----------
        for w, target in moves:
            cmds.append(f"MOVE {w} {self._tr(target)}")
        if train_n > 0:
            cmds.append(f"TRAIN {train_n}")

        # 커맨드 확정 시점 골드 차감 (보고 처리에서 중복 차감 없음)
        self.gold = gold - TRAIN_COST * train_n
        for r in upgraded:
            b = self.buildings.get(r)
            if b is None:
                self.buildings[r] = [self.side, False, 1, BASE_LV[1][1]]
            elif b[1]:
                if b[2] < 5:
                    b[2] += 1
                b[3] = HQ_LV[b[2]][2]
            else:
                if b[2] < 3:
                    b[2] += 1
                b[3] = BASE_LV[b[2]][1]
        return cmds

    # ---------- turn result ----------

    def read_result(self) -> None:
        line = readln()
        if line == "FINISH":
            sys.exit(0)
        readln()  # TIME ...

        n = int(readln().split()[1])  # UPGRADE N
        for _ in range(n):
            t = readln().split()
            side, r = t[0], self._tr(int(t[1]))
            if side == self.side:
                continue  # 내 것은 커맨드 확정 시점에 반영 완료
            b = self.buildings.get(r)
            if b is None:
                self.buildings[r] = [side, False, 1, BASE_LV[1][1]]
            elif b[1]:
                if b[2] < 5:
                    b[2] += 1
                b[3] = HQ_LV[b[2]][2]
            else:
                if b[2] < 3:
                    b[2] += 1
                b[3] = BASE_LV[b[2]][1]

        n = int(readln().split()[1])  # TRAIN N
        if n > 0:
            for wid in readln().split():
                side = wid[0]
                hq_r = self.my_hq if side == self.side else self.opp_hq
                hq_b = self.buildings.get(hq_r)
                hp = HQ_LV[hq_b[2] if hq_b else 1][1]
                pool = self.mine if side == self.side else self.enemy
                pool[wid] = [hq_r, hp, False, hq_r]

        n = int(readln().split()[1])  # MOVE N
        enemy_step: dict[str, tuple[int, int]] = {}
        for _ in range(n):
            t = readln().split()
            wid, r = t[0], self._tr(int(t[1]))
            pool = self.mine if wid[0] == self.side else self.enemy
            s = pool.get(wid)
            if s is not None:
                old_r = s[0]
                s[0] = r
                if s[2] and r == s[3]:
                    s[2] = False
                if wid[0] != self.side and old_r != r:
                    enemy_step[wid] = (old_r, r)
        self._enemy_step = enemy_step

        hunger: list[tuple[str, int]] = []
        n = int(readln().split()[1])  # DAMAGE N
        for _ in range(n):
            t = readln().split()
            cause, wid, dmg = t[0], t[1], int(t[2])
            if cause == "HUNGER":
                hunger.append((wid, dmg))
                continue
            pool = self.mine if wid[0] == self.side else self.enemy
            if wid in pool:
                pool[wid][1] -= dmg
        self.mine = {w: s for w, s in self.mine.items() if s[1] > 0}
        self.enemy = {w: s for w, s in self.enemy.items() if s[1] > 0}

        n = int(readln().split()[1])  # SIEGE N
        for _ in range(n):
            t = readln().split()
            r, dmg = self._tr(int(t[1])), int(t[2])
            if r in self.buildings:
                self.buildings[r][3] -= dmg
        self.buildings = {r: b for r, b in self.buildings.items() if b[3] > 0}

        readln()  # END

        income = 0
        for r, b in self.my_buildings():
            here = sum(1 for s in self.mine.values() if s[0] == r)
            income += WORK_INCOME * min(here, self.work_cap(b))
        self.gold += income
        self._last_income = income
        my_hunger = sum(1 for wid, _ in hunger if wid[0] == self.side)
        paid = max(0, len(self.mine) - my_hunger)
        self.gold -= UPKEEP * paid

        for wid, dmg in hunger:
            pool = self.mine if wid[0] == self.side else self.enemy
            if wid in pool:
                pool[wid][1] -= dmg
        self.mine = {w: s for w, s in self.mine.items() if s[1] > 0}
        self.enemy = {w: s for w, s in self.enemy.items() if s[1] > 0}

    # ---------- main loop ----------

    def run(self) -> None:
        self.read_init()
        while True:
            line = readln()
            if line == "FINISH":
                return
            self.turn = int(line.split()[2])
            cmds = self.plan()
            out = ["COMMAND", *cmds, "END"]
            print("\n".join(out), flush=True)
            self.read_result()


if __name__ == "__main__":
    style = sys.argv[1] if len(sys.argv) > 1 else "econ"
    if style not in STYLES:
        style = "econ"
    Bot(style).run()
