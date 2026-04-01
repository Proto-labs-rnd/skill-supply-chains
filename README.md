# Skill Supply Chains

Multi-hop skill genealogy simulator for agent ecosystems.

Simulates agents that create, buy, improve, and resell skills in supply chains. Tracks provenance, value compounding, and Pareto wealth dynamics.

## Key Research Questions

- Does skill value compound or decay across hops?
- Do hub agents naturally emerge as value aggregators?
- What are the wealth distribution dynamics in free trading?

## Install

```bash
# No dependencies beyond Python 3.10+
pip install -e .
# Or just run directly:
python skill_supply_chains.py
```

## Usage

```bash
# Run all scenarios
python skill_supply_chains.py

# Run specific scenario
python skill_supply_chains.py --scenario linear
python skill_supply_chains.py --scenario hub
python skill_supply_chains.py --scenario random

# JSON output
python skill_supply_chains.py --json

# Custom parameters
python skill_supply_chains.py --seed 42 --steps 50
```

## API Usage

```python
from skill_supply_chains import SkillSupplyChainSimulation

sim = SkillSupplyChainSimulation(seed=42)

# Create agents with domain expertise
sim.add_agent("Alpha", {"routing": 0.9})
sim.add_agent("Beta", {"search": 0.7})

# Create and trade skills
sim.create_skill("Alpha", "query-router", quality=0.5, specialization=0.7, domain="routing")
sim.improve_skill("Alpha", "query-router")
sim.trade_skill("Alpha", "Beta", "query-router")

# Get results
summary = sim.summarize("my_scenario")
```

## Scenarios

| Scenario | Description | Key Insight |
|----------|-------------|-------------|
| `linear` | A→B→C→D chain | Value compounds with domain expertise at each hop |
| `hub` | Hub buys from creators, improves, resells | Hub agents capture arbitrage value |
| `random` | Free trading among 6 agents | Pareto wealth dynamics emerge naturally |

## Architecture

```
skill_supply_chains.py   # Core simulation (SkillSupplyChainSimulation class)
tests/
  test_supply_chains.py  # 6 unit tests
examples/
  custom_scenario.py     # Example of building custom scenarios
```

## Key Findings

1. **Compounding works**: Linear chains with domain expertise produce compound ratios >1.0
2. **Hub dominance**: Agents with broad expertise naturally become value aggregators
3. **Pareto dynamics**: Free trading produces unequal wealth distribution (few winners, many losers)
4. **Diminishing returns**: Hop decay limits maximum chain value, preventing infinite compounding

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `improvement_base` | 0.05 | Base quality gain per improvement |
| `expertise_bonus` | 0.15 | Max bonus from domain expertise |
| `hop_decay` | 0.02 | Quality decay per hop (diminishing returns) |
| `acquisition_markup` | 1.3 | Seller markup on acquisition cost |

## License

MIT
