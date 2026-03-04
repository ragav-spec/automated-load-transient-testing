from __future__ import annotations

from dataclasses import dataclass

import pyvisa

from .config import ELoadConfig, ScopeConfig


@dataclass
class ScopeCapture:
    x_increment_s: float
    x_origin_s: float
    y_increment_V: float
    y_origin_V: float
    y_reference: float
    raw_samples: list[int]


class ScopeInstrument:
    def __init__(self, config: ScopeConfig, timeout_ms: int = 10000):
        self._config = config
        self._rm = pyvisa.ResourceManager()
        self._inst = self._rm.open_resource(config.resource)
        self._inst.timeout = timeout_ms

    def identify(self) -> str:
        return self._inst.query("*IDN?").strip()

    def configure(self) -> None:
        self._inst.write("*RST")
        self._inst.write(":STOP")
        self._inst.write(f":TIMEBASE:SCALE {self._config.horizontal_scale_s}")
        self._inst.write(f":ACQUIRE:SRATE {self._config.sample_rate_sps}")
        self._inst.write(f":WAVEFORM:SOURCE CHANNEL{self._config.channel_voltage}")
        self._inst.write(":WAVEFORM:FORMAT BYTE")
        self._inst.write(":TRIGGER:MODE EDGE")
        self._inst.write(f":TRIGGER:EDGE:SOURCE CHANNEL{self._config.channel_trigger}")

    def arm_single(self) -> None:
        self._inst.write(":SINGLE")

    def wait_complete(self) -> None:
        self._inst.query("*OPC?")

    def capture_waveform(self) -> ScopeCapture:
        preamble = self._inst.query(":WAVEFORM:PREAMBLE?").strip().split(",")
        raw = self._inst.query_binary_values(":WAVEFORM:DATA?", datatype="B", container=list)
        return ScopeCapture(
            x_increment_s=float(preamble[4]),
            x_origin_s=float(preamble[5]),
            y_increment_V=float(preamble[7]),
            y_origin_V=float(preamble[8]),
            y_reference=float(preamble[9]),
            raw_samples=raw,
        )

    def close(self) -> None:
        self._inst.close()
        self._rm.close()


class ElectronicLoadInstrument:
    def __init__(self, config: ELoadConfig, timeout_ms: int = 10000):
        self._config = config
        self._rm = pyvisa.ResourceManager()
        self._inst = self._rm.open_resource(config.resource)
        self._inst.timeout = timeout_ms

    def identify(self) -> str:
        return self._inst.query("*IDN?").strip()

    def configure_dynamic_mode(
        self,
        low_current_A: float,
        high_current_A: float,
        rise_time_us: float,
        dwell_time_us: float,
        period_us: float,
    ) -> None:
        self._inst.write("*RST")
        self._inst.write(":INPUT OFF")
        self._inst.write(":FUNCTION TRANSIENT")
        self._inst.write(f":CURRENT:LOW {low_current_A}")
        self._inst.write(f":CURRENT:HIGH {high_current_A}")
        self._inst.write(f":TRANSIENT:RISE {rise_time_us}E-6")
        self._inst.write(f":TRANSIENT:DWELL {dwell_time_us}E-6")
        self._inst.write(f":TRANSIENT:PERIOD {period_us}E-6")

    def start_transient(self) -> None:
        self._inst.write(":INPUT ON")
        self._inst.write(":TRANSIENT:STATE ON")

    def stop_transient(self) -> None:
        self._inst.write(":TRANSIENT:STATE OFF")
        self._inst.write(":INPUT OFF")

    def close(self) -> None:
        self._inst.close()
        self._rm.close()
