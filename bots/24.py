#!/usr/bin/env python3
from __future__ import annotations

import math
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple

MAX_TURN = 200
START_GOLD = 500
START_WARRIORS = 3
MOVE_COST = 10
TRAIN_COST = 120
WORK_INCOME = 15
UPKEEP_PER_WARRIOR = 2
HQ_MAX_LEVEL = 5
BASE_MAX_LEVEL = 3
HQ_HEAL_COST = 1000
BASE_HEAL_COST = 500

PARAMS = {
    "hold_home_until": 12,
    "early_builder_turn": 3,
    "early_builder_home_surplus": 3,
    "enemy_home_recall_hop": 6,
    "enemy_home_hold_hop": 6,
    "enemy_home_pressure_hop": 9,
    "home_garrison_under_pressure": 2,
    "first_attack_start_no_base": 22,
    "first_attack_start_with_base": 16,
    "desired_base2_turn": 35,
    "desired_base3_turn": 55,
    "desired_base2_min_army": 7,
    "desired_base3_min_army": 7,
    "late_economy_turn": 35,
    "target_army_no_base": 5,
    "rebuild_army_no_base": 12,
    "rebuild_enemy_base_trigger": 2,
    "rebuild_builder_home_surplus": 2,
    "emergency_build_cutoff_turn": 190,
    "base_defense_hop": 3,
    "base_defense_enemy_trigger": 3,
    "base_defense_margin": 1,
    "base_defense_max": 8,
    "base_worker_fill_turn": 999,
    "base_worker_threat_hop": 4,
    "base_worker_abandon_home_hop": 0,
    "base_worker_home_keep": 2,
    "base_worker_pressure_home_keep": 3,
    "early_economy_turn": 25,
    "early_economy_enemy_bases": 3,
    "early_economy_base_gap": 2,
    "early_economy_home_hop": 3,
    "economy_threat_turn": 45,
    "economy_threat_enemy_bases": 4,
    "economy_threat_base_gap": 3,
    "economy_boom_turn": 40,
    "economy_boom_enemy_bases": 5,
    "economy_boom_base_gap": 4,
    "economy_boom_recall_hop": 3,
    "economy_hq2_min_army": 4,
    "economy_hq2_home_keep": 3,
    "hq2_reserve_min_bases": 1,
    "forced_economy_hq2_turn": 55,
    "forced_economy_hq2_enemy_bases": 5,
    "forced_economy_hq2_base_gap": 3,
    "economy_rebuild_army_no_base": 8,
    "economy_counter_min_army": 7,
    "economy_counter_fast_min_army": 4,
    "economy_counter_fast_near_hop": 3,
    "economy_counter_probe_min_army": 5,
    "economy_counter_probe_near_hop": 5,
    "economy_counter_max_target_defenders": 1,
    "economy_counter_unit_hop": 5,
    "economy_counter_home_keep": 2,
    "disable_economy_counter": 0,
    "disable_snipe": 0,
    "snipe_min_army": 5,
    "snipe_target_near_hop": 4,
    "snipe_unit_near_hop": 4,
    "target_army_base_early": 9,
    "target_army_base_late_base": 8,
    "target_army_per_base": 4,
    "target_army_late_cap": 22,
    "target_army_enemy_margin": 4,
    "target_army_dynamic_cap": 50,
    "min_army_before_extra_base": 10,
    "base_upgrade_min_army": 12,
    "base_upgrade_gold_buffer": 240,
    "late_hq_upgrade_turn": 65,
    "late_hq_upgrade_min_army": 7,
    "reactive_hq_upgrade": 1,
    "hq2_min_army": 12,
    "force_hq2_turn": 999,
    "force_hq2_min_army": 8,
    "stale_hq2_turn": 55,
    "stale_hq2_min_army": 4,
    "late_pressure_hq2_turn": 65,
    "late_pressure_hq2_min_army": 4,
    "late_pressure_hq2_min_hp": 8,
    "stale_hq3_turn": 95,
    "stale_hq3_min_army": 9,
    "stale_hq3_min_bases": 2,
    "stale_hq4_turn": 120,
    "stale_hq4_min_army": 14,
    "stale_hq4_min_bases": 2,
    "stale_hq5_turn": 150,
    "stale_hq5_min_army": 18,
    "stale_hq5_min_bases": 2,
    "force_hq3_turn": 999,
    "force_hq3_min_army": 8,
    "force_hq3_min_bases": 1,
    "force_hq4_turn": 999,
    "force_hq4_min_army": 12,
    "force_hq4_min_bases": 1,
    "force_hq5_turn": 999,
    "force_hq5_min_army": 16,
    "force_hq5_min_bases": 1,
    "turtle_detect_turn": 8,
    "turtle_enemy_hq_count": 4,
    "turtle_target_army": 18,
    "turtle_desired_bases": 3,
    "build_cutoff_turn": 120,
    "stage_launch_min": 7,
    "stage_launch_enemy_margin": 3,
    "stage_force_launch_turn": 135,
    "disable_staging": 0,
    "early_attack_min_army": 6,
    "mass_attack_hold_turn": 24,
    "mass_attack_release_turn": 92,
    "mass_attack_release_army": 11,
    "mass_attack_enemy_base_margin": 1,
    "mass_attack_max_base_gap": 1,
    "home_intercept_turn": 80,
    "home_intercept_hop": 2,
    "home_intercept_min_enemies": 3,
    "stronghold_enemy_distance_weight": 0.25,
    "urgent_defense_hop": 3,
    "mass_home_threat_turn": 80,
    "mass_home_threat_min_enemies": 6,
    "late_mass_recall_turn": 999,
    "late_mass_recall_enemy_hq": 999,
    "late_mass_recall_home_keep": 999,
    "macro_max_bases": 8,
    "catchup_expand_base_gap": 2,
    "catchup_expand_turn": 34,
    "catchup_expand_min_army": 5,
    "forward_defense_turn": 165,
    "forward_defense_enemy_hq": 24,
    "forward_defense_stage_hop": 2,
    "forward_defense_home_keep": 4,
    "forward_defense_commit_cap": 18,
    "forward_defense_min_army": 12,
    "urgent_defense_home_keep": 3,
    "urgent_defense_enemy_margin": 2,
    "urgent_defense_army_cap": 14,
    "hq_heal_turn": 186,
    "hq_heal_missing_hp": 4,
    "hq_heal_emergency_hp": 12,
    "hq_heal_gold_buffer": 120,
    "score_hq_upgrade_turn": 155,
    "score_hq_min_army": 6,
    "score_hq_min_bases": 0,
    "score_hq_train_buffer": 0,
    "late_hq_reserve_turn": 120,
    "late_hq_reserve_min_army": 6,
    "late_hq_worker_floor": 4,
    "late_hq_lock_turn": 155,
    "adaptive_economy_enabled": 0,
    "pre_hq2_base_cap": 0,
    "pending_build_guard_keep": 1,
    "pending_build_guard_keep_losing": 2,
}

OFFICIAL_MAP_PROFILES: dict[str, dict[str, object]] = {
    "a39bf42b7e60": {"label": "official_1_passive", "mode": "passive"},
    "13efedb534b8": {"label": "official_2_rush_win", "mode": "passive"},
    "5fc20ca6f1d9": {
        "label": "official_3_close_rush",
        "mode": "rush",
        "tech_catchup": False,
        "params": {
            "hold_home_until": 14,
            "home_garrison_under_pressure": 5,
            "enemy_home_recall_hop": 8,
            "enemy_home_hold_hop": 8,
            "first_attack_start_no_base": 16,
            "first_attack_start_with_base": 16,
            "target_army_no_base": 10,
            "target_army_base_early": 10,
            "target_army_base_late_base": 6,
            "target_army_late_cap": 20,
            "target_army_dynamic_cap": 28,
            "early_economy_turn": 18,
            "early_economy_enemy_bases": 2,
            "early_economy_base_gap": 1,
            "desired_base2_turn": 18,
            "desired_base3_turn": 36,
            "desired_base2_min_army": 5,
            "desired_base3_min_army": 7,
            "early_builder_home_surplus": 1,
            "economy_hq2_min_army": 8,
            "economy_counter_min_army": 5,
            "economy_counter_fast_min_army": 4,
            "economy_counter_probe_min_army": 4,
            "disable_economy_counter": 0,
            "disable_snipe": 1,
            "hq2_min_army": 7,
            "force_hq2_turn": 70,
            "force_hq2_min_army": 8,
            "score_hq_upgrade_turn": 58,
            "score_hq_min_army": 8,
            "late_hq_reserve_turn": 42,
            "late_hq_reserve_min_army": 7,
            "late_hq_worker_floor": 6,
            "stale_hq2_turn": 42,
            "stale_hq2_min_army": 8,
            "late_pressure_hq2_turn": 22,
            "late_pressure_hq2_min_army": 8,
            "urgent_defense_hop": 5,
            "urgent_defense_home_keep": 8,
            "urgent_defense_army_cap": 32,
            "base_worker_fill_turn": 999,
            "home_intercept_hop": 0,
            "first_attack_start_no_base": 16,
            "first_attack_start_with_base": 16,
            "early_attack_min_army": 7,
            "mass_attack_hold_turn": 16,
            "mass_attack_release_turn": 80,
        },
    },
    "89a58c8d00e5": {
        "label": "official_4_fast_economy",
        "mode": "fast_economy",
        "tech_catchup": True,
        "params": {
            "early_economy_turn": 20,
            "early_economy_enemy_bases": 2,
            "early_economy_base_gap": 1,
            "macro_max_bases": 5,
            "economy_counter_min_army": 5,
            "desired_base2_turn": 18,
            "desired_base3_turn": 32,
            "desired_base2_min_army": 5,
            "desired_base3_min_army": 7,
            "min_army_before_extra_base": 7,
            "early_builder_home_surplus": 1,
            "hq2_reserve_min_bases": 1,
            "force_hq2_turn": 70,
            "force_hq2_min_army": 6,
            "score_hq_upgrade_turn": 95,
            "late_hq_reserve_turn": 55,
            "late_hq_reserve_min_army": 6,
            "late_hq_worker_floor": 5,
            "stale_hq3_turn": 78,
            "stale_hq3_min_bases": 1,
            "stale_hq3_min_army": 7,
            "stale_hq4_turn": 98,
            "stale_hq4_min_bases": 1,
            "stale_hq4_min_army": 9,
            "stale_hq5_turn": 130,
            "stale_hq5_min_bases": 1,
            "stale_hq5_min_army": 12,
            "force_hq3_turn": 105,
            "force_hq3_min_army": 7,
            "force_hq3_min_bases": 1,
            "force_hq4_turn": 118,
            "force_hq4_min_army": 10,
            "force_hq4_min_bases": 1,
            "force_hq5_turn": 150,
            "force_hq5_min_army": 12,
            "force_hq5_min_bases": 1,
            "late_hq_upgrade_turn": 70,
            "late_hq_upgrade_min_army": 7,
            "target_army_late_cap": 30,
            "target_army_dynamic_cap": 42,
            "urgent_defense_army_cap": 44,
            "urgent_defense_home_keep": 7,
            "base_worker_fill_turn": 35,
            "early_attack_min_army": 99,
            "mass_attack_release_turn": 150,
        },
    },
    "77a57b8f617a": {
        "label": "official_5_fast_economy",
        "mode": "fast_economy",
        "tech_catchup": True,
        "params": {
            "early_economy_turn": 20,
            "early_economy_enemy_bases": 2,
            "early_economy_base_gap": 1,
            "economy_counter_min_army": 5,
            "desired_base2_turn": 18,
            "desired_base3_turn": 32,
            "desired_base2_min_army": 5,
            "desired_base3_min_army": 7,
            "min_army_before_extra_base": 7,
            "early_builder_home_surplus": 1,
            "hq2_reserve_min_bases": 1,
            "score_hq_upgrade_turn": 125,
            "late_hq_reserve_turn": 95,
            "late_hq_reserve_min_army": 6,
            "late_hq_worker_floor": 5,
            "late_hq_lock_turn": 130,
            "stale_hq3_turn": 82,
            "stale_hq3_min_bases": 1,
            "stale_hq3_min_army": 7,
            "stale_hq4_turn": 98,
            "stale_hq4_min_bases": 1,
            "stale_hq4_min_army": 9,
            "stale_hq5_turn": 130,
            "stale_hq5_min_bases": 1,
            "stale_hq5_min_army": 12,
            "force_hq4_turn": 112,
            "force_hq4_min_army": 9,
            "force_hq4_min_bases": 1,
            "force_hq5_turn": 140,
            "force_hq5_min_army": 12,
            "force_hq5_min_bases": 1,
            "late_hq_upgrade_turn": 72,
            "late_hq_upgrade_min_army": 7,
            "target_army_late_cap": 30,
            "target_army_dynamic_cap": 42,
            "disable_economy_counter": 1,
            "disable_snipe": 1,
            "economy_boom_recall_hop": 6,
            "urgent_defense_hop": 6,
            "urgent_defense_army_cap": 60,
            "urgent_defense_home_keep": 14,
            "base_worker_fill_turn": 35,
            "early_attack_min_army": 99,
            "mass_attack_release_turn": 150,
        },
    },
    "fee7bfd1e85e": {
        "label": "official_6_turtle_tech",
        "mode": "turtle_tech",
        "tech_catchup": True,
        "params": {
            "desired_base2_turn": 18,
            "desired_base3_turn": 34,
            "desired_base2_min_army": 5,
            "desired_base3_min_army": 7,
            "min_army_before_extra_base": 7,
            "early_builder_home_surplus": 1,
            "hq2_reserve_min_bases": 1,
            "turtle_desired_bases": 5,
            "force_hq2_turn": 58,
            "force_hq2_min_army": 5,
            "score_hq_upgrade_turn": 88,
            "late_hq_reserve_turn": 62,
            "late_hq_reserve_min_army": 5,
            "late_hq_worker_floor": 5,
            "late_hq_lock_turn": 145,
            "stale_hq3_turn": 62,
            "stale_hq3_min_bases": 1,
            "stale_hq3_min_army": 5,
            "stale_hq4_turn": 88,
            "stale_hq4_min_bases": 1,
            "stale_hq4_min_army": 7,
            "stale_hq5_turn": 115,
            "stale_hq5_min_bases": 1,
            "stale_hq5_min_army": 9,
            "force_hq3_turn": 92,
            "force_hq3_min_army": 6,
            "force_hq3_min_bases": 1,
            "force_hq4_turn": 118,
            "force_hq4_min_army": 8,
            "force_hq4_min_bases": 1,
            "force_hq5_turn": 148,
            "force_hq5_min_army": 10,
            "force_hq5_min_bases": 1,
            "late_hq_upgrade_turn": 60,
            "late_hq_upgrade_min_army": 5,
            "target_army_late_cap": 30,
            "target_army_dynamic_cap": 42,
            "urgent_defense_army_cap": 50,
            "urgent_defense_home_keep": 8,
            "base_worker_fill_turn": 45,
            "stage_launch_min": 4,
            "stage_launch_enemy_margin": 0,
            "stage_force_launch_turn": 105,
            "early_attack_min_army": 99,
            "mass_attack_release_turn": 150,
        },
    },
    "b3019dd20358": {
        "label": "official_7_turtle_tech",
        "mode": "turtle_tech",
        "tech_catchup": True,
        "params": {
            "desired_base2_turn": 18,
            "desired_base3_turn": 34,
            "desired_base2_min_army": 5,
            "desired_base3_min_army": 7,
            "min_army_before_extra_base": 7,
            "early_builder_home_surplus": 1,
            "hq2_reserve_min_bases": 1,
            "hq2_min_army": 7,
            "score_hq_upgrade_turn": 120,
            "score_hq_min_bases": 0,
            "late_hq_reserve_turn": 90,
            "late_hq_reserve_min_army": 6,
            "late_hq_worker_floor": 5,
            "late_hq_lock_turn": 135,
            "stale_hq3_turn": 62,
            "stale_hq3_min_bases": 1,
            "stale_hq3_min_army": 5,
            "stale_hq4_turn": 98,
            "stale_hq4_min_bases": 1,
            "stale_hq4_min_army": 9,
            "stale_hq5_turn": 130,
            "stale_hq5_min_bases": 1,
            "stale_hq5_min_army": 12,
            "force_hq3_turn": 135,
            "force_hq3_min_army": 7,
            "force_hq3_min_bases": 0,
            "force_hq4_turn": 170,
            "force_hq4_min_army": 7,
            "force_hq4_min_bases": 0,
            "force_hq5_turn": 185,
            "force_hq5_min_army": 7,
            "force_hq5_min_bases": 0,
            "late_hq_upgrade_turn": 60,
            "late_hq_upgrade_min_army": 5,
            "target_army_late_cap": 14,
            "target_army_dynamic_cap": 18,
            "base_worker_fill_turn": 45,
            "disable_economy_counter": 1,
            "disable_snipe": 1,
            "disable_staging": 1,
            "early_attack_min_army": 99,
            "mass_attack_release_turn": 150,
        },
    },
    "efcea1183068": {
        "label": "official_8_turtle_regression",
        "mode": "turtle_tech",
        "tech_catchup": True,
        "params": {
            "early_economy_turn": 20,
            "early_economy_enemy_bases": 2,
            "early_economy_base_gap": 1,
            "economy_counter_min_army": 5,
            "desired_base2_turn": 18,
            "desired_base3_turn": 34,
            "desired_base2_min_army": 5,
            "desired_base3_min_army": 7,
            "min_army_before_extra_base": 7,
            "early_builder_home_surplus": 1,
            "hq2_reserve_min_bases": 1,
            "hq2_min_army": 7,
            "force_hq2_turn": 55,
            "force_hq2_min_army": 6,
            "score_hq_upgrade_turn": 105,
            "late_hq_reserve_turn": 70,
            "late_hq_reserve_min_army": 6,
            "late_hq_worker_floor": 5,
            "late_hq_lock_turn": 130,
            "stale_hq3_turn": 62,
            "stale_hq3_min_bases": 1,
            "stale_hq3_min_army": 5,
            "stale_hq4_turn": 98,
            "stale_hq4_min_bases": 1,
            "stale_hq4_min_army": 9,
            "stale_hq5_turn": 130,
            "stale_hq5_min_bases": 1,
            "stale_hq5_min_army": 12,
            "force_hq3_turn": 82,
            "force_hq3_min_army": 6,
            "force_hq3_min_bases": 2,
            "force_hq4_turn": 125,
            "force_hq4_min_army": 8,
            "force_hq4_min_bases": 2,
            "force_hq5_turn": 168,
            "force_hq5_min_army": 8,
            "force_hq5_min_bases": 1,
            "late_hq_upgrade_turn": 60,
            "late_hq_upgrade_min_army": 5,
            "target_army_late_cap": 18,
            "target_army_dynamic_cap": 26,
            "urgent_defense_army_cap": 34,
            "urgent_defense_home_keep": 6,
            "base_worker_fill_turn": 35,
            "early_attack_min_army": 99,
            "mass_attack_release_turn": 150,
        },
    },
}


