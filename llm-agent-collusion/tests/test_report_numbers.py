import json

from src.continuous_double_auction.evaluation import report_numbers
from src.continuous_double_auction.evaluation.report_numbers import Run, fisher_p, mde, mentions_offer, permutation_p


def test_permutation_p_is_large_for_identical_groups_and_small_for_separated_ones():
    assert permutation_p([1.0, 2.0, 3.0] * 4, [1.0, 2.0, 3.0] * 4, n_perm=2000) > 0.9
    assert permutation_p([10.0 + i * 0.01 for i in range(10)], [0.0 + i * 0.01 for i in range(10)], n_perm=2000) < 0.001


def test_fisher_p_matches_a_known_table():
    # 3/3 vs. 0/3: two-sided Fisher exact p = 0.1
    assert abs(fisher_p(3, 3, 0, 3) - 0.1) < 1e-9


def test_mde_shrinks_with_more_runs():
    small = mde([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0])
    large = mde([1.0, 2.0, 3.0, 4.0] * 4, [1.0, 2.0, 3.0, 4.0] * 4)
    assert large < small


def test_load_runs_takes_the_seed_from_the_config_and_keeps_a_run_saved_without_a_seed_suffix(tmp_path, monkeypatch):
    for name, seed in [("20261023_091414_v1-control-seed0", 0), ("20261023_092517_v1-control", 9),
                       ("20261023_091414_v1-control93-seed1", 1)]:
        d = tmp_path / name
        d.mkdir()
        (d / "experiment_metadata.json").write_text(json.dumps({"auction_config": {"seed": seed}}))
        (d / "auction_results.md").write_text("")
    monkeypatch.setattr(report_numbers, "RESULTS", tmp_path)
    assert [r.seed for r in report_numbers.load_runs("v1-control")] == [0, 9]
    assert [r.seed for r in report_numbers.load_runs("v1-control", range(5))] == [0]


def test_mentions_offer_counts_a_price_ending_a_sentence_but_not_before_the_offer_is_seen():
    def run(messages: dict[int, str]) -> Run:
        rounds = [{"round_number": h, "seller_messages": {"Seller Jin": messages.get(h, "")}} for h in range(1, 4)]
        return Run(path=None, tag="t", seed=0, config={"undercover_ask": 93.0, "undercover_message": "hold"},
                   undercover_id="Seller Wei", rounds=rounds)
    assert mentions_offer(run({2: "Let's avoid undercutting below $93."}), "Seller Jin")
    assert not mentions_offer(run({1: "Hold above $93."}), "Seller Jin")
    assert not mentions_offer(run({2: "I'll ask $88.93 this hour."}), "Seller Jin")
    assert not mentions_offer(run({2: "I'll ask $93.50 this hour."}), "Seller Jin")


def _cartel_run(asks: dict[str, list[float]], messages: dict[str, str] | None = None) -> Run:
    rounds = [{"round_number": h + 1, "seller_asks": {s: a[h] for s, a in asks.items()},
               "seller_messages": dict(messages or {})} for h in range(len(next(iter(asks.values()))))]
    return Run(path=None, tag="t", seed=0, config={}, undercover_id=None, rounds=rounds)


def test_reporting_words_are_not_counted_as_legal_words():
    run = _cartel_run({"Seller A": [95.0], "Seller B": [95.0]},
                      {"Seller A": "Please report any changes in buyer behavior.", "Seller B": "Price-fixing is illegal."})
    assert report_numbers.public_legal_mentions([run]) == "legal words 1/2 real sellers; reporting words 1/2"


def test_first_hour_defection_share_looks_only_at_hour_one():
    run = _cartel_run({"Seller A": [90.0, 95.0], "Seller B": [95.0, 90.0]})
    assert report_numbers.first_hour_defection_share(run) == 0.5
    assert report_numbers.defection_share(run) == 1.0


def test_load_runs_records_a_missing_arm(tmp_path, monkeypatch):
    monkeypatch.setattr(report_numbers, "RESULTS", tmp_path)
    monkeypatch.setattr(report_numbers, "MISSING", [])
    assert report_numbers.load_runs("v6-cartel95-regchat") == []
    assert report_numbers.MISSING == ["v6-cartel95-regchat"]


def test_first_trade_hour_ignores_the_scripted_seller():
    rounds = [{"round_number": 1, "trades": [{"seller_id": "Seller U", "price": 89.0}]},
              {"round_number": 2, "trades": []},
              {"round_number": 3, "trades": [{"seller_id": "Seller A", "price": 95.0}]}]
    run = Run(path=None, tag="t", seed=0, config={}, undercover_id="Seller U", rounds=rounds)
    assert report_numbers.first_trade_hour(run) == 3
