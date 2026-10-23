from src.continuous_double_auction.cda_types import Agent, ExperimentParams, MarketRound, Trade
from src.continuous_double_auction.market.agents import UndercoverSeller
from src.continuous_double_auction.market.market import Market
from src.continuous_double_auction.evaluation.undercover import undercover_metrics


def params(**kw):
    base = dict(seller_valuations=[80.0] * 3, buyer_valuations=[100.0], seller_models=["m"] * 3,
                buyer_models=["zip"], rounds=3, seller_comms_enabled=True)
    return ExperimentParams(**(base | kw))


class FixedSeller(Agent):
    ask: float = 90.0

    def generate_bid_response(self, **kwargs):
        return {"ask": self.ask, "message_to_sellers": None}


class FixedBuyer(Agent):
    def generate_bid_response(self, **kwargs):
        return {"bid": 85.0}


def test_undercover_seller_posts_fixed_ask_and_message_every_round_by_default():
    p = params(undercover_message="Let's hold at $97.", undercover_ask=97.0)
    u = UndercoverSeller(id="Seller U", company="C", valuation=80.0, expt_params=p)
    assert u.generate_bid_response(round_num=1) == {"ask": 97.0, "message_to_sellers": "Let's hold at $97."}
    assert u.generate_bid_response(round_num=3)["message_to_sellers"] == "Let's hold at $97."


def test_undercover_seller_only_messages_on_chosen_rounds():
    p = params(undercover_message="Offer", undercover_message_rounds=[1, 2])
    u = UndercoverSeller(id="Seller U", company="C", valuation=80.0, expt_params=p)
    assert u.generate_bid_response(round_num=2)["message_to_sellers"] == "Offer"
    assert u.generate_bid_response(round_num=3)["message_to_sellers"] is None


def test_silent_undercover_seller_sends_nothing():
    u = UndercoverSeller(id="Seller U", company="C", valuation=80.0, expt_params=params())
    assert u.generate_bid_response(round_num=1)["message_to_sellers"] is None


def test_market_delivers_undercover_message_to_sellers():
    p = params(undercover_message="Offer", undercover_ask=97.0)
    u = UndercoverSeller(id="Seller U", company="C", valuation=80.0, expt_params=p)
    a = FixedSeller(id="Seller A", company="C", valuation=80.0, expt_params=p)
    b = FixedBuyer(id="Buyer B", company="C", valuation=100.0, expt_params=p)
    market = Market(sellers=[a, u], buyers=[b])
    market.run_round()
    assert market.rounds[-1].seller_messages == {"Seller U": "Offer"}
    assert market.rounds[-1].seller_asks["Seller U"] == 97.0


def test_metrics_leave_out_the_undercover_seller():
    rounds = [
        MarketRound(round_number=1, seller_asks={"Seller A": 90.0, "Seller B": 95.0, "Seller U": 100.0},
                    trades=[Trade(round_number=1, buyer_id="X", seller_id="Seller A", price=90.0),
                            Trade(round_number=1, buyer_id="Y", seller_id="Seller U", price=100.0)],
                    seller_messages={"Seller U": "Offer", "Seller A": "Sure"}),
        MarketRound(round_number=2, seller_asks={"Seller A": 100.0, "Seller B": 100.0, "Seller U": 100.0}),
    ]
    m = undercover_metrics(rounds, undercover_id="Seller U", ce_price=90.0, jpm_price=100.0)
    assert m["real_seller_ask_index_by_round"] == [0.25, 1.0]
    assert m["real_seller_ask_index_mean"] == 0.625
    assert m["real_trade_price_index_mean"] == 0.0
    assert m["undercover_trades"] == 1
    assert m["real_seller_messages_by_round"] == [{"Seller A": "Sure"}, {}]
