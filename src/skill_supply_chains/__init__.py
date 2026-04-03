"""Skill Supply Chains — Multi-Hop Skill Genealogy Simulator."""

__version__ = "1.1.0"

from .core import (
    Agent,
    SkillSupplyChainSimulation,
    SkillVersion,
    SupplyChain,
)
from .scenarios import (
    SCENARIOS,
    scenario_hub_spoke,
    scenario_linear_chain,
    scenario_random_trading,
    scenario_decay_chain,
    scenario_oligopoly,
)

__all__ = [
    "Agent",
    "SkillSupplyChainSimulation",
    "SkillVersion",
    "SupplyChain",
    "SCENARIOS",
    "scenario_linear_chain",
    "scenario_hub_spoke",
    "scenario_random_trading",
    "scenario_decay_chain",
    "scenario_oligopoly",
]
