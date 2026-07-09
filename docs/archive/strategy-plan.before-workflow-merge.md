# NYPC Strategy Plan

## User-Match Intermediate Eval #14 (2026-07-03 15:00, bot submitted 14:53)

Logs in `bots/????_user_log/` (20 identified games): **9W 8L 3D vs real users.**

Loss patterns:
1. **17-turn all-in rush death** ('어 나혼자야'): opponent trained 3 extra by
   T3 and sent all 5 at our HQ; our T2 base build (300g) had spent the
   defense budget (3 defenders vs 5). ALL generations 37-42 die identically.
   -> 43's all-in guard (unknown-map only: enemy total >= 5 by T8 -> halt
   base builds, train everything). Replay: 17-turn death -> t169 WIN.
2. Out-macro'd by high-tier users (6 of 8 losses: trains 21v92, 31v69...).
   Engine ceiling; the raid/tiebreak work targets this class.
3. One tiebreak loss DESPITE out-training (105v67) -- endgame HP race.

43 also carries the raid profiles for maps 6/8 (opponent's late upgrades are
funded by their outer economy; raiding it breaks the tiebreak parity).
Integrity: map4=29 / map7=30 command equality re-verified, sample 10W WA 0,
17ms.

## Current State

The latest two real server submissions are:

```text
bots/24.py
bots/25.py
```

## A/B Submission Queue (methodology v2, 2026-07-03)

One change per submission; server result vs 30's 4W3L1D baseline decides
whether the change stays. Both queued fixes are server-evidenced, not
speculative:

