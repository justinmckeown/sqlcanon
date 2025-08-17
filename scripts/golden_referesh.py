from __future__ import annotations

import argparse
from pathlib import Path

from sqlcanon import Canonicalizer, Config

BASE = Path(__file__).resolve().parent.parent / "tests" / "golden"

PROFILES = {
    "default": Config(),  # includes literal scrubbing
    "exec": Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"]),
}


def refresh_profile(profile: str) -> int:
    inputs = BASE / profile / "inputs"
    expected = BASE / profile / "expected"
    expected.mkdir(parents=True, exist_ok=True)

    cfg = PROFILES[profile]
    canon = Canonicalizer()

    changed = 0
    for in_path in sorted(inputs.glob("*.sql")):
        out = canon.normalise(in_path.read_text(encoding="utf-8"), cfg)
        exp_path = expected / in_path.name
        old = exp_path.read_text(encoding="utf-8") if exp_path.exists() else None
        if old != out:
            exp_path.write_text(out, encoding="utf-8")
            changed += 1
            print(f"[{profile}] updated: {in_path.name}")
    return changed


def main():
    ap = argparse.ArgumentParser(description="Refresh golden expected SQL outputs.")
    ap.add_argument("--profile", choices=["default", "exec", "all"], default="all")
    args = ap.parse_args()

    total = 0
    if args.profile == "all":
        for p in ("default", "exec"):
            total += refresh_profile(p)
    else:
        total += refresh_profile(args.profile)

    if total == 0:
        print("No changes.")
    else:
        print(f"Updated {total} file(s).")


if __name__ == "__main__":
    main()


# NOTE: To use this in Powershell do the following: python scripts/golden_refresh.py --profile all
