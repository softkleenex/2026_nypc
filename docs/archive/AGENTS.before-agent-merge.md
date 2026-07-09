# Repository Guidelines

## Project Structure & Module Organization

`bots/` contains numbered, self-contained Python bot submissions. Keep server and user logs in `bots/<n>_nypc_log/` and `bots/<n>_user_log*/` as source data. `tools/` holds evaluation, replay, and log-analysis scripts; `run_many.py` forwards to `tools/evaluate.py`. `nation-providing/` contains the official `testing-tool.py`, sample bot, and config. `opponents/proxy.py` provides local proxy opponents. `results/` is generated output from evaluations. `docs/`, `game-rule.md`, `strategy-plan.md`, and `CLAUDE.md` document rules, workflow, and current strategy.

## Build, Test, and Development Commands

There is no package build step. Use Python directly:

```bash
python3 -m py_compile bots/<n>.py tools/*.py
```

Checks syntax for a candidate and tool scripts.

```bash
python3 tools/evaluate_pool.py --bot bots/<n>.py --start 1 --count 5 --side both --pools sample --name <n>-sample-smoke
python3 tools/evaluate.py --bot bots/<n>.py --opponent "python3 $PWD/bots/<base>.py" --left-opponent "python3 $PWD/bots/<base>.py" --side both --start 1 --count 10 --timeout 300 --name <n>-vs-<base> --quiet
```

Runs the standard smoke and sparring gates. For one official-tool match, run from `nation-providing/` with `python3 testing-tool.py --seed 42 -l ../results/smoke.log -a "python3 ../bots/<n>.py" -b "python3 sample-code.py P2"`.

## Coding Style & Naming Conventions

Use Python 3 with four-space indentation. Existing code favors `from __future__ import annotations`, stdlib-only dependencies, `pathlib.Path`, `argparse`, dataclasses where useful, `snake_case` functions, `PascalCase` classes, and uppercase constants. Bot files are numbered (`bots/135.py`); create a new candidate by copying the best server bot to the next number and making one focused change. Submitted bots must stay self-contained and avoid network or external API calls.

## Testing Guidelines

There is no unit-test suite. Treat `py_compile`, sample smoke, sparring, replay, and log analysis as the verification loop. Inspect `results/<name>/results.csv` for WA, max turn time, and side-specific regressions. Use `python3 tools/analyze_server_logs.py bots/<n>_nypc_log` and `python3 tools/log_timeline.py <log> --every 40` to validate server-log hypotheses.

## Commit & Pull Request Guidelines

This workspace root has no Git history, so no project commit convention is detectable. If contributing through Git, use concise imperative commits such as `Add candidate 136 pressure gate`. PRs should state the bot number, exact change, commands run, win/loss/draw and WA counts, max ms from `results.csv`, and any server or user logs used. Link the relevant `strategy-plan.md` note when applicable.

## Data Safety

Do not delete or rewrite `*_nypc_log/`, `*_user_log*/`, or `bots/archive/` data. Treat `results/` as disposable only after conclusions are recorded in `strategy-plan.md`.
