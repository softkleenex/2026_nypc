# Official Log Coverage

`bots/145.py` was replayed against every archived official `*_nypc_log`
directory using the recorded RIGHT-side opponent commands.

## Summary

| Source logs | Games | Original W/L/D | 145 replay W/L/D | Replay WA |
|---|---:|---:|---:|---:|
| `30`, `45`, `60`, `61` | 32 | mixed | 32/0/0 | 21 |
| `62`, `76`, `77`, `78` | 33 | mixed | 33/0/0 | 13 |
| `91`, `125`, `143`, `145` | 32 | mixed | 32/0/0 | 3 |
| **Total** | **97** | **87/5/5** | **97/0/0** | **37** |

Commands:

```bash
python3 tools/run_log_replay.py bots/30_nypc_log bots/45_nypc_log bots/60_nypc_log bots/61_nypc_log --candidate bots/145.py --replay-side right --name 145-official-logs-30-61-right --timeout 60
python3 tools/run_log_replay.py bots/62_nypc_log bots/76_nypc_log bots/77_nypc_log bots/78_nypc_log --candidate bots/145.py --replay-side right --name 145-official-logs-62-78-right --timeout 60
python3 tools/run_log_replay.py bots/91_nypc_log bots/125_nypc_log bots/143_nypc_log bots/145_nypc_log --candidate bots/145.py --replay-side right --name 145-official-logs-91-145-right --timeout 60
```

## Original Non-Win Logs Covered By 145

| Original log | Original result | 145 replay status |
|---|---|---|
| `bots/30_nypc_log/4.txt` | `RIGHT_WIN HQ_DESTROYED` | win |
| `bots/30_nypc_log/5.txt` | `RIGHT_WIN HQ_DESTROYED` | win |
| `bots/30_nypc_log/6.txt` | `RIGHT_WIN TURN_LIMIT` | win |
| `bots/30_nypc_log/8.txt` | `DRAW TURN_LIMIT` | win |
| `bots/45_nypc_log/6.txt` | `DRAW TURN_LIMIT` | win |
| `bots/60_nypc_log/6.txt` | `DRAW TURN_LIMIT` | win |
| `bots/76_nypc_log/3.txt` | `RIGHT_WIN HQ_DESTROYED` | win |
| `bots/78_nypc_log/211083 .txt` | `RIGHT_WIN HQ_DESTROYED` | win |
| `bots/125_nypc_log/8.txt` | `DRAW TURN_LIMIT` | win |
| `bots/143_nypc_log/8.txt` | `DRAW TURN_LIMIT` | win |

## Interpretation

This is replay evidence, not a guarantee against adaptive user bots. Still, it
is useful regression coverage: every archived official-bot loss/draw pattern
now branches to a `145.py` win when the recorded opponent side is replayed.
