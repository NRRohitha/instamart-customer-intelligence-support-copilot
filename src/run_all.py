"""Run the full pipeline in dependency order."""

import subprocess
import sys

STAGES = [
    "src.part_a_audit",
    "src.part_a_clean",
    "src.part_a_validate",
    "src.part_a_sql",
    "src.part_a_eda",
    "src.part_b_segments",
    "src.part_b_lapse",
    "src.part_c_triage",
    "src.part_d_rag",
    "src.part_d_agent",
]


def main():
    for stage in STAGES:
        print(f"\n=== {stage} ===", flush=True)
        subprocess.run([sys.executable, "-m", stage], check=True)


if __name__ == "__main__":
    main()
