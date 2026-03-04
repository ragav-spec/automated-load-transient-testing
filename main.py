from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .reporting import write_measurements_csv, write_report
from .runner import compute_statistics, run_test



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automated load transient test runner")
    parser.add_argument("--config", required=True, help="Path to Annexure YAML config")
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)

    captures_df = run_test(cfg)
    stats_df = compute_statistics(captures_df)

    base_dir = Path(cfg.output.base_dir)
    csv_path = base_dir / cfg.output.csv_file
    report_path = Path(cfg.output.report_file)

    write_measurements_csv(captures_df, csv_path)
    write_report(cfg, captures_df, stats_df, report_path)

    print(f"Measurements CSV: {csv_path}")
    print(f"Report file: {report_path}")


if __name__ == "__main__":
    main()
