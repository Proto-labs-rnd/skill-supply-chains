"""Comprehensive tests for Skill Supply Chains."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

import pytest

from skill_supply_chains import (
    Agent,
    SkillSupplyChainSimulation,
    SkillVersion,
    SupplyChain,
    scenario_linear_chain,
    scenario_hub_spoke,
    scenario_random_trading,
    scenario_decay_chain,
    scenario_oligopoly,
)
from skill_supply_chains.core import DEFAULT_CONFIG, Transaction


# ── Unit Tests: Data Models ──────────────────────────────────────────


class TestSkillVersion:
    def test_to_dict(self):
        sv = SkillVersion(
            skill_id="test", version=1, owner="A", quality=0.5,
            specialization=0.7, parent=None, improvements=["orig"],
            acquisition_cost=0.0,
        )
        d = sv.to_dict()
        assert d["skill_id"] == "test"
        assert d["quality"] == 0.5
        assert d["parent"] is None

    def test_quality_bounds(self):
        sv = SkillVersion("x", 1, "A", 1.5, 0.5, None, [], 0.0)
        assert sv.quality == 1.5  # stored as-is, bounded at creation


class TestAgent:
    def test_profit_calculation(self):
        a = Agent("test", budget=100.0, total_earned=50.0, total_spent=30.0)
        assert a.profit == 20.0

    def test_portfolio_value_empty(self):
        a = Agent("test")
        assert a.portfolio_value == 0.0

    def test_portfolio_value_with_skills(self):
        a = Agent("test")
        a.skills["s1"] = SkillVersion("s1", 1, "test", 0.5, 0.5, None, [], 0.0)
        assert a.portfolio_value == 5.0  # 0.5 * 10

    def test_to_dict(self):
        a = Agent("test", budget=50.0)
        d = a.to_dict()
        assert d["name"] == "test"
        assert "profit" in d
        assert "portfolio_value" in d


class TestSupplyChain:
    def test_empty_chain(self):
        sc = SupplyChain("test")
        assert sc.total_hops() == 0
        assert sc.value_compound_ratio() == 1.0
        assert sc.quality_range() == (0.0, 0.0)
        assert sc.unique_owners() == []
        assert sc.to_dict()["hops"] == 0

    def test_single_hop(self):
        sv = SkillVersion("s", 1, "A", 0.5, 0.5, None, [], 0.0)
        sc = SupplyChain("s", [sv])
        assert sc.total_hops() == 1
        assert sc.value_compound_ratio() == 1.0
        assert sc.quality_range() == (0.5, 0.5)

    def test_multi_hop_compound(self):
        sv1 = SkillVersion("s", 1, "A", 0.4, 0.5, None, [], 0.0)
        sv2 = SkillVersion("s", 2, "B", 0.8, 0.5, "A", [], 0.0)
        sc = SupplyChain("s", [sv1, sv2])
        assert sc.total_hops() == 2
        assert sc.value_compound_ratio() > 1.0
        assert sc.unique_owners() == ["A", "B"]

    def test_unique_owners_dedup(self):
        sv1 = SkillVersion("s", 1, "A", 0.5, 0.5, None, [], 0.0)
        sv2 = SkillVersion("s", 2, "A", 0.6, 0.5, "A", [], 0.0)
        sv3 = SkillVersion("s", 3, "B", 0.7, 0.5, "A", [], 0.0)
        sc = SupplyChain("s", [sv1, sv2, sv3])
        assert sc.unique_owners() == ["A", "B"]


class TestTransaction:
    def test_to_dict(self):
        tx = Transaction(tick=1, seller="A", buyer="B", skill_id="s",
                         price=15.0, quality_at_trade=0.5, hop=2)
        d = tx.to_dict()
        assert d["from"] == "A"
        assert d["to"] == "B"
        assert d["price"] == 15.0


# ── Unit Tests: Simulation Engine ────────────────────────────────────


class TestSimulationCreate:
    def test_create_agent(self):
        sim = SkillSupplyChainSimulation()
        a = sim.add_agent("A", {"nlp": 0.8})
        assert a.name == "A"
        assert a.domain_expertise["nlp"] == 0.8

    def test_duplicate_agent_raises(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A")
        with pytest.raises(ValueError, match="already exists"):
            sim.add_agent("A")

    def test_create_skill(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A", {"nlp": 0.9})
        sv = sim.create_skill("A", "nlp-tool", 0.5, 0.7, "nlp")
        assert sv.quality == 0.5
        assert sv.version == 1
        assert "nlp-tool" in sim.agents["A"].skills

    def test_create_skill_unknown_agent(self):
        sim = SkillSupplyChainSimulation()
        with pytest.raises(ValueError, match="Unknown agent"):
            sim.create_skill("Ghost", "s", 0.5, 0.5, "nlp")

    def test_create_skill_duplicate(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A")
        sim.create_skill("A", "s", 0.5, 0.5, "nlp")
        with pytest.raises(ValueError, match="already exists"):
            sim.create_skill("A", "s", 0.6, 0.5, "nlp")

    def test_create_skill_clamps_quality(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A")
        sv = sim.create_skill("A", "s", 1.5, -0.1, "nlp")
        assert sv.quality == 1.0
        assert sv.specialization == 0.0


class TestSimulationImprove:
    def test_improve_increases_quality(self):
        sim = SkillSupplyChainSimulation(seed=42)
        sim.add_agent("A", {"nlp": 0.9})
        sim.create_skill("A", "s", 0.3, 0.5, "nlp")
        old_q = sim.agents["A"].skills["s"].quality
        result = sim.improve_skill("A", "s")
        assert result is not None
        assert result.quality >= old_q

    def test_improve_unknown_agent(self):
        sim = SkillSupplyChainSimulation()
        assert sim.improve_skill("Ghost", "s") is None

    def test_improve_unowned_skill(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A")
        assert sim.improve_skill("A", "nonexistent") is None


class TestSimulationTrade:
    def test_trade_success(self):
        sim = SkillSupplyChainSimulation(seed=10)
        sim.add_agent("Seller", {"nlp": 0.8})
        sim.add_agent("Buyer", {"nlp": 0.5})
        sim.create_skill("Seller", "nlp-tool", 0.6, 0.5, "nlp")
        tx = sim.trade_skill("Seller", "Buyer", "nlp-tool")
        assert tx is not None
        assert "nlp-tool" in sim.agents["Buyer"].skills
        assert sim.agents["Seller"].total_earned > 0

    def test_trade_insufficient_budget(self):
        sim = SkillSupplyChainSimulation(seed=10)
        sim.add_agent("Seller", {"nlp": 0.8})
        sim.add_agent("Poor", {"nlp": 0.5})
        sim.agents["Poor"].budget = 0.0
        sim.create_skill("Seller", "s", 0.9, 0.5, "nlp")
        assert sim.trade_skill("Seller", "Poor", "s") is None

    def test_trade_unowned_skill(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A")
        sim.add_agent("B")
        assert sim.trade_skill("A", "B", "nonexistent") is None

    def test_trade_unknown_agents(self):
        sim = SkillSupplyChainSimulation()
        assert sim.trade_skill("Ghost1", "Ghost2", "s") is None


class TestSimulationAnalysis:
    def test_summarize(self):
        sim = SkillSupplyChainSimulation(seed=42)
        sim.add_agent("A", {"nlp": 0.8})
        sim.add_agent("B", {"nlp": 0.5})
        sim.create_skill("A", "s", 0.5, 0.5, "nlp")
        summary = sim.summarize("test")
        assert summary["scenario"] == "test"
        assert "s" in summary["chains"]
        assert "A" in summary["agent_summary"]

    def test_wealth_gini_empty(self):
        sim = SkillSupplyChainSimulation()
        assert sim.wealth_gini() == 0.0

    def test_wealth_gini_equal(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A")
        sim.add_agent("B")
        assert sim.wealth_gini() < 0.01  # nearly equal

    def test_wealth_gini_unequal(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("Rich")
        sim.agents["Rich"].budget = 1000.0
        sim.add_agent("Poor")
        sim.agents["Poor"].budget = 1.0
        assert sim.wealth_gini() > 0.4

    def test_top_agents(self):
        sim = SkillSupplyChainSimulation()
        sim.add_agent("A")
        sim.add_agent("B")
        sim.add_agent("C")
        sim.agents["B"].total_earned = 100.0
        sim.agents["A"].total_earned = 50.0
        top = sim.top_agents(k=2)
        assert len(top) == 2
        assert top[0]["name"] == "B"

    def test_run_scenario(self):
        sim = SkillSupplyChainSimulation(seed=42)
        sim.add_agent("A", {"nlp": 0.8})
        sim.add_agent("B", {"nlp": 0.5})
        sim.create_skill("A", "s", 0.5, 0.5, "nlp")
        result = sim.run_scenario("test", steps=10)
        assert result["scenario"] == "test"


# ── Scenario Tests ───────────────────────────────────────────────────


class TestLinearChain:
    def test_compounds(self):
        result = scenario_linear_chain(seed=42)
        assert result["compound_ratio"] > 1.0
        assert result["chains"]["query-router"]["quality_delta"] > 0

    def test_quality_progression(self):
        result = scenario_linear_chain(seed=42)
        prog = result["quality_progression"]
        assert len(prog) > 1
        assert prog[-1] > prog[0]


class TestHubSpoke:
    def test_hub_profit(self):
        result = scenario_hub_spoke(seed=123)
        agents = result["agent_summary"]
        hub = agents["Hub"]["profit"]
        creators = [agents[n]["profit"] for n in ["Creator1", "Creator2"]]
        assert hub > max(creators)

    def test_gini_reported(self):
        result = scenario_hub_spoke(seed=123)
        assert "gini" in result


class TestRandomTrading:
    def test_produces_chains(self):
        result = scenario_random_trading(seed=777, steps=40)
        assert len(result["chains"]) > 0

    def test_json_serializable(self):
        result = scenario_random_trading(seed=42)
        serialized = json.dumps(result)
        assert len(serialized) > 100


class TestDecayChain:
    def test_decay_limits_growth(self):
        result = scenario_decay_chain(seed=42)
        # Under high decay, compound ratio should be near or below 1.0
        assert result["compound_ratio"] < scenario_linear_chain()["compound_ratio"]


class TestOligopoly:
    def test_wealth_concentrates(self):
        result = scenario_oligopoly(seed=99, steps=30)
        agents = result["agent_summary"]
        mega_wealth = agents["MegaCorp1"]["budget"] + agents["MegaCorp2"]["budget"]
        small_wealth = sum(
            agents[n]["budget"] for n in ["Small1", "Small2", "Small3", "Small4"]
        )
        # Mega agents should hold more total wealth
        assert mega_wealth > small_wealth


# ── Config Override Tests ────────────────────────────────────────────


class TestConfigOverrides:
    def test_custom_config(self):
        sim = SkillSupplyChainSimulation(
            seed=42, config={"hop_decay": 0.5, "default_budget": 200.0}
        )
        assert sim.hop_decay == 0.5
        assert sim._config["default_budget"] == 200.0

    def test_default_config_unchanged(self):
        assert DEFAULT_CONFIG["hop_decay"] == 0.02
        sim = SkillSupplyChainSimulation(seed=42, config={"hop_decay": 0.5})
        assert DEFAULT_CONFIG["hop_decay"] == 0.02  # not mutated


# ── CLI Tests ────────────────────────────────────────────────────────


class TestCLI:
    def test_cli_json_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "skill_supply_chains", "--json", "--scenario", "linear"],
            capture_output=True, text=True, cwd=_project_root(),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["scenario"] == "linear_chain"

    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "skill_supply_chains", "--help"],
            capture_output=True, text=True, cwd=_project_root(),
        )
        assert result.returncode == 0
        assert "scenario" in result.stdout.lower()

    def test_cli_decay_scenario(self):
        result = subprocess.run(
            [sys.executable, "-m", "skill_supply_chains", "--scenario", "decay", "--json"],
            capture_output=True, text=True, cwd=_project_root(),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["scenario"] == "decay_chain"


# ── Helpers ──────────────────────────────────────────────────────────

def _project_root():
    """Find the project root directory."""
    import os
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