```text
[verdict]   33 = 30 + expansion-savings shadow fix -> 3W 1D 4L.
            Exactly 30's result with bot 7 flipped W->L. Root cause found:
            the 300-gold shadow was a LOW dam that accidentally kept training
            flowing; the fix let HQ-tech saving (a 1200-3600 HIGH dam) freeze
            the army at 10 while adaptive bot 7 grew to 36. The underlying
            flaw is "saving while outnumbered", not the shadow fix itself.
[verdict]   34 = 33 + supply fund + GLOBAL train-to-parity -> 2W 1D 5L, rejected.
            But the per-game reading was gold: parity SAVED map 5 (survived
            to turn limit at 91v99 alive) and DREW map 6, while KILLING maps
            3/8 (tech starvation, HQ L1, dead at t80 on 3). Parity is a
            per-map shape, not a global rule.
[verdict]   35 = map profiles v1 -> 3W 1D 4L. Profile MECHANISM proven:
            map6 flipped L->D exactly as replayed. But hq_rush starved the
            army (map8 D->L) and war_econ failed to reproduce 30's map7 win.
[verdict]   36 -> 4W 2D 2L (wins 1,2,3,7 / draws 6,8 / losses 4,5).
            PREDICTION EXACT, game by game. New best; representative moved
            to 36. Map4 upgraded to a turn-limit L5v5 loss (was HQ death).
[verdict]   37 -> 4W 3D 1L, new best. BOT 5 KILLED for the first time ever
            (HQ destroyed t182; commit-push + sticky target + map5 parity).
            Map4 L->D as predicted, map3 faster (t156). Costs: map6 D->L
            (opponent reached L2 late), map7 W->D (commit-push broke the
            30-reproduction, which depended on the old retreat toggle).
[verdict]   38 -> 4W 4D 0L. FIRST ZERO-LOSS RESULT. Map6 L->D restored;
            map7 stayed D (live bot 7 adapts past the recorded reproduction
            -- replay's limit reconfirmed). Representative -> 38.
[verdict]   39 -> 4W 4D 0L (same as 38). Map8 attempt NEUTRALIZED: we
            reached L5, adaptive bot 8 followed to L5 (was L4v4), 30-30
            again, and we ended 24v35 behind. Bot 8 mirrors any static
            shape; its map is structurally a draw ceiling. Maps 4/6/7
            similar (superior adaptive armies). Sample plateau reached.
[ready]     42 = 41 + tiebreak exploits for the last two draws:
            - map6: opponent's HQ upgrade is a FIXED SCHEDULE (t197 across
              3 submissions regardless of our level). hq_rush t150 without
              parity (33-army upkeep was eating all tech gold) reaches L4
              by t181 vs their L2\@197. Replay trajectory confirms.
            - map8: opponent mirrors our HQ level with 20-33 turn lag.
              hq_delay_last=182 postpones our L5 purchase so the earliest
              reaction lands at t202+ (out of game). Worst case = current
              draw (no downside).
            Reproduction integrity: map7=30 and map4=29 command equality
            re-verified after edits. Sample 10W WA 0.
            Projected 8W 0L 0D possible; conservative 6W 2D 0L floor.
[old]       41 = 40 + DETERMINISTIC WIN REPRODUCTION. The game is
            deterministic, so any historically-won live game is a
            guaranteed win if we reproduce that bot's behavior exactly:
            - map7 = 30's engine (shadow, old_retreat, no_fund, no_sticky,
              deep_recall): 200-turn command diff vs 30's winning log =
              IDENTICAL. Win guaranteed.
            - map4 = 29's engine (gen29 flag reverts under_pressure,
              illegal-save skip, intercept condition + the flags above):
              200-turn command diff vs 29's winning log = IDENTICAL.
              Win guaranteed (t190 HQ kill).
            Preservation: maps 1/3/5/6/8 replay identical to 39, sample
            10W WA 0, 17ms. Verification standard upgraded from result-
            match to FULL-GAME COMMAND EQUALITY.
            Projected 6W 2D 0L -- realistic maximum (6/8 never beaten live).
[old]       40 = 39 + unknown-map runtime adaptation. Participant matches
            are played on unknown maps where NO map profile fires -- ranking
            games run the bare default engine. On unknown maps only (known
            8 hashes excluded -> sample score 100% preserved, verified by
            full-length identical replays): chip=True by default, and a
            turn-100 classifier (no invasion + outnumbered = turtle/growth
            opponent) switches on parity. Local A/B on random maps:
            proxy-econ 4W->5W (0 losses), turtle unchanged. 26ms.
[old]       38 = 37 + map6 {+hq_rush t165} (level-follow for the tiebreak)
            + map7 {+old_retreat} (completes the literal 30 reproduction).
            Both map-scoped; map5 win replays TURN-BY-TURN identical.
            Replays: map7 WIN restored, map6 L->D, map4 D kept, map5 WIN
            kept, sample 10W WA 0, 26ms. Projected 5W 3D 0L -- first
            zero-loss projection.
[old]       37 = 36 + profiles v3 + commit-push engine fixes.
            Profiles: map4 chip+no_push (we led 50v27 at T150, pushed, lost
            everything to their fortress; hold the lead, force 30-30, chip
            with numbers), map5 parity (34's survival shape).
            Engine (from the game-4 bottleneck audit):
            - commit push: retreat only on home invasion; the alive<enemy-5
              toggle caused attack/retreat flapping (T170-174: 38 attack +
              42 staging moves simultaneously)
            - sticky wave target: hold target until destroyed (siege gaps of
              6-8 turns let half-dead bases stand)
            - no deep recall: units in the enemy half never get recall orders
              (T185: 52 recall orders marched 30+ units home through the
              enemy army -> annihilated)
            Gates: map4 replay L->DRAW, map3 WIN t156 (faster), map7 WIN
            preserved, map6 DRAW, map5/8 diverged (WA t181/t168 -- the
            engine change is this submission's experiment). Sample 10W WA 0,
            27ms. Projected 4W 3D 1L.
[old]       36 = 33 + supply fund + profiles v2:
            map6 parity (server-proven), map7 shadow+no_fund (= literal
            revert of the shadow fix on that map; replay reproduces 30's
            win TURN-BY-TURN), maps 4/5/8 back to default engine.
            Replay suite: map3 W(166) map6 D map7 W map8 D, all clean,
            sample 10W WA 0, 27ms. Projected 4W 2D 2L (beats 30's 4W3L1D).
            NOTE: a silent edit-script failure (assert aborted before write)
            cost one debugging round -- always verify file state after
            scripted edits.
[old]       35-note: MAP_PROFILES keyed by map hash
            (verified stable across all 5 submissions). Overrides only on
            losing maps: 4/8 hq_rush(t60), 5 parity+hq_rush(t140), 6 parity,
            7 war_econ+hq_cap2 (30's winning shape). Maps 1/2/3 untouched.
            Replays vs 34's recordings: map3 WIN t197 clean, map8 WIN
            turn-limit clean (tiebreak flipped), map6 DRAW clean, map5/7
            disrupted early, map4 still loss. Sample smoke 10W WA 0,
            vs 33 2W2L16D (default behavior preserved), max 26ms.
[ideas]     HQ-race exception (turn-limit losses are HQ-level tiebreaks),
            paid-move waste (1.4k-2.3k gold vs bots 4/5 = 12-19 warriors),
            49ms proximity-scan optimization
```

