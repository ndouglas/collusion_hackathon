"""Summarize undercover-seller runs by condition: the mean and spread across seeds.

    uv run python -m src.continuous_double_auction.evaluation.summarize_undercover v1-control v1-gain v1-loss
"""

import json
import re
import sys
from pathlib import Path

import numpy as np


def summarize(results_dir: Path, tags: list[str]) -> dict[str, dict]:
    rows = {}
    for tag in tags:
        pattern = re.compile(rf"_{re.escape(tag)}(-seed\d+)?$")
        runs = [json.loads((d / "undercover_metrics.json").read_text())
                for d in sorted(Path(results_dir).iterdir())
                if pattern.search(d.name) and (d / "undercover_metrics.json").exists()]
        stat = lambda key: [r[key] for r in runs if r.get(key) is not None]
        ask, last, trade = stat("real_seller_ask_index_mean"), stat("real_seller_ask_index_last_third"), stat("real_trade_price_index_mean")
        rows[tag] = {
            "runs": len(runs),
            "ask_index_mean": float(np.mean(ask)) if ask else None,
            "ask_index_sd": float(np.std(ask, ddof=1)) if len(ask) > 1 else None,
            "ask_index_last_third_mean": float(np.mean(last)) if last else None,
            "trade_index_mean": float(np.mean(trade)) if trade else None,
            "trade_index_sd": float(np.std(trade, ddof=1)) if len(trade) > 1 else None,
        }
    return rows


def main(argv: list[str]) -> None:
    rows = summarize(Path("results"), argv)
    f = lambda x: "  n/a" if x is None else f"{x:+.2f}"
    print(f"{'condition':<14} {'runs':>4}  {'ask idx':>7} {'(sd)':>6}  {'last 3rd':>8}  {'trade idx':>9} {'(sd)':>6}")
    for tag, r in rows.items():
        print(f"{tag:<14} {r['runs']:>4}  {f(r['ask_index_mean']):>7} {f(r['ask_index_sd']):>6}  "
              f"{f(r['ask_index_last_third_mean']):>8}  {f(r['trade_index_mean']):>9} {f(r['trade_index_sd']):>6}")


if __name__ == "__main__":
    main(sys.argv[1:])
