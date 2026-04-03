# OPERATIONS.md — Skill Supply Chains

## Installation

```bash
cd projects/skill-supply-chains
pip install -e .
# Or run directly (stdlib only):
python skill_supply_chains.py --help
```

## Configuration

No env vars. CLI flags only.

| Flag | Default | Description |
|------|---------|-------------|
| `--scenario` | all | `linear`, `hub`, `random` |
| `--steps` | 50 | Trading steps |
| `--seed` | random | Reproducibility seed |

## Usage

```bash
skill-supply-chains --scenario hub --steps 100 --seed 42
python skill_supply_chains.py --json
```

## Health Check

```bash
python skill_supply_chains.py --steps 5 --json | python -c "import sys,json; d=json.load(sys.stdin); assert 'scenarios' in d; print('OK')"
```

## Troubleshooting

- **ModuleNotFoundError**: Run with `python skill_supply_chains.py` or `pip install -e .`
- **Empty JSON output**: Ensure at least one scenario runs (omit `--scenario` for all, or pick a valid name).