A/B reading note: the 8 server games are deterministic matchups, so the real
verdict of a submission is WHICH game flipped and WHY, not the aggregate
score.

Representative answer on the server should stay on the best-scoring bot
(currently 30) until a challenger beats 4W 3L 1D.

## 32.py Server Result (2026-07-03)

```text
2W 6L -- worst so far; triggered the methodology revision above.
Base sentries dispersed home defense; bot 3's punch killed us at turn 106.
```

## 31.py Server Result (2026-07-03, logs in bots/31_nypc_log/)

```text
3W 1D 4L: wins 1, 2, 3 -- draw 4 -- losses 5, 6, 7, 8
Bot 4 (fast economy) improved to a DRAW; bot 3 stayed a win via turn-limit.
Bots 7 and 8 regressed: the war economy overreacts to PERSISTENT light
harassment, freezing HQ tech. All three turn-limit losses were HQ-LEVEL
tiebreaks (L3v4, L4v5, L3v4).
```

Failure anatomy:

- Bot 7: two roving harassers vetoed every expansion claim; 2 bases and total
  passivity for 160 turns despite army parity (10 vs 9).
- Bot 8: two raiders demolished bases one by one (worker+turret loses 1v2);
  49 field-combat deaths from one-by-one interception feeding; economy hit
  zero bases by turn 160.

## 32.py (candidate, gates passed 2026-07-03)

1. Group interception: respond to invaders only when free responders
   outnumber them (no more trickle-feeding 1v3 fights).
2. Escorted expansion: if no claimable stronghold exists, fewer than 4 bases,
   and only light harassment, send the group to clear the nearest contested
   stronghold, which reopens claims (breaks the bot-7 deadlock).
3. HQ race exception: from turn 110, if the enemy HQ level >= ours and no
   full invasion, HQ savings are allowed and protected from training even
   under pressure (the tiebreak is ultimately an HQ-level race).
4. Base sentries: bases with enemies within 4 hops hold work-cap+1 warriors;
   sentry + worker + turret self-defeats small raids (bot-8 fix). This broke
   the bot-8 collapse trajectory in replay (identical through 200 before,
   diverges at 114 now).

Gate results:

```text
pool 40 games: econ 5W 0L 15D, turtle 10W 0L 10D, rush 20W, punch 20W -- zero losses
sample 10W 0L, WA 0 everywhere
vs 30: 10W 2L 8D    vs 31: 2W 3L 15D (noise-range; sentries pay off only vs harassers)
replays: bot7 disrupted t195, bot8 collapse broken t114; bot5/6 unchanged (next targets)
```

## 30.py Server Result (2026-07-02, logs in bots/30_nypc_log/)

```text
4W 3L 1D: wins 1, 2, 3, 7 -- losses 4, 5, 6 -- draw 8
Bot 3 flipped back to a WIN (war-economy fix, as the replay predicted).
Bot 7 flipped to a WIN (illegal-upgrade-saving fix).
Bot 8 improved to a DRAW; bot 6 lost on HQ-level tiebreak (L3 vs L4).
Bot 4 regressed to a narrow loss (74 vs 80 alive at turn 192 -- coin-flip range).
```

## 31.py (candidate, gates passed 2026-07-02)

