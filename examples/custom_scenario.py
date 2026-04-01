"""Example: Building custom scenarios with Skill Supply Chains."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill_supply_chains import SkillSupplyChainSimulation


def main():
    # Custom simulation with tuned parameters
    sim = SkillSupplyChainSimulation(
        seed=2026,
        improvement_base=0.08,     # faster improvement
        expertise_bonus=0.20,      # stronger expertise effect
        hop_decay=0.01,            # slower decay
        acquisition_markup=1.5,    # higher margins
    )

    # Specialized agents
    sim.add_agent("Researcher", {"nlp": 0.95, "search": 0.7})
    sim.add_agent("Engineer", {"routing": 0.9, "infra": 0.85})
    sim.add_agent("Generalist", {"nlp": 0.4, "routing": 0.4, "search": 0.4})
    sim.add_agent("Specialist", {"security": 0.95})

    # Seed skills
    sim.create_skill("Researcher", "doc-summarizer", 0.3, 0.8, "nlp")
    sim.create_skill("Engineer", "load-balancer", 0.5, 0.6, "routing")
    sim.create_skill("Specialist", "vuln-scanner", 0.6, 0.9, "security")

    # Run 60 ticks of random trading
    result = sim.run_scenario("custom", steps=60)

    print("=== Custom Scenario Results ===")
    for sid, info in result["chains"].items():
        verdict = "COMPOUNDING" if info["compound_ratio"] > 1.0 else "DECAYING"
        print(f"  {sid}: {info['hops']} hops, ratio={info['compound_ratio']:.3f} ({verdict})")

    print("\nAgent economics:")
    for name, info in sorted(result["agent_summary"].items(), key=lambda x: -x[1]["profit"]):
        print(f"  {name}: profit={info['profit']:+.1f}, skills={info['skills_owned']}")


if __name__ == "__main__":
    main()
