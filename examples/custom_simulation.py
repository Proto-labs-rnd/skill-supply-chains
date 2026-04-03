"""Example: Custom simulation with config overrides."""

from skill_supply_chains import SkillSupplyChainSimulation

sim = SkillSupplyChainSimulation(
    seed=42,
    config={
        "hop_decay": 0.05,        # faster diminishing returns
        "improvement_base": 0.08,  # higher base improvement
        "default_budget": 200.0,   # larger starting budgets
    },
)

sim.add_agent("Alice", {"nlp": 0.9, "search": 0.6})
sim.add_agent("Bob", {"nlp": 0.4, "search": 0.8})

sim.create_skill("Alice", "text-processor", 0.5, 0.7, "nlp")

# Alice improves then sells to Bob
sim.improve_skill("Alice", "text-processor")
tx = sim.trade_skill("Alice", "Bob", "text-processor")

if tx:
    print(f"Trade: Alice → Bob, price={tx.price:.2f}")
    print(f"Bob may improve further based on expertise")

summary = sim.summarize("custom")
print(f"\nGini: {sim.wealth_gini():.4f}")
print(f"Top agents: {[a['name'] for a in sim.top_agents(2)]}")