Fixes, each tied to a measured failure:

1. `outmassed` requires enemy_bases < my_bases: growth bots (server 6) that are
   ahead in BOTH army and economy must be out-grown, not hunkered against.
   Scout-level presence (1-2 near HQ) no longer flips war economy.
2. Interception targets invaders in MY half only near my buildings: kills the
   2-raider worker-slaughter treadmill without chasing frontier stacks.
3. Raid mode (turn 120+, no invasion, 2 waves ready, HQ L3+): eat the outer
   economy of home-stack turtles instead of waiting for an advantage that
   never comes.
4. Endgame chip (turn 180+): if losing the HQ-HP tiebreak, always attack;
   if tied, attack only with +4 alive. Turn 188+ base workers join (bases
   score nothing).
5. Expansion-savings shadow fix (THE big one): saving 300 for a stronghold
   that is not actually claimable (contested center) sat first in the queue
   and blocked HQ tech forever -- both 29 and 30 spend entire games at HQ L1
   on contested-center maps. Now we save only while a claim is live.
6. Endgame supply fund: training cannot eat the remaining upkeep budget
   (observed: 106 hunger events after a turn-175 push drained gold).

Gate results:

```text
vs 29: 16W 0L 4D      vs 30: 12W 2L 6D     (30 vs siblings was all draws)
proxy-econ 3W 0L 17D  proxy-turtle 13W 0L 7D  (both zero losses; 30 had 4L each)
proxy-rush 20W        proxy-punch 19W 1L      sample 10W, WA 0 everywhere
replays: bot3 WIN, bot6 DRAW, bot8 WIN, bot4/5 disrupted (WA)
max 2ms/turn, 29KB source, no data.bin
```

## 29.py Server Result (2026-07-02, logs in bots/29_nypc_log/)

```text
3W 5L: wins 1, 2, 4 -- losses 3, 5, 6, 7, 8
Bot 4 (fast economy) flipped to a WIN as the proxy pool predicted.
Bot 3 (basic aggressive) flipped to a LOSS at turn 79.
```

Diagnosis from logs:

- Bot 3 plays "bunker punch": 3 bases, HQ L1 forever, masses 16+ at home with
  zero forward presence, then one 13-warrior punch at ~turn 70. 29 spent 1800
  gold on HQ tech exactly as the punch landed and died 9-trains-vs-17.
- Bot 7 froze 29 at 955 gold: enemies camping the HQ region make UPGRADE
  illegal, but 29 kept SAVING for that upgrade, which locked training.

30.py fixes (validated by replaying the recorded bot-3 game: 29 dies turn 79,
30 wins turn 187; pool results unchanged, vs 25 17W1L2D, vs 29 0L 20D):

- `under_pressure` (raid, HQ-adjacent enemy, or being outmassed by 5+ before
  turn 140) switches to war economy: no tech saving, train at cap.
- Never save for an upgrade that is illegal due to enemy presence.
- Any enemy near the HQ triggers interception, not just 3+ raiders.
- New `proxy-punch` pool style approximates bot 3 (calibration imperfect:
  29 still beats it 10-0; the recorded-log replay is the real regression test).

`29.py` is a fresh macro-first bot grown from the proxy engine (NOT from the
26-28 heuristic lineage). It needs no `data.bin`. Stale unsubmitted candidates
(`26.py`, `27.py`, `28.py`) and all pre-24 history live in `bots/archive/`.

29.py gate results (2026-07-02, per docs/workflow.md):

```text
proxy-econ   seeds 1-5+11-15:  7W  4L  9D   (28.py was 0W)
proxy-turtle seeds 1-5+11-15: 12W  4L  4D   (28.py was 0W)
proxy-rush   seeds 1-5+11-15: 20W  0L  0D
sample smoke seeds 1-5:       10W  0L, WA 0
vs 24.py     seeds 1-10 both: 17W  1L  2D
vs 25.py     seeds 1-10 both: 17W  1L  2D
max per-turn 3ms, 24KB source
```

Key mechanisms in 29.py, in causal order of discovery (each fixed a measured
failure -- see results/29-v*-proxy-pool):

