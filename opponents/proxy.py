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
        hq_cap=5, target_bases=8, expand_parallel=2, half_ratio=1.0,
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
    # 공식 3번 모사 (29.py가 79턴에 패배): 기지 3개/HQ 1렙 고정으로 집에서
    # 조용히 매스를 모은 뒤 ~70턴에 13명 원펀치 + 지속 증원.
    "punch": dict(
        push_army=13, push_turn=68, hq_push_lv=1, garrison=0, wave=12,
        hq_cap=1, target_bases=3, expand_parallel=2, half_ratio=0.8,
        repair_turn=190, threat_hops=2, threat_min=3,
    ),
    # 유저전 AlphaBeta 모사 (평가#25 205140_A 패배): HQ 투자 0(hq_cap=1),
    # 대신 순수 확장(기지 10개 목표)+지속 훈련으로 물량을 밀어붙인다.
    "nohq_expand": dict(
        push_army=20, push_turn=140, hq_push_lv=1, garrison=2, wave=6,
        hq_cap=1, target_bases=10, expand_parallel=3, half_ratio=1.0,
        repair_turn=190, threat_hops=2, threat_min=3,
    ),
    # 유저전 갈치 모사 (평가#25 204345_A 패배): T29/42/60에 서로 다른 기지를
    # 순차로 소규모(3~4기) 습격 -- 한 곳에 집중하는 대신 적 기지를 돌며
    # 각개격파. 소규모 습격 반복형(raider) -- 소규모 웨이브를 자주 보낸다.
    "raider": dict(
        push_army=10, push_turn=25, hq_push_lv=1, garrison=1, wave=3,
        hq_cap=5, target_bases=9, expand_parallel=3, half_ratio=1.0,
        repair_turn=190, threat_hops=2, threat_min=3,
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
        self.style = style
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
        base_target = min(p["target_bases"], 3 if t < 30 else (5 if t < 70 else 99))
        hq_target = min(p["hq_cap"], 1 if t < 45 else (3 if t < 100 else 5))
        base_lv_target = 1 if t < 50 else (2 if t < 110 else 3)

        # 1) 거점 기지 건설: 도착한 전사가 있으면 짓고, 확장 진행 중이면 저축
        expandable = any(
            r not in self.buildings
            and self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r] * p["half_ratio"]
            for r in self.strongholds
        )
        if n_bases < base_target and expandable:
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

        # 2) 본부 레벨업. 공세 중에는 잉여로만 올린다.
        if saving_for == 0 and hq is not None and hq[2] < hq_target:
            cost = HQ_LV[hq[2] + 1][0]
            if can_upgrade_region(self.my_hq) and gold >= cost + reserve:
                do_upgrade(self.my_hq, cost)
            elif not self.attacking:
                saving_for = cost

        # 3) 기지 레벨업 (본부에서 가까운 순, 앞선 저축 목표가 없을 때만)
        if saving_for == 0:
            for r, b in sorted(self.my_buildings(), key=lambda rb: self.dist[self.my_hq][rb[0]]):
                if b[1] or b[2] >= base_lv_target or not can_upgrade_region(r):
                    continue
                cost = BASE_LV[b[2] + 1][0]
                if gold >= cost + reserve:
                    do_upgrade(r, cost)
                elif not self.attacking:
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

        # 노동자: 각 건물 노동 한도만큼 현지 전사 고정
        worker_slots = 0
        deficits: list[tuple[int, int]] = []  # (region, 부족 인원)
        for r, b in self.my_buildings():
            cap = self.work_cap(b)
            here = [w for w in self.my_at(r) if w in movable and w not in assigned]
            for w in here[:cap]:
                assigned.add(w)
            worker_slots += cap
            heading_here = sum(1 for s in self.mine.values() if s[2] and s[3] == r)
            lack = cap - len(here[:cap]) - heading_here
            if lack > 0:
                deficits.append((r, lack))

        # 위협 감지: 본부 근처 적 병력 -> 자유 병력 귀환
        near_enemy = sum(
            1 for s in self.enemy.values()
            if 0 <= self.hops[self.my_hq][s[0]] <= p["threat_hops"]
        )
        threatened = near_enemy >= p["threat_min"]

        # 확장: 미점유 거점(내 반경)으로 가장 가까운 자유 전사 파견
        if not threatened and n_bases < base_target:
            heading = {s[3] for s in self.mine.values() if s[2]}
            targets = [
                r for r in self.strongholds
                if r not in self.buildings and r not in planned_builds and r not in heading
                and self.dist[self.my_hq][r] <= self.dist[self.opp_hq][r] * p["half_ratio"]
            ]
            targets.sort(key=lambda r: self.dist[self.my_hq][r])
            n_claims = min(p["expand_parallel"], base_target - n_bases)
            for r in targets[:n_claims]:
                free = [w for w in movable if w not in assigned]
                if not free:
                    break
                w = min(free, key=lambda w: self.dist[self.mine[w][0]][r])
                move_to(w, r)

        # 노동자 충원: 부족한 건물에 가까운 자유 전사 파견 (아군 건물이라 이동 무료)
        # 공세 중에는 새 병력을 전선으로 보내야 하므로 본부 노동만 채운다.
        deficits.sort(key=lambda d: self.dist[self.my_hq][d[0]])
        if not threatened:
            for r, lack in deficits:
                if self.attacking and r != self.my_hq:
                    continue
                for _ in range(lack):
                    free = [w for w in movable if w not in assigned]
                    if not free:
                        break
                    w = min(free, key=lambda w: self.dist[self.mine[w][0]][r])
                    move_to(w, r)

        # 군대: 집결 -> 병력·테크 임계점 도달 시 총공세
        army_size = max(0, alive - worker_slots)
        hq_lv = hq[2] if hq is not None else 1
        if ((army_size >= p["push_army"] and hq_lv >= p["hq_push_lv"])
                or self.turn >= p["push_turn"]):
            self.attacking = True
        my_regions = [r for r, _ in self.my_buildings()]
        staging = min(my_regions, key=lambda r: self.dist[self.opp_hq][r], default=self.my_hq)

        hq_holders = sum(1 for w in assigned if self.mine[w][0] == self.my_hq)
        free = [w for w in movable if w not in assigned]
        staging_ready = sum(1 for w in free if self.mine[w][0] == staging)
        release = self.attacking and (
            staging_ready >= p["wave"] or self.turn >= p["push_turn"] + 20
        )
        # raider 스타일: 본부 직행 대신 적 기지를 순차로 소규모 습격한다
        # (~15턴마다 목표 갱신, 유저전 갈치 패턴 재현).
        raid_target = self.opp_hq
        if self.style == "raider":
            enemy_bases = [r for r, b in self.buildings.items()
                           if b[0] == self.foe and not b[1]]
            if enemy_bases:
                if (getattr(self, "_raid_t", None) not in enemy_bases
                        or self.turn - getattr(self, "_raid_since", 0) >= 15):
                    self._raid_t = min(enemy_bases, key=lambda r: self.dist[self.my_hq][r])
                    self._raid_since = self.turn
                raid_target = self._raid_t
        for w in free:
            s = self.mine[w]
            if threatened:
                move_to(w, self.my_hq)
            elif hq_holders < p["garrison"] and s[0] == self.my_hq and not self.attacking:
                assigned.add(w)
                hq_holders += 1
            elif s[0] == staging and release:
                move_to(w, raid_target)
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
            hold = 0 if (threatened or self.attacking or open_slots > 0) else saving_for
            afford = (gold - reserve - hold) // TRAIN_COST
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
