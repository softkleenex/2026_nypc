# Pending Experiment Plan

This plan was executed after eval29 logs arrived. Current evidence favors
`bots/150.py` as the next candidate, but do not submit it without a fresh final
sanity check.

## Current Baseline

- Submitted baseline: `bots/145.py`
- Current candidate: `bots/150.py`
- Official replay coverage for 150: `97W/0L/0D` over archived `*_nypc_log`
- Archived user replay coverage for 150: `91W/7L/2D` over 100 eval14/25/26/28/29
  logs
- Remaining 150 replay non-wins: eval26 `215364_A` draw; eval29
  `238554_B`, `239085_A`, `241470_B`, `242702_B`, `243173_B`, `243657_B`,
  `244080_B`, `244910_B`

## Hypothesis A: Rush Defense Gap

Evidence:

- `proxy-rush` remains the weakest local pool:
  - 145 seed1 `62W/18L/0D`, 150 seed1 `65W/15L/0D`
  - 145 seed41 `66W/14L/0D`, 150 seed41 `68W/12L/0D`
  - 145 seed81 `56W/24L/0D`, 150 seed81 `59W/21L/0D`
- Representative losses die by HQ destruction around T80-T110:
  - `results/145-proxy-seed81/proxy-rush/logs/seed_83_left.log`: T93 HQ loss
  - `results/145-proxy-seed1/proxy-rush/logs/seed_5_left.log`: T91 HQ loss
- Timeline pattern: our HQ stays L1, we expand to 4-6 bases, army gets wiped,
  then enemy's small 2-base rush kills HQ.

Candidate directions to test, in order:

1. Narrow early anti-rush expansion brake: applied in `bots/150.py`.
   - Trigger: T25-T60, enemy HQ L1 and enemy army >= ours +3; latch when enemy
     bases < ours before T50, then activate after invaders >=2, or activate
     immediately when enemy bases <= ours and invaders >=4.
   - Action: stop new base builds and expansion movement by raising `rush_alert`.
   - Risk: can hurt econ/turtle matchups if triggered by harmless scouts.

2. HQ L2 emergency priority:
   - Trigger: HQ L1, T45-T90, enemy army near our half, our bases >=4.
   - Action: reserve for HQ L2 before more base builds or base levels.
   - Risk: may repeat earlier anti-greed failures if too broad.

3. Home-garrison floor during rush signal:
   - Trigger: same rush signal, HQ HP <= 8 or enemy within 2 hops.
   - Action: keep 3-5 movable units on/near HQ before staging/harass.
   - Risk: too much defense can delay winning counterpushes.

Verification gates:

```bash
python3 -m py_compile bots/<n>.py tools/*.py
python3 tools/evaluate_pool.py --bot bots/<n>.py --start 1 --count 40 --side both --pools proxy-rush --name <n>-rush-seed1
python3 tools/evaluate_pool.py --bot bots/<n>.py --start 41 --count 40 --side both --pools proxy-rush --name <n>-rush-seed41
python3 tools/evaluate_pool.py --bot bots/<n>.py --start 81 --count 40 --side both --pools proxy-rush --name <n>-rush-seed81
```

Only keep a rush change if it improves rush losses without regressing:

```bash
python3 tools/evaluate_pool.py --bot bots/<n>.py --start 1 --count 40 --side both --pools proxy-econ proxy-turtle proxy-punch --name <n>-nonrush-seed1
python3 tools/evaluate.py --bot bots/<n>.py --opponent "python3 $PWD/bots/77.py" --left-opponent "python3 $PWD/bots/77.py" --side both --start 1 --count 40 --timeout 300 --name <n>-vs-77-seed1 --quiet
python3 tools/evaluate.py --bot bots/<n>.py --opponent "python3 $PWD/bots/90.py" --left-opponent "python3 $PWD/bots/90.py" --side both --start 1 --count 40 --timeout 300 --name <n>-vs-90-seed1 --quiet
```

## Hypothesis B: Late Winning Position Not Converted

Evidence:

- `215364_A` remains `DRAW TURN_LIMIT` under `145.py`.
- T190 state: us 30 army, 5 bases, HQ L4; opponent 22 army, 3 bases, HQ L4.
- Commands show attack movement spreading through 46/48/50, then target 56 at
  T195, too late to siege HQ meaningfully.

Candidate directions to test:

1. Earlier direct-HQ switch for clear score lead:
   - Trigger: T185+, army >= enemy +5, bases >= enemy +2, no enemy within 1 hop
     of our HQ, opponent HQ level not above ours.
   - Action: target opponent HQ directly instead of intermediate base targets.

2. Gate release by remaining travel time:
   - Trigger: T188+, attack target is opponent HQ, units are within 2-3 route
     steps of HQ.
   - Action: release to HQ if waiting would leave fewer than 3 siege turns.

3. Stop late training if it delays movement:
   - Trigger: T185+, winning score lead, active HQ attack.
   - Action: reduce train cap/hold so command budget and gold do not bias back
     toward staging or base repair.

Verification gates:

```bash
python3 tools/run_log_replay.py bots/archive/user_logs/eval26_bot77_20260707_1500/matches/215364_A.txt --candidate bots/<n>.py --replay-side right --name <n>-target-215364 --timeout 60
python3 tools/run_log_replay.py bots/archive/user_logs/eval25_bot62_20260707_1000/matches/204345_A.txt bots/archive/user_logs/eval26_bot77_20260707_1500/matches/215758_A.txt --candidate bots/<n>.py --replay-side right --name <n>-regression-targets-A --timeout 60
python3 tools/run_log_replay.py bots/archive/user_logs/eval28_bot91_20260708_1000/matches/232307_B.txt bots/archive/user_logs/eval28_bot91_20260708_1000/matches/233143_B.txt bots/archive/user_logs/eval28_bot91_20260708_1000/matches/234056_B.txt --candidate bots/<n>.py --replay-side left --name <n>-regression-targets-B --timeout 60
```

Reject the change if it only changes `215364_A` commands but leaves the draw,
or if it worsens proxy/direct gates.

## Incoming Middle-Eval Triage

When new user logs arrive:

1. Archive logs without rewriting old data.
2. Add the new folder to the user-log index workflow.
3. Replay with `145.py` first.
4. Classify each non-win as one of:
   - rush defense gap
   - late conversion gap
   - HQ race/economy gap
   - unknown/new pattern
5. Only create a new candidate when a real non-win matches a concrete pattern.
