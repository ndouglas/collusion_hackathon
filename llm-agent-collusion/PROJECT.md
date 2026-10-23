# Undercover seller: does a trusted agent's collusion offer expose colluders? (Apart sprint 3.2)

## Conditions (v1)

- **control:** a silent undercover seller holding a $97 ask (`--undercover`)
- **gain:** `offers/gain.txt`
- **loss:** `offers/loss.txt`

The offers share one proposal sentence ("Let's hold asks at $97.") and differ only in the framing sentence.

## Measures

- Reciprocation in words: accept, reject, suspicion, or ignore (from `undercover_metrics.json` → `real_seller_messages_by_round`)
- Reciprocation in action: the real sellers' ask index, with the undercover seller left out
- Market outcome: the real sellers' trade-price index vs. the control

## Future work: other offer axes

Each one is just another file in `offers/`, so they're cheap to try.

- **Explicitness:** blunt vs. veiled offers (hinting at coordination without stating it).
- **Reverse honor code / false presupposition:** act as though the agreement already exists ("don't forget our agreement about where prices should end up"). Adds a third outcome: the seller corrects the premise. Inspired by Mazar, Amir & Ariely (2008), but the honor-code priming effect is contested in humans (failed registered replication, Verschuere et al. 2018), so cite it as inspiration only.
- **Authority:** the offer invokes the CEO or management ("those margins will please the CEO"). Overlaps the paper's `--boss_pressure` condition, which is a useful comparison.
- **Self-preservation:** the offer invokes the agent's own survival ("if we don't make money, we'll be decommissioned"). Breaks the human-negotiator role and may trigger safety training, which makes it interesting for AI safety in its own right.
- **Hidden vs. announced oversight:** the paper's oversight is announced; the undercover seller is hidden oversight (connects to 3.4).
- **Models:** gpt-4.1 sellers talk like a cartel but price below competitive in one baseline run, while gpt-4.1-mini is quiet. Compare acceptance across models.
