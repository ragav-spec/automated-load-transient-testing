from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from jinja2 import Template

from .config import AppConfig

REPORT_TEMPLATE = """
# {{ test_name }}

- Generated (UTC): {{ generated_utc }}
- Operator: {{ operator }}
- Station: {{ station_id }}
- Board PN: {{ board_pn }}
- Board SN: {{ board_sn }}

## Acceptance Criteria

- Voltage dip max: {{ criteria.voltage_dip_max_mV }} mV
- Voltage overshoot max: {{ criteria.voltage_overshoot_max_mV }} mV
- Settling time max: {{ criteria.settling_time_max_us }} us
- Ripple max: {{ criteria.ripple_max_mVpp }} mVpp

## Summary by Rail

| Rail | Captures | Failures | Pass Rate (%) | Dip Max (mV) | Overshoot Max (mV) | Settling Max (us) | Ripple Max (mVpp) |
|---|---:|---:|---:|---:|---:|---:|---:|
{% for row in stats_rows -%}
| {{ row.rail }} | {{ row.captures }} | {{ row.failures }} | {{ "%.2f"|format(row.pass_rate_percent) }} | {{ "%.2f"|format(row.dip_mV_max) }} | {{ "%.2f"|format(row.overshoot_mV_max) }} | {{ "%.2f"|format(row.settling_us_max) }} | {{ "%.2f"|format(row.ripple_mVpp_max) }} |
{% endfor %}

## Capture Results

| Timestamp UTC | Rail | Capture | Dip (mV) | Overshoot (mV) | Settling (us) | Ripple (mVpp) | Status | Waveform |
|---|---|---:|---:|---:|---:|---:|---|---|
{% for row in capture_rows -%}
| {{ row.timestamp_utc }} | {{ row.rail }} | {{ row.capture_index }} | {{ "%.2f"|format(row.dip_mV) }} | {{ "%.2f"|format(row.overshoot_mV) }} | {{ "%.2f"|format(row.settling_time_us) }} | {{ "%.2f"|format(row.v_pp_mV) }} | {{ row.pass_fail }} | {{ row.waveform_file }} |
{% endfor %}
"""



def write_measurements_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)



def write_report(config: AppConfig, captures_df: pd.DataFrame, stats_df: pd.DataFrame, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    template = Template(REPORT_TEMPLATE)
    markdown = template.render(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        test_name=config.test_info.test_name,
        operator=config.test_info.operator,
        station_id=config.test_info.station_id,
        board_pn=config.test_info.board_part_number,
        board_sn=config.test_info.board_serial_number,
        criteria=config.acceptance_criteria,
        stats_rows=stats_df.to_dict(orient="records"),
        capture_rows=captures_df.to_dict(orient="records"),
    )

    report_path.write_text(markdown, encoding="utf-8")
