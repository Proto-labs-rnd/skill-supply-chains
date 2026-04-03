"""Built-in scenarios for Skill Supply Chains."""

from __future__ import annotations

import random
from typing import Any

from .core import Agent, SkillSupplyChainSimulation


def scenario_linear_chain(seed: int = 42) -> dict[str, Any]:
    """Linear A→B→C→D chain. Does value compound?

    Four agents with decreasing domain expertise trade a single skill
    down a linear chain. Tests whether value compounds across hops
    even as expertise decreases.
    """
    sim = SkillSupplyChainSimulation(seed=seed)
    agents = [
        ("Alpha", {"routing": 0.9}),
        ("Beta", {"routing": 0.6}),
        ("Gamma", {"routing": 0.3}),
        ("Delta", {"routing": 0.1}),
    ]
    for name, domains in agents:
        sim.add_agent(name, domains)

    sim.create_skill("Alpha", "query-router", 0.5, 0.7, "routing")

    order = ["Alpha", "Beta", "Gamma", "Delta"]
    current = "Alpha"
    for i in range(3):
        nxt = order[i + 1]
        sim.improve_skill(current, "query-router")
        sim.trade_skill(current, nxt, "query-router")
        current = nxt
    sim.improve_skill(current, "query-router")

    chain = sim.chains["query-router"]
    qualities = [sv.quality for sv in chain.chain]
    summary = sim.summarize("linear_chain")
    summary["compound_ratio"] = round(chain.value_compound_ratio(), 3)
    summary["quality_progression"] = [round(q, 3) for q in qualities]
    return summary


def scenario_hub_spoke(seed: int = 123) -> dict[str, Any]:
    """Hub agent buys from many, improves, resells. Value arbitrage?

    Tests whether a well-connected hub agent can capture value through
    domain-expertise-driven improvements and resell at higher prices.
    """
    sim = SkillSupplyChainSimulation(seed=seed)
    configs = [
        ("Creator1", {"nlp": 0.7}),
        ("Creator2", {"search": 0.8}),
        ("Hub", {"nlp": 0.9, "search": 0.9, "routing": 0.8}),
        ("Buyer1", {"routing": 0.5}),
        ("Buyer2", {"nlp": 0.4}),
    ]
    for name, domains in configs:
        sim.add_agent(name, domains)

    sim.create_skill("Creator1", "text-analyzer", 0.4, 0.6, "nlp")
    sim.create_skill("Creator2", "web-search", 0.5, 0.5, "search")

    for skill, seller, buyer in [
        ("text-analyzer", "Creator1", "Hub"),
        ("web-search", "Creator2", "Hub"),
    ]:
        sim.improve_skill(seller, skill)
        sim.trade_skill(seller, buyer, skill)

    sim.improve_skill("Hub", "text-analyzer")
    sim.improve_skill("Hub", "web-search")
    sim.trade_skill("Hub", "Buyer1", "text-analyzer")
    sim.trade_skill("Hub", "Buyer2", "web-search")

    summary = sim.summarize("hub_spoke")
    summary["gini"] = round(sim.wealth_gini(), 4)
    return summary


def scenario_random_trading(seed: int = 777, steps: int = 40) -> dict[str, Any]:
    """Many random trades. Measure compounding vs decay statistics.

    Creates 6 agents with random domain expertise and 3 skills,
    then runs free-form random trading for N steps.
    """
    sim = SkillSupplyChainSimulation(seed=seed)

    domains = ["routing", "search", "security", "monitoring", "nlp"]
    for name in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]:
        sim.add_agent(name, {random.choice(domains): random.uniform(0.2, 0.95)})

    skills = ["skill-router", "skill-monitor", "skill-scanner"]
    for i, s in enumerate(skills):
        creator = random.choice(list(sim.agents.keys()))
        sim.create_skill(
            creator,
            s,
            random.uniform(0.3, 0.6),
            random.uniform(0.3, 0.7),
            domains[i % len(domains)],
        )

    return sim.run_scenario("random_trading", steps=steps)


def scenario_decay_chain(seed: int = 42) -> dict[str, Any]:
    """High hop decay → value should plateau or decline.

    Tests behavior under aggressive hop decay where improvement
    gains are suppressed at later hops.
    """
    sim = SkillSupplyChainSimulation(
        seed=seed,
        config={"hop_decay": 0.15, "improvement_base": 0.03},
    )
    agents = [
        ("A", {"nlp": 0.5}),
        ("B", {"nlp": 0.5}),
        ("C", {"nlp": 0.5}),
        ("D", {"nlp": 0.5}),
        ("E", {"nlp": 0.5}),
    ]
    for name, domains in agents:
        sim.add_agent(name, domains)

    sim.create_skill("A", "nlp-tool", 0.5, 0.5, "nlp")

    order = ["A", "B", "C", "D", "E"]
    current = "A"
    for i in range(4):
        nxt = order[i + 1]
        sim.improve_skill(current, "nlp-tool")
        sim.trade_skill(current, nxt, "nlp-tool")
        current = nxt

    summary = sim.summarize("decay_chain")
    chain = sim.chains["nlp-tool"]
    summary["compound_ratio"] = round(chain.value_compound_ratio(), 3)
    return summary


def scenario_oligopoly(seed: int = 99, steps: int = 30) -> dict[str, Any]:
    """Two wealthy agents dominate trading. Does wealth concentrate?

    Tests Pareto wealth dynamics when two agents start with much
    larger budgets than the rest.
    """
    sim = SkillSupplyChainSimulation(seed=seed, config={"default_budget": 50.0})

    # Two rich agents
    sim.add_agent("MegaCorp1", {"nlp": 0.9, "search": 0.8})
    sim.agents["MegaCorp1"].budget = 500.0
    sim.add_agent("MegaCorp2", {"routing": 0.85, "security": 0.7})
    sim.agents["MegaCorp2"].budget = 500.0

    # Four small agents
    for name in ["Small1", "Small2", "Small3", "Small4"]:
        sim.add_agent(name, {random.choice(["nlp", "search"]): random.uniform(0.2, 0.5)})

    skills = [("MegaCorp1", "premium-nlp", 0.7, 0.6, "nlp"),
              ("MegaCorp2", "premium-router", 0.6, 0.5, "routing")]
    for creator, sid, q, s, d in skills:
        sim.create_skill(creator, sid, q, s, d)

    return sim.run_scenario("oligopoly", steps=steps)


SCENARIOS = {
    "linear": scenario_linear_chain,
    "hub": scenario_hub_spoke,
    "random": scenario_random_trading,
    "decay": scenario_decay_chain,
    "oligopoly": scenario_oligopoly,
    "all": None,
}
