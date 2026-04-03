"""Allow running as `python -m skill_supply_chains`."""

import sys
from .cli import main

sys.exit(main())
