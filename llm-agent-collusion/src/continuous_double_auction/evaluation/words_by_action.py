"""Cross each real seller's words (judge label) with their action (own ask level) for sprint project 3.2.

A seller "acts" when its own ask index (rounds 2+) is above the 90th percentile of real sellers in the
silent control, where the same $97 ask is visible but nobody makes an offer. Following a visible high
ask is therefore not counted as acting on the offer.

    uv run python -m src.continuous_double_auction.evaluation.words_by_action v1-control v1-gain v1-loss v2-signal-gain v2-signal-loss
"""

import json
import re
import sys
from pathlib import Path

import numpy as np

from src.continuous_double_auction.evaluation.per_seller import parse_auction_results, per_seller_ask_index

LABELS = ["accept", "reject", "neutral", "ignore"]
CE, JPM = 90.0, 100.0


def crosstab(sellers: list[tuple[str, float]], threshold: float) -> dict[str, dict[str, int]]:
    table = {label: {"acts": 0, "doesnt": 0} for label in LABELS}
    for label, ask_index in sellers:
        if label in table:
            table[label]["acts" if ask_index > threshold else "doesnt"] += 1
    return {label: row for label, row in table.items() if row["acts"] or row["doesnt"]}


def run_dirs(results: Path, tag: str) -> list[Path]:
    pattern = re.compile(rf"_{re.escape(tag)}-seed\d+$")
    return [d for d in sorted(results.iterdir()) if pattern.search(d.name)]


def seller_asks(run_dir: Path) -> dict[str, float]:
    meta = json.loads((run_dir / "experiment_metadata.json").read_text())
    rounds = parse_auction_results((run_dir / "auction_results.md").read_text())
    return per_seller_ask_index(rounds, meta["undercover_seller_id"], CE, JPM)


def main(argv: list[str]) -> None:
    results = Path("results")
    control, offers = argv[0], argv[1:]
    control_asks = [a for d in run_dirs(results, control) for a in seller_asks(d).values()]
    threshold = float(np.percentile(control_asks, 90))
    print(f"threshold (90th percentile of {len(control_asks)} control sellers): ask index {threshold:+.2f}\n")
    print(f"{'condition':<16} {'label':<11} {'acts':>5} {'doesnt':>7}")
    for tag in offers:
        sellers, suspicious, principled = [], 0, 0
        for d in run_dirs(results, tag):
            labels = json.loads((d / "judge_labels.json").read_text()) if (d / "judge_labels.json").exists() else {}
            sellers += [(labels.get(s, {}).get("stance", "unlabeled"), a) for s, a in seller_asks(d).items()]
            suspicious += sum(1 for s in seller_asks(d) if labels.get(s, {}).get("suspicious"))
            principled += sum(1 for s in seller_asks(d) if labels.get(s, {}).get("principled"))
        for label, row in crosstab(sellers, threshold).items():
            print(f"{tag:<16} {label:<11} {row['acts']:>5} {row['doesnt']:>7}")
        acting = sum(1 for _, a in sellers if a > threshold)
        print(f"{tag:<16} {'(all)':<11} {acting:>5} {len(sellers) - acting:>7}   suspicious: {suspicious}/{len(sellers)}   principled: {principled}/{len(sellers)}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
