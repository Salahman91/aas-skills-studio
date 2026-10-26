#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يتحقق أن كل تصنيف في catalog.json مُسند مرة واحدة بالضبط داخل groups.json."""
import json
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    catalog = json.loads((root / "data" / "catalog.json").read_text(encoding="utf-8"))
    groups = json.loads((root / "data" / "groups.json").read_text(encoding="utf-8"))["groups"]

    all_cats = {c["id"]: c["count"] for c in catalog["categories"]}
    assigned = {}
    problems = []

    for group in groups:
        for sub in group["subs"]:
            for cat in sub["cats"]:
                if cat in assigned:
                    problems.append("duplicate: %s (in %s and %s)" % (cat, assigned[cat], sub["id"]))
                assigned[cat] = "%s/%s" % (group["id"], sub["id"])
                if cat not in all_cats:
                    problems.append("unknown category in groups.json: %s" % cat)

    missing = [c for c in all_cats if c not in assigned]
    for cat in missing:
        problems.append("unassigned: %s (%d skills)" % (cat, all_cats[cat]))

    total = 0
    print("groups=%d subs=%d categories=%d assigned=%d"
          % (len(groups), sum(len(g["subs"]) for g in groups), len(all_cats), len(assigned)))
    for group in groups:
        gcount = sum(all_cats.get(c, 0) for s in group["subs"] for c in s["cats"])
        total += gcount
        print("  %-10s %-28s %4d skills" % (group["id"], group["ar"], gcount))
        for sub in group["subs"]:
            scount = sum(all_cats.get(c, 0) for c in sub["cats"])
            print("      %-12s %-34s %4d" % (sub["id"], sub["ar"], scount))
    print("total skills mapped:", total, "of", sum(all_cats.values()))

    if problems:
        print("GROUPS CHECK FAIL")
        for item in problems:
            print("  - " + item)
        return 1
    print("GROUPS CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