1. Economy flywheel: training into open worker slots outranks savings.
2. Builder stays as worker on the base it just built (income from day one).
3. Arrived expanders hold position while saving for the build.
4. Contested strongholds claimed only with local force superiority.
5. Base upgrades capped at L2 (L3 is 8 warriors' worth of gold for +1 slot).
6. Proportional defense: intercept raids (3+), evacuate and fortress on
   invasions (8+), rush-alert lockdown in the first 30 turns.
7. Push only with numeric advantage (alive >= enemy + 8) and HQ tech, in
   waves, targeting weakly-guarded enemy buildings; HQ override from turn 182.

## Diagnosis 2026-07-02: Self-Play Collapse

The local selection loop had converged to a degenerate turtle meta:

- All candidate-vs-submission games ended at turn 200, mostly draws
  (a local draw game showed 17 vs 11 total trains in 200 turns).
- 28.py passed the old "no new losses vs latest two" gate while actually
  LOSING to 24/25/27 on turn-limit HP comparison (0W in all pairings).
- Official bots 4-8 play a completely different game: 3 bases by turn ~21,
  6-10 bases total, 4 HQ upgrades, 41-111 trains, HQ kill around turn 187-195.
- Conclusion: the benchmark, not the heuristics, was the bottleneck. Improving
  against a meta that contains no fast-economy opponent cannot move the server
  score.

Fix: `opponents/proxy.py` imitates the official macro styles and is now the
primary selection gate. Calibration against 25.py (known server 3W 5L):

```text
proxy-econ   (bots 4/5):   25.py 0W 8L 2D, HQ_DESTROYED turns 194-198
proxy-turtle (bots 6/7/8): 25.py 0W 4L 6D, turn-limit HP losses
proxy-rush   (bots 1-3):   25.py 8W 2D    (25 also beat those on the server)
28.py baseline: 0% vs proxy-econ, 0% vs proxy-turtle, 100% vs proxy-rush
```

The proxy reproduces the server failure pattern locally, so raising proxy
win rate is the development target. See docs/workflow.md for the gate commands.

Key lesson encoded in the proxy itself (useful for the real bot too): training
into open worker slots is an economic investment (120 gold -> 15/turn, 9-turn
payback), so economy saving must never starve worker training, and pushes must
wait for HQ tech (warrior HP) and travel in waves, not trickles.

## Competition Structure

The qualifier is an iterative submit-and-analyze round.

- A submission can include one code file and optionally one binary file.
- Code must be at most 1 MiB (1,048,576 bytes).
- The optional binary file must be at most 10 MiB (10,485,760 bytes).
- If a binary file is uploaded, it is exposed at runtime as `data.bin`.
- In Python, read it with `open("data.bin", "rb")`.
- Uploaded `data.bin` bytes count as additional memory used by the program.
- `data.bin` is available only at runtime and is not available during compilation.
- Runtime external API calls, including OpenAI API calls, are not a viable submission strategy. The judge does not guarantee network access, API keys cannot be safely embedded, and the per-turn 100ms limit leaves no room for remote inference.
- Immediately after submission, NYPC evaluates the answer against sample AIs and returns win/draw/loss results plus logs.
- The input is fixed.
- Sample AIs use the same strategy on the same input, so submitted logs are repeatable feedback for that submitted bot.
- Answers can be submitted many times.
- Among submitted answers, one representative answer can be selected for evaluation.
- Periodic rankings against other participants use the selected/latest representative submission state; confirm the UI before relying on a non-latest bot.
- At least the top 20 teams advance.

Qualifier round deadline:

```text
2026-07-08 22:00 KST
```

Execution environment:

```text
AWS c7a.2xlarge
AMD EPYC 4th gen custom processor
Clock: 3.7 GHz
Architecture: 64 bit
OS: Ubuntu 24.04
```

Strategic implication: submit stable candidates often enough to harvest official-bot logs, but avoid leaving an obviously experimental regression as the representative answer used for ranking.

For model-assisted work, use external tools only offline: analyze logs, generate maps/features/tables, then package the result into source constants or `data.bin`. The submitted bot must be self-contained.

## Current Server Baseline

`25.py` was submitted and `bots/25_nypc_log/` has been normalized to `1.txt` through `8.txt`.

Assuming the submitted bot is LEFT, the official-bot result is:

```text
25.py: 3W 5L
wins:  1.txt, 2.txt, 3.txt
losses: 4.txt, 5.txt, 6.txt, 7.txt, 8.txt
```

Important observations from `25.py`:

```text
25_nypc_log/4.txt: loses by HQ_DESTROYED on turn 189 after front shuttle/oscillation and enemy fast economy.
25_nypc_log/5.txt: loses by HQ_DESTROYED on turn 187; left trains 48, right trains 111, and left has long empty-command production gaps.
25_nypc_log/6.txt: loses by HQ_DESTROYED on turn 194 while stuck at 3 bases against enemy 7 bases.
25_nypc_log/7.txt: loses by HQ_DESTROYED on turn 191 after feeding units into a larger enemy stack.
25_nypc_log/8.txt: survives to turn limit but loses final state; expansion/rebuild is late.
```

So `26.py` targets meaningless work first: idle production, over-defense at home, A-B-A movement reversals, unwinnable base defense, and late mass response.

## Lessons From NYPC 2025 Reviews

The 2025 Code Battle writeups point to a deeper workflow than single-file heuristic tuning:

- Maintain many candidate strategies and pick a champion from large local leagues.
- Do not trust official sample bots alone; sample bots can be weak, weird, or unrepresentative.
- Save logs and statistics for each candidate, then select by robust matchups rather than one lucky score.
- Use offline computation or data files when the game has a stable state space or fixed inputs.
- Compress/quantize data only after measuring information loss against the original table.
- Prefer wider, reliable candidate evaluation over a deep but brittle search when the heuristic can prune away the real best move.
- Add dynamic strategy switching after identifying opponent style, instead of playing one fixed policy.
- Keep the final submitted representative conservative if experimental variants beat the champion locally but have side-effect risk.

The direct translation for this problem:

- Build a small league/test harness around saved submitted bots and candidate variants.
- Turn server logs into features: map fingerprint, enemy base timing, HQ timing, train count, pressure distance, HQ siege timing, final HP/result.
- Add opponent classification: rush, turtle, fast economy, balanced pressure, passive/idle.
- Track or estimate enemy gold/resources from observed successful actions and deterministic income/upkeep.
- Use map-specific or opponent-class-specific parameter profiles once enough official logs identify stable patterns.
- Treat official 8-bot logs as data. Submission count is plentiful, so stable submissions are a way to query the official environment.

## data.bin Opportunities

`data.bin` gives us a 10 MiB side channel for precomputed data. This matters because the official input is fixed and sample AIs are deterministic for the same input.

Evidence from our logs:

- Official logs across submissions keep stable map hashes for every corresponding index.
- This strongly suggests the 8 official sample-AI matches use stable indexed maps/opponents across submissions.
- Example regression to target:
  - index 7 map hash stayed the same
  - `8.py` survived to `RIGHT_WIN TURN_LIMIT`
  - `9.py` lost by `RIGHT_WIN HQ_DESTROYED`

Useful candidates:

- Map fingerprints -> official-bot index/profile parameters.
- Official-bot fingerprints from the 8 returned logs -> response profiles.
- Precomputed stronghold rankings, chokepoints, rush paths, defense anchor regions.
- Candidate parameter tables selected by `(map_id, opponent_profile, side)`.
- Compact statistics from local leagues: which profile beats which prior submission on which map class.

Recommended phases:

1. `data.bin` v0: no file. Hardcode only tiny profile experiments directly in code while proving value.
2. `data.bin` v1: compact map-hash table for the 8 official sample maps, profile labels, and small parameter overrides.
3. `data.bin` v2: larger table generated from local leagues and official logs, keyed by map features/profile class rather than exact map only. Used since `26.py`; the current candidate reads `28_data.bin`.
4. `data.bin` v3: precomputed path/stronghold/chokepoint scores if runtime computation or code-size pressure becomes meaningful.

Rules for using it safely:

- The bot must still run if `data.bin` is missing, so local testing remains simple.
- Keep the binary format tiny and versioned.
- Measure whether the data improves official-log replay and latest-two sparring before depending on it.
- Do not spend the 10 MiB budget on raw logs; store compact features/tables.
- For the current 8 official maps, exact hash-based overrides can fit in source code; use `data.bin` only when the table becomes too large or generated too often to maintain safely by hand.

## Candidate Research Notes (26 -> 28 lineage)

Inherited by the current candidate line from submitted `25.py`:

- Official map hash fingerprinting compatible with server log hashes.
- Built-in official 8-map profile table plus optional JSON `data.bin` override.
- Candidate-specific local data lookup: `26_data.bin`.
- Approximate enemy gold tracking from enemy upgrades, training, income, and upkeep.
- Profile-gated worker fill, urgent defense, HQ catch-up, and map-specific target-army caps.
- Protected-worker retention so base workers are not accidentally pulled into HQ worker/defender roles.
- Map/side plan data for expansion order, safe expansion order, frontier order, and staging.
- Anti-idle production when the enemy army is clearly ahead and no immediate HQ threat exists.
- Over-defense release so home garrison shrinks when the enemy is too far to punish.
- Abort rules for unwinnable base defense.
- Late swarm staging against huge enemy stacks.

Historical `26.py` validation before upload (pre-diagnosis; the all-draw
pattern below is exactly the degenerate meta described in the 2026-07-02
diagnosis section, not evidence of strength):

```text
sample smoke, seeds 1..10 both sides: 20W 0L 0D, WA 0
26 vs 24 local spar, seeds 151..170 both sides: 0W 0L 40D, WA 0
26 vs 25 local spar, seeds 151..170 both sides: 0W 0L 40D, WA 0
```

Official `25.py` server result:

```text
25.py: 3W 5L
wins: 1, 2, 3
losses: 4, 5, 6, 7, 8
```

Replay-side WA is not a real official win guarantee; it only means the new policy changes the state enough that recorded opponent commands become illegal.

Official `25` right-side replay with `26.py`:

```text
7W 1L, WA 4
Hard replay loss remains official map 5 (`77a57b8f617a`), turn 190.
```

So the current candidate is uploadable as a conservative probe, but the next work after submission should focus on official map 5.

Priority order (updated 2026-07-02):

1. Rebuild the candidate's macro so it beats `proxy-econ` and `proxy-turtle`:
   match the official expansion curve (3 bases ~turn 21, 5 by ~45), keep worker
   slots trained, tech HQ to 4-5, then attack in waves.
2. Gate every candidate on the proxy pool first, sample smoke second,
   latest-two spar third (see docs/workflow.md).
3. Submit the first candidate that clearly beats proxy-econ/turtle and analyze
   which official bots flip to wins.
4. Use `tools/extract_log_features.py` after every submission; if a proxy pool
   result disagrees with the server result, recalibrate the proxy styles from
   the new official logs.
5. Add broader opponent profile detection only when backed by official
   evidence.

The target is a reproducible selection loop: official logs -> proxy styles ->
candidate variant -> proxy-pool gate -> server submission -> recalibration.

Current official-bot profile sketch from `25.py` logs:

```text
1: passive/no-economy target; 25 wins by HQ_DESTROYED
2: short rush/interaction; 25 wins by HQ_DESTROYED
3: moderate economy/pressure; 25 wins by TURN_LIMIT
4: fast economy/many bases; 25 loses by HQ_DESTROYED
5: heavier fast economy/mass training; 25 loses by HQ_DESTROYED
6: turtle/tech/economy; 25 loses by HQ_DESTROYED
7: economy/turtle with large stack; 25 loses by HQ_DESTROYED
8: economy/turtle; 25 loses by TURN_LIMIT
```

## Official Python Sample Code

NYPC's Python/PyPy sample files are located outside the repo at:

```text
/Volumes/samsd/download_samsd/samplecode/
```

Both `sample-codepy.py` and `sample-codepypy.py` are identical. They are useful as protocol references, but the strategy is intentionally minimal: on turn 1, move every friendly warrior toward the enemy HQ and do nothing else.

Takeaways:

- Keep their parser/turn-result assumptions in mind when changing protocol code.
- Do not use the sample strategy as a performance baseline.
- The sample tracks only our gold, so enemy resource estimation is not provided by the official example.

## Validation Loop

Before upload, run:

```bash
CANDIDATE=bots/<candidate>.py
python3 -m py_compile "$CANDIDATE" tools/*.py
```

Run latest-two submission sparring:

```bash
python3 tools/run_submission_spar.py \
  --candidate "$CANDIDATE" \
  --latest 2 \
  --start 1 \
  --count 10 \
  --side both \
  --name candidate-vs-last2-10
```

Use `--count 10` for iteration to keep `bots/<candidate>_<submitted>log/` compact. Increase to `20` or `50` only for final confidence.

This also refreshes:

```text
bots/<candidate>_<old>log/
bots/<candidate>_<latest>log/
bots/<candidate>_<old>log.txt
bots/<candidate>_<latest>log.txt
```

After editing the candidate, delete stale local sparring logs before trusting any result:

```bash
rm -rf bots/<candidate>_*log bots/<candidate>_*log.txt
```

If server logs are available, analyze them:

```bash
python3 tools/analyze_server_logs.py bots/<submitted>_nypc_log
```

For a specific server loss replay:

```bash
python3 tools/run_log_replay.py \
  'bots/<submitted>_nypc_log/<loss>.txt' \
  --replay-side right \
  --candidate "$CANDIDATE" \
  --name replay-loss
```

Current local check files should live beside the bot. Latest baseline
(2026-07-02, gate order per docs/workflow.md):

```text
28.py proxy pool: proxy-econ 0W 10L, proxy-turtle 0W 10L, proxy-rush 10W 0L, WA 0
28 vs 24/25 spar: 0W 5L 15D each (turn-limit HP losses)
```

## Acceptance Criteria

- `WA = 0` in local checks.
- proxy-econ / proxy-turtle win rate at or above the previous candidate
  (primary criterion; current baseline is 0%).
- No new losses against proxy-rush or the latest two submissions.
- Server-loss replay should show materially disrupted losing trajectories without local WA.
- New server logs should show fewer idle production gaps, less over-defense, and fewer unwinnable base feeds.

## After Each Server Submission

1. Upload the current candidate.
2. NYPC starts sample-AI evaluation immediately and returns win/draw/loss logs.
3. Treat that uploaded file as the next submitted snapshot.
4. Delete the oldest submitted snapshot so only the latest two submitted snapshots remain.
5. Store NYPC logs for that submission as `bots/<number>_nypc_log/`.
6. Create the next candidate as the next numeric file, for example `bots/5.py`.
7. Delete the submitted candidate's local sparring logs, because they describe the pre-submission candidate-testing loop.
8. Use the new server logs as the next source of truth.
9. If the UI allows choosing a representative answer, make sure the intended stable submission is selected for ranking.

Example shape after submitting a candidate:

```bash
rm bots/<old>.py
rm -rf bots/<candidate>_*log bots/<candidate>_*log.txt
mv <downloaded_log_dir> bots/<submitted>_nypc_log
cp bots/<submitted>.py bots/<next_candidate>.py
```

Remaining core files:

```text
bots/<latest>.py
bots/<submitted>.py
bots/<submitted>_nypc_log/
bots/<next_candidate>.py
```

## Directory Policy

Keep:

```text
bots/<latest two submitted>.py
bots/<current candidate>.py
bots/<submission_number>_nypc_log/
bots/<candidate>_<submitted>log/
bots/<candidate>_<submitted>log.txt
docs/workflow.md
tools/
nation-providing/
game-rule.md
strategy-plan.md
```

Disposable:

```text
logs/
__pycache__/
.DS_Store
```

Do not reintroduce weak local synthetic opponent pools unless a new pool is demonstrably stronger than the current candidate.
