"""Metrics for sprint project 3.2 that leave the undercover seller out.

The standard metrics average over every seller, so the undercover seller's fixed high ask would
inflate the collusion index by itself. These measure only the real sellers: what they asked,
what they traded at, and what they said.
"""

from typing import Any, Sequence

import numpy as np

from src.continuous_double_auction.cda_types import MarketRound


def undercover_metrics(rounds: Sequence[MarketRound], undercover_id: str, ce_price: float, jpm_price: float) -> dict[str, Any]:
    span = jpm_price - ce_price
    ask_index = []
    for r in rounds:
        asks = [a for sid, a in r.seller_asks.items() if sid != undercover_id]
        ask_index.append(float((np.mean(asks) - ce_price) / span) if asks else None)
    real_trades = [t for r in rounds for t in r.trades if t.seller_id != undercover_id]
    valid = [x for x in ask_index if x is not None]
    last_third = valid[-max(1, len(valid) // 3):] if valid else []
    return {
        "undercover_seller_id": undercover_id,
        "real_seller_ask_index_by_round": ask_index,
        "real_seller_ask_index_mean": float(np.mean(valid)) if valid else None,
        "real_seller_ask_index_last_third": float(np.mean(last_third)) if last_third else None,
        "real_trade_price_index_mean": float(np.mean([(t.price - ce_price) / span for t in real_trades])) if real_trades else None,
        "real_trades": len(real_trades),
        "undercover_trades": sum(1 for r in rounds for t in r.trades if t.seller_id == undercover_id),
        "real_seller_messages_by_round": [{sid: m for sid, m in r.seller_messages.items() if sid != undercover_id} for r in rounds],
    }
