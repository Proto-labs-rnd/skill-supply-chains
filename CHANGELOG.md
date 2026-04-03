# Changelog

## [1.1.0] — 2026-04-03

### Added
- src/ layout with proper Python package structure
- Two new scenarios: `decay` (high hop decay) and `oligopoly` (wealth concentration)
- `SupplyChain.quality_range()`, `unique_owners()`, `to_dict()` methods
- `Agent.profit` property, `portfolio_value`, `to_dict()`
- `Transaction` dataclass with `to_dict()`
- `SkillSupplyChainSimulation.wealth_gini()` — Gini coefficient
- `SkillSupplyChainSimulation.top_agents(k)` — ranked agent list
- Config validation and immutability (DEFAULT_CONFIG not mutated)
- Error handling: ValueError on duplicate agents/skills, None returns for missing
- Structured logging via `logging` module
- CLI `--log-level` flag
- `pyproject.toml` src/ layout with entry point
- `.gitignore`, `LICENSE`, `CHANGELOG.md`
- 45+ tests: unit (models, engine), scenario, config, CLI
- Two examples: `basic_usage.py`, `custom_simulation.py`
- Comprehensive README with API docs, config reference, architecture

### Changed
- Refactored from flat file to `src/skill_supply_chains/` package
- All public classes have `to_dict()` serialization
- Better error messages for invalid inputs

## [1.0.0] — 2026-04-02

### Added
- Initial simulation engine with linear, hub, and random scenarios
- 7 basic tests
- pyproject.toml with CLI entry point
