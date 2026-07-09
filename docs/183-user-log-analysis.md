# 183 User Log Analysis

Source: `bots/183_user_log` middle evaluation #30, July 8 21:00 KST.

## Result Summary

- Site result: Tier 7, rating 1710, rank 579 / 937.
- Match score: 8 wins, 2 draws, 10 losses.
- Non-win set: `248550_R`, `248899_A`, `249753_A`, `250543_B`,
  `251402_B`, `252269_B`, `252705_B`, `253568_B`, `254038_A`,
  `255293_B`, `256149_B`, `256630_A`.

## Main Failure Modes

### Lower-Tier Losses Are Real

This result was not only "lost to strong opponents." The bot also lost or drew
against lower-tier opponents:

- Tier 1 `248899_A`: loss at T95 with both sides stuck at 0 bases.
- Tier 3 `249753_A`: draw at T200 with both sides stuck at 0 bases.
- Tier 5 `254038_A`: loss at T87 despite equal base count.

These games point to brittle strategic branches rather than opponent strength.

### Late Economy Collapse

The largest group is not an early-rush failure. We stay playable through
T60-T100, then lose base count and army count while the opponent scales.

Representative logs:

- `248550_R`: by T100, bases are 3 vs 11; by T180, 1 vs 10 and enemy HQ is L5.
- `251402_B`: similar army until T120, then enemy reaches 32 army by T180.
- `252705_B`: even until T100, then enemy reaches 38 army / 9 bases by T150.
- `253568_B`, `256149_B`, `256630_A`: bases fall to 0-2 while enemy reaches 11-12 bases.

Likely weakness: midgame defense spends bodies but does not preserve or retake
economic strongholds fast enough. Once the base network collapses, training and
HQ upgrades cannot recover.

### Midgame HQ Breakthrough

Several losses are direct HQ races where the signal is visible but too late to
change the result.

- `250543_B`: enemy HQ-bound wave starts around T74; trace becomes strong T79-T84.
- `254038_A`: enemy HQ-bound wave starts around T71; trace is strong immediately.
- `255293_B`: no bases from early game, then a huge T134-T136 HQ wave finishes.

Likely weakness: HQ-intent detection has high precision, but the response is
mostly generic threat handling. It does not always convert into enough local
HQ blockers or emergency training before the wave arrives.

### Zero-Base / No-Expansion Games

`248899_A` and `249753_A` spend almost the whole game with 0 bases on both sides.
`248899_A` loses at T95; `249753_A` draws at T200. These are special topology or
opening-interaction games where the ordinary expansion queue never establishes
economy.

Likely weakness: if no safe expansion exists early, the bot needs a fallback
plan: HQ timing, controlled all-in, or alternate stronghold claim instead of
waiting in a low-economy loop.

## Movement Prediction Findings

The data-driven HQ intent signal generalized well:

- `target_policy_hq_support >= 1`: 43 predicted turns, 42 correct.
- grouped HQ policy: 32 predicted turns, 32 correct.
- `trace_hq_support >= 8`: 39 predicted turns, 35 correct.

The issue is recall and timing, not precision. The model catches many committed
HQ moves correctly, but only a small fraction of all HQ-bound turns and often
after the strategic damage is already done.

## Actionable Next Work

1. Add a midgame base-preservation mode for T90-T160 when enemy base count leads
   by 3+ and our army is not clearly ahead.
2. Convert strong HQ-intent signals into explicit emergency actions: stop
   expansion, train to cap, keep HQ-local blockers, and avoid sending local
   defenders to staging.
3. Add a zero-base fallback for no-expansion maps: if both sides have 0 bases
   past T25-T35, choose HQ tech / all-in / alternate claim deliberately.
4. Use `data.bin` for higher-recall movement policy only if it predicts earlier
   than trace; current policy is safe but too sparse.
