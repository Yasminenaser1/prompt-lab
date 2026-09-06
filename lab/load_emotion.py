"""Build tasks/emotion/dataset.json from the dair-ai/emotion dataset
via the Hugging Face datasets-server REST API (no `datasets` dependency)."""
import json
import random
from collections import Counter

import requests

URL = "https://datasets-server.huggingface.co/rows"
DATASET = "dair-ai/emotion"
OUT = "tasks/emotion/dataset.json"
SPLIT_SIZES = {"train": 60, "dev": 30, "test": 20}


def fetch(n, split="train"):
    rows, names = [], None
    offset = 0
    while len(rows) < n:
        r = requests.get(URL, params={"dataset": DATASET, "config": "split",
                                      "split": split, "offset": offset,
                                      "length": 100}, timeout=60)
        r.raise_for_status()
        data = r.json()
        if names is None:
            names = next(f["type"]["names"] for f in data["features"]
                         if f["name"] == "label")
        batch = [d["row"] for d in data["rows"]]
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
    return rows[:n], names


def main():
    total = sum(SPLIT_SIZES.values())
    rows, names = fetch(total)
    print(f"fetched {len(rows)} rows; labels: {names}")

    random.seed(0)
    random.shuffle(rows)

    cases, i = [], 0
    for split, size in SPLIT_SIZES.items():
        for row in rows[i:i + size]:
            cases.append({
                "id": f"e{len(cases):03d}",
                "split": split,
                "input": row["text"],
                "expected": names[row["label"]],
            })
        i += size

    with open(OUT, "w") as f:
        json.dump(cases, f, indent=1)

    print(f"wrote {len(cases)} cases to {OUT}\n")
    for split in SPLIT_SIZES:
        c = Counter(x["expected"] for x in cases if x["split"] == split)
        print(f"{split:<6} {dict(c.most_common())}")


if __name__ == "__main__":
    main()
