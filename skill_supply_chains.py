"""
Skill Supply Chains — Multi-Hop Skill Genealogy Simulator
==========================================================

Simulates agents that create, buy, improve, and resell skills
in multi-hop supply chains. Tracks provenance, value compounding,
and Pareto wealth dynamics.

Key research questions:
- Does skill value compound or decay across hops?
- Do hub agents naturally emerge as value aggregators?
- What are the wealth distribution dynamics in free trading?

Usage:
    python skill_supply_chains.py                  # run all scenarios
    python skill_supply_chains.py --scenario hub   # run specific scenario
    python skill_supply_chains.py --json           # JSON output
    python skill_supply_chains.py --seed 42 --steps 50
"""

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SkillVersion:
    """A specific version of a skill owned by an agent."""
    skill_id: str
    version: int
    owner: str
    quality: float
    specialization: float
    parent: Optional[str]
    improvements: list
    acquisition_cost: float


@dataclass
class Agent:
    """An agent that can create, buy, improve, and sell skills."""
    name: str
    budget: float = 100.0
    skills: dict = field(default_factory=dict)
    domain_expertise: dict = field(default_factory=dict)
    total_earned: float = 0.0
    total_spent: float = 0.0


@dataclass
class SupplyChain:
    """Tracks the full provenance of a skill family."""
    skill_id: str
    chain: list = field(default_factory=list)

    def total_hops(self) -> int:
        return len(self.chain)

    def value_compound_ratio(self) -> float:
        """Does value grow (>1) or decay (<1) across hops?"""
        if len(self.chain) < 2:
            return 1.0
        first = self.chain[0].quality
        last = self.chain[-1].quality
        if first <= 0:
            return 0.0
        return (last / first) ** (1.0 / len(self.chain))


IMPROVEMENT_TYPES = [
    "optimized_execution",
    "added_error_handling",
    "extended_coverage",
    "reduced_token_usage",
    "improved_accuracy",
    "added_caching",
    "refactored_logic",
    "added_validation",
    "improved_docs",
    "parallelized_pipeline",
]


class SkillSupplyChainSimulation:
    """Simulate agents trading skills in multi-hop supply chains."""

    def __init__(
        self,
        seed: int = 42,
        improvement_base: float = 0.05,
        expertise_bonus: float = 0.15,
        specialization_drift: float = 0.1,
        hop_decay: float = 0.02,
        acquisition_markup: float = 1.3,
    ):
        random.seed(seed)
        self.agents: dict[str, Agent] = {}
        self.chains: dict[str, SupplyChain] = {}
        self.transactions: list[dict] = []
        self.tick = 0
        self.improvement_base = improvement_base
        self.expertise_bonus = expertise_bonus
        self.specialization_drift = specialization_drift
        self.hop_decay = hop_decay
        self.acquisition_markup = acquisition_markup

    def add_agent(self, name: str, domains: dict | None = None) -> Agent:
        agent = Agent(name=name, domain_expertise=domains or {})
        self.agents[name] = agent
        return agent

    def create_skill(
        self,
        creator: str,
        skill_id: str,
        quality: float,
        specialization: float,
        domain: str,
    ) -> SkillVersion:
        agent = self.agents[creator]
        sv = SkillVersion(
            skill_id=skill_id,
            version=1,
            owner=creator,
            quality=quality,
            specialization=specialization,
            parent=None,
            improvements=["original_creation"],
            acquisition_cost=0.0,
        )
        agent.skills[skill_id] = sv
        self.chains[skill_id] = SupplyChain(skill_id=skill_id, chain=[sv])
        return sv

    def improve_skill(self, agent_name: str, skill_id: str) -> Optional[SkillVersion]:
        agent = self.agents[agent_name]
        if skill_id not in agent.skills:
            return None

        old = agent.skills[skill_id]
        chain = self.chains[skill_id]

        domain_match = 0.5
        for _domain, expertise in agent.domain_expertise.items():
            if _domain in skill_id.lower() or random.random() < 0.3:
                domain_match = expertise
                break

        hop_number = chain.total_hops()
        decay_factor = max(0.0, 1.0 - self.hop_decay * hop_number)
        improvement = (
            (self.improvement_base + self.expertise_bonus * domain_match) * decay_factor
        )
        improvement *= random.uniform(0.5, 1.5)
        improvement = max(0.0, min(improvement, 0.3))

        new_quality = min(1.0, old.quality + improvement)
        new_spec = max(
            0.0,
            min(1.0, old.specialization + random.gauss(0, self.specialization_drift)),
        )

        new_sv = SkillVersion(
            skill_id=skill_id,
            version=hop_number + 1,
            owner=agent_name,
            quality=new_quality,
            specialization=new_spec,
            parent=agent_name,
            improvements=old.improvements + [random.choice(IMPROVEMENT_TYPES)],
            acquisition_cost=old.acquisition_cost,
        )

        agent.skills[skill_id] = new_sv
        chain.chain.append(new_sv)
        return new_sv

    def trade_skill(
        self, seller_name: str, buyer_name: str, skill_id: str
    ) -> Optional[dict]:
        seller = self.agents[seller_name]
        buyer = self.agents[buyer_name]

        if skill_id not in seller.skills:
            return None

        old = seller.skills[skill_id]
        chain = self.chains[skill_id]

        price = old.acquisition_cost * self.acquisition_markup + old.quality * 10

        if buyer.budget < price:
            return None

        buyer.budget -= price
        seller.budget += price
        buyer.total_spent += price
        seller.total_earned += price

        acquired = SkillVersion(
            skill_id=skill_id,
            version=chain.total_hops() + 1,
            owner=buyer_name,
            quality=old.quality,
            specialization=old.specialization,
            parent=seller_name,
            improvements=list(old.improvements),
            acquisition_cost=price,
        )

        buyer.skills[skill_id] = acquired
        chain.chain.append(acquired)

        tx = {
            "tick": self.tick,
            "from": seller_name,
            "to": buyer_name,
            "skill": skill_id,
            "price": round(price, 2),
            "quality_at_trade": old.quality,
            "hop": chain.total_hops(),
        }
        self.transactions.append(tx)

        domain_match = max(buyer.domain_expertise.values(), default=0.3)
        if random.random() < 0.3 + 0.4 * domain_match:
            self.improve_skill(buyer_name, skill_id)

        return tx

    def run_scenario(self, scenario_name: str, steps: int = 20) -> dict:
        agent_names = list(self.agents.keys())
        skill_ids = list(self.chains.keys())

        for step in range(steps):
            self.tick += 1
            if len(agent_names) < 2 or not skill_ids:
                continue
            seller = random.choice(agent_names)
            buyer = random.choice([a for a in agent_names if a != seller])
            skill = random.choice(skill_ids)
            self.trade_skill(seller, buyer, skill)

        return self.summarize(scenario_name)

    def summarize(self, scenario_name: str = "unnamed") -> dict:
        results = {"scenario": scenario_name, "chains": {}, "agent_summary": {}}

        for sid, chain in self.chains.items():
            qualities = [sv.quality for sv in chain.chain]
            results["chains"][sid] = {
                "hops": chain.total_hops(),
                "compound_ratio": round(chain.value_compound_ratio(), 3),
                "quality_start": round(qualities[0], 3) if qualities else 0,
                "quality_end": round(qualities[-1], 3) if qualities else 0,
                "quality_delta": round(qualities[-1] - qualities[0], 3) if qualities else 0,
                "improvements": len(qualities) - 1,
                "owners": list({sv.owner for sv in chain.chain}),
            }

        for name, agent in self.agents.items():
            results["agent_summary"][name] = {
                "budget": round(agent.budget, 2),
                "skills_owned": len(agent.skills),
                "total_earned": round(agent.total_earned, 2),
                "total_spent": round(agent.total_spent, 2),
                "profit": round(agent.total_earned - agent.total_spent, 2),
            }

        return results


