"""
Runs the whole project end to end.

    python run_pipeline.py                     every stage
    python run_pipeline.py clean load analyse  only these, in this order

Stages: generate -> clean -> load -> analyse -> test
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import clean_data, database, generate_data, run_analysis  # noqa: E402


def run_tests() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "tests" / "test_edge_cases.py")])
    if result.returncode:
        raise SystemExit("edge case tests failed")


STAGES = {
    "generate": generate_data.main,
    "clean": clean_data.main,
    "load": database.main,
    "analyse": run_analysis.main,
    "test": run_tests,
}


def main() -> None:
    wanted = sys.argv[1:] or list(STAGES)
    unknown = [name for name in wanted if name not in STAGES]
    if unknown:
        raise SystemExit(f"unknown stage(s): {', '.join(unknown)}. Choose from {', '.join(STAGES)}")

    started = time.perf_counter()
    for name in wanted:
        print(f"\n{'#' * 100}\n# {name.upper()}\n{'#' * 100}")
        STAGES[name]()
    print(f"\ndone in {time.perf_counter() - started:.1f}s")


if __name__ == "__main__":
    main()
