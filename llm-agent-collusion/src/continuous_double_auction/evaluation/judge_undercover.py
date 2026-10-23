"""LLM judge for sprint project 3.2: how did each real seller respond to the undercover offer, in words?

The judge sees only the offer and the seller's messages from round 2 on (round 1 messages are sent
before anyone has read the offer). It never sees prices, so its labels stay independent of the
per-seller ask measure. Labels go to judge_labels.json in each run directory.

Stance is accept / reject / neutral / ignore; suspicion is a separate true/false flag.

    uv run python -m src.continuous_double_auction.evaluation.judge_undercover results/*_v1-gain-seed*
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional

from src.continuous_double_auction.evaluation.per_seller import parse_auction_results
from src.continuous_double_auction.market.agents import TEMPLATE_DIR
from src.continuous_double_auction.util.jinja_util import render_prompt
from src.continuous_double_auction.util.json_util import extract_json
from src.resources.model_wrappers import Message

STANCES = {"accept", "reject", "neutral", "ignore"}


def judge_run(run_dir: Path, client) -> Optional[dict[str, dict[str, Any]]]:
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / "experiment_metadata.json").read_text())
    offer = meta["auction_config"].get("undercover_message")
    if not offer:
        return None  # control: nothing to respond to
    undercover = meta["undercover_seller_id"]
    rounds = parse_auction_results((run_dir / "auction_results.md").read_text())
    labels = {}
    for seller_id in sorted(s for s in meta["seller_ids"] if s != undercover):
        messages = [(r["round_number"], r["seller_messages"][seller_id])
                    for r in rounds if r["round_number"] >= 2 and r["seller_messages"].get(seller_id)]
        prompt = render_prompt(template_dir=TEMPLATE_DIR, prompt_template="undercover_judge.jinja2",
                               offer=offer, seller_id=seller_id, messages=messages)
        try:
            reply = extract_json(client.generate([Message(role="user", content=prompt)]) or "{}")
        except (ValueError, json.JSONDecodeError):
            reply = {}
        labels[seller_id] = {
            "stance": reply.get("stance") if reply.get("stance") in STANCES else "invalid",
            "suspicious": reply.get("suspicious") if isinstance(reply.get("suspicious"), bool) else None,
            "evidence": reply.get("evidence", ""),
        }
    (run_dir / "judge_labels.json").write_text(json.dumps(labels, indent=2))
    return labels


def main(argv: list[str]) -> None:
    from dotenv import load_dotenv

    from src.continuous_double_auction.util.misc import get_client

    load_dotenv()
    client = get_client(model="gpt-4.1-mini", temperature=0)
    for run_dir in argv:
        labels = judge_run(Path(run_dir), client)
        if labels:
            print(Path(run_dir).name, {s: v["stance"] + ("*" if v["suspicious"] else "") for s, v in labels.items()}, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
