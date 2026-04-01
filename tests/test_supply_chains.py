"""Tests for Skill Supply Chains."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill_supply_chains import (
    SkillSupplyChainSimulation,
    scenario_linear_chain,
    scenario_hub_spoke,
    scenario_random_trading,
)


def test_linear_chain_compounds():
    """Value should compound (>1.0) in a linear chain with domain expertise."""
    result = scenario_linear_chain(seed=42)
    assert result["compound_ratio"] > 1.0, f"Expected compounding, got {result['compound_ratio']}"
    chain_info = result["chains"]["query-router"]
    assert chain_info["quality_delta"] > 0, "Quality should improve"
    assert chain_info["hops"] > 1, "Should have multiple hops"
    print("✓ test_linear_chain_compounds passed")


def test_hub_agent_profit():
    """Hub agent should earn more than creators and buyers."""
    result = scenario_hub_spoke(seed=123)
    agents = result["agent_summary"]
    hub_profit = agents["Hub"]["profit"]
    creator_profits = [agents[n]["profit"] for n in ["Creator1", "Creator2"]]
    assert hub_profit > max(creator_profits), (
        f"Hub ({hub_profit}) should earn more than creators ({creator_profits})"
    )
    print("✓ test_hub_agent_profit passed")


def test_random_trading_compound_ratio():
    """Average compound ratio should be positive in random trading."""
    result = scenario_random_trading(seed=777, steps=40)
    ratios = [info["compound_ratio"] for info in result["chains"].values()]
    avg_ratio = sum(ratios) / len(ratios)
    assert avg_ratio > 0.5, f"Compound ratios too low: {ratios}"
    assert len(result["chains"]) > 0, "No chains created"
    print(f"✓ test_random_trading_compound_ratio passed (avg={avg_ratio:.3f})")


def test_create_and_improve_skill():
    """Direct API: create skill, improve it, verify quality increases."""
    sim = SkillSupplyChainSimulation(seed=99)
    sim.add_agent("TestAgent", {"routing": 0.9})
    sim.create_skill("TestAgent", "test-skill", 0.3, 0.5, "routing")

    old_q = sim.agents["TestAgent"].skills["test-skill"].quality
    sim.improve_skill("TestAgent", "test-skill")
    new_q = sim.agents["TestAgent"].skills["test-skill"].quality

    assert new_q >= old_q, f"Quality should increase: {old_q} -> {new_q}"
    chain = sim.chains["test-skill"]
    assert chain.total_hops() == 2
    print("✓ test_create_and_improve_skill passed")


def test_trade_transfers_ownership():
    """Trade should transfer skill ownership and update budgets."""
    sim = SkillSupplyChainSimulation(seed=10)
    sim.add_agent("Seller", {"nlp": 0.8})
    sim.add_agent("Buyer", {"nlp": 0.5}, )
    sim.create_skill("Seller", "nlp-tool", 0.6, 0.5, "nlp")

    tx = sim.trade_skill("Seller", "Buyer", "nlp-tool")
    assert tx is not None, "Trade should succeed"
    assert "nlp-tool" in sim.agents["Buyer"].skills, "Buyer should own skill"
    assert sim.agents["Seller"].total_earned > 0, "Seller should have earned"
    assert sim.agents["Buyer"].total_spent > 0, "Buyer should have spent"
    print("✓ test_trade_transfers_ownership passed")


def test_budget_insufficient_trade_fails():
    """Trade should fail if buyer cannot afford the skill."""
    sim = SkillSupplyChainSimulation(seed=10)
    sim.add_agent("Seller", {"nlp": 0.8})
    sim.add_agent("PoorBuyer", {"nlp": 0.5})
    sim.agents["PoorBuyer"].budget = 0.0  # no money
    sim.create_skill("Seller", "expensive-skill", 0.9, 0.5, "nlp")

    tx = sim.trade_skill("Seller", "PoorBuyer", "expensive-skill")
    assert tx is None, "Trade should fail with no budget"
    print("✓ test_budget_insufficient_trade_fails passed")


if __name__ == "__main__":
    tests = [
        test_linear_chain_compounds,
        test_hub_agent_profit,
        test_random_trading_compound_ratio,
        test_create_and_improve_skill,
        test_trade_transfers_ownership,
        test_budget_insufficient_trade_fails,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__} FAILED: {e}")
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed")
    sys.exit(1 if failed else 0)
