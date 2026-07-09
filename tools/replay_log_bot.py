#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def load_commands(log_path: Path, side: str) -> dict[int, list[str]]:
    commands: dict[int, list[str]] = {}
    turn = 0
    capture = False
    current: list[str] = []
    start = f"COMMAND {side} START"
    end = f"COMMAND {side} END"

    for line in log_path.read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == "TURN":
            turn = int(parts[1])
        elif line == start:
            capture = True
            current = []
        elif line == end:
            commands[turn] = current
            capture = False
        elif capture:
            current.append(line)

    return commands


def read_required() -> str:
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return line.rstrip("\n")


def drain_init() -> None:
    ready = read_required().split()
    if len(ready) < 2 or ready[0] != "READY":
        sys.exit(1)
    n, _k = map(int, read_required().split()[:2])
    read_required()
    read_required()
    read_required()
    for _ in range(n):
        read_required()
    print("OK", flush=True)


def drain_result_block() -> None:
    while True:
        line = read_required()
        if line == "FINISH" or line == "END":
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay one side's command blocks from a saved NYPC log.")
    parser.add_argument("log", type=Path)
    parser.add_argument("--side", choices=["LEFT", "RIGHT"], required=True)
    args = parser.parse_args()

    commands = load_commands(args.log, args.side)
    drain_init()

    while True:
        line = read_required()
        if line == "FINISH":
            return
        parts = line.split()
        if len(parts) != 3 or parts[0] != "START" or parts[1] != "TURN":
            sys.exit(1)
        turn = int(parts[2])

        print("COMMAND")
        for cmd in commands.get(turn, []):
            print(cmd)
        print("END", flush=True)
        drain_result_block()


if __name__ == "__main__":
    main()