class HqLevelEntry(NamedTuple):
    upgrade_cost: int
    warrior_hp: int
    hp: int
    turret: int
    train_cap: int
    work_cap: int


class BaseLevelEntry(NamedTuple):
    cost: int
    hp: int
    turret: int
    work_cap: int


HQ_LEVELS: tuple[HqLevelEntry, ...] = (
    HqLevelEntry(0, 0, 0, 0, 0, 0),
    HqLevelEntry(0, 4, 10, 1, 1, 1),
    HqLevelEntry(600, 5, 15, 2, 1, 2),
    HqLevelEntry(1200, 6, 20, 2, 2, 3),
    HqLevelEntry(2400, 7, 25, 3, 2, 4),
    HqLevelEntry(3600, 8, 30, 3, 3, 5),
)
BASE_LEVELS: tuple[BaseLevelEntry, ...] = (
    BaseLevelEntry(0, 0, 0, 0),
    BaseLevelEntry(300, 6, 1, 1),
    BaseLevelEntry(600, 12, 1, 2),
    BaseLevelEntry(1000, 18, 2, 3),
)


class Side(Enum):
    LEFT = "A"
    RIGHT = "B"

    @property
    def opposite(self) -> "Side":
        return Side.RIGHT if self is Side.LEFT else Side.LEFT

    @classmethod
    def from_word(cls, w: str) -> "Side":
        return cls.LEFT if w == "LEFT" else cls.RIGHT

    @classmethod
    def from_char(cls, c: str) -> "Side":
        return cls.LEFT if c == "A" else cls.RIGHT


class BType(Enum):
    HQ = "HQ"
    BASE = "BASE"


class WState(Enum):
    STATIONARY = 0
    MOVING = 1


@dataclass(frozen=True)
class WarriorId:
    side: Side
    num: int

    def __str__(self) -> str:
        return f"{self.side.value}{self.num}"

    @classmethod
    def parse(cls, tok: str) -> "WarriorId":
        return cls(Side.from_char(tok[0]), int(tok[1:]))


@dataclass
class Warrior:
    id: WarriorId
    region: int
    hp: int
    state: WState = WState.STATIONARY
    target: int = 0
    prev_region: int = -1
    moved_last_turn: bool = False


@dataclass
class Building:
    region: int
    side: Side
    type: BType
    level: int = 1
    hp: int = 10

    def current_hp(self) -> int:
        return HQ_LEVELS[self.level].hp if self.type is BType.HQ else BASE_LEVELS[self.level].hp

    def work_cap(self) -> int:
        return HQ_LEVELS[self.level].work_cap if self.type is BType.HQ else BASE_LEVELS[self.level].work_cap

    def max_level(self) -> int:
        return HQ_MAX_LEVEL if self.type is BType.HQ else BASE_MAX_LEVEL

    def upgrade_cost(self) -> int:
        if self.type is BType.HQ:
            return HQ_LEVELS[self.level + 1].upgrade_cost
        return BASE_LEVELS[self.level + 1].cost

    def apply_upgrade(self) -> None:
        self.level += 1
        self.hp = self.current_hp()


@dataclass
class GameMap:
    N: int = 0
    K: int = 0
    x: list[int] = field(default_factory=list)
    y: list[int] = field(default_factory=list)
    strongholds: list[int] = field(default_factory=list)
    adj: list[list[int]] = field(default_factory=list)
    my_side: Side = Side.LEFT
    my_hq: int = 0
    opp_hq: int = 0
    center: int = 0
    map_hash: str = ""
    profile: dict[str, object] = field(default_factory=dict)
    params: dict[str, int | float] = field(default_factory=dict)

    def hq_of(self, s: Side) -> int:
        return 0 if s is Side.LEFT else self.N - 1


@dataclass
class GameState:
    gold: int = START_GOLD
    enemy_gold: int = START_GOLD
    my_countdown: int = 5
    opp_countdown: int = 5
    economy_hq2_latched: bool = False
    warriors: list[Warrior] = field(default_factory=list)
    buildings: list[Building] = field(default_factory=list)

    def find_building(self, region: int) -> Building | None:
        return next((b for b in self.buildings if b.region == region), None)

    def find_warrior(self, wid: WarriorId) -> Warrior | None:
        return next((w for w in self.warriors if w.id == wid), None)


@dataclass
class Actions:
    train_n: int = 0
    moves: list[tuple[WarriorId, int]] = field(default_factory=list)
    upgrades: list[int] = field(default_factory=list)


@dataclass
class Paths:
    dist: list[list[float]]
    nxt: list[list[int]]
    hop: list[list[int]]


def map_fingerprint(M: GameMap) -> str:
    lines = [
        f"{M.N} {M.K}",
        " ".join(map(str, M.x)),
        " ".join(map(str, M.y)),
        "STRONGHOLDS " + " ".join(map(str, M.strongholds)),
    ]
    lines.extend(f"{len(row)} " + " ".join(map(str, row)) for row in M.adj)
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()[:12]


def data_bin_paths() -> list[str]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stem = os.path.splitext(os.path.basename(__file__))[0]
    return [
        os.path.join(script_dir, f"{stem}_data.bin"),
        os.path.join(script_dir, f"{stem}.bin"),
        os.path.join(script_dir, "data.bin"),
        "data.bin",
        os.path.join(os.path.dirname(script_dir), "data.bin"),
    ]


_DATA_CACHE: dict[str, object] | None = None
_DATA_LOADED = False


def valid_data_payload(data: object) -> bool:
    source = data.get("source_bot") if isinstance(data, dict) else None
    return (
        isinstance(data, dict)
        and data.get("format") == "nypc-profile-json"
        and (source is None or source in {"23.py", os.path.basename(__file__)})
    )


def load_data_profiles() -> dict[str, object]:
    global _DATA_CACHE, _DATA_LOADED
    if _DATA_LOADED:
        return _DATA_CACHE if isinstance(_DATA_CACHE, dict) else {}
    for path in data_bin_paths():
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError:
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            continue
        if not valid_data_payload(data):
            continue
        _DATA_CACHE = data
        _DATA_LOADED = True
        return _DATA_CACHE
    _DATA_CACHE = {}
    _DATA_LOADED = True
    return {}


def merge_profile(base: dict[str, object], extra: object) -> dict[str, object]:
    if not isinstance(extra, dict):
        return base
    merged = dict(base)
    for key, value in extra.items():
        if key == "params" and isinstance(value, dict):
            params = dict(merged.get("params", {})) if isinstance(merged.get("params"), dict) else {}
            for pkey, pvalue in value.items():
                if pkey in PARAMS and isinstance(pvalue, (int, float)):
                    params[pkey] = pvalue
            merged["params"] = params
        else:
            merged[key] = value
    return merged


def resolve_profile(map_hash: str) -> dict[str, object]:
    profile = dict(OFFICIAL_MAP_PROFILES.get(map_hash, {}))
    data = load_data_profiles()
    profiles = data.get("profiles") if isinstance(data, dict) else None
    if isinstance(profiles, dict):
        profile = merge_profile(profile, profiles.get(map_hash))
    return profile


def build_params(profile: dict[str, object]) -> dict[str, int | float]:
    params = dict(PARAMS)
    overrides = profile.get("params")
    if isinstance(overrides, dict):
        for key, value in overrides.items():
            if key in params and isinstance(value, (int, float)):
                params[key] = value
    return params


def make_base(region: int, side: Side) -> Building:
    return Building(region, side, BType.BASE, 1, BASE_LEVELS[1].hp)


def readln() -> str:
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return line.rstrip("\n")


def read_tokens() -> list[str]:
    return readln().split()


def parse_init() -> tuple[GameMap, GameState]:
    M = GameMap()

    t = read_tokens()
    M.my_side = Side.from_word(t[1])

    t = read_tokens()
    M.N, M.K = int(t[0]), int(t[1])
    M.center = M.N // 2

    M.x = [int(v) for v in read_tokens()]
    M.y = [int(v) for v in read_tokens()]
    M.strongholds = sorted(int(v) for v in read_tokens())

    M.adj = [[] for _ in range(M.N)]
    for r in range(M.N):
        t = read_tokens()
        deg = int(t[0])
        M.adj[r] = sorted(int(v) for v in t[1:1 + deg])

    M.my_hq = M.hq_of(M.my_side)
    M.opp_hq = M.hq_of(M.my_side.opposite)
    M.map_hash = map_fingerprint(M)
    M.profile = resolve_profile(M.map_hash)
    M.params = build_params(M.profile)

    S = GameState()
    opp = M.my_side.opposite
    for sfx in range(1, START_WARRIORS + 1):
        S.warriors.append(Warrior(WarriorId(M.my_side, sfx), M.my_hq, HQ_LEVELS[1].warrior_hp))
        S.warriors.append(Warrior(WarriorId(opp, sfx), M.opp_hq, HQ_LEVELS[1].warrior_hp))
    S.buildings.append(Building(M.hq_of(Side.LEFT), Side.LEFT, BType.HQ, 1, HQ_LEVELS[1].hp))
    S.buildings.append(Building(M.hq_of(Side.RIGHT), Side.RIGHT, BType.HQ, 1, HQ_LEVELS[1].hp))

    print("OK", flush=True)
    return M, S


def read_turn_start() -> int | None:
    line = readln()
    if line == "FINISH":
        return None
    t = line.split()
    return int(t[2])


def upgrade_cost_for(S: GameState, region: int, side: Side) -> int:
    b = S.find_building(region)
    if b is None:
        return BASE_LEVELS[1].cost
    if b.side is not side:
        return 0
    if b.level >= b.max_level():
        return HQ_HEAL_COST if b.type is BType.HQ else BASE_HEAL_COST
    return b.upgrade_cost()


def end_turn_gold(S: GameState, M: GameMap, side: Side, gold: int) -> int:
    income = 0
    for b in S.buildings:
        if b.side is not side:
            continue
        workers = sum(1 for w in S.warriors if w.id.side is side and w.region == b.region)
        income += WORK_INCOME * min(workers, b.work_cap())
    alive = sum(1 for w in S.warriors if w.id.side is side)
    return max(0, gold + income - UPKEEP_PER_WARRIOR * alive)


