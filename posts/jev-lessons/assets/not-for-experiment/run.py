# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk~=0.7.0", "numpy"]
# ///
"""Banking77 not_for experiment: same sample and split as 19_calibration_check_and_fix.py (seed 7, 8 per label),
with an optional descriptions file for the 77 options.

Each request asks:
  intent      the 77-way Choice, options in alphabetical order (as in script 19)
  intent_rev  the same Choice with the options reversed (questions are isolated, so it doesn't affect `intent`)
  candidate   the Noul from script 19, unchanged

Usage: uv run run.py --variant baseline --split dev
       uv run run.py --variant notfor --descriptions descriptions.json --split dev
Results (one row per message, full probabilities) go to results_<variant>.json; responses are cached per variant.
"""
import argparse
import csv
import io
import json
import random
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from typesafe_sdk import Choice, Noul, TypeSafeClient

SOURCE = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv"
STOP = {"a", "or", "of", "by", "to", "my", "not", "on", "in", "the", "is", "up"}


def human(label):
    return label.replace("_", " ").strip().lower()


def sample(rows, per_label, rng):
    by = defaultdict(list)
    for text, label in rows:
        by[label].append(text)
    dev, test = [], []
    for label in sorted(by):
        picks = rng.sample(by[label], min(per_label, len(by[label])))
        half = len(picks) // 2
        dev += [(t, label) for t in picks[:half]]
        test += [(t, label) for t in picks[half:]]
    return dev, test


def candidate_for(label, labels, rng):
    if rng.random() < 0.5:
        return label, True
    words = set(label.lower().split("_")) - STOP
    near = [l for l in labels if l != label and words & (set(l.lower().split("_")) - STOP)]
    return rng.choice(near or [l for l in labels if l != label]), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--descriptions")
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    # Reproduce script 19's random sequence exactly: sample, then candidates for dev then test.
    rng = random.Random(7)
    raw = Path("banking77_test.csv")
    if not raw.exists():
        raw.write_text(urllib.request.urlopen(SOURCE, timeout=60).read().decode())
    rows = [(r["text"], r["category"]) for r in csv.DictReader(io.StringIO(raw.read_text()))]
    labels = sorted({l for _, l in rows})
    dev, test = sample(rows, 8, rng)
    jobs = []
    for split, items in (("dev", dev), ("test", test)):
        for text, label in items:
            cand, ok = candidate_for(label, labels, rng)
            jobs.append({"split": split, "text": text, "label": label, "candidate": cand, "candidate_ok": ok})
    jobs = [j for j in jobs if j["split"] == a.split]

    if a.descriptions:
        desc = json.loads(Path(a.descriptions).read_text())
        missing = [l for l in labels if l not in desc]
        assert not missing, f"no description for {missing}"
        options = {l: desc[l] for l in labels}
    else:
        options = {l: human(l) for l in labels}
    reversed_options = dict(reversed(list(options.items())))

    cache_path = Path(f"cache_{a.variant}.json")
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    client = TypeSafeClient(model="jev-1.13.0")

    def ask(job):
        key = json.dumps([job["text"], job["candidate"]])
        if key not in cache:
            r = client.system_one({"message": job["text"]}, {
                "intent": Choice(instructions="What is the customer asking about?", criteria=options),
                "intent_rev": Choice(instructions="What is the customer asking about?", criteria=reversed_options),
                "candidate": Noul(instructions=f"Is the customer asking about {human(job['candidate'])}?"),
            })
            ans = r.answers
            cache[key] = {"choice": ans["intent"].choice, "confidence": ans["intent"].confidence,
                          "probs": ans["intent"].probabilities,
                          "choice_rev": ans["intent_rev"].choice, "confidence_rev": ans["intent_rev"].confidence,
                          "probs_rev": ans["intent_rev"].probabilities,
                          "noul": ans["candidate"].noul, "tokens": r.usage.input_tokens, "model": r.model}
        return {**job, **cache[key]}

    try:
        with ThreadPoolExecutor(a.workers) as pool:
            results = list(pool.map(ask, jobs))
    finally:
        cache_path.write_text(json.dumps(cache))
    out = Path(f"results_{a.variant}.json")
    prev = json.loads(out.read_text()) if out.exists() else []
    prev = [r for r in prev if r["split"] != a.split] + results
    out.write_text(json.dumps(prev))
    tokens = sum(r["tokens"] for r in results)
    acc = sum(r["choice"] == r["label"] for r in results) / len(results)
    print(f"{a.variant} {a.split}: {len(results)} messages, accuracy {acc:.3f}, "
          f"{tokens:,} input tokens (~${tokens * 0.042 / 1e6:.3f} if uncached), model {results[0]['model']}")


if __name__ == "__main__":
    main()
