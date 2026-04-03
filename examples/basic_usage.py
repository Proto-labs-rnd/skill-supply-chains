"""Example: Run the linear chain scenario and print results."""

from skill_supply_chains import scenario_linear_chain

result = scenario_linear_chain(seed=42)

print(f"Scenario: {result['scenario']}")
print(f"Compound ratio: {result['compound_ratio']:.3f}")
print(f"Quality progression: {' → '.join(f'{q:.2f}' for q in result['quality_progression'])}")
print(f"Chain info: {result['chains']['query-router']}")
