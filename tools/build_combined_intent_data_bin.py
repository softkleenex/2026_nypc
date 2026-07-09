#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_intent_data_bin import build_profiles, collect_logs, default_roots
from intent_policy_data import build as build_policy
from movement_target_policy_data import build as build_target_policy


ROOT = Path(__file__).resolve().parents[1]
MAX_DATA_BIN = 10 * 1024 * 1024


def main() -> None:
    parser = argparse.ArgumentParser(description="Build combined map-edge and generic intent data.bin.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "bots" / "158_data.bin")
    parser.add_argument("--edge-min-count", type=int, default=3)
    parser.add_argument("--edge-min-precision", type=float, default=0.75)
    parser.add_argument("--policy-min-count", type=int, default=20)
    parser.add_argument("--policy-min-precision", type=float, default=0.85)
    parser.add_argument("--target-policy-min-count", type=int, default=20)
    parser.add_argument("--target-policy-min-precision", type=float, default=0.9)
    parser.add_argument("--target-policy-labels", default="my_hq,enemy_hq")
    args = parser.parse_args()

    roots = args.paths or default_roots()
    logs = collect_logs(roots)
    policy_payload = build_policy(logs, args.policy_min_count, args.policy_min_precision)
    target_labels = set(args.target_policy_labels.split(",")) if args.target_policy_labels else set()
    target_payload = build_target_policy(
        logs,
        args.target_policy_min_count,
        args.target_policy_min_precision,
        target_labels,
    )
    payload = {
        "format": "nypc-158-intent-combined-json",
        "version": 2,
        "edge_min_count": args.edge_min_count,
        "edge_min_precision": args.edge_min_precision,
        "policy_min_count": args.policy_min_count,
        "policy_min_precision": args.policy_min_precision,
        "target_policy_min_count": args.target_policy_min_count,
        "target_policy_min_precision": args.target_policy_min_precision,
        "target_policy_labels": sorted(target_labels),
        "profiles": build_profiles(logs, args.edge_min_count, args.edge_min_precision),
        "policy": policy_payload["policy"],
        "target_policy": target_payload["policy"],
    }
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_DATA_BIN:
        raise SystemExit(f"data.bin too large: {len(raw)} > {MAX_DATA_BIN}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    edge_count = sum(
        len(side.get("hq_edges", {}))
        for profile in payload["profiles"].values()
        for side in (profile.get("left", {}), profile.get("right", {}))
        if isinstance(side, dict)
    )
    print(
        f"wrote {args.output} ({len(raw)} bytes, profiles={len(payload['profiles'])}, "
        f"edges={edge_count}, policy_keys={len(payload['policy'])}, "
        f"target_policy_keys={len(payload['target_policy'])})"
    )


if __name__ == "__main__":
    main()