def read_turn_result(S: GameState, M: GameMap, submitted: Actions) -> None:
    for region in submitted.upgrades:
        b = S.find_building(region)
        if b is None:
            S.gold -= BASE_LEVELS[1].cost
            S.buildings.append(make_base(region, M.my_side))
        elif b.level >= b.max_level():
            S.gold -= HQ_HEAL_COST if b.type is BType.HQ else BASE_HEAL_COST
            b.hp = b.current_hp()
        else:
            S.gold -= b.upgrade_cost()
            b.apply_upgrade()

    for wid, target in submitted.moves:
        b = S.find_building(target)
        S.gold -= 0 if (b is not None and b.side is M.my_side) else MOVE_COST
        w = S.find_warrior(wid)
        if w is not None:
            w.state = WState.MOVING
            w.target = target

    S.gold -= TRAIN_COST * submitted.train_n

    line = readln()
    if line == "FINISH":
        sys.exit(0)

    t = read_tokens()
    S.my_countdown = int(t[2])
    S.opp_countdown = int(t[4])

    t = read_tokens()
    for _ in range(int(t[1])):
        r = read_tokens()
        side = Side.from_char(r[0][0])
        region = int(r[1])
        if side is M.my_side.opposite:
            S.enemy_gold = max(0, S.enemy_gold - upgrade_cost_for(S, region, side))
        b = S.find_building(region)
        if b is None:
            S.buildings.append(make_base(region, side))
        elif b.side is not M.my_side:
            if b.level >= b.max_level():
                b.hp = b.current_hp()
            else:
                b.apply_upgrade()

    t = read_tokens()
    train_count = int(t[1])
    if train_count > 0:
        ids = read_tokens()
        enemy_trains = 0
        for i in range(train_count):
            wid = WarriorId.parse(ids[i])
            if wid.side is M.my_side.opposite:
                enemy_trains += 1
            hq_region = M.hq_of(wid.side)
            hq_b = S.find_building(hq_region)
            hq_level = hq_b.level if hq_b is not None else 1
            S.warriors.append(Warrior(wid, hq_region, HQ_LEVELS[hq_level].warrior_hp))
        if enemy_trains:
            S.enemy_gold = max(0, S.enemy_gold - TRAIN_COST * enemy_trains)

    for w in S.warriors:
        w.prev_region = w.region
        w.moved_last_turn = False

    t = read_tokens()
    for _ in range(int(t[1])):
        r = read_tokens()
        wid = WarriorId.parse(r[0])
        region = int(r[1])
        w = S.find_warrior(wid)
        if w is not None:
            old_region = w.region
            w.region = region
            w.prev_region = old_region
            w.moved_last_turn = old_region != region
            if wid.side is M.my_side and w.state is WState.MOVING and w.region == w.target:
                w.state = WState.STATIONARY

    t = read_tokens()
    for _ in range(int(t[1])):
        r = read_tokens()
        wid = WarriorId.parse(r[1])
        damage = int(r[2])
        w = S.find_warrior(wid)
        if w is not None:
            w.hp -= damage
    S.warriors = [w for w in S.warriors if w.hp > 0]

    t = read_tokens()
    for _ in range(int(t[1])):
        r = read_tokens()
        region = int(r[1])
        damage = int(r[2])
        b = S.find_building(region)
        if b is not None:
            b.hp -= damage
    S.buildings = [b for b in S.buildings if b.hp > 0]

    readln()

    S.gold = end_turn_gold(S, M, M.my_side, S.gold)
    S.enemy_gold = end_turn_gold(S, M, M.my_side.opposite, S.enemy_gold)


def euclid_ceil(M: GameMap, u: int, v: int) -> int:
    return math.ceil(math.hypot(M.x[u] - M.x[v], M.y[u] - M.y[v]))


def calculate_paths(M: GameMap) -> Paths:
    inf = math.inf
    hop_inf = 10**9
    N = M.N
    dist = [[inf] * N for _ in range(N)]
    nxt = [[-1] * N for _ in range(N)]
    hop = [[hop_inf] * N for _ in range(N)]

    for i in range(N):
        dist[i][i] = 0
        nxt[i][i] = i
        hop[i][i] = 0
    for u in range(N):
        for v in M.adj[u]:
            w = euclid_ceil(M, u, v)
            if w < dist[u][v]:
                dist[u][v] = w
            hop[u][v] = 1

    for k in range(N):
        dk = dist[k]
        hk = hop[k]
        for u in range(N):
            du = dist[u]
            base = du[k]
            if base != inf:
                for v in range(N):
                    cand = base + dk[v]
                    if cand < du[v]:
                        du[v] = cand

            hu = hop[u]
            hbase = hu[k]
            if hbase != hop_inf:
                for v in range(N):
                    cand = hbase + hk[v]
                    if cand < hu[v]:
                        hu[v] = cand

    for u in range(N):
        for v in range(N):
            if u == v or dist[u][v] == inf:
                continue
            best_score = inf
            for nb in M.adj[u]:
                if dist[nb][v] == inf:
                    continue
                score = euclid_ceil(M, u, nb) + dist[nb][v]
                if score < best_score:
                    best_score = score
                    nxt[u][v] = nb

    return Paths(dist, nxt, hop)


def emit(a: Actions) -> None:
    out = ["COMMAND"]
    for wid, target in a.moves:
        out.append(f"MOVE {wid} {target}")
    for region in a.upgrades:
        out.append(f"UPGRADE {region}")
    if a.train_n > 0:
        out.append(f"TRAIN {a.train_n}")
    out.append("END")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def my_warriors(S: GameState, M: GameMap) -> list[Warrior]:
    return [w for w in S.warriors if w.id.side is M.my_side]


def enemy_warriors(S: GameState, M: GameMap) -> list[Warrior]:
    return [w for w in S.warriors if w.id.side is M.my_side.opposite]


def occupied_by_enemy(S: GameState, M: GameMap) -> set[int]:
    return {w.region for w in enemy_warriors(S, M)}


def warrior_count_at(warriors: list[Warrior], region: int) -> int:
    return sum(1 for w in warriors if w.region == region)


def hp_sum_at(warriors: list[Warrior], region: int) -> int:
    return sum(w.hp for w in warriors if w.region == region)


