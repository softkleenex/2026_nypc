#!/usr/bin/env python3
"""로컬 벤치마크 상대: 공식 샘플 AI 4~8번의 매크로 스타일을 모사한다.

사용법: python3 proxy.py [econ|turtle|rush]

  econ   -- 공식 4/5번 모사: 빠른 확장 + 상시 훈련 + 물량 임계점 도달 시 총공세
  turtle -- 공식 6/7/8번 모사: 더 무거운 경제, 더 큰 스택, 늦은 공세, 종반 본부 수리
  rush   -- 초반 소규모 압박 (다양성용)

이 봇들은 후보 선택을 정직하게 유지하기 위한 벤치마크이며 제출 후보가 아니다.
공식 로그 근거 수치는 strategy-plan.md 참고:
  적 기지 3개 도달 ~21턴, 5개 ~40턴대, HQ 업글 4회, 총 훈련 41~111명,
  185~195턴 사이 본부 파괴.
"""
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
        self.my_hq = 0 if self.side == "A" else self.N - 1
        self.opp_hq = self.N - 1 if self.side == "A" else 0

        for i in range(1, 4):
            self.mine[f"{self.side}{i}"] = [self.my_hq, 4, False, self.my_hq]
            self.enemy[f"{self.foe}{i}"] = [self.opp_hq, 4, False, self.opp_hq]
        self.buildings[0] = ["A", True, 1, 10]
        self.buildings[self.N - 1] = ["B", True, 1, 10]

        self.dist = [self._dijkstra(s) for s in range(self.N)]
        self.hops = [self._bfs(s) for s in range(self.N)]
        print("OK", flush=True)

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
            cmds.append(f"UPGRADE {r}")
            upgraded.add(r)
            gold -= cost

        # ---------- 위협 평가 (지출 우선순위가 여기 의존) ----------
        invaders = sum(
            1 for s in self.enemy.values()
            if self.dist[self.my_hq][s[0]] < self.dist[self.opp_hq][s[0]]
        )
        invaded = invaders >= 8    # 침공(웨이브 규모): 소개 + 본부 농성
        raided = invaders >= 3     # 소규모 습격: 병력으로 요격
        near_enemy = sum(
            1 for s in self.enemy.values()
            if 0 <= self.hops[self.my_hq][s[0]] <= p["threat_hops"]
        )
        # 초반 러시 감지: 개막 직후 적 전사가 내 쪽 절반 가까이 들어오면
        # (샘플/공격형 봇의 3전사 러시) 확장을 멈추고 집을 지킨다.
        rush_alert = self.turn < 30 and any(
            self.dist[self.my_hq][s[0]] < 0.45 * self.dist[self.my_hq][self.opp_hq]
            for s in self.enemy.values()
        )
        # 집 근처에 적이 있는 동안은 테크보다 병력이다. 서버 3번(79턴 패배,
        # 훈련 9 vs 17)과 7번(골드 955 동결)의 패인: 압박 중 HQ 테크 저축이
        # 훈련을 잠갔다.
        # 단, 과잉반응 금지 (서버 6번 패인): 정찰병 1~2명이나 "경제도 같이 큰"
        # 상대의 병력 우위에 전시경제로 들어가면 테크/확장이 동결되어 성장형에게
        # 말라 죽는다. 진짜 올인 신호 = 병력 우위 + 적 경제가 우리보다 작음.
        my_bases = sum(1 for _, b in self.my_buildings() if not b[1])
        enemy_bases = sum(
            1 for b in self.buildings.values() if b[0] == self.foe and not b[1]
        )
        outmassed = (self.turn < 140
                     and len(self.enemy) >= len(self.mine) + 5
                     and enemy_bases < my_bases)
        under_pressure = raided or near_enemy >= 3 or outmassed

        # 종반 칩: 턴제한 판정은 본부 HP만 본다. 지고 있으면 잃을 게 없으니
        # 무조건 공성으로 1이라도 깎으러 가고, 동점이면 병력 우위가 있을 때만
        # 간다 (요새 돌격으로 확정 무승부를 패배로 바꾸지 않기).
        my_hq_b = self.buildings.get(self.my_hq)
        their_hq_b = self.buildings.get(self.opp_hq)
        endgame_chip = False
        if (self.turn >= 180 and my_hq_b is not None
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
            if urgent or endgame:
                do_upgrade(self.my_hq, cost)

        # 공식 봇 확장 곡선 근사: 기지 3개(~턴30) -> 5개(~턴70) -> 최대,
        # HQ 레벨 3(~턴100) -> 5, 기지 레벨 2(~턴110) -> 3.
        t = self.turn
        # 공식 봇 곡선(기지 3개 ~턴21, 4개 ~31, 5개 ~40대)에 맞춘 빠른 오프닝.
        # 기지 L2는 노동 슬롯을 2배로 늘리므로 (600골드 -> +15/턴) 일찍 간다.
        base_target = min(p["target_bases"], 3 if t < 25 else (5 if t < 45 else 99))
        hq_target = min(p["hq_cap"], 1 if t < 45 else (3 if t < 100 else 5))
        # 기지 L3(1000골드)는 전사 8명분 값에 슬롯 +1이라 ROI가 나쁘다. L2까지만.
        base_lv_target = 1 if t < 40 else 2

        # 1) 거점 기지 건설: 도착한 전사가 있으면 짓고, 확장이 실제로 진행
        #    중일 때만 저축한다. 경합 등으로 클레임 불가능한 목표를 위한 300
        #    저축은 큐 1순위라 HQ 테크를 영원히 차단한다 (양쪽 HQ 1렙 동결로
        #    200턴을 보낸 seed1 스파링의 원인).
        def force_near(pool: dict, r: int, k: int) -> int:
            return sum(1 for s in pool.values() if 0 <= self.hops[r][s[0]] <= k)

        heading_now = {s[3] for s in self.mine.values() if s[2]}
        expansion_live = any(
            r not in self.buildings
            and self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r] * p["half_ratio"]
            and (
                r in heading_now  # 이미 확장병이 가는 중
                or force_near(self.enemy, r, 2) == 0
                or force_near(self.mine, r, 2) >= force_near(self.enemy, r, 2) + 2
            )
            for r in self.strongholds
        )
        if n_bases < base_target and expansion_live:
            for r in self.strongholds:
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
        if saving_for == 0 and hq is not None and hq[2] < hq_target:
            cost = HQ_LV[hq[2] + 1][0]
            if can_upgrade_region(self.my_hq) and gold >= cost + reserve:
                do_upgrade(self.my_hq, cost)
            elif not (self.attacking or under_pressure) and can_upgrade_region(self.my_hq):
                saving_for = cost

        # 3) 기지 레벨업 (본부에서 가까운 순, 앞선 저축 목표가 없을 때만)
        if saving_for == 0:
            for r, b in sorted(self.my_buildings(), key=lambda rb: self.dist[self.my_hq][rb[0]]):
                if b[1] or b[2] >= base_lv_target or not can_upgrade_region(r):
                    continue
                cost = BASE_LV[b[2] + 1][0]
                if gold >= cost + reserve:
                    do_upgrade(r, cost)
                elif not (self.attacking or under_pressure):
                    saving_for = cost
                    break

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
            if invaded and r != self.my_hq and enemy_within(r, 3):
                worker_slots += cap
                continue  # 고정하지 않음 -> 아래에서 자유 병력으로 회군
            if endgame_chip and self.turn >= 188 and r != self.my_hq:
                worker_slots += cap
                continue  # 종반 칩: 기지는 점수가 아니다. 노동자도 공성 투입.
            here = [w for w in self.my_at(r) if w in movable and w not in assigned]
            for w in here[:cap]:
                assigned.add(w)
            worker_slots += cap
            heading_here = sum(1 for s in self.mine.values() if s[2] and s[3] == r)
            lack = cap - len(here[:cap]) - heading_here
            if lack > 0:
                deficits.append((r, lack))

        # 오늘 지은 기지의 건설자는 그 자리에 노동자로 고정한다. 짓자마자 떠나면
        # 기지가 무노동(수입 0)이 되고 다른 전사가 왕복하는 낭비가 생긴다.
        for r in planned_builds:
            here = [w for w in self.my_at(r) if w in movable and w not in assigned]
            for w in here[:1]:
                assigned.add(w)
            worker_slots += 1

        # 위협 감지: 본부 근처 적 병력 -> 자유 병력 귀환
        threatened = near_enemy >= p["threat_min"] or invaded or rush_alert

        # 확장: 미점유 거점(내 반경)으로 가장 가까운 자유 전사 파견.
        # 턴 50 이후에는 적이 근처에 없는 거점이면 상대 반경까지 탐욕 확장한다
        # (수비적 상대에게서 맵 전체 경제를 가져오는 것이 미러전의 승부처).
        # 경합 거점은 국지 우세가 있을 때만 클레임한다. 확장병 1명을 적 스택
        # 옆에 보내면 공짜 킬 -> 빈 슬롯 -> 재훈련 -> 재파견 골드 쳇바퀴가 돌아
        # 본부 업글 저축이 영영 안 모이고 (v4의 HQ 2렙 정체), 반대로 경합지를
        # 전부 양보하면 상대가 경제로 앞선다 (v5 turtle 전패). 힘이 있으면 먹는다.
        if not threatened and n_bases < base_target:
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
            targets.sort(key=lambda r: self.dist[self.my_hq][r])
            # 첫 2턴은 1명만 내보낸다. 개막 러시가 오면 남은 병력으로 막아야 한다.
            parallel = 1 if self.turn < 3 else (3 if self.turn < 30 else p["expand_parallel"])
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
        # 레이드: 적이 집에 대군을 쌓고 안 나오면 (침공 0) 총병력 열세여도
        # 바깥 경제를 뜯는다. 홈 스택은 외곽 기지를 지켜주지 못하고, 우리
        # 공격 목표 선정이 호위 얇은 건물을 고르므로 스택과의 정면충돌은 없다.
        # (서버 6번 패인: 43 vs 29 열세라는 이유로 200턴 내내 한 번도 안 나감)
        army_size = max(0, alive - worker_slots)
        hq_lv = hq[2] if hq is not None else 1
        enemy_alive = len(self.enemy)
        advantage = alive >= enemy_alive + 8
        raid_ready = (self.turn >= 120 and invaders < 3
                      and army_size >= 2 * p["wave"] and hq_lv >= 3)
        # 종반 폴백 출격은 필수다: 상호 요새전에서 공격자만 상대 HQ를 조금씩
        # 깎을 수 있어, 안 나가면 턴제한 HP 비교에서 일방적으로 진다
        # (실측: 상호 출격 17무 3패 vs 일방 농성 11무 9패).
        if ((army_size >= p["push_army"] and hq_lv >= p["hq_push_lv"] and advantage)
                or (self.turn >= p["push_turn"] and advantage)
                or (self.turn >= p["push_turn"] + 25 and army_size >= p["wave"])
                or raid_ready or endgame_chip):
            self.attacking = True
        elif self.attacking and (invaded or alive < enemy_alive - 5):
            self.attacking = False  # 집이 뚫리거나 크게 밀리면 재정비 (헌납 방지)
        # 집결지는 내 반경 안의 최전방 건물로 제한 (적진 깊숙한 확장 기지에
        # 병력을 모아두면 각개격파당한다)
        my_regions = [
            r for r, _ in self.my_buildings()
            if self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r]
        ]
        staging = min(my_regions, key=lambda r: self.dist[self.opp_hq][r], default=self.my_hq)

        # 소규모 습격 요격 지점: 적이 2홉 이내에 붙은 내 건물 중 가장 위험한 곳
        # 내 반경에 들어온 적이 내 건물 2홉 이내면 요격한다. 유격병 2~3명을
        # 방치하면 외곽 노동자 학살 -> 재충원 -> 재학살 쳇바퀴로 군대가 영영
        # 안 모인다 (서버 6번 리플레이: 유격 2명에 120턴간 병력 8명 정체).
        # 단 적 반경의 전선 주둔군까지 쫓으면 아군이 평생 추격만 하므로
        # 반드시 침입자(내 쪽 절반)로 한정한다.
        defend_at = None
        if not invaded and invaders >= 1:
            in_my_half = [
                s for s in self.enemy.values()
                if self.dist[self.my_hq][s[0]] < self.dist[self.opp_hq][s[0]]
            ]
            cands = [
                (sum(1 for s in in_my_half if 0 <= self.hops[r][s[0]] <= 2), r)
                for r, _ in self.my_buildings()
            ]
            cands = [c for c in cands if c[0] > 0]
            if cands:
                defend_at = max(cands)[1]

        hq_holders = sum(1 for w in assigned if self.mine[w][0] == self.my_hq)
        free = [w for w in movable if w not in assigned]
        staging_ready = sum(1 for w in free if self.mine[w][0] == staging)
        release = self.attacking and not threatened and (
            staging_ready >= p["wave"] or self.turn >= p["push_turn"] + 20
        )
        # 공격 목표: 적 본부 직행 대신 호위가 얇은 적 건물부터 부순다.
        # 경제를 먼저 죽이면 적의 훈련이 말라 소모전이 저절로 무너진다.
        # 적 기지가 없어지면 자연히 목표가 본부가 된다.
        enemy_bldgs = [r for r, b in self.buildings.items() if b[0] == self.foe]
        if enemy_bldgs:
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
        if self.turn >= 180:
            attack_at = self.opp_hq  # 턴제한 판정은 본부 HP만 본다

        for w in free:
            s = self.mine[w]
            if threatened:
                move_to(w, self.my_hq)
            elif defend_at is not None and (
                not self.attacking or 0 <= self.hops[defend_at][s[0]] <= 4
            ):
                # 공세 중에는 요격 지점 근처(4홉)의 병력만 대응하고
                # 전선의 웨이브는 계속 나간다
                move_to(w, defend_at)
            elif hq_holders < p["garrison"] and s[0] == self.my_hq and not self.attacking:
                assigned.add(w)
                hq_holders += 1
            elif s[0] == staging and release:
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
            hold = 0 if (threatened or self.attacking or open_slots > 0
                         or under_pressure) else saving_for
            # 종반 보급 보증: 남은 턴의 식비를 훈련이 먹으면 굶주림 연쇄로
            # 군대가 융해된다 (실측: 175턴 출격 후 177턴부터 굶주림 106건).
            supply_fund = 0
            if self.turn >= 160:
                supply_fund = min(1000, alive * (200 - self.turn))
            afford = (gold - reserve - hold - supply_fund) // TRAIN_COST
            train_n = max(0, min(cap, afford))

        # ---------- 커맨드 확정 + 골드 반영 ----------
        for w, target in moves:
            cmds.append(f"MOVE {w} {target}")
        if train_n > 0:
            cmds.append(f"TRAIN {train_n}")

        # 제출 시점 골드 차감 (보고 처리에서 중복 차감 없음)
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
            side, r = t[0], int(t[1])
            if side == self.side:
                continue  # 내 것은 제출 시점에 반영 완료
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
                hq_r = 0 if side == "A" else self.N - 1
                hq_b = self.buildings.get(hq_r)
                hp = HQ_LV[hq_b[2] if hq_b else 1][1]
                pool = self.mine if side == self.side else self.enemy
                pool[wid] = [hq_r, hp, False, hq_r]

        n = int(readln().split()[1])  # MOVE N
        for _ in range(n):
            t = readln().split()
            wid, r = t[0], int(t[1])
            pool = self.mine if wid[0] == self.side else self.enemy
            s = pool.get(wid)
            if s is not None:
                s[0] = r
                if s[2] and r == s[3]:
                    s[2] = False

        n = int(readln().split()[1])  # DAMAGE N
        for _ in range(n):
            t = readln().split()
            wid, dmg = t[1], int(t[2])
            pool = self.mine if wid[0] == self.side else self.enemy
            if wid in pool:
                pool[wid][1] -= dmg
        self.mine = {w: s for w, s in self.mine.items() if s[1] > 0}
        self.enemy = {w: s for w, s in self.enemy.items() if s[1] > 0}

        n = int(readln().split()[1])  # SIEGE N
        for _ in range(n):
            t = readln().split()
            r, dmg = int(t[1]), int(t[2])
            if r in self.buildings:
                self.buildings[r][3] -= dmg
        self.buildings = {r: b for r, b in self.buildings.items() if b[3] > 0}

        readln()  # END

        income = 0
        for r, b in self.my_buildings():
            here = sum(1 for s in self.mine.values() if s[0] == r)
            income += WORK_INCOME * min(here, self.work_cap(b))
        self.gold += income
        self.gold = max(0, self.gold - UPKEEP * len(self.mine))

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
