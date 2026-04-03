"""Core simulation models and engine for Skill Supply Chains."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────

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

DEFAULT_CONFIG: dict[str, Any] = {
    "improvement_base": 0.05,
    "expertise_bonus": 0.15,
    "specialization_drift": 0.1,
    "hop_decay": 0.02,
    "acquisition_markup": 1.3,
    "default_budget": 100.0,
}


# ── Data Models ──────────────────────────────────────────────────────


@dataclass
class SkillVersion:
    """A specific version of a skill owned by an agent."""

    skill_id: str
    version: int
    owner: str
    quality: float
    specialization: float
    parent: Optional[str]
    improvements: list[str]
    acquisition_cost: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "owner": self.owner,
            "quality": round(self.quality, 4),
            "specialization": round(self.specialization, 4),
            "parent": self.parent,
            "improvements": self.improvements,
            "acquisition_cost": round(self.acquisition_cost, 4),
        }


@dataclass
class Agent:
    """An agent that can create, buy, improve, and sell skills."""

    name: str
    budget: float = 100.0
    skills: dict[str, SkillVersion] = field(default_factory=dict)
    domain_expertise: dict[str, float] = field(default_factory=dict)
    total_earned: float = 0.0
    total_spent: float = 0.0

    @property
    def profit(self) -> float:
        """Net profit (earned minus spent)."""
        return self.total_earned - self.total_spent

    @property
    def portfolio_value(self) -> float:
        """Total quality-adjusted value of owned skills."""
        return sum(sv.quality * 10.0 for sv in self.skills.values())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "name": self.name,
            "budget": round(self.budget, 2),
            "skills_owned": len(self.skills),
            "total_earned": round(self.total_earned, 2),
            "total_spent": round(self.total_spent, 2),
            "profit": round(self.profit, 2),
            "portfolio_value": round(self.portfolio_value, 2),
            "domain_expertise": self.domain_expertise,
        }


@dataclass
class SupplyChain:
    """Tracks the full provenance of a skill family across hops."""

    skill_id: str
    chain: list[SkillVersion] = field(default_factory=list)

    def total_hops(self) -> int:
        """Number of hops (versions) in the chain."""
        return len(self.chain)

    def value_compound_ratio(self) -> float:
        """Per-hop compound ratio. >1 = growth, <1 = decay."""
        if len(self.chain) < 2:
            return 1.0
        first = self.chain[0].quality
        last = self.chain[-1].quality
        if first <= 0:
            return 0.0
        return (last / first) ** (1.0 / len(self.chain))

    def quality_range(self) -> tuple[float, float]:
        """Return (min, max) quality across the chain."""
        if not self.chain:
            return (0.0, 0.0)
        qualities = [sv.quality for sv in self.chain]
        return (min(qualities), max(qualities))

    def unique_owners(self) -> list[str]:
        """Return list of unique owners in order of first appearance."""
        seen: set[str] = set()
        owners: list[str] = []
        for sv in self.chain:
            if sv.owner not in seen:
                seen.add(sv.owner)
                owners.append(sv.owner)
        return owners

    def to_dict(self) -> dict[str, Any]:
        """Serialize chain summary."""
        qualities = [sv.quality for sv in self.chain]
        return {
            "skill_id": self.skill_id,
            "hops": self.total_hops(),
            "compound_ratio": round(self.value_compound_ratio(), 4),
            "quality_start": round(qualities[0], 4) if qualities else 0.0,
            "quality_end": round(qualities[-1], 4) if qualities else 0.0,
            "quality_delta": round(qualities[-1] - qualities[0], 4) if qualities else 0.0,
            "improvements": max(0, len(qualities) - 1),
            "owners": self.unique_owners(),
        }


@dataclass
class Transaction:
    """Record of a single skill trade between agents."""

    tick: int
    seller: str
    buyer: str
    skill_id: str
    price: float
    quality_at_trade: float
    hop: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "from": self.seller,
            "to": self.buyer,
            "skill": self.skill_id,
            "price": round(self.price, 2),
            "quality_at_trade": round(self.quality_at_trade, 4),
            "hop": self.hop,
        }


# ── Simulation Engine ────────────────────────────────────────────────


class SkillSupplyChainSimulation:
    """Simulate agents trading skills in multi-hop supply chains.

    Args:
        seed: Random seed for reproducibility.
        config: Optional dict overriding default simulation parameters.
    """

    def __init__(
        self,
        seed: int = 42,
        config: dict[str, Any] | None = None,
    ):
        self._config = {**DEFAULT_CONFIG, **(config or {})}
        random.seed(seed)
        self.seed = seed
        self.agents: dict[str, Agent] = {}
        self.chains: dict[str, SupplyChain] = {}
        self.transactions: list[Transaction] = []
        self.tick = 0
        logger.debug(
            "Simulation initialized seed=%d config=%s",
            seed,
            list(self._config.keys()),
        )

    @property
    def improvement_base(self) -> float:
        return self._config["improvement_base"]

    @property
    def expertise_bonus(self) -> float:
        return self._config["expertise_bonus"]

    @property
    def specialization_drift(self) -> float:
        return self._config["specialization_drift"]

    @property
    def hop_decay(self) -> float:
        return self._config["hop_decay"]

    @property
    def acquisition_markup(self) -> float:
        return self._config["acquisition_markup"]

    # ── Agent Management ─────────────────────────────────────────────

    def add_agent(self, name: str, domains: dict[str, float] | None = None) -> Agent:
        """Register a new agent with optional domain expertise.

        Args:
            name: Unique agent identifier.
            domains: Mapping of domain name to expertise level (0.0–1.0).

        Returns:
            The created Agent.

        Raises:
            ValueError: If an agent with this name already exists.
        """
        if name in self.agents:
            raise ValueError(f"Agent '{name}' already exists")
        agent = Agent(
            name=name,
            budget=self._config["default_budget"],
            domain_expertise=domains or {},
        )
        self.agents[name] = agent
        logger.debug("Agent added: %s (domains=%s)", name, domains)
        return agent

    # ── Skill Operations ─────────────────────────────────────────────

    def create_skill(
        self,
        creator: str,
        skill_id: str,
        quality: float,
        specialization: float,
        domain: str,
    ) -> SkillVersion:
        """Create a new skill and register it with its creator.

        Args:
            creator: Agent name that creates the skill.
            skill_id: Unique skill identifier.
            quality: Initial quality (0.0–1.0).
            specialization: Initial specialization (0.0–1.0).
            domain: Domain category for the skill.

        Returns:
            The created SkillVersion.

        Raises:
            ValueError: If creator doesn't exist or skill_id already registered.
        """
        if creator not in self.agents:
            raise ValueError(f"Unknown agent: '{creator}'")
        if skill_id in self.chains:
            raise ValueError(f"Skill '{skill_id}' already exists")

        quality = max(0.0, min(1.0, quality))
        specialization = max(0.0, min(1.0, specialization))

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
        self.agents[creator].skills[skill_id] = sv
        self.chains[skill_id] = SupplyChain(skill_id=skill_id, chain=[sv])
        logger.debug("Skill created: %s by %s (q=%.3f)", skill_id, creator, quality)
        return sv

    def improve_skill(self, agent_name: str, skill_id: str) -> Optional[SkillVersion]:
        """Attempt to improve a skill owned by an agent.

        The improvement magnitude depends on domain expertise match,
        hop decay, and randomness. Returns None if the agent doesn't
        own the skill.

        Args:
            agent_name: Name of the improving agent.
            skill_id: Skill to improve.

        Returns:
            New SkillVersion with improved quality, or None.
        """
        if agent_name not in self.agents:
            logger.warning("Unknown agent: '%s'", agent_name)
            return None

        agent = self.agents[agent_name]
        if skill_id not in agent.skills:
            logger.debug("Agent '%s' doesn't own '%s'", agent_name, skill_id)
            return None

        old = agent.skills[skill_id]
        chain = self.chains[skill_id]

        # Domain match: how well does agent expertise align with this skill
        domain_match = 0.5
        for _domain, expertise in agent.domain_expertise.items():
            if _domain in skill_id.lower() or random.random() < 0.3:
                domain_match = expertise
                break

        hop_number = chain.total_hops()
        decay_factor = max(0.0, 1.0 - self.hop_decay * hop_number)
        improvement = (
            (self.improvement_base + self.expertise_bonus * domain_match)
            * decay_factor
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
        logger.debug(
            "Improved: %s by %s q=%.3f→%.3f (+%.4f)",
            skill_id,
            agent_name,
            old.quality,
            new_quality,
            improvement,
        )
        return new_sv

    def trade_skill(
        self,
        seller_name: str,
        buyer_name: str,
        skill_id: str,
    ) -> Optional[Transaction]:
        """Trade a skill from seller to buyer.

        Price is calculated from acquisition cost markup plus quality value.
        The trade fails silently if the seller doesn't own the skill or the
        buyer can't afford it. After a successful trade, the buyer has a
        chance to improve the skill based on their domain expertise.

        Args:
            seller_name: Name of the selling agent.
            buyer_name: Name of the buying agent.
            skill_id: Skill to trade.

        Returns:
            Transaction record if successful, None otherwise.
        """
        if seller_name not in self.agents or buyer_name not in self.agents:
            logger.warning("Trade: unknown agent(s) seller=%s buyer=%s", seller_name, buyer_name)
            return None

        seller = self.agents[seller_name]
        buyer = self.agents[buyer_name]

        if skill_id not in seller.skills:
            return None

        old = seller.skills[skill_id]
        chain = self.chains[skill_id]

        price = old.acquisition_cost * self.acquisition_markup + old.quality * 10.0

        if buyer.budget < price:
            logger.debug(
                "Trade failed: %s can't afford %s (%.2f > %.2f)",
                buyer_name,
                skill_id,
                price,
                buyer.budget,
            )
            return None

        # Transfer funds
        buyer.budget -= price
        seller.budget += price
        buyer.total_spent += price
        seller.total_earned += price

        # Create new version for buyer
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

        tx = Transaction(
            tick=self.tick,
            seller=seller_name,
            buyer=buyer_name,
            skill_id=skill_id,
            price=price,
            quality_at_trade=old.quality,
            hop=chain.total_hops(),
        )
        self.transactions.append(tx)

        # Buyer may improve the skill
        domain_match = max(buyer.domain_expertise.values(), default=0.3)
        if random.random() < 0.3 + 0.4 * domain_match:
            self.improve_skill(buyer_name, skill_id)

        logger.debug(
            "Trade: %s → %s skill=%s price=%.2f",
            seller_name,
            buyer_name,
            skill_id,
            price,
        )
        return tx

    # ── Scenario Runner ──────────────────────────────────────────────

    def run_scenario(self, scenario_name: str, steps: int = 20) -> dict[str, Any]:
        """Run random trading for a number of steps.

        Args:
            scenario_name: Label for the scenario.
            steps: Number of trading ticks.

        Returns:
            Summary dict with chain and agent statistics.
        """
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

    # ── Analysis ─────────────────────────────────────────────────────

    def summarize(self, scenario_name: str = "unnamed") -> dict[str, Any]:
        """Generate a summary of the simulation state.

        Args:
            scenario_name: Label for this summary.

        Returns:
            Dict with per-chain and per-agent statistics.
        """
        results: dict[str, Any] = {
            "scenario": scenario_name,
            "total_transactions": len(self.transactions),
            "chains": {},
            "agent_summary": {},
        }

        for sid, chain in self.chains.items():
            results["chains"][sid] = chain.to_dict()

        for name, agent in self.agents.items():
            results["agent_summary"][name] = agent.to_dict()

        return results

    def wealth_gini(self) -> float:
        """Compute Gini coefficient of agent wealth (budget + portfolio).

        Returns 0.0 for perfect equality, 1.0 for total inequality.
        """
        wealths = sorted(
            a.budget + a.portfolio_value for a in self.agents.values()
        )
        n = len(wealths)
        if n == 0:
            return 0.0
        total = sum(wealths)
        if total == 0:
            return 0.0
        cumsum = 0.0
        gini_sum = 0.0
        for i, w in enumerate(wealths):
            cumsum += w
            gini_sum += (i + 1) * w
        return (2.0 * gini_sum) / (n * total) - (n + 1.0) / n

    def top_agents(self, k: int = 3) -> list[dict[str, Any]]:
        """Return top-k agents sorted by profit descending.

        Args:
            k: Number of agents to return.

        Returns:
            List of agent summary dicts.
        """
        ranked = sorted(
            self.agents.values(),
            key=lambda a: a.profit,
            reverse=True,
        )
        return [a.to_dict() for a in ranked[:k]]