def warrior_counts_by_region(warriors: list[Warrior]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for w in warriors:
        counts[w.region] = counts.get(w.region, 0) + 1
    return counts


def movement_ready_warriors(warriors: list[Warrior], enemy_regions: set[int]) -> list[Warrior]:
    return [w for w in warriors if w.state is WState.STATIONARY and w.region not in enemy_regions]


def one_step_reachable_regions(warriors: list[Warrior], M: GameMap) -> set[int]:
    regions: set[int] = set()
    for w in warriors:
        regions.add(w.region)
        regions.update(M.adj[w.region])
    return regions


def most_crowded_region(warriors: list[Warrior]) -> int | None:
    counts: dict[int, int] = {}
    for w in warriors:
        counts[w.region] = counts.get(w.region, 0) + 1
    if not counts:
        return None
    return max(counts, key=lambda r: (counts[r], -r))


def nearest_warrior_hop(warriors: list[Warrior], P: Paths, region: int) -> int:
    return min((P.hop[w.region][region] for w in warriors), default=10**9)


def nearby_warrior_count(warriors: list[Warrior], P: Paths, region: int, max_hop: int) -> int:
    return sum(1 for w in warriors if P.hop[w.region][region] <= max_hop)


def moving_toward(w: Warrior, P: Paths, region: int) -> bool:
    return w.moved_last_turn and w.prev_region >= 0 and P.dist[w.region][region] < P.dist[w.prev_region][region]


def side_plan_key(side: Side) -> str:
    return "left" if side is Side.LEFT else "right"


def valid_region_list(value: object, M: GameMap) -> list[int]:
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for item in value:
        if isinstance(item, int) and 0 <= item < M.N and item not in out:
            out.append(item)
    return out


def build_plan_for_side(M: GameMap, P: Paths, side: Side) -> dict[str, object]:
    hq = M.hq_of(side)
    opp = M.hq_of(side.opposite)
    rows = []
    for r in M.strongholds:
        if r in (0, M.N - 1):
            continue
        home_hop = P.hop[hq][r]
        opp_hop = P.hop[opp][r]
        if home_hop >= 10**8 or opp_hop >= 10**8:
            continue
        ratio = home_hop / max(1, home_hop + opp_hop)
        forward = r if side is Side.LEFT else M.N - 1 - r
        degree = len(M.adj[r])
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
    safe = [r for home, opp_hop, ratio, *_rest, r in rows if home <= opp_hop and ratio <= 0.56]
    if len(safe) < 3:
        safe = [r for home, opp_hop, ratio, *_rest, r in rows if home <= opp_hop and ratio <= 0.64]
    safe.sort(key=lambda r: (P.hop[hq][r], -P.hop[opp][r], -len(M.adj[r]), r))

    frontier_rows = [
        (abs(ratio - 0.5), home, neg_degree, r)
        for home, _opp_hop, ratio, neg_degree, _forward, r in rows
        if 0.40 <= ratio <= 0.64
    ]
    frontier = [r for *_prefix, r in sorted(frontier_rows)]
    max_cap = int(M.params.get("macro_max_bases", 8)) if M.params else 8
    max_bases = min(max_cap, max(3, len(safe)))
    schedule = [[18, 2, 5], [34, 3, 7]]
    if max_bases >= 4:
        schedule.append([62, 4, 10])
    if max_bases >= 5:
        schedule.append([92, 5, 13])
    if max_bases >= 6:
        schedule.append([122, 6, 16])
    if max_bases >= 7:
        schedule.append([150, 7, 20])
    if max_bases >= 8:
        schedule.append([168, 8, 24])
    return {
        "expansion_order": expansion,
        "safe_expansion_order": safe,
        "frontier_order": frontier,
        "stage_region": frontier[0] if frontier else (expansion[-1] if expansion else hq),
        "max_bases": max_bases,
        "base_targets": schedule,
    }


def map_plan(M: GameMap, P: Paths) -> dict[str, object]:
    raw = M.profile.get("plan")
    if isinstance(raw, dict) and isinstance(raw.get(side_plan_key(M.my_side)), dict):
        return raw
    cached = M.profile.get("_derived_plan")
    if isinstance(cached, dict):
        return cached
    derived = {
        "left": build_plan_for_side(M, P, Side.LEFT),
        "right": build_plan_for_side(M, P, Side.RIGHT),
    }
    M.profile["_derived_plan"] = derived
    return derived


def my_side_plan(M: GameMap, P: Paths) -> dict[str, object]:
    plan = map_plan(M, P)
    side = plan.get(side_plan_key(M.my_side))
    return side if isinstance(side, dict) else {}


def plan_regions(M: GameMap, P: Paths, key: str) -> list[int]:
    return valid_region_list(my_side_plan(M, P).get(key), M)


def clamp_int(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def policy_value(policy: object, index: int, default: int = 0) -> int:
    if isinstance(policy, list) and 0 <= index < len(policy) and isinstance(policy[index], int):
        return policy[index]
    return default


def state_policy(
    turn: int,
    M: GameMap,
    base_count: int,
    enemy_base_count: int,
    army_count: int,
    enemy_count: int,
    raw_enemy_home_hop: int,
    plan_max_bases: int,
    hq_level: int,
    enemy_hq_level: int,
) -> list[int]:
    data = load_data_profiles()
    table = data.get("policy_table") if isinstance(data, dict) else None
    if not isinstance(table, dict):
        return []
    entries = table.get("entries")
    if not isinstance(entries, dict):
        return []

    if turn < 18:
        phase = 0
    elif turn < 40:
        phase = 1
    elif turn < 75:
        phase = 2
    elif turn < 120:
        phase = 3
    else:
        phase = 4

    base_gap = clamp_int(enemy_base_count - base_count, -2, 7)
    army_gap = enemy_count - army_count
    if army_gap <= -4:
        army_bucket = 0
    elif army_gap <= 0:
        army_bucket = 1
    elif army_gap <= 3:
        army_bucket = 2
    elif army_gap <= 6:
        army_bucket = 3
    else:
        army_bucket = 4

    if raw_enemy_home_hop >= 10**8 or raw_enemy_home_hop > 8:
        threat = 0
    elif raw_enemy_home_hop > 5:
        threat = 1
    elif raw_enemy_home_hop > 2:
        threat = 2
    else:
        threat = 3

    safe = clamp_int(plan_max_bases, 0, 8)
    tech_gap = clamp_int(enemy_hq_level - hq_level, -1, 3)
    key = f"{phase}:{base_gap}:{army_bucket}:{threat}:{safe}:{tech_gap}"
    entry = entries.get(key)
    return entry if isinstance(entry, list) else []


def count_bucket(value: int) -> int:
    if value <= 3:
        return 0
    if value <= 5:
        return 1
    if value <= 8:
        return 2
    if value <= 12:
        return 3
    if value <= 18:
        return 4
    return 5


def hp_bucket(hp: int, max_hp: int) -> int:
    if hp <= 0:
        return 0
    ratio = hp / max(1, max_hp)
    if ratio <= 0.25:
        return 1
    if ratio <= 0.50:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def reinforcement_bucket(hop: int) -> int:
    if hop >= 10**8 or hop > 8:
        return 0
    if hop > 5:
        return 1
    if hop > 3:
        return 2
    if hop > 1:
        return 3
    return 4


def range_bucket(value: int, limits: tuple[int, ...]) -> int:
    for i, limit in enumerate(limits):
        if value <= limit:
            return i
    return len(limits)


def map_policy(M: GameMap, P: Paths) -> list[int]:
    data = load_data_profiles()
    table = data.get("map_policy_table") if isinstance(data, dict) else None
    if not isinstance(table, dict):
        return []
    entries = table.get("entries")
    if not isinstance(entries, dict):
        return []
    plan = my_side_plan(M, P)
    safe = len(plan_regions(M, P, "safe_expansion_order"))
    expansion = plan_regions(M, P, "expansion_order")
    first_base = expansion[0] if expansion else M.my_hq
    stage = staging_region(M, P)
    key = (
        f"{range_bucket(P.hop[M.my_hq][M.opp_hq], (5, 8, 11))}:"
        f"{clamp_int(safe, 0, 8)}:"
        f"{range_bucket(P.hop[M.my_hq][first_base], (1, 2, 3))}:"
        f"{range_bucket(P.hop[M.my_hq][stage], (3, 5, 7))}"
    )
    entry = entries.get(key)
    return entry if isinstance(entry, list) else []


def building_turret(b: Building | None) -> int:
    if b is None:
        return 0
    return HQ_LEVELS[b.level].turret if b.type is BType.HQ else BASE_LEVELS[b.level].turret


def battle_policy(
    kind: str,
    turn: int,
    attackers: int,
    defenders: int,
    turret: int,
    hp: int,
    max_hp: int,
    reinforcement_hop: int,
    hq_level: int,
    enemy_hq_level: int,
) -> list[int]:
    data = load_data_profiles()
    table = data.get("battle_table") if isinstance(data, dict) else None
    if not isinstance(table, dict):
        return []
    entries = table.get("entries")
    if not isinstance(entries, dict):
        return []

    if turn < 18:
        phase = 0
    elif turn < 40:
        phase = 1
    elif turn < 75:
        phase = 2
    elif turn < 120:
        phase = 3
    else:
        phase = 4

    kind_id = 1 if kind == "hq" else 0
    key = (
        f"{kind_id}:{phase}:{count_bucket(attackers)}:{count_bucket(defenders)}:"
        f"{clamp_int(turret, 0, 3)}:{hp_bucket(hp, max_hp)}:"
        f"{reinforcement_bucket(reinforcement_hop)}:{clamp_int(enemy_hq_level - hq_level, -1, 3)}"
    )
    entry = entries.get(key)
    return entry if isinstance(entry, list) else []


def contest_policy(
    turn: int,
    base_count: int,
    enemy_base_count: int,
    army_count: int,
    enemy_count: int,
    raw_enemy_home_hop: int,
    target_home_hop: int,
    enemy_base: bool,
) -> list[int]:
    data = load_data_profiles()
    table = data.get("contest_table") if isinstance(data, dict) else None
    if not isinstance(table, dict):
        return []
    entries = table.get("entries")
    if not isinstance(entries, dict):
        return []

    if turn < 18:
        phase = 0
    elif turn < 40:
        phase = 1
    elif turn < 75:
        phase = 2
    elif turn < 120:
        phase = 3
    else:
        phase = 4

    base_gap = clamp_int(enemy_base_count - base_count, -1, 5)
    army_gap = enemy_count - army_count
    if army_gap <= -4:
        army_bucket = 0
    elif army_gap <= 0:
        army_bucket = 1
    elif army_gap <= 3:
        army_bucket = 2
    elif army_gap <= 6:
        army_bucket = 3
    else:
        army_bucket = 4

    if raw_enemy_home_hop >= 10**8 or raw_enemy_home_hop > 8:
        threat = 0
    elif raw_enemy_home_hop > 5:
        threat = 1
    elif raw_enemy_home_hop > 2:
        threat = 2
    else:
        threat = 3

    key = (
        f"{phase}:{base_gap}:{army_bucket}:{threat}:"
        f"{range_bucket(target_home_hop, (2, 4, 6, 8))}:{1 if enemy_base else 0}"
    )
    entry = entries.get(key)
    return entry if isinstance(entry, list) else []


def mass_bucket(value: int) -> int:
    if value <= 8:
        return 0
    if value <= 16:
        return 1
    if value <= 28:
        return 2
    if value <= 44:
        return 3
    return 4


def defense_policy(
    turn: int,
    enemy_hq_stack: int,
    army_count: int,
    enemy_count: int,
    raw_enemy_home_hop: int,
    base_gap: int,
) -> list[int]:
    data = load_data_profiles()
    table = data.get("defense_table") if isinstance(data, dict) else None
    if not isinstance(table, dict):
        return []
    entries = table.get("entries")
    if not isinstance(entries, dict):
        return []

    if turn < 120:
        phase = 0
    elif turn < 150:
        phase = 1
    elif turn < 175:
        phase = 2
    else:
        phase = 3

    army_gap = enemy_count - army_count
    if army_gap <= -6:
        army_bucket = 0
    elif army_gap <= 0:
        army_bucket = 1
    elif army_gap <= 8:
        army_bucket = 2
    else:
        army_bucket = 3

    if raw_enemy_home_hop >= 10**8 or raw_enemy_home_hop > 8:
        threat = 0
    elif raw_enemy_home_hop > 5:
        threat = 1
    elif raw_enemy_home_hop > 2:
        threat = 2
    else:
        threat = 3

    key = (
        f"{phase}:{mass_bucket(enemy_hq_stack)}:{army_bucket}:"
        f"{threat}:{clamp_int(base_gap, -2, 7)}"
    )
    entry = entries.get(key)
    return entry if isinstance(entry, list) else []


def home_intercept_policy(
    turn: int,
    enemy_stack: int,
    available_interceptors: int,
    hq_level: int,
    target_hop: int,
) -> list[int]:
    data = load_data_profiles()
    table = data.get("home_intercept_table") if isinstance(data, dict) else None
    if not isinstance(table, dict):
        return []
    entries = table.get("entries")
    if not isinstance(entries, dict):
        return []

    if turn < 18:
        phase = 0
    elif turn < 40:
        phase = 1
    elif turn < 75:
        phase = 2
    elif turn < 120:
        phase = 3
    else:
        phase = 4

    key = (
        f"{phase}:{count_bucket(enemy_stack)}:{count_bucket(available_interceptors)}:"
        f"{clamp_int(hq_level, 1, HQ_MAX_LEVEL)}:{range_bucket(target_hop, (1, 2, 3))}"
    )
    entry = entries.get(key)
    return entry if isinstance(entry, list) else []


def nearest_open_strongholds(S: GameState, M: GameMap, P: Paths) -> list[int]:
    building_by_region = {b.region: b for b in S.buildings}
    occupied = set(building_by_region)
    mine = my_warriors(S, M)
    enemies = enemy_warriors(S, M)
    enemy_regions = occupied_by_enemy(S, M)
    raw_enemy_home_hop = min((P.hop[w.region][M.my_hq] for w in enemies if w.region != M.opp_hq), default=10**9)
    defensive_mode = raw_enemy_home_hop <= M.params["base_worker_threat_hop"] + 1
    planned = plan_regions(M, P, "safe_expansion_order" if defensive_mode else "expansion_order")
    safe_planned = set(plan_regions(M, P, "safe_expansion_order"))
    planned_rank = {r: i for i, r in enumerate(planned)}
    safe_available = any(
        r not in occupied and r not in enemy_regions
        for r in safe_planned
    )
    builders = [w for w in mine if w.state is WState.STATIONARY] or mine
    my_buildings = [b for b in S.buildings if b.side is M.my_side]
    enemy_buildings = [b for b in S.buildings if b.side is M.my_side.opposite]
    items = []
    for r in M.strongholds:
        if r in occupied or r in enemy_regions:
            continue
        if defensive_mode and safe_available and r not in safe_planned:
            continue
        d_home = P.dist[M.my_hq][r]
        d_opp = P.dist[M.opp_hq][r]
        forward = r if M.my_side is Side.LEFT else M.N - 1 - r
        builder_hop = nearest_warrior_hop(builders, P, r)
        my_near = nearby_warrior_count(mine, P, r, 2)
        enemy_near1 = nearby_warrior_count(enemies, P, r, 1)
        enemy_near2 = nearby_warrior_count(enemies, P, r, 2)
        if enemy_near2 >= 3 and my_near == 0:
            continue
        my_build_hop = min((P.hop[b.region][r] for b in my_buildings), default=P.hop[M.my_hq][r])
        enemy_build_hop = min((P.hop[b.region][r] for b in enemy_buildings), default=P.hop[M.opp_hq][r])
        mirror = M.N - 1 - r
        mirror_building = building_by_region.get(mirror)
        mirror_enemy_base = 1 if mirror_building is not None and mirror_building.side is M.my_side.opposite else 0
        path_total = max(1.0, d_home + d_opp)
        front_ratio = d_home / path_total
        overextended = max(0.0, front_ratio - 0.62)
        base_score = d_home - M.params["stronghold_enemy_distance_weight"] * d_opp
        state_score = 45 * builder_hop
        state_score += 24 * (my_build_hop - enemy_build_hop)
        state_score += 380 * enemy_near1 + 480 * enemy_near2
        state_score -= 45 * my_near
        state_score -= 18 * len(M.adj[r])
        state_score += 2200 * mirror_enemy_base
        state_score += 450 * overextended
        rank = planned_rank.get(r, len(planned) + 3)
        score = base_score + state_score + rank * (1200 if defensive_mode else 700)
        items.append((score, builder_hop, -forward, r))
    items.sort()
    return [r for *_, r in items]


def can_upgrade_here(S: GameState, M: GameMap, region: int) -> bool:
    if region not in M.strongholds and region not in (0, M.N - 1):
        return False
    if any(w.region == region and w.id.side is M.my_side.opposite for w in S.warriors):
        return False
    return any(w.region == region and w.id.side is M.my_side for w in S.warriors)


def staging_region(M: GameMap, P: Paths) -> int:
    planned = my_side_plan(M, P).get("stage_region")
    if isinstance(planned, int) and 0 <= planned < M.N and planned != M.my_hq:
        return planned
    u = M.my_hq
    prev = u
    seen: set[int] = set()
    while u != M.opp_hq and u not in seen:
        seen.add(u)
        nxt = P.nxt[u][M.opp_hq]
        if nxt < 0:
            break
        prev = u
        u = nxt
    return prev


def home_choke_region(M: GameMap, P: Paths, hop_from_home: int) -> int:
    u = M.opp_hq
    path = [u]
    seen: set[int] = set()
    while u != M.my_hq and u not in seen:
        seen.add(u)
        nxt = P.nxt[u][M.my_hq]
        if nxt < 0:
            break
        u = nxt
        path.append(u)
    candidates = [
        r for r in path
        if r != M.my_hq and P.hop[M.my_hq][r] <= hop_from_home
    ]
    if candidates:
        return max(candidates, key=lambda r: (P.hop[M.my_hq][r], -P.hop[r][M.opp_hq], -r))
    nxt = P.nxt[M.my_hq][M.opp_hq]
    return nxt if nxt >= 0 else M.my_hq


def enemy_economy_target(S: GameState, M: GameMap, P: Paths) -> int | None:
    mine = my_warriors(S, M)
    enemies = enemy_warriors(S, M)
    enemy_bases = [
        b
        for b in S.buildings
        if b.side is M.my_side.opposite and b.type is BType.BASE
    ]
    if not enemy_bases:
        return None
    enemy_bases.sort(
        key=lambda b: (
            warrior_count_at(enemies, b.region),
            hp_sum_at(enemies, b.region),
            sum(1 for w in enemies if moving_toward(w, P, b.region) and P.hop[w.region][b.region] <= 2),
            nearest_warrior_hop(mine, P, b.region),
            P.hop[M.my_hq][b.region],
            b.hp,
            -b.level,
            -min(warrior_count_at(enemies, b.region), b.work_cap()),
            -P.hop[b.region][M.opp_hq],
            b.region,
        )
    )
    return enemy_bases[0].region


def decide(S: GameState, M: GameMap, P: Paths, turn: int) -> Actions:
    a = Actions()
    reserved_gold = S.gold
    moved: set[WarriorId] = set()
    upgrade_regions: set[int] = set()

    mine = my_warriors(S, M)
    enemies = enemy_warriors(S, M)
    enemy_alive = len(enemies)
    idle = [w for w in mine if w.state is WState.STATIONARY]
    idle.sort(key=lambda w: (P.hop[w.region][M.opp_hq], P.dist[w.region][M.opp_hq], w.id.num))
    enemy_regions = set(warrior_counts_by_region(enemies))
    move_ready_idle_ids = {w.id for w in movement_ready_warriors(idle, enemy_regions)}
    base_count = sum(1 for b in S.buildings if b.side is M.my_side and b.type is BType.BASE)
    enemy_base_count = sum(1 for b in S.buildings if b.side is M.my_side.opposite and b.type is BType.BASE)
    if M.map_hash == "5fc20ca6f1d9" and turn >= 25 and enemy_base_count >= 3:
        M.params.update(
            {
                "target_army_base_early": 14,
                "target_army_base_late_base": 12,
                "target_army_late_cap": 26,
                "target_army_dynamic_cap": 34,
                "score_hq_upgrade_turn": 999,
                "late_hq_reserve_turn": 999,
                "stale_hq2_turn": 999,
                "late_pressure_hq2_turn": 999,
                "force_hq2_turn": 999,
                "urgent_defense_hop": 5,
                "urgent_defense_home_keep": 8,
                "base_worker_threat_hop": 8,
                "base_worker_abandon_home_hop": 4,
                "base_worker_home_keep": 8,
                "base_worker_pressure_home_keep": 10,
                "disable_economy_counter": 0,
                "economy_counter_min_army": 5,
                "economy_counter_fast_min_army": 4,
                "economy_counter_probe_min_army": 4,
                "first_attack_start_no_base": 16,
                "first_attack_start_with_base": 16,
                "early_attack_min_army": 7,
                "mass_attack_release_turn": 80,
            }
        )
    enemy_opp_hq_count = sum(1 for w in enemies if w.region == M.opp_hq)
    turtle_like = turn >= M.params["turtle_detect_turn"] and enemy_opp_hq_count >= M.params["turtle_enemy_hq_count"]
    late_mass_recall = (
        turn >= M.params["late_mass_recall_turn"]
        and enemy_opp_hq_count >= M.params["late_mass_recall_enemy_hq"]
        and not any(w.region == M.my_hq for w in enemies)
    )
    threatening_enemies = [
        w for w in enemies
        if w.region != M.opp_hq
    ]
    raw_enemy_home_hop = min((P.hop[w.region][M.my_hq] for w in threatening_enemies), default=10**9)
    holding_enemies = []
    for w in threatening_enemies:
        b = S.find_building(w.region)
        if (
            b is not None
            and b.side is M.my_side.opposite
            and P.hop[w.region][M.my_hq] > 3
            and P.hop[w.region][M.my_hq] > P.hop[w.region][M.opp_hq]
        ):
            continue
        holding_enemies.append(w)
    enemy_home_hop = min((P.hop[w.region][M.my_hq] for w in holding_enemies), default=10**9)
    enemy_pressure_count = sum(1 for w in holding_enemies if P.hop[w.region][M.my_hq] <= M.params["enemy_home_pressure_hop"])
    home_garrison_target = M.params["home_garrison_under_pressure"] if enemy_pressure_count > 0 else 1
    profile_tuned = any(key in M.profile for key in ("mode", "params", "tech_catchup"))
    adaptive_unknown = not profile_tuned
    urgent_home_threat = (
        (
            profile_tuned
            and (
                any(w.region == M.my_hq for w in enemies)
                or raw_enemy_home_hop <= M.params["urgent_defense_hop"]
            )
        )
        or (
            adaptive_unknown
            and (
                any(w.region == M.my_hq for w in enemies)
                or raw_enemy_home_hop <= 2
            )
        )
    )
    adaptive_economy_clear = (
        adaptive_unknown
        and M.params["adaptive_economy_enabled"] > 0
        and not urgent_home_threat
        and not any(w.region == M.my_hq for w in enemies)
        and enemy_home_hop > 2
    )
    urgent_army_target = min(
        M.params["urgent_defense_army_cap"],
        max(
            M.params["urgent_defense_home_keep"],
            enemy_pressure_count + M.params["urgent_defense_enemy_margin"],
        ),
    )
    mass_home_threat = (
        turn >= M.params["mass_home_threat_turn"]
        and enemy_pressure_count >= M.params["mass_home_threat_min_enemies"]
        and enemy_pressure_count >= len(mine)
        and raw_enemy_home_hop <= M.params["enemy_home_recall_hop"]
    )
    if urgent_home_threat or mass_home_threat:
        home_garrison_target = max(home_garrison_target, M.params["urgent_defense_home_keep"])
    if late_mass_recall:
        home_garrison_target = max(home_garrison_target, min(len(mine), M.params["late_mass_recall_home_keep"]))
    safe_enemy_economy = enemy_base_count >= 2 and enemy_home_hop > M.params["enemy_home_hold_hop"]
    economy_threat = (
        turn >= M.params["economy_threat_turn"]
        and enemy_base_count >= M.params["economy_threat_enemy_bases"]
        and enemy_base_count >= base_count + M.params["economy_threat_base_gap"]
        and raw_enemy_home_hop > M.params["enemy_home_recall_hop"]
    )
    economy_boom = (
        turn >= M.params["economy_boom_turn"]
        and enemy_base_count >= M.params["economy_boom_enemy_bases"]
        and enemy_base_count >= base_count + M.params["economy_boom_base_gap"]
        and enemy_home_hop > 3
        and not any(w.region == M.my_hq for w in enemies)
    )
    early_economy = (
        turn >= M.params["early_economy_turn"]
        and enemy_base_count >= M.params["early_economy_enemy_bases"]
        and enemy_base_count >= base_count + M.params["early_economy_base_gap"]
        and enemy_home_hop > M.params["early_economy_home_hop"]
        and not any(w.region == M.my_hq for w in enemies)
    )
    hq = S.find_building(M.my_hq)
    enemy_hq = S.find_building(M.opp_hq)
    enemy_hq_level = (
        enemy_hq.level
        if enemy_hq is not None and enemy_hq.side is M.my_side.opposite and enemy_hq.type is BType.HQ
        else 0
    )
    tech_catchup_enabled = M.profile.get("tech_catchup") is True or adaptive_unknown
    enemy_can_upgrade_hq = (
        enemy_hq is not None
        and enemy_hq.side is M.my_side.opposite
        and enemy_hq.type is BType.HQ
        and enemy_hq.level < enemy_hq.max_level()
        and S.enemy_gold >= enemy_hq.upgrade_cost()
    )
    economy_alert = economy_threat or economy_boom or early_economy
    economy_gap = enemy_base_count - base_count
    losing_economy = economy_gap >= M.params["catchup_expand_base_gap"] and enemy_base_count >= 4
    if hq is not None and hq.level == 1 and economy_alert and base_count >= 1:
        S.economy_hq2_latched = True
    elif hq is not None and hq.level >= 2:
        S.economy_hq2_latched = False
    forced_economy_hq2 = (
        hq is not None
        and hq.level == 1
        and turn >= M.params["forced_economy_hq2_turn"]
        and base_count >= 1
        and enemy_base_count >= M.params["forced_economy_hq2_enemy_bases"]
        and enemy_base_count >= base_count + M.params["forced_economy_hq2_base_gap"]
        and not any(w.region == M.my_hq for w in enemies)
        and len(mine) >= M.params["economy_hq2_min_army"]
    )
    tech_catchup_hq2 = (
        tech_catchup_enabled
        and hq is not None
        and hq.level == 1
        and base_count >= 1
        and turn >= 42
        and (enemy_hq_level >= 2 or enemy_can_upgrade_hq)
        and not any(w.region == M.my_hq for w in enemies)
        and len(mine) >= M.params["economy_hq2_min_army"]
    )
    economy_hq2 = (
        economy_alert
        or S.economy_hq2_latched
        or forced_economy_hq2
        or tech_catchup_hq2
    ) and base_count >= 1
    economy_probe = turn < M.params["early_economy_turn"] and safe_enemy_economy and enemy_base_count > base_count
    economy_target = enemy_economy_target(S, M, P) if (economy_alert or economy_probe or losing_economy) else None
    economy_target_enemy_count = warrior_count_at(enemies, economy_target) if economy_target is not None else 10**9
    economy_target_my_hop = nearest_warrior_hop(mine, P, economy_target) if economy_target is not None else 10**9
    economy_counter_defender_cap = M.params["economy_counter_max_target_defenders"]
    if losing_economy and len(mine) >= 10:
        economy_counter_defender_cap = max(economy_counter_defender_cap, 2 if len(mine) < 12 else 3)
    economy_counter_min_army = M.params["economy_counter_min_army"]
    if economy_target_enemy_count <= economy_counter_defender_cap:
        if economy_target_my_hop <= M.params["economy_counter_fast_near_hop"] and (early_economy or economy_boom):
            economy_counter_min_army = M.params["economy_counter_fast_min_army"]
        elif economy_target_my_hop <= M.params["economy_counter_probe_near_hop"]:
            economy_counter_min_army = M.params["economy_counter_probe_min_army"]

    pressure_hq2 = base_count >= 1 and (enemy_pressure_count > 0 or (hq is not None and hq.hp <= 7 and turn >= 25))
    turtle_hq2 = turtle_like and base_count >= 3
    late_pressure_hq2 = (
        hq is not None
        and hq.level == 1
        and turn >= M.params["late_pressure_hq2_turn"]
        and pressure_hq2
        and base_count >= 1
        and hq.hp >= M.params["late_pressure_hq2_min_hp"]
        and not any(w.region == M.my_hq for w in enemies)
        and enemy_alive <= len(mine) + M.params["target_army_enemy_margin"]
        and len(mine) >= M.params["late_pressure_hq2_min_army"]
    )
    stale_hq2 = (
        hq is not None
        and hq.level == 1
        and turn >= M.params["stale_hq2_turn"]
        and base_count >= 1
        and enemy_pressure_count == 0
        and not economy_alert
        and not any(w.region == M.my_hq for w in enemies)
        and len(mine) >= M.params["stale_hq2_min_army"]
    )
    force_hq2 = (
        hq is not None
        and hq.level == 1
        and turn >= M.params["force_hq2_turn"]
        and base_count >= 1
        and not any(w.region == M.my_hq for w in enemies)
        and len(mine) >= M.params["force_hq2_min_army"]
    )
    tech_catchup_hq3 = (
        tech_catchup_enabled
        and hq is not None
        and hq.level == 2
        and turn >= M.params["stale_hq3_turn"]
        and base_count >= M.params["stale_hq3_min_bases"]
        and len(mine) >= M.params["stale_hq3_min_army"]
        and (enemy_hq_level >= 3 or enemy_can_upgrade_hq or S.enemy_gold >= HQ_LEVELS[3].upgrade_cost)
        and not any(w.region == M.my_hq for w in enemies)
    )
    stale_hq3 = tech_catchup_hq3 or (
        hq is not None
        and hq.level == 2
        and turn >= M.params["stale_hq3_turn"]
        and base_count >= M.params["stale_hq3_min_bases"]
        and len(mine) >= M.params["stale_hq3_min_army"]
        and enemy_alive <= len(mine) + M.params["target_army_enemy_margin"]
        and not any(w.region == M.my_hq for w in enemies)
    )
    tech_catchup_hq4 = (
        tech_catchup_enabled
        and hq is not None
        and hq.level == 3
        and turn >= M.params["stale_hq4_turn"]
        and base_count >= M.params["stale_hq4_min_bases"]
        and len(mine) >= M.params["stale_hq4_min_army"]
        and (enemy_hq_level >= 4 or (enemy_can_upgrade_hq and enemy_hq_level >= 3) or S.enemy_gold >= HQ_LEVELS[4].upgrade_cost)
        and not any(w.region == M.my_hq for w in enemies)
    )
    tech_catchup_hq5 = (
        tech_catchup_enabled
        and hq is not None
        and hq.level == 4
        and turn >= M.params["stale_hq5_turn"]
        and base_count >= M.params["stale_hq5_min_bases"]
        and len(mine) >= M.params["stale_hq5_min_army"]
        and (enemy_hq_level >= 5 or (enemy_can_upgrade_hq and enemy_hq_level >= 4))
        and not any(w.region == M.my_hq for w in enemies)
    )
    force_hq3 = (
        hq is not None
        and hq.level == 2
        and turn >= M.params["force_hq3_turn"]
        and base_count >= M.params["force_hq3_min_bases"]
        and len(mine) >= M.params["force_hq3_min_army"]
        and not any(w.region == M.my_hq for w in enemies)
    )
    force_hq4 = (
        hq is not None
        and hq.level == 3
        and turn >= M.params["force_hq4_turn"]
        and base_count >= M.params["force_hq4_min_bases"]
        and len(mine) >= M.params["force_hq4_min_army"]
        and not any(w.region == M.my_hq for w in enemies)
    )
    force_hq5 = (
        hq is not None
        and hq.level == 4
        and turn >= M.params["force_hq5_turn"]
        and base_count >= M.params["force_hq5_min_bases"]
        and len(mine) >= M.params["force_hq5_min_army"]
        and not any(w.region == M.my_hq for w in enemies)
    )
    adaptive_hq3 = (
        adaptive_economy_clear
        and hq is not None
        and hq.level == 2
        and turn >= 92
        and base_count >= 2
        and len(mine) >= 8
        and enemy_alive <= len(mine) + M.params["target_army_enemy_margin"]
    )
    adaptive_hq4 = (
        adaptive_economy_clear
        and hq is not None
        and hq.level == 3
        and turn >= 128
        and base_count >= 2
        and len(mine) >= 12
        and enemy_alive <= len(mine) + M.params["target_army_enemy_margin"]
    )
    score_hq_upgrade_needed = (
        hq is not None
        and hq.level < hq.max_level()
        and turn >= M.params["score_hq_upgrade_turn"]
        and base_count >= M.params["score_hq_min_bases"]
        and len(mine) >= M.params["score_hq_min_army"]
        and not any(w.region == M.my_hq for w in enemies)
        and (
            enemy_hq_level > hq.level
            or turn >= M.params["late_hq_lock_turn"]
            or hq.level <= 2
        )
    )
    late_hq_upgrade_needed = (
        stale_hq3
        or tech_catchup_hq4
        or tech_catchup_hq5
        or force_hq3
        or force_hq4
        or force_hq5
        or adaptive_hq3
        or adaptive_hq4
        or score_hq_upgrade_needed
    )
    late_hq_next_cost = (
        hq.upgrade_cost()
        if hq is not None and hq.level < hq.max_level()
        else HQ_LEVELS[3].upgrade_cost
    )
    late_hq_reserve_active = (
        hq is not None
        and hq.level < hq.max_level()
        and turn >= M.params["late_hq_reserve_turn"]
        and len(mine) >= M.params["late_hq_reserve_min_army"]
        and not any(w.region == M.my_hq for w in enemies)
        and (
            enemy_hq_level > hq.level
            or enemy_can_upgrade_hq
            or turn >= M.params["score_hq_upgrade_turn"]
            or late_hq_upgrade_needed
        )
    )
    late_hq_lockdown = (
        hq is not None
        and hq.level < hq.max_level()
        and turn >= M.params["late_hq_lock_turn"]
        and (enemy_hq_level > hq.level or late_hq_reserve_active)
    )
    hq_missing_hp = (
        hq.current_hp() - hq.hp
        if hq is not None and hq.level >= hq.max_level()
        else 0
    )
    hq_heal_emergency = (
        hq is not None
        and hq.level >= hq.max_level()
        and hq.hp <= M.params["hq_heal_emergency_hp"]
        and raw_enemy_home_hop <= M.params["urgent_defense_hop"] + 1
    )
    hq_heal_needed = (
        hq is not None
        and hq.level >= hq.max_level()
        and M.my_hq not in upgrade_regions
        and hq_missing_hp > 0
        and can_upgrade_here(S, M, M.my_hq)
        and (
            hq_heal_emergency
            or (
                turn >= M.params["hq_heal_turn"]
                and hq_missing_hp >= M.params["hq_heal_missing_hp"]
            )
            or (
                turn >= 195
                and enemy_hq is not None
                and enemy_hq.side is M.my_side.opposite
                and hq.hp < enemy_hq.hp
            )
        )
    )
    hq_heal_buffer = 0 if hq_heal_emergency else M.params["hq_heal_gold_buffer"]
    hq_heal_reserve_active = (
        hq is not None
        and hq.level >= hq.max_level()
        and turn >= M.params["hq_heal_turn"]
        and not any(w.region == M.my_hq for w in enemies)
        and (
            enemy_alive >= len(mine) + M.params["target_army_enemy_margin"]
            or raw_enemy_home_hop <= M.params["enemy_home_recall_hop"] + 2
            or turn >= 190
        )
    )
    if late_mass_recall:
        urgent_army_target = max(urgent_army_target, min(M.params["urgent_defense_army_cap"], enemy_opp_hq_count + 5))
    urgent_training_needed = (urgent_home_threat or mass_home_threat or late_mass_recall) and len(mine) < urgent_army_target
    hq2_gold_candidate = (
        hq is not None
        and hq.level == 1
        and (economy_hq2 or stale_hq2 or late_pressure_hq2 or force_hq2)
        and base_count >= 1
    )

    plan = my_side_plan(M, P)
    map_hint = map_policy(M, P)
    plan_max_bases = plan.get("max_bases")
    if not isinstance(plan_max_bases, int):
        plan_max_bases = 0
    hinted_max_bases = policy_value(map_hint, 0, 0)
    if hinted_max_bases > 0 and not urgent_home_threat and not any(w.region == M.my_hq for w in enemies):
        plan_max_bases = max(plan_max_bases, hinted_max_bases)
    plan_max_bases = min(plan_max_bases, int(M.params["macro_max_bases"]))
    mode = M.profile.get("mode")
    if mode == "turtle_tech":
        plan_max_bases = min(plan_max_bases, int(M.params["turtle_desired_bases"]))
    elif mode != "fast_economy" and not losing_economy:
        plan_max_bases = min(plan_max_bases, 3)
    policy = [] if mode == "rush" else state_policy(
        turn,
        M,
        base_count,
        enemy_base_count,
        len(mine),
        enemy_alive,
        raw_enemy_home_hop,
        plan_max_bases,
        hq.level if hq is not None else 1,
        enemy_hq_level,
    )
    home_garrison_target = max(home_garrison_target, policy_value(policy, 2, 0))

    desired_bases = 1
    if turtle_like:
        desired_bases = 1 if base_count == 0 else int(M.params["turtle_desired_bases"])
    elif base_count > 0 and (
        safe_enemy_economy
        or turn >= M.params["desired_base2_turn"]
    ):
        desired_bases = 2
    if not turtle_like and (
        (safe_enemy_economy and enemy_base_count >= 3 and turn >= M.params["late_economy_turn"])
        or (turn >= M.params["desired_base3_turn"] and len(mine) >= M.params["desired_base3_min_army"])
    ):
        desired_bases = 3
    if adaptive_economy_clear:
        if turn >= 24 and len(mine) >= 5:
            desired_bases = max(desired_bases, 2)
        if turn >= 55 and base_count >= 1 and len(mine) >= 7:
            desired_bases = max(desired_bases, 3)
    if economy_alert and base_count >= 1 and len(mine) >= M.params["min_army_before_extra_base"]:
        desired_bases = max(desired_bases, min(plan_max_bases or M.params["macro_max_bases"], enemy_base_count - 1))
    if (
        losing_economy
        and turn >= M.params["catchup_expand_turn"]
        and base_count >= 1
        and len(mine) >= M.params["catchup_expand_min_army"]
        and plan_max_bases > 0
    ):
        desired_bases = max(desired_bases, min(plan_max_bases, enemy_base_count))
    if plan_max_bases > 0 and not urgent_home_threat and not any(w.region == M.my_hq for w in enemies):
        for entry in plan.get("base_targets", []):
            if not (isinstance(entry, list) and len(entry) >= 2):
                continue
            turn_req, target_req = entry[0], entry[1]
            army_req = entry[2] if len(entry) >= 3 and isinstance(entry[2], int) else 0
            if not isinstance(turn_req, int) or not isinstance(target_req, int):
                continue
            safe_to_spread = enemy_home_hop > M.params["base_worker_threat_hop"] + 1
            if turn >= turn_req and target_req <= plan_max_bases and (len(mine) >= army_req or safe_to_spread or losing_economy):
                desired_bases = max(desired_bases, target_req)
        if losing_economy and base_count > 0:
            desired_bases = max(desired_bases, min(plan_max_bases, max(3, enemy_base_count)))
    if map_hint and mode == "turtle_tech" and plan_max_bases > 0 and not urgent_home_threat and not any(w.region == M.my_hq for w in enemies):
        for turn_idx, target_req in ((1, 2), (2, 3), (3, 4), (4, 5), (12, 6), (14, 7)):
            turn_req = policy_value(map_hint, turn_idx, 999)
            army_idx = turn_idx + 4 if turn_idx <= 4 else turn_idx + 1
            army_req = policy_value(map_hint, army_idx, 0)
            if turn >= turn_req and target_req <= plan_max_bases and (len(mine) >= army_req or losing_economy):
                desired_bases = max(desired_bases, target_req)

    policy_desired = policy_value(policy, 0, 0)
    policy_cap = policy_value(policy, 1, 0)
    if policy_desired > 0 and not urgent_home_threat and not any(w.region == M.my_hq for w in enemies):
        desired_bases = max(desired_bases, min(policy_desired, plan_max_bases or policy_desired))
    if policy_cap > 0 and not losing_economy and not safe_enemy_economy and not economy_alert:
        desired_bases = min(max(base_count, desired_bases), max(base_count, policy_cap))
    pre_hq2_base_cap = int(M.params["pre_hq2_base_cap"])
    if hq2_gold_candidate and hq is not None and hq.level == 1 and pre_hq2_base_cap > 0:
        desired_bases = min(desired_bases, max(base_count, pre_hq2_base_cap))

    if (
        hq_heal_needed
        and reserved_gold >= HQ_HEAL_COST + hq_heal_buffer
    ):
        a.upgrades.append(M.my_hq)
        upgrade_regions.add(M.my_hq)
        reserved_gold -= HQ_HEAL_COST

    def open_build_target(region: int) -> bool:
        return (
            region in M.strongholds
            and S.find_building(region) is None
            and not any(w.region == region and w.id.side is M.my_side.opposite for w in S.warriors)
        )

    pending_build_regions = {
        (w.target if w.state is WState.MOVING else w.region)
        for w in mine
        if open_build_target(w.target if w.state is WState.MOVING else w.region)
    }
    max_new_bases = max(0, desired_bases - base_count)
    direct_build_slots = max(0, max_new_bases - len(pending_build_regions))
    direct_build_regions = set()
    if direct_build_slots > 0:
        for region in nearest_open_strongholds(S, M, P):
            if region in pending_build_regions:
                continue
            direct_build_regions.add(region)
            if len(direct_build_regions) >= direct_build_slots:
                break
    buildable_new_regions = pending_build_regions | direct_build_regions
    expansion_upgrade_blocked = losing_economy and base_count < desired_bases and bool(buildable_new_regions)
    if (
        expansion_upgrade_blocked
        and hq is not None
        and hq.level >= 2
        and base_count >= 4
        and enemy_hq_level > hq.level
        and turn >= M.params["late_hq_upgrade_turn"]
    ):
        expansion_upgrade_blocked = False
    scheduled_new_bases = 0
    new_base_regions: set[int] = set()
    for r in M.strongholds:
        if r in upgrade_regions or not can_upgrade_here(S, M, r):
            continue
        b = S.find_building(r)
        if b is None:
            if scheduled_new_bases >= max_new_bases or r not in buildable_new_regions:
                continue
            cost = BASE_LEVELS[1].cost
        elif b.side is M.my_side and b.level < b.max_level():
            if b.type is BType.BASE and base_count < desired_bases:
                continue
            cost = b.upgrade_cost()
            if (
                len(mine) < M.params["base_upgrade_min_army"]
                or reserved_gold < cost + M.params["base_upgrade_gold_buffer"]
            ):
                continue
        else:
            continue
        urgent_build_exception = (
            losing_economy
            and b is None
            and r in direct_build_regions
            and not any(w.region == M.my_hq for w in enemies)
        ) or (
            b is None
            and r in pending_build_regions
            and base_count < desired_bases
            and enemy_base_count >= base_count + 2
            and raw_enemy_home_hop > 2
            and not any(w.region == M.my_hq for w in enemies)
        )
        if urgent_training_needed and not urgent_build_exception:
            continue
        hq2_base_limit = 2
        if turtle_like or mode == "turtle_tech":
            hq2_base_limit = 4
        if economy_alert or losing_economy:
            hq2_base_limit = max(hq2_base_limit, min(desired_bases, 5))
        allow_hq2_economy_base = (
            hq is not None
            and hq.level <= 2
            and b is None
            and base_count < hq2_base_limit
        )
        reserve_hq2_now = hq2_gold_candidate and base_count >= M.params["hq2_reserve_min_bases"]
        if reserve_hq2_now and not allow_hq2_economy_base and reserved_gold < HQ_LEVELS[2].upgrade_cost + cost:
            continue
        if late_hq_reserve_active and not allow_hq2_economy_base and reserved_gold < late_hq_next_cost + cost:
            continue
        if (hq_heal_needed or hq_heal_reserve_active) and reserved_gold < HQ_HEAL_COST + hq_heal_buffer + cost:
            continue
        if reserved_gold >= cost:
            a.upgrades.append(r)
            upgrade_regions.add(r)
            reserved_gold -= cost
            if b is None:
                scheduled_new_bases += 1
                new_base_regions.add(r)

    save_for_hq2 = hq is not None and hq.level == 1 and (turtle_hq2 or pressure_hq2 or economy_hq2 or stale_hq2 or late_pressure_hq2 or force_hq2)
    hq_upgrade_buffer = 0 if save_for_hq2 else TRAIN_COST
    if economy_hq2:
        hq2_min_army = M.params["economy_hq2_min_army"]
    elif late_pressure_hq2:
        hq2_min_army = M.params["late_pressure_hq2_min_army"]
    elif force_hq2:
        hq2_min_army = M.params["force_hq2_min_army"]
    elif stale_hq2:
        hq2_min_army = M.params["stale_hq2_min_army"]
    else:
        hq2_min_army = M.params["hq2_min_army"]
    if save_for_hq2 and economy_hq2:
        home_garrison_target = max(home_garrison_target, M.params["economy_hq2_home_keep"])
    hq2_army_ready = len(mine) >= hq2_min_army or score_hq_upgrade_needed
    if (
        hq is not None
        and can_upgrade_here(S, M, M.my_hq)
        and hq.level == 1
        and hq2_army_ready
        and reserved_gold >= HQ_LEVELS[2].upgrade_cost + hq_upgrade_buffer
    ):
        a.upgrades.append(M.my_hq)
        upgrade_regions.add(M.my_hq)
        reserved_gold -= HQ_LEVELS[2].upgrade_cost

    if (
        profile_tuned
        and hq is not None
        and hq.level >= 2
        and hq.level < hq.max_level()
        and M.my_hq not in upgrade_regions
        and turn >= M.params["late_hq_upgrade_turn"]
        and len(mine) >= M.params["late_hq_upgrade_min_army"]
        and (
            ((turtle_like or economy_boom) and M.params["reactive_hq_upgrade"] > 0)
            or late_hq_upgrade_needed
            or (
                M.params["reactive_hq_upgrade"] > 0
                and enemy_alive >= len(mine) + M.params["target_army_enemy_margin"]
            )
        )
        and can_upgrade_here(S, M, M.my_hq)
        and not urgent_training_needed
        and not expansion_upgrade_blocked
    ):
        cost = hq.upgrade_cost()
        buffer = (
            M.params["score_hq_train_buffer"]
            if score_hq_upgrade_needed or late_hq_lockdown
            else TRAIN_COST * max(1, HQ_LEVELS[hq.level].train_cap)
        )
        if reserved_gold >= cost + buffer:
            a.upgrades.append(M.my_hq)
            upgrade_regions.add(M.my_hq)
            reserved_gold -= cost

    saving_for_late_hq = False
    if hq is not None:
        hq_upgrade_this_turn = M.my_hq in upgrade_regions and hq.level < hq.max_level()
        effective_hq_level = hq.level + 1 if hq_upgrade_this_turn else hq.level
        train_cap = HQ_LEVELS[effective_hq_level].train_cap
        alive = len(mine)
        rebuild_army_needed = (
            M.params["economy_rebuild_army_no_base"]
            if economy_alert
            else M.params["rebuild_army_no_base"]
        )
        if turtle_like:
            target_army = min(M.params["target_army_late_cap"], M.params["target_army_base_late_base"] + M.params["target_army_per_base"] * base_count)
            target_army = max(target_army, M.params["turtle_target_army"])
        elif turn >= M.params["late_economy_turn"]:
            target_army = min(M.params["target_army_late_cap"], M.params["target_army_base_late_base"] + M.params["target_army_per_base"] * base_count)
        else:
            target_army = M.params["target_army_no_base"] if base_count == 0 else M.params["target_army_base_early"]
        if (
            base_count == 0
            and (turn >= M.params["late_economy_turn"] or enemy_base_count >= M.params["rebuild_enemy_base_trigger"])
        ):
            target_army = max(target_army, rebuild_army_needed)
        if enemy_alive >= alive + M.params["target_army_enemy_margin"]:
            target_army = max(
                target_army,
                min(M.params["target_army_dynamic_cap"], enemy_alive + M.params["target_army_enemy_margin"]),
            )
        policy_army_floor = policy_value(policy, 3, 0)
        if policy_value(policy, 2, 0) >= 3 or losing_economy or economy_alert:
            target_army = max(target_army, policy_army_floor)
        if base_count < desired_bases or economy_alert or losing_economy:
            target_army = max(target_army, policy_value(map_hint, 11, 0))
        if adaptive_economy_clear and base_count < desired_bases:
            target_army = min(target_army, 6 if base_count < 2 else 8)
        if urgent_home_threat:
            target_army = max(target_army, urgent_army_target)
        affordable = reserved_gold // TRAIN_COST
        base_gold_reserve = BASE_LEVELS[1].cost + MOVE_COST + TRAIN_COST * max(1, train_cap)
        saving_for_base = base_count < desired_bases and reserved_gold < base_gold_reserve
        if urgent_training_needed:
            saving_for_base = False
        if (
            base_count == 0
            and alive < rebuild_army_needed
            and (turn >= M.params["late_economy_turn"] or enemy_base_count >= M.params["rebuild_enemy_base_trigger"])
        ):
            saving_for_base = False
        min_army_before_extra_base = M.params["desired_base2_min_army"]
        if turtle_like:
            min_army_before_extra_base = M.params["min_army_before_extra_base"]
        min_army_before_extra_base = max(min_army_before_extra_base, home_garrison_target + 5)
        if (adaptive_economy_clear or economy_alert or safe_enemy_economy) and base_count > 0:
            min_army_before_extra_base = min(min_army_before_extra_base, 5 if base_count == 1 else 7)
        if base_count > 0 and alive < min_army_before_extra_base:
            saving_for_base = False
        if (
            pending_build_regions
            and base_count < desired_bases
            and reserved_gold < BASE_LEVELS[1].cost
            and not urgent_training_needed
        ):
            saving_for_base = True
        hq_upgrade_blocked_by_expansion = expansion_upgrade_blocked
        min_army_before_hq = hq2_min_army if (economy_hq2 or stale_hq2 or late_pressure_hq2) else max(hq2_min_army, home_garrison_target + 5)
        saving_for_hq = save_for_hq2 and reserved_gold < HQ_LEVELS[2].upgrade_cost
        if urgent_training_needed and not (force_hq2 or late_hq_reserve_active or score_hq_upgrade_needed):
            saving_for_hq = False
        if alive < min_army_before_hq:
            saving_for_hq = False
        if enemy_alive >= alive + M.params["target_army_enemy_margin"] and not (economy_hq2 or stale_hq2 or late_pressure_hq2 or force_hq2):
            saving_for_hq = False
        late_hq_train_buffer = (
            M.params["score_hq_train_buffer"]
            if score_hq_upgrade_needed or late_hq_lockdown
            else TRAIN_COST * max(1, train_cap) if profile_tuned else 0
        )
        still_waiting_for_hq_upgrade = (
            (late_hq_upgrade_needed or late_hq_reserve_active)
            and not hq_upgrade_this_turn
            and not hq_upgrade_blocked_by_expansion
        )
        saving_for_late_hq = still_waiting_for_hq_upgrade and reserved_gold < late_hq_next_cost + late_hq_train_buffer
        heal_reserve_target = HQ_HEAL_COST + hq_heal_buffer
        if hq_heal_reserve_active and not hq_heal_needed:
            heal_reserve_target += TRAIN_COST * train_cap
        saving_for_hq_heal = (
            (hq_heal_needed or hq_heal_reserve_active)
            and reserved_gold < heal_reserve_target
        )
        if urgent_training_needed and not (late_hq_reserve_active or score_hq_upgrade_needed):
            saving_for_late_hq = False
            if not hq_heal_reserve_active:
                saving_for_hq_heal = False
        if (
            alive < target_army
            and not saving_for_base
            and not saving_for_hq
            and not saving_for_late_hq
            and not saving_for_hq_heal
            and not (
                late_hq_upgrade_needed
                and not hq_upgrade_blocked_by_expansion
                and not urgent_training_needed
                and alive >= M.params["late_hq_upgrade_min_army"]
                and can_upgrade_here(S, M, M.my_hq)
                and reserved_gold >= late_hq_next_cost
            )
        ):
            a.train_n = min(train_cap, affordable)
            reserved_gold -= a.train_n * TRAIN_COST
    else:
        alive = len(mine)
        min_army_before_extra_base = M.params["min_army_before_extra_base"]

    if (
        hq is not None
        and hq.level >= 2
        and hq.level < hq.max_level()
        and turn >= M.params["late_hq_upgrade_turn"]
        and alive >= M.params["late_hq_upgrade_min_army"]
        and (
            ((turtle_like or economy_boom) and M.params["reactive_hq_upgrade"] > 0)
            or late_hq_upgrade_needed
            or (
                M.params["reactive_hq_upgrade"] > 0
                and enemy_alive >= alive + M.params["target_army_enemy_margin"]
            )
        )
        and can_upgrade_here(S, M, M.my_hq)
        and not urgent_training_needed
        and not expansion_upgrade_blocked
        and M.my_hq not in upgrade_regions
    ):
        cost = hq.upgrade_cost()
        buffer = (
            M.params["score_hq_train_buffer"]
            if score_hq_upgrade_needed or late_hq_lockdown
            else TRAIN_COST * max(1, HQ_LEVELS[hq.level].train_cap)
        )
        if reserved_gold >= cost + buffer:
            a.upgrades.append(M.my_hq)
            upgrade_regions.add(M.my_hq)
            reserved_gold -= cost

    economy_hop_relaxed = (economy_boom or early_economy) and not economy_threat
    recall_hop = M.params["economy_boom_recall_hop"] if economy_hop_relaxed else M.params["enemy_home_recall_hop"]
    hold_hop = M.params["economy_boom_recall_hop"] if economy_hop_relaxed else M.params["enemy_home_hold_hop"]
    hold_home = turn < M.params["hold_home_until"] or enemy_home_hop <= hold_hop
    recall_home = enemy_home_hop <= recall_hop or mass_home_threat or late_mass_recall
    snipe_target = enemy_economy_target(S, M, P) if enemy_base_count > 0 else None
    snipe_active = (
        not M.params["disable_snipe"]
        and snipe_target is not None
        and len(mine) >= M.params["snipe_min_army"]
        and warrior_count_at(enemies, snipe_target) == 0
        and nearest_warrior_hop(mine, P, snipe_target) <= M.params["snipe_target_near_hop"]
        and enemy_home_hop > recall_hop
        and not any(w.region == M.my_hq for w in enemies)
        and not late_hq_lockdown
        and not hq_heal_reserve_active
    )
    distant_enemy_economy = (
        enemy_base_count >= 2
        and M.params["enemy_home_hold_hop"] < raw_enemy_home_hop <= M.params["enemy_home_hold_hop"] + 1
    )

    effective_base_count = base_count + scheduled_new_bases
    build_need = max(0, desired_bases - effective_base_count)
    build_slots = build_need
    economy_mode = (turtle_like or turn >= M.params["late_economy_turn"] or safe_enemy_economy or economy_alert) and build_need > 0
    if (
        (late_hq_reserve_active and hq is not None and hq.level >= 3 and base_count > 0 and not losing_economy)
        or hq_heal_reserve_active
    ):
        economy_mode = False
    if base_count > 0 and len(mine) < min_army_before_extra_base:
        economy_mode = False
    if base_count > 0:
        affordable_build_slots = reserved_gold // BASE_LEVELS[1].cost
        if build_need > 0 and reserved_gold >= 180 and not urgent_home_threat:
            affordable_build_slots = max(affordable_build_slots, 1)
        build_slots = min(build_slots, affordable_build_slots)
    build_cutoff = M.params["build_cutoff_turn"]
    if base_count == 0 or losing_economy:
        build_cutoff = M.params["emergency_build_cutoff_turn"]
    build_cutoff = max(build_cutoff, policy_value(policy, 5, 0))
    targets = nearest_open_strongholds(S, M, P)[:build_slots] if turn < build_cutoff else []
    if not targets:
        economy_mode = False
    builder_orders: dict[WarriorId, int] = {}
    used_builders: set[WarriorId] = set()
    protected_workers: set[WarriorId] = set()
    if max_new_bases > 0:
        protected_by_region: dict[int, int] = {}
        pending_guard_keep = int(M.params["pending_build_guard_keep"])
        if losing_economy or economy_alert or enemy_base_count >= base_count + 2:
            pending_guard_keep = max(pending_guard_keep, int(M.params["pending_build_guard_keep_losing"]))
        pending_guard_keep = max(1, pending_guard_keep)
        for w in sorted(idle, key=lambda w: w.id.num):
            if (
                w.region in pending_build_regions
                and w.region in buildable_new_regions
                and protected_by_region.get(w.region, 0) < pending_guard_keep
            ):
                protected_workers.add(w.id)
                protected_by_region[w.region] = protected_by_region.get(w.region, 0) + 1
    home_under_worker_threat = late_mass_recall or mass_home_threat or enemy_home_hop <= M.params["base_worker_threat_hop"] or any(w.region == M.my_hq for w in enemies)
    adaptive_worker_fill = (
        adaptive_economy_clear
        and not home_under_worker_threat
        and base_count >= 2
        and hq is not None
        and hq.level >= 2
        and turn >= 70
    )
    base_worker_fill_enabled = (
        (profile_tuned or adaptive_worker_fill)
        and not home_under_worker_threat
        and base_count > 0
        and (
            turn >= M.params["base_worker_fill_turn"]
            or economy_alert
            or turtle_like
            or (hq is not None and hq.level >= 2)
            or adaptive_worker_fill
        )
    )
    abandon_base_workers = (
        late_mass_recall
        or mass_home_threat
        or (
            M.params["base_worker_abandon_home_hop"] > 0
            and enemy_home_hop <= M.params["base_worker_abandon_home_hop"]
        )
    )
    late_worker_floor = M.params["late_hq_worker_floor"]
    if raw_enemy_home_hop > M.params["enemy_home_recall_hop"] + 2 and not any(w.region == M.my_hq for w in enemies):
        late_worker_floor = min(late_worker_floor, 1)
    base_worker_home_keep = max(
        home_garrison_target,
        M.params["base_worker_pressure_home_keep"] if home_under_worker_threat else M.params["base_worker_home_keep"],
        late_worker_floor if (late_hq_reserve_active or late_hq_lockdown or hq_heal_reserve_active) else 0,
    )
    for b in S.buildings:
        if b.side is not M.my_side:
            continue
        workers = [w for w in idle if w.region == b.region]
        keep = (
            base_worker_home_keep
            if b.region == M.my_hq
            else 0 if abandon_base_workers else (b.work_cap() if base_worker_fill_enabled else 1)
        )
        for w in sorted(workers, key=lambda w: w.id.num)[:keep]:
            protected_workers.add(w.id)
    home_count_for_build = sum(1 for w in mine if w.region == M.my_hq)
    early_home_builder = (
        turn >= M.params["early_builder_turn"]
        and enemy_pressure_count == 0
        and home_count_for_build >= home_garrison_target + M.params["early_builder_home_surplus"]
    )
    rebuild_home_builder = (
        turn < M.params["emergency_build_cutoff_turn"]
        and base_count == 0
        and reserved_gold >= BASE_LEVELS[1].cost
        and home_count_for_build >= home_garrison_target + M.params["rebuild_builder_home_surplus"]
    )
    surplus_home_builder = (
        turn >= M.params["late_economy_turn"]
        and base_count > 0
        and enemy_base_count >= base_count + 3
        and home_count_for_build >= home_garrison_target + M.params["rebuild_builder_home_surplus"]
    )
    catchup_home_builder = (
        losing_economy
        and base_count < desired_bases
        and not any(w.region == M.my_hq for w in enemies)
        and home_count_for_build >= 4
    )
    allow_home_builder = early_home_builder or rebuild_home_builder or surplus_home_builder or catchup_home_builder
    def can_leave_worked_base_for_build(worker: Warrior, target: int) -> bool:
        current = S.find_building(worker.region)
        if current is None or current.side is not M.my_side or current.type is not BType.BASE:
            return True
        if S.find_building(target) is not None:
            return True
        workers_here = sum(1 for other in mine if other.region == current.region)
        if workers_here > current.work_cap():
            return True
        return reserved_gold >= BASE_LEVELS[1].cost + MOVE_COST + WORK_INCOME * 2

    for target in targets:
        candidates = [
            w for w in idle
            if w.id not in used_builders
            and w.id not in protected_workers
            and not (hold_home and w.region == M.my_hq and not allow_home_builder)
            and can_leave_worked_base_for_build(w, target)
        ]
        if not candidates:
            candidates = [
                w for w in idle
                if w.id not in used_builders
                and not (hold_home and w.region == M.my_hq and not allow_home_builder)
                and can_leave_worked_base_for_build(w, target)
            ]
        if not candidates:
            break
        builder = min(
            candidates,
            key=lambda w: (0 if w.id in move_ready_idle_ids else 1, P.hop[w.region][target], P.dist[w.region][target], w.id.num),
        )
        builder_orders[builder.id] = target
        used_builders.add(builder.id)

    if economy_mode and not builder_orders and not pending_build_regions:
        economy_mode = False

    base_worker_orders: dict[WarriorId, int] = {}
    selected_home_workers = 0
    for b in sorted(S.buildings, key=lambda b: (P.hop[M.my_hq][b.region], b.region)):
        if b.side is not M.my_side or b.type is not BType.BASE:
            continue
        if abandon_base_workers:
            continue
        if any(w.region == b.region for w in enemies):
            continue
        assigned = sum(
            1 for w in mine
            if w.region == b.region or (w.state is WState.MOVING and w.target == b.region)
        )
        desired_workers = b.work_cap() if base_worker_fill_enabled else 1
        need_workers = max(0, desired_workers - assigned)
        if need_workers <= 0:
            continue
        candidates = [
            w for w in idle
            if w.id not in used_builders
            and w.id not in protected_workers
            and w.id not in base_worker_orders
            and (
                w.region != M.my_hq
                or home_count_for_build - selected_home_workers > base_worker_home_keep
            )
        ]
        if not candidates:
            continue
        candidates.sort(key=lambda w: (P.hop[w.region][b.region], P.dist[w.region][b.region], w.id.num))
        for worker in candidates[:need_workers]:
            base_worker_orders[worker.id] = b.region
            if worker.region == M.my_hq:
                selected_home_workers += 1

    base_defender_orders: dict[WarriorId, int] = {}
    if (
        turn >= M.params["late_economy_turn"]
        and enemy_base_count >= 3
        and not any(w.region == M.my_hq for w in enemies)
    ):
        selected_home_defenders = 0
        my_bases = [
            b for b in sorted(S.buildings, key=lambda b: (P.hop[M.my_hq][b.region], b.region))
            if b.side is M.my_side and b.type is BType.BASE
        ]
        safe_base_set = set(plan_regions(M, P, "safe_expansion_order")[:max(3, int(plan_max_bases or 3))])
        for b in my_bases:
            nearby_enemies = [
                w for w in enemies
                if P.hop[w.region][b.region] <= M.params["base_defense_hop"] + (1 if economy_alert else 0)
            ]
            enemy_on_base = any(w.region == b.region for w in enemies)
            planned_safe_base = b.region in safe_base_set
            defense_trigger = 2 if economy_alert else M.params["base_defense_enemy_trigger"]
            if planned_safe_base and enemy_base_count >= base_count + 1:
                defense_trigger = min(defense_trigger, 1)
            if not enemy_on_base and len(nearby_enemies) < defense_trigger:
                continue
            assigned = sum(
                1 for w in mine
                if w.region == b.region or (w.state is WState.MOVING and w.target == b.region)
            )
            desired = min(
                M.params["base_defense_max"],
                len(nearby_enemies) + M.params["base_defense_margin"],
            )
            if planned_safe_base and nearby_enemies:
                desired = max(desired, min(M.params["base_defense_max"], len(nearby_enemies) + 2))
            need = max(0, desired - assigned)
            if need <= 0:
                continue
            candidates = [
                w for w in idle
                if w.id not in builder_orders
                and w.id not in base_worker_orders
                and w.id not in base_defender_orders
                and w.id not in protected_workers
                and (
                    w.region != M.my_hq
                    or home_count_for_build - selected_home_defenders > home_garrison_target
                )
            ]
            candidates.sort(key=lambda w: (P.hop[w.region][b.region], P.dist[w.region][b.region], w.id.num))
            for w in candidates[:need]:
                base_defender_orders[w.id] = b.region
                if w.region == M.my_hq:
                    selected_home_defenders += 1

    home_intercept_orders: dict[WarriorId, int] = {}
    close_home_enemies = [
        w for w in threatening_enemies
        if 0 < P.hop[w.region][M.my_hq] <= M.params["home_intercept_hop"]
    ]
    intercept_target = most_crowded_region(close_home_enemies)
    intercept_guard = (
        P.nxt[M.my_hq][intercept_target]
        if intercept_target is not None and P.nxt[M.my_hq][intercept_target] >= 0
        else intercept_target
    )
    if (
        intercept_target is not None
        and intercept_guard is not None
        and intercept_guard != M.my_hq
        and turn <= M.params["home_intercept_turn"]
        and len(close_home_enemies) >= M.params["home_intercept_min_enemies"]
        and not any(w.region == M.my_hq for w in enemies)
    ):
        target_enemy_count = warrior_count_at(enemies, intercept_target)
        friendly_at_guard = warrior_count_at(mine, intercept_guard)
        need = min(max(0, len(mine) - 1), target_enemy_count + 1)
        candidates = [
            w for w in idle
            if w.region == M.my_hq
            and w.id not in home_intercept_orders
        ]
        entry = home_intercept_policy(
            turn,
            target_enemy_count,
            len(candidates) + friendly_at_guard,
            hq.level if hq is not None else 1,
            P.hop[M.my_hq][intercept_target],
        )
        required_edge = policy_value(entry, 2, 1)
        overrun_gate_enabled = M.profile.get("avoid_home_intercept_overrun") is True
        if (
            overrun_gate_enabled
            and target_enemy_count >= 6
            and (
                policy_value(entry, 0, 1) <= 0
                or len(candidates) + friendly_at_guard < target_enemy_count + required_edge
            )
        ):
            candidates = []
        elif overrun_gate_enabled and target_enemy_count >= 6:
            need = min(need, policy_value(entry, 1, need))
            home_keep = policy_value(entry, 3, 1)
            need = min(need, max(0, home_count_for_build - home_keep))
        candidates.sort(key=lambda w: w.id.num)
        for w in candidates[:need]:
            home_intercept_orders[w.id] = intercept_guard

    hq_worker_order: WarriorId | None = None
    if (save_for_hq2 or late_hq_upgrade_needed or late_hq_reserve_active or hq_heal_reserve_active) and not any(w.region == M.my_hq for w in mine):
        candidates = [
            w for w in idle
            if w.id not in builder_orders
            and w.id not in base_worker_orders
            and w.id not in protected_workers
            and w.region != M.my_hq
        ]
        if candidates:
            hq_worker_order = min(candidates, key=lambda w: (P.hop[w.region][M.my_hq], P.dist[w.region][M.my_hq], w.id.num)).id

    home_defender_orders: set[WarriorId] = set()
    home_count = sum(1 for w in mine if w.region == M.my_hq)
    defender_need = max(0, home_garrison_target - home_count)
    if defender_need > 0:
        candidates = [
            w for w in idle
            if w.region != M.my_hq
            and w.id not in builder_orders
            and w.id not in base_worker_orders
            and w.id not in protected_workers
            and (hq_worker_order is None or w.id != hq_worker_order)
        ]
        candidates.sort(key=lambda w: (P.hop[w.region][M.my_hq], P.dist[w.region][M.my_hq], w.id.num))
        for w in candidates[:defender_need]:
            home_defender_orders.add(w.id)

    forward_defense_orders: dict[WarriorId, int] = {}
    defense_entry = defense_policy(
        turn,
        enemy_opp_hq_count,
        len(mine),
        enemy_alive,
        raw_enemy_home_hop,
        economy_gap,
    )
    forward_defense_active = (
        policy_value(defense_entry, 0, 0) > 0
        and turn >= M.params["forward_defense_turn"]
        and enemy_opp_hq_count >= M.params["forward_defense_enemy_hq"]
        and len(mine) >= max(M.params["forward_defense_min_army"], policy_value(defense_entry, 2, 0))
        and not any(w.region == M.my_hq for w in enemies)
        and not urgent_home_threat
    )
    if forward_defense_active:
        stage_hop = policy_value(defense_entry, 1, int(M.params["forward_defense_stage_hop"]))
        stage_hop = clamp_int(stage_hop, 1, 4)
        choke = home_choke_region(M, P, stage_hop)
        if choke != M.my_hq and raw_enemy_home_hop > stage_hop:
            assigned = sum(
                1 for w in mine
                if w.region == choke or (w.state is WState.MOVING and w.target == choke)
            )
            commit_cap = min(
                int(M.params["forward_defense_commit_cap"]),
                policy_value(defense_entry, 4, int(M.params["forward_defense_commit_cap"])),
            )
            desired_stage = min(commit_cap, max(6, enemy_opp_hq_count // 2 + 2))
            need = max(0, desired_stage - assigned)
            home_keep = max(home_garrison_target, policy_value(defense_entry, 3, int(M.params["forward_defense_home_keep"])))
            release_workers = policy_value(defense_entry, 5, 0) > 0
            selected_home_forward = 0

            def releasable_for_forward(worker: Warrior) -> bool:
                if worker.id in builder_orders or worker.id in base_defender_orders or worker.id in home_defender_orders:
                    return False
                if hq_worker_order is not None and worker.id == hq_worker_order:
                    return False
                if worker.id in protected_workers and not release_workers:
                    return False
                current = S.find_building(worker.region)
                if current is not None and current.side is M.my_side and current.type is BType.BASE:
                    workers_here = sum(1 for other in mine if other.region == current.region)
                    if workers_here <= max(1, current.work_cap()):
                        return False
                return True

            candidates = [
                w for w in idle
                if w.id not in forward_defense_orders
                and w.region != choke
                and releasable_for_forward(w)
            ]
            candidates.sort(key=lambda w: (P.hop[w.region][choke], P.dist[w.region][choke], w.id.num))
            selected_forward = 0
            for w in candidates:
                if selected_forward >= need:
                    break
                if w.region == M.my_hq and home_count_for_build - selected_home_forward <= home_keep:
                    continue
                forward_defense_orders[w.id] = choke
                base_worker_orders.pop(w.id, None)
                protected_workers.discard(w.id)
                selected_forward += 1
                if w.region == M.my_hq:
                    selected_home_forward += 1

    keep_slots: dict[int, int] = {}
    for b in S.buildings:
        if b.side is not M.my_side:
            continue
        count_here = sum(
            1 for w in idle
            if w.region == b.region
            and w.id not in builder_orders
            and w.id not in forward_defense_orders
        )
        if count_here <= 0:
            continue
        keep = (
            base_worker_home_keep
            if b.region == M.my_hq
            else 0 if abandon_base_workers else (b.work_cap() if base_worker_fill_enabled else 1)
        )
        keep_slots[b.region] = min(keep, count_here)

    attack_start = M.params["first_attack_start_with_base"] if base_count > 0 else M.params["first_attack_start_no_base"]
    attack_start = max(attack_start, policy_value(map_hint, 9, attack_start))
    stage = staging_region(M, P)
    economy_clear_for_attack = enemy_base_count <= base_count + M.params["mass_attack_max_base_gap"]
    available_attackers = sum(
        1 for w in mine
        if w.id not in builder_orders
        and w.id not in base_worker_orders
        and w.id not in base_defender_orders
        and w.id not in home_defender_orders
        and w.id not in forward_defense_orders
        and (hq_worker_order is None or w.id != hq_worker_order)
    )
    available_attackers = max(available_attackers, max(0, len(mine) - home_garrison_target))
    contest_target: int | None = None
    contest_home_keep = home_garrison_target
    contest_unit_hop = 0
    contest_commit = 0
    contest_sent = 0
    contest_home_sent = 0
    contest_excluded = (
        set(builder_orders)
        | set(base_worker_orders)
        | set(base_defender_orders)
        | set(forward_defense_orders)
        | home_defender_orders
        | protected_workers
    )
    if hq_worker_order is not None:
        contest_excluded.add(hq_worker_order)
    contest_pool = [w for w in idle if w.id not in contest_excluded]
    contest_home_safe = (
        not any(w.region == M.my_hq for w in enemies)
        and raw_enemy_home_hop > 2
        and not mass_home_threat
        and not late_hq_lockdown
        and not hq_heal_reserve_active
    )
    if contest_home_safe and contest_pool and enemy_base_count > base_count:
        contest_candidates: list[tuple[int, int, int, int, list[int]]] = []

        def add_contest_candidate(region: int, enemy_building: Building | None, claimed: bool) -> None:
            nonlocal contest_candidates
            target_home_hop = P.hop[M.my_hq][region]
            entry = contest_policy(
                turn,
                base_count,
                enemy_base_count,
                len(mine),
                enemy_alive,
                raw_enemy_home_hop,
                target_home_hop,
                enemy_building is not None or claimed,
            )
            if policy_value(entry, 0, 0) <= 0:
                return
            defenders = warrior_count_at(enemies, region)
            if defenders > policy_value(entry, 2, 0):
                return
            if len(mine) < policy_value(entry, 1, 99):
                return
            unit_hop = policy_value(entry, 4, 0)
            reachable = [w for w in contest_pool if P.hop[w.region][region] <= unit_hop]
            already = sum(
                1 for w in mine
                if w.region == region or (w.state is WState.MOVING and w.target == region)
            )
            if not reachable and already <= 0:
                return
            turret = building_turret(enemy_building)
            max_hp = enemy_building.current_hp() if enemy_building is not None else 1
            hp = enemy_building.hp if enemy_building is not None else 0
            reinforce_hop = min(
                (P.hop[w.region][region] for w in enemies if w.region != region),
                default=10**9,
            )
            battle = battle_policy(
                "base",
                turn,
                len(reachable) + already,
                defenders,
                turret,
                hp,
                max_hp,
                reinforce_hop,
                hq.level if hq is not None else 1,
                enemy_hq_level,
            )
            min_edge = policy_value(entry, 5, 1)
            required = max(defenders + turret + min_edge, policy_value(battle, 1, 0), 1)
            if policy_value(battle, 0, 1) <= 0 and len(reachable) + already < required + 1:
                return
            if len(reachable) + already < required:
                return
            commit = max(0, min(policy_value(entry, 6, required), required) - already)
            if commit <= 0:
                return
            worker_value = 0
            if enemy_building is not None:
                worker_value = min(defenders, enemy_building.work_cap())
            score = (
                target_home_hop * 120
                + defenders * 420
                + hp * 25
                - (enemy_base_count - base_count) * 260
                - worker_value * 140
                - (enemy_building.level if enemy_building is not None else 0) * 120
                - len(M.adj[region]) * 20
                + (350 if claimed else 0)
            )
            contest_candidates.append((score, region, policy_value(entry, 3, home_garrison_target), unit_hop, entry[:6] + [commit]))

        for b in S.buildings:
            if b.side is M.my_side.opposite and b.type is BType.BASE:
                add_contest_candidate(b.region, b, False)

        for region in plan_regions(M, P, "frontier_order")[:8]:
            if S.find_building(region) is not None:
                continue
            if warrior_count_at(enemies, region) <= 0:
                continue
            if warrior_count_at(mine, region) > 0:
                continue
            add_contest_candidate(region, None, True)

        if contest_candidates:
            contest_candidates.sort()
            _score, contest_target, contest_home_keep, contest_unit_hop, contest_entry = contest_candidates[0]
            contest_commit = policy_value(contest_entry, 6, 0)
    enemy_hq_near_count = sum(1 for w in enemies if P.hop[w.region][M.opp_hq] <= 2)
    enemy_hq_reinforce_hop = min(
        (P.hop[w.region][M.opp_hq] for w in enemies if P.hop[w.region][M.opp_hq] > 2),
        default=10**9,
    )
    enemy_hq_max_hp = enemy_hq.current_hp() if enemy_hq is not None else HQ_LEVELS[1].hp
    hq_battle = battle_policy(
        "hq",
        turn,
        available_attackers,
        enemy_hq_near_count,
        building_turret(enemy_hq),
        enemy_hq.hp if enemy_hq is not None else HQ_LEVELS[1].hp,
        enemy_hq_max_hp,
        enemy_hq_reinforce_hop,
        hq.level if hq is not None else 1,
        enemy_hq_level,
    )
    hq_min_attackers = policy_value(hq_battle, 1, 0)
    hq_battle_bad = (
        policy_value(hq_battle, 0, 1) <= 0
        and enemy_hq_near_count >= 8
        and enemy_hq_near_count >= available_attackers + 3
    ) or (
        hq_min_attackers > 0
        and enemy_hq_near_count >= 4
        and turn < M.params["stage_force_launch_turn"]
        and available_attackers < hq_min_attackers
    )
    hq_battle_ok = not hq_battle_bad
    attack_enemy_margin = M.params["target_army_enemy_margin"]
    attack_required_edge = policy_value(policy, 7, 0)
    hq_breakthrough_clear = len(mine) >= enemy_opp_hq_count + M.params["stage_launch_enemy_margin"] + 3
    clear_attack_return = (
        not losing_economy
        and not mass_home_threat
        and (economy_clear_for_attack or hq_breakthrough_clear)
        and enemy_alive + attack_required_edge <= len(mine) + attack_enemy_margin
        and enemy_opp_hq_count <= max(len(mine), M.params["stage_launch_min"]) + M.params["stage_launch_enemy_margin"]
        and hq_battle_ok
    )
    if policy_value(policy, 4, 1) <= 0 and not hq_breakthrough_clear:
        clear_attack_return = False
    staging_mode = (
        not M.params["disable_staging"]
        and turtle_like
        and clear_attack_return
        and stage != M.my_hq
        and not late_hq_lockdown
        and not hq_heal_reserve_active
    )
    staged_count = sum(1 for w in mine if w.region == stage)
    launch_threshold = max(M.params["stage_launch_min"], enemy_opp_hq_count + M.params["stage_launch_enemy_margin"])
    if hq_min_attackers > 0 and enemy_hq_near_count >= 4:
        launch_threshold = max(launch_threshold, hq_min_attackers)
    stage_force_turn = max(M.params["stage_force_launch_turn"], policy_value(map_hint, 10, M.params["stage_force_launch_turn"]))
    launch_stage = staged_count >= launch_threshold or turn >= stage_force_turn
    adaptive_expansion_guard = base_count < desired_bases and turn < build_cutoff
    counter_home_safe = enemy_home_hop > recall_hop or (
        losing_economy
        and raw_enemy_home_hop > 2
        and not any(w.region == M.my_hq for w in enemies)
    )
    economy_counter_active = (
        not M.params["disable_economy_counter"]
        and economy_target is not None
        and economy_target_enemy_count <= economy_counter_defender_cap
        and (not adaptive_expansion_guard or losing_economy)
        and len(mine) >= economy_counter_min_army
        and counter_home_safe
        and not any(w.region == M.my_hq for w in enemies)
        and not late_hq_lockdown
        and not hq_heal_reserve_active
    )
    mass_attack_prepare = (
        not turtle_like
        and not economy_alert
        and turn >= M.params["mass_attack_hold_turn"]
        and enemy_base_count <= base_count + M.params["mass_attack_enemy_base_margin"]
        and enemy_home_hop > recall_hop
        and not any(w.region == M.my_hq for w in enemies)
        and not late_hq_lockdown
        and not hq_heal_reserve_active
    )
    mass_attack_ready = (
        not mass_attack_prepare
        or len(mine) >= M.params["mass_attack_release_army"]
        or turn >= M.params["mass_attack_release_turn"]
    )
    ordered_idle = sorted(
        idle,
        key=lambda w: (0 if w.id in builder_orders else 1 if w.id in base_worker_orders else 2, P.hop[w.region][M.opp_hq], w.id.num),
    )

    for w in ordered_idle:
        if w.id in moved:
            continue
        target = None
        contest_move = False
        if w.id in home_intercept_orders:
            target = home_intercept_orders[w.id]
        elif w.id in builder_orders:
            target = builder_orders[w.id]
        elif w.id in forward_defense_orders:
            target = forward_defense_orders[w.id]
        elif w.id in base_worker_orders:
            target = base_worker_orders[w.id]
        elif w.id in base_defender_orders:
            target = base_defender_orders[w.id]
        elif hq_worker_order is not None and w.id == hq_worker_order:
            target = M.my_hq
        elif w.id in home_defender_orders:
            target = M.my_hq
        elif (
            contest_target is not None
            and contest_sent < contest_commit
            and w.region != contest_target
            and P.hop[w.region][contest_target] <= contest_unit_hop
            and not (
                w.region == M.my_hq
                and home_count - contest_home_sent <= contest_home_keep
            )
        ):
            target = contest_target
            contest_move = True
        elif w.id in protected_workers:
            continue
        elif (
            economy_counter_active
            and w.region != M.opp_hq
            and P.hop[w.region][economy_target] <= M.params["economy_counter_unit_hop"]
            and not (w.region == M.my_hq and home_count <= M.params["economy_counter_home_keep"])
        ):
            target = economy_target
        elif hold_home and w.region == M.my_hq:
            continue
        elif keep_slots.get(w.region, 0) > 0:
            keep_slots[w.region] -= 1
            continue
        elif recall_home and w.region != M.my_hq:
            if mode == "rush" and base_count == 0 and w.region in new_base_regions:
                continue
            target = M.my_hq
        elif (
            snipe_active
            and snipe_target is not None
            and w.region != M.opp_hq
            and P.hop[w.region][snipe_target] <= M.params["snipe_unit_near_hop"]
            and not (w.region == M.my_hq and home_count <= M.params["economy_counter_home_keep"])
        ):
            target = snipe_target
        elif economy_mode:
            continue
        elif staging_mode:
            if w.region == M.opp_hq:
                continue
            if w.region == stage:
                if launch_stage:
                    target = M.opp_hq
                else:
                    continue
            else:
                target = stage
        elif (
            not turtle_like
            and not adaptive_expansion_guard
            and not late_hq_lockdown
            and not hq_heal_reserve_active
            and clear_attack_return
            and mass_attack_ready
            and (len(mine) >= M.params["early_attack_min_army"] or (turn >= attack_start and not distant_enemy_economy))
        ):
            target = M.opp_hq

        if target == M.my_hq and mode == "rush" and base_count == 0 and w.region in new_base_regions:
            continue
        if target is None or target == w.region:
            continue
        b = S.find_building(target)
        cost = 0 if (b is not None and b.side is M.my_side) else MOVE_COST
        expansion_builder_move = w.id in builder_orders and (losing_economy or base_count < desired_bases)
        if force_hq2 and cost > 0 and reserved_gold < HQ_LEVELS[2].upgrade_cost and not expansion_builder_move:
            continue
        if late_hq_reserve_active and cost > 0 and reserved_gold < late_hq_next_cost + cost and not expansion_builder_move:
            continue
        if saving_for_late_hq and cost > 0 and reserved_gold < late_hq_next_cost and not expansion_builder_move:
            continue
        if hq_heal_reserve_active and cost > 0 and reserved_gold < HQ_HEAL_COST + hq_heal_buffer + cost:
            continue
        if reserved_gold < cost:
            continue
        a.moves.append((w.id, target))
        moved.add(w.id)
        reserved_gold -= cost
        if contest_move:
            contest_sent += 1
            if w.region == M.my_hq:
                contest_home_sent += 1

    return a


def run_bot() -> None:
    M, S = parse_init()
    P = calculate_paths(M)
    while (turn := read_turn_start()) is not None:
        a = decide(S, M, P, turn)
        emit(a)
        read_turn_result(S, M, a)


run_bot()
