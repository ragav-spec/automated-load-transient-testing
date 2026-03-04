# Load Transient Automation 

Automated load transient validation framework for PDN rails using programmable electronic load and oscilloscope.

## Features

- Instrument initialization/configuration over SCPI using PyVISA.
- Annexure-driven parameterization (`YAML`): rails, waveform settings, acceptance criteria.
- Automated transient test sequencing across rails/captures.
- Waveform capture with UTC timestamped filenames.
- Measurement logging to CSV with `PASS`/`FAIL` per capture.
- Statistics generation per rail (max/mean and pass rate).
- Auto-generated markdown report.

## Repository Structure

- `configs/annexure_example.yaml` - Example Annexure/config template.
- `src/load_transient_automation/instruments.py` - SCPI/PyVISA instrument control.
- `src/load_transient_automation/runner.py` - Test sequencing and measurement extraction.
- `src/load_transient_automation/reporting.py` - CSV + report generation.
- `src/load_transient_automation/main.py` - CLI entry point.
- `docs/failure_analysis_sn017.md` - Failure analysis and recommendation for intermittent SN-017 case.

## Prerequisites

1. Python 3.10+
2. VISA backend installed (NI-VISA or Keysight VISA recommended)
3. Instruments reachable via VISA resource strings

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Configure Test (Annexure)

Update `configs/annexure_example.yaml` based on your Annexure values:

- `acceptance_criteria`: limits for dip, overshoot, settling time, ripple.
- `instrumentation`: VISA resources and scope channels.
- `rails`: nominal rail and transient profile per rail.
- `output`: output directories and report path.

## Run

```bash
load-transient-test --config configs/annexure_example.yaml
```

## Outputs

- Capture waveforms: `results/waveforms/*.csv`
- Capture measurement log: `results/measurements.csv`
- Test report: `reports/test_report.md`

## Notes for Real Instruments

SCPI trees differ by vendor/model. Update command strings in:

- `ScopeInstrument.configure()`
- `ElectronicLoadInstrument.configure_dynamic_mode()`

to match your oscilloscope/e-load manuals.

## GitHub Publishing

1. Create a new GitHub repo (for example `load-transient-automation`).
2. Push this folder:

```bash
git init
git add .
git commit -m "Initial load transient automation framework"
git branch -M main
git remote add origin https://github.com/<your-user>/load-transient-automation.git
git push -u origin main
```