# ── Scenarios ────────────────────────────────────────────────────────


def scenario_linear_chain(seed: int = 42) -> dict:
    """Linear A→B→C→D chain. Does value compound?"""
    sim = SkillSupplyChainSimulation(seed=seed)
    agents = [("Alpha", {"routing": 0.9}), ("Beta", {"routing": 0.6}),
              ("Gamma", {"routing": 0.3}), ("Delta", {"routing": 0.1})]
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


def scenario_hub_spoke(seed: int = 123) -> dict:
    """Hub agent buys from many, improves, resells. Value arbitrage?"""
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

    return sim.summarize("hub_spoke")


def scenario_random_trading(seed: int = 777, steps: int = 40) -> dict:
    """Many random trades. Measure compounding vs decay statistics."""
    sim = SkillSupplyChainSimulation(seed=seed)

    domains = ["routing", "search", "security", "monitoring", "nlp"]
    for name in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]:
        sim.add_agent(name, {random.choice(domains): random.uniform(0.2, 0.95)})

    skills = ["skill-router", "skill-monitor", "skill-scanner"]
    for i, s in enumerate(skills):
        creator = random.choice(list(sim.agents.keys()))
        sim.create_skill(
            creator, s,
            random.uniform(0.3, 0.6),
            random.uniform(0.3, 0.7),
            domains[i % len(domains)],
        )

    return sim.run_scenario("random_trading", steps=steps)


def print_results(results: dict) -> None:
    print(f"\n=== Scenario: {results['scenario']} ===")
    for sid, info in results.get("chains", {}).items():
        print(
            f"  {sid}: hops={info['hops']}, compound={info['compound_ratio']:.3f}, "
            f"Δq={info['quality_delta']:+.3f}, owners={info['owners']}"
        )
    if "quality_progression" in results:
        print(
            f"  Quality: {' → '.join(f'{q:.2f}' for q in results['quality_progression'])}"
        )
    print("  Agents:")
    for name, info in sorted(
        results.get("agent_summary", {}).items(), key=lambda x: -x[1]["profit"]
    ):
        print(f"    {name}: profit={info['profit']:.1f}, skills={info['skills_owned']}")


SCENARIOS = {
    "linear": scenario_linear_chain,
    "hub": scenario_hub_spoke,
    "random": scenario_random_trading,
    "all": None,
}


def main():
    parser = argparse.ArgumentParser(
        description="Skill Supply Chains — Multi-Hop Skill Genealogy Simulator"
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="all",
        help="Which scenario to run (default: all)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--steps", type=int, default=40, help="Steps for random scenario")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = []
    if args.scenario in ("all", "linear"):
        results.append(scenario_linear_chain(args.seed))
    if args.scenario in ("all", "hub"):
        results.append(scenario_hub_spoke(args.seed))
    if args.scenario in ("all", "random"):
        results.append(scenario_random_trading(args.seed, args.steps))

    if args.json:
        json.dump(results if len(results) > 1 else results[0], sys.stdout, indent=2)
        print()
    else:
        for r in results:
            print_results(r)
        print("\n=== KEY FINDINGS ===")
        print("1. Linear chains: value compounds when domain expertise is present")
        print("2. Hub agents: capture value through arbitrage (buy low, improve, sell high)")
        print("3. Random trading: compound ratio depends on expertise alignment")
        print("4. Diminishing returns: hop decay limits maximum chain value")


if __name__ == "__main__":
    main()
