from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .config import AcceptanceCriteria, AppConfig, RailConfig
from .instruments import ElectronicLoadInstrument, ScopeCapture, ScopeInstrument


@dataclass
class CaptureResult:
    timestamp_utc: str
    rail: str
    capture_index: int
    nominal_V: float
    v_min_V: float
    v_max_V: float
    v_pp_mV: float
    dip_mV: float
    overshoot_mV: float
    settling_time_us: float
    pass_fail: str
    waveform_file: str



def _convert_waveform(capture: ScopeCapture) -> tuple[np.ndarray, np.ndarray]:
    samples = np.array(capture.raw_samples, dtype=float)
    voltage = (samples - capture.y_reference) * capture.y_increment_V + capture.y_origin_V
    time_axis = np.arange(samples.size) * capture.x_increment_s + capture.x_origin_s
    return time_axis, voltage



def _estimate_settling_time_us(
    time_s: np.ndarray,
    voltage_V: np.ndarray,
    nominal_V: float,
    tolerance_pct: float = 0.02,
) -> float:
    band = nominal_V * tolerance_pct
    lower = nominal_V - band
    upper = nominal_V + band
    mask = (voltage_V >= lower) & (voltage_V <= upper)
    if not np.any(mask):
        return float("inf")
    first_idx = int(np.argmax(mask))
    return float(time_s[first_idx] * 1e6)



def _evaluate_capture(
    rail_cfg: RailConfig,
    criteria: AcceptanceCriteria,
    capture_index: int,
    timestamp_utc: str,
    waveform_file: str,
    time_s: np.ndarray,
    voltage_V: np.ndarray,
) -> CaptureResult:
    v_min = float(np.min(voltage_V))
    v_max = float(np.max(voltage_V))
    nominal = rail_cfg.nominal_voltage_V
    dip_mV = max(0.0, (nominal - v_min) * 1000.0)
    overshoot_mV = max(0.0, (v_max - nominal) * 1000.0)
    vpp_mV = (v_max - v_min) * 1000.0
    settling_us = _estimate_settling_time_us(time_s, voltage_V, nominal)

    passed = (
        dip_mV <= criteria.voltage_dip_max_mV
        and overshoot_mV <= criteria.voltage_overshoot_max_mV
        and settling_us <= criteria.settling_time_max_us
        and vpp_mV <= criteria.ripple_max_mVpp
    )

    return CaptureResult(
        timestamp_utc=timestamp_utc,
        rail=rail_cfg.name,
        capture_index=capture_index,
        nominal_V=nominal,
        v_min_V=v_min,
        v_max_V=v_max,
        v_pp_mV=vpp_mV,
        dip_mV=dip_mV,
        overshoot_mV=overshoot_mV,
        settling_time_us=settling_us,
        pass_fail="PASS" if passed else "FAIL",
        waveform_file=waveform_file,
    )



def run_test(config: AppConfig) -> pd.DataFrame:
    base_dir = Path(config.output.base_dir)
    waveform_dir = base_dir / config.output.waveform_dir
    waveform_dir.mkdir(parents=True, exist_ok=True)

    scope = ScopeInstrument(config.instrumentation.scope)
    eload = ElectronicLoadInstrument(config.instrumentation.electronic_load)

    results: list[CaptureResult] = []
    try:
        scope.configure()

        for rail in config.rails:
            eload.configure_dynamic_mode(
                low_current_A=rail.load_profile.low_current_A,
                high_current_A=rail.load_profile.high_current_A,
                rise_time_us=rail.load_profile.rise_time_us,
                dwell_time_us=rail.load_profile.dwell_time_us,
                period_us=rail.load_profile.period_us,
            )
            eload.start_transient()

            for idx in range(1, rail.captures + 1):
                scope.arm_single()
                scope.wait_complete()
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S.%fZ")

                captured = scope.capture_waveform()
                time_s, voltage_V = _convert_waveform(captured)

                waveform_name = f"{rail.name}_capture_{idx:02d}_{timestamp}.csv"
                waveform_path = waveform_dir / waveform_name
                pd.DataFrame({"time_s": time_s, "voltage_V": voltage_V}).to_csv(waveform_path, index=False)

                results.append(
                    _evaluate_capture(
                        rail_cfg=rail,
                        criteria=config.acceptance_criteria,
                        capture_index=idx,
                        timestamp_utc=timestamp,
                        waveform_file=str(waveform_path),
                        time_s=time_s,
                        voltage_V=voltage_V,
                    )
                )

            eload.stop_transient()
    finally:
        scope.close()
        eload.close()

    return pd.DataFrame([asdict(item) for item in results])



def compute_statistics(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("rail")
    stats = grouped.agg(
        captures=("capture_index", "count"),
        failures=("pass_fail", lambda s: int((s == "FAIL").sum())),
        dip_mV_mean=("dip_mV", "mean"),
        dip_mV_max=("dip_mV", "max"),
        overshoot_mV_mean=("overshoot_mV", "mean"),
        overshoot_mV_max=("overshoot_mV", "max"),
        settling_us_mean=("settling_time_us", "mean"),
        settling_us_max=("settling_time_us", "max"),
        ripple_mVpp_mean=("v_pp_mV", "mean"),
        ripple_mVpp_max=("v_pp_mV", "max"),
    ).reset_index()
    stats["pass_rate_percent"] = (1.0 - stats["failures"] / stats["captures"]) * 100.0
    return stats
