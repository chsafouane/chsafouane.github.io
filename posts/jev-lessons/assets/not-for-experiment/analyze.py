# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scikit-learn>=1.3"]
# ///
"""Report one variant on one split, or compare two variants on the same messages (paired).

uv run analyze.py baseline dev            # errors, confusions, calibration, automation curve
uv run analyze.py baseline notfor test    # paired comparison
"""
import json
import sys
from collections import Counter

import numpy as np

EDGES = np.array([0, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0])


def load(variant, split):
    rows = [r for r in json.load(open(f"results_{variant}.json")) if r["split"] == split]
    return sorted(rows, key=lambda r: (r["label"], r["text"]))


def ece(p, y):
    p, y = np.asarray(p, float), np.asarray(y, float)
    idx = np.clip(np.searchsorted(EDGES, p, side="right") - 1, 0, len(EDGES) - 2)
    return sum((idx == b).mean() * abs(p[idx == b].mean() - y[idx == b].mean())
               for b in range(len(EDGES) - 1) if (idx == b).any())


def summary(rows):
    right = np.array([r["choice"] == r["label"] for r in rows])
    top = np.array([max(r["probs"].values()) for r in rows])
    conf = np.array([r["confidence"] for r in rows])
    flips = np.mean([r["choice"] != r["choice_rev"] for r in rows])
    shift = np.array([max(abs(r["probs"][k] - r["probs_rev"][k]) for k in r["probs"]) for r in rows])
    return right, top, conf, flips, shift


def curve(conf, right):
    out = []
    for t in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99):
        auto = conf >= t
        out.append((t, auto.mean(), right[auto].mean() if auto.any() else float("nan"), int((~right[auto]).sum())))
    return out


def report(variant, split):
    rows = load(variant, split)
    right, top, conf, flips, shift = summary(rows)
    print(f"{variant} / {split}: n={len(rows)} accuracy {right.mean():.3f}  ECE {ece(top, right):.3f}  "
          f"Brier {np.mean((top - right) ** 2):.3f}")
    print(f"  order check: winner flips {flips:.1%}, median max shift {np.median(shift):.3f}, "
          f"share shift > 0.1 {np.mean(shift > 0.1):.1%}")
    for t, cov, acc, wrong in curve(conf, right):
        print(f"  threshold {t:.2f}  automate {cov:6.1%}  accuracy {acc:6.1%}  wrong {wrong}")
    pairs = Counter((r["label"], r["choice"]) for r in rows if r["choice"] != r["label"])
    print("  confusions (label -> pick):")
    for (l, c), n in pairs.most_common():
        print(f"    {n}  {l} -> {c}")
    print("  confident errors (top >= 0.9):")
    for r in sorted(rows, key=lambda r: -max(r["probs"].values())):
        if r["choice"] != r["label"] and max(r["probs"].values()) >= 0.9:
            print(f"    {max(r['probs'].values()):.2f}  {r['label']} -> {r['choice']}  | {r['text']}")


def compare(a, b, split):
    ra, rb = load(a, split), load(b, split)
    assert [r["text"] for r in ra] == [r["text"] for r in rb]
    ya, ta, ca, fa, sa = summary(ra)
    yb, tb, cb, fb, sb = summary(rb)
    rng = np.random.default_rng(0)
    n = len(ya)
    diffs = [yb[i].mean() - ya[i].mean() for i in (rng.integers(0, n, n) for _ in range(5000))]
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    print(f"{split}, n={n}")
    print(f"  accuracy  {a} {ya.mean():.3f}   {b} {yb.mean():.3f}   diff {yb.mean() - ya.mean():+.3f} "
          f"(95% paired bootstrap {lo:+.3f} to {hi:+.3f})")
    print(f"  fixed by {b}: {int((~ya & yb).sum())}   broken by {b}: {int((ya & ~yb).sum())}")
    print(f"  ECE       {a} {ece(ta, ya):.3f}   {b} {ece(tb, yb):.3f}")
    print(f"  Brier     {a} {np.mean((ta - ya) ** 2):.3f}   {b} {np.mean((tb - yb) ** 2):.3f}")
    print(f"  order: winner flips {fa:.1%} -> {fb:.1%}; share shift > 0.1 {np.mean(sa > 0.1):.1%} -> {np.mean(sb > 0.1):.1%}")
    print("  automation curve (threshold: automate / accuracy)")
    for (t, c1, a1, w1), (_, c2, a2, w2) in zip(curve(ca, ya), curve(cb, yb)):
        print(f"    {t:.2f}   {a}: {c1:6.1%} / {a1:6.1%} ({w1} wrong)   {b}: {c2:6.1%} / {a2:6.1%} ({w2} wrong)")
    watch = ["How can I check the exchange rate applied to my transaction?", "How long can an EU transfer take?",
             "How do I reset my PIN?", "Do I need to verify my identity?"]
    for r1, r2 in zip(ra, rb):
        if r1["text"] in watch:
            print(f"  [{r1['label']}] {r1['text']}\n     {a}: {r1['choice']} {max(r1['probs'].values()):.2f}"
                  f"   {b}: {r2['choice']} {max(r2['probs'].values()):.2f}")


if __name__ == "__main__":
    args = sys.argv[1:]
    report(*args) if len(args) == 2 else compare(*args)
