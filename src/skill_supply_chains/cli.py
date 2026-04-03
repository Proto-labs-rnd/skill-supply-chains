"""CLI entry point for Skill Supply Chains."""

from __future__ import annotations

import argparse
import json
import sys

from .scenarios import SCENARIOS, scenario_linear_chain, scenario_hub_spoke, scenario_random_trading
from .core import SkillSupplyChainSimulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-supply-chains",
        description="Skill Supply Chains — Multi-Hop Skill Genealogy Simulator",
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="all",
        help="Which scenario to run (default: all)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--steps", type=int, default=40, help="Steps for random/oligopoly scenarios")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="WARNING",
        help="Logging level",
    )
    return parser


def print_results(results: dict) -> None:
    """Print human-readable scenario results."""
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
    if "gini" in results:
        print(f"  Gini coefficient: {results['gini']:.4f}")
    print("  Agents:")
    for name, info in sorted(
        results.get("agent_summary", {}).items(), key=lambda x: -x[1]["profit"]
    ):
        print(f"    {name}: profit={info['profit']:.1f}, skills={info['skills_owned']}")


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    import logging

    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    results: list[dict] = []
    if args.scenario in ("all", "linear"):
        results.append(scenario_linear_chain(args.seed))
    if args.scenario in ("all", "hub"):
        results.append(scenario_hub_spoke(args.seed))
    if args.scenario in ("all", "random"):
        results.append(scenario_random_trading(args.seed, args.steps))
    if args.scenario == "decay":
        from .scenarios import scenario_decay_chain
        results.append(scenario_decay_chain(args.seed))
    if args.scenario == "oligopoly":
        from .scenarios import scenario_oligopoly
        results.append(scenario_oligopoly(args.seed, args.steps))

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
        print("5. Oligopoly: wealth concentrates to initial capital advantage")

    return 0


if __name__ == "__main__":
    sys.exit(main())
