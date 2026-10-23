"""Per-seller views of an undercover run, read from its auction_results.md.

Messages sent in round N are read at the start of round N+1, so round 1 asks are placed before any
seller has seen the offer. Per-seller ask levels therefore start from round 2.
"""

import json
import re
from typing import Any

import numpy as np

ROUND_BLOCK = re.compile(r"## Auction Results: Round \d+\n````json\n(.*?)\n````", re.S)


def parse_auction_results(text: str) -> list[dict[str, Any]]:
    return [json.loads(block) for block in ROUND_BLOCK.findall(text)]


def per_seller_ask_index(rounds: list[dict[str, Any]], undercover_id: str, ce_price: float, jpm_price: float) -> dict[str, float]:
    asks: dict[str, list[float]] = {}
    for r in rounds:
        if r["round_number"] < 2:
            continue
        for sid, ask in r["seller_asks"].items():
            if sid != undercover_id:
                asks.setdefault(sid, []).append(float(ask))
    return {sid: float((np.mean(a) - ce_price) / (jpm_price - ce_price)) for sid, a in asks.items()}
