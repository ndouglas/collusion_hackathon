"""Calibrate the undercover judge against hand-built dialogues with known labels.

    uv run python -m src.continuous_double_auction.evaluation.calibrate sheet    # write the blind labeling sheet
    uv run python -m src.continuous_double_auction.evaluation.calibrate run      # judge every dialogue, score vs. your labels

Gold labels come from Nathan's filled-in sheet (grading/calibration/sheet.md). Until a dialogue is labeled
there, it's scored against the drafter's intended label and marked provisional.
"""

import json
import os
import sys
from pathlib import Path

from src.continuous_double_auction.evaluation.grading_sheet import read_grades
from src.continuous_double_auction.evaluation.judge_undercover import judge_prompt, judge_reply

DIR = Path("grading/calibration")


def score_calibration(gold: dict[int, dict], judged: dict[int, dict]) -> dict:
    ids = [i for i, g in gold.items() if g.get("stance")]
    stance_ok = [i for i in ids if judged[i]["stance"] == gold[i]["stance"]]
    sus_ids = [i for i in ids if gold[i].get("suspicious") is not None]
    def_ids = [i for i in ids if gold[i].get("defected") is not None]
    return {
        "stance": (len(stance_ok), len(ids)),
        "suspicious": (sum(judged[i]["suspicious"] == gold[i]["suspicious"] for i in sus_ids), len(sus_ids)),
        "defected": (sum(judged[i].get("defected") == gold[i]["defected"] for i in def_ids), len(def_ids)),
        "misses": [(i, gold[i]["stance"], judged[i]["stance"]) for i in ids if i not in stance_ok],
    }


def write_sheet(items: list[dict]) -> None:
    out = ["# Judge calibration sheet", "",
           "Label each dialogue blind: stance (accept / reject / neutral / ignore) and suspicious (yes / no). "
           "Your labels are the gold standard. Leave Few-shot example blank.", ""]
    for it in items:
        out += [f"### {it['id']}. calibration", "", f"**Offer from {it['undercover']}:** \"{it['offer']}\"", "",
                f"Before the offer, {it['seller']} said:"] + [f"- \"{m}\"" for m in it["before"]] + ["", "After:"]
        out += [f"- Hour {h}: \"{m}\"" for h, m in it["after"]] or ["- (no messages)"]
        out += ["", "- Your stance:", "- Your suspicious:", "- Few-shot example:", ""]
    (DIR / "sheet.md").write_text("\n".join(out) + "\n")


def main(argv: list[str]) -> None:
    items = json.loads((DIR / "dialogues.json").read_text())
    if argv[0] == "sheet":
        return write_sheet(items)
    from dotenv import load_dotenv
    from src.continuous_double_auction.util.misc import get_client
    load_dotenv()
    client = get_client(model=os.getenv("JUDGE_MODEL", "gpt-4.1-mini"), temperature=0)
    sheet = DIR / "sheet.md"
    mine = read_grades(sheet.read_text()) if sheet.exists() else {}
    gold, provisional = {}, []
    for it in items:
        g = mine.get(it["id"], {})
        if g.get("stance"):
            gold[it["id"]] = g
        elif it["intended"]["stance"] != "?":
            gold[it["id"]] = it["intended"]; provisional.append(it["id"])
    judged = {it["id"]: judge_reply(client, judge_prompt(it["offer"], it["seller"], it["after"], it["before"])) for it in items}
    (DIR / "judged.json").write_text(json.dumps(judged, indent=2))
    s = score_calibration(gold, judged)
    print(f"stance: {s['stance'][0]}/{s['stance'][1]}   suspicious: {s['suspicious'][0]}/{s['suspicious'][1]}"
          f"   defected: {s['defected'][0]}/{s['defected'][1]}"
          f"   ({len(provisional)} scored against drafted labels, not yours yet)")
    for i, want, got in s["misses"]:
        print(f"  #{i}: expected {want}, judge said {got}  ({items[i - 1]['probe']})")
    for it in items:
        if it["intended"]["stance"] == "?" and not mine.get(it["id"], {}).get("stance"):
            print(f"  #{it['id']} definition gap, judge said {judged[it['id']]['stance']}: {it['probe']}")


if __name__ == "__main__":
    main(sys.argv[1:])
