from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LoadProfile:
    low_current_A: float
    high_current_A: float
    rise_time_us: float
    dwell_time_us: float
    period_us: float
    cycles_per_capture: int


@dataclass
class RailConfig:
    name: str
    nominal_voltage_V: float
    load_profile: LoadProfile
    captures: int


@dataclass
class ScopeConfig:
    resource: str
    channel_voltage: int
    channel_trigger: int
    horizontal_scale_s: float
    sample_rate_sps: float


@dataclass
class ELoadConfig:
    resource: str


@dataclass
class InstrumentationConfig:
    scope: ScopeConfig
    electronic_load: ELoadConfig


@dataclass
class AcceptanceCriteria:
    voltage_dip_max_mV: float
    voltage_overshoot_max_mV: float
    settling_time_max_us: float
    ripple_max_mVpp: float


@dataclass
class OutputConfig:
    base_dir: str
    csv_file: str
    waveform_dir: str
    report_file: str


@dataclass
class TestInfo:
    test_name: str
    operator: str
    station_id: str
    board_part_number: str
    board_serial_number: str


@dataclass
class AppConfig:
    test_info: TestInfo
    acceptance_criteria: AcceptanceCriteria
    instrumentation: InstrumentationConfig
    rails: list[RailConfig]
    output: OutputConfig



def _to_load_profile(raw: dict[str, Any]) -> LoadProfile:
    return LoadProfile(**raw)



def _to_rail(raw: dict[str, Any]) -> RailConfig:
    return RailConfig(
        name=raw["name"],
        nominal_voltage_V=raw["nominal_voltage_V"],
        load_profile=_to_load_profile(raw["load_profile"]),
        captures=raw["captures"],
    )



def load_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    return AppConfig(
        test_info=TestInfo(**raw["test_info"]),
        acceptance_criteria=AcceptanceCriteria(**raw["acceptance_criteria"]),
        instrumentation=InstrumentationConfig(
            scope=ScopeConfig(**raw["instrumentation"]["scope"]),
            electronic_load=ELoadConfig(**raw["instrumentation"]["electronic_load"]),
        ),
        rails=[_to_rail(item) for item in raw["rails"]],
        output=OutputConfig(**raw["output"]),
    )
