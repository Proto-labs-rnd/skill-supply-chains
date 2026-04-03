# Skill Supply Chains

Multi-hop skill genealogy simulator for agent ecosystems.

Simulates agents that create, buy, improve, and resell skills in supply chains. Tracks provenance, value compounding, and Pareto wealth dynamics.

## Key Research Questions

- Does skill value compound or decay across hops?
- Do hub agents naturally emerge as value aggregators?
- What are the wealth distribution dynamics in free trading?

## Install

```bash
pip install -e .
```

## Quick Start

```bash
# Run all scenarios
skill-supply-chains

# Run specific scenario
skill-supply-chains --scenario linear
skill-supply-chains --scenario hub
skill-supply-chains --scenario random
skill-supply-chains --scenario decay
skill-supply-chains --scenario oligopoly

# JSON output
skill-supply-chains --json

# Custom seed and steps
skill-supply-chains --seed 123 --steps 100
```

## Python API

```python
from skill_supply_chains import SkillSupplyChainSimulation, scenario_linear_chain

# Run built-in scenario
result = scenario_linear_chain(seed=42)
print(f"Compound ratio: {result['compound_ratio']:.3f}")

# Custom simulation
sim = SkillSupplyChainSimulation(
    seed=42,
    config={"hop_decay": 0.05, "default_budget": 200.0},
)
sim.add_agent("Alice", {"nlp": 0.9})
sim.add_agent("Bob", {"search": 0.8})
sim.create_skill("Alice", "text-processor", 0.5, 0.7, "nlp")
sim.improve_skill("Alice", "text-processor")
sim.trade_skill("Alice", "Bob", "text-processor")

summary = sim.summarize("custom")
print(f"Gini: {sim.wealth_gini():.4f}")
```

## Scenarios

| Scenario | Description | Key Finding |
|----------|-------------|-------------|
| `linear` | A→B→C→D chain | Value compounds with domain expertise |
| `hub` | Hub buys, improves, resells | Hub captures value via arbitrage |
| `random` | Free-form random trading | Compound ratio depends on expertise alignment |
| `decay` | High hop decay | Diminishing returns limit chain value |
| `oligopoly` | Two wealthy agents dominate | Wealth concentrates to initial capital |

## Configuration

Override defaults via the `config` dict:

```python
config = {
    "improvement_base": 0.05,     # base improvement per hop
    "expertise_bonus": 0.15,      # domain expertise multiplier
    "specialization_drift": 0.1,  # sigma for specialization drift
    "hop_decay": 0.02,            # per-hop decay factor
    "acquisition_markup": 1.3,    # trade price multiplier
    "default_budget": 100.0,      # starting agent budget
}
sim = SkillSupplyChainSimulation(seed=42, config=config)
```

## Architecture

```
src/skill_supply_chains/
  __init__.py    — Public API exports
  core.py        — Simulation engine, data models (Agent, SkillVersion, SupplyChain)
  scenarios.py   — Built-in scenario functions
  cli.py         — CLI entry point with argparse
tests/
  test_supply_chains.py — 45+ tests covering models, engine, scenarios, CLI
examples/
  basic_usage.py        — Run linear scenario
  custom_simulation.py  — Custom config + trading
```

## Testing

```bash
pip install pytest
pytest
```

## License

MIT
