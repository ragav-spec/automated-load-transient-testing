# Failure Analysis: Board SN-017 (Intermittent 3.3V Load Transient Fail)

## Problem Statement

- Board `SN-017` passes static voltage and ripple tests.
- Board intermittently fails load transient on `3.3V` rail.
- Observed: `3 FAIL / 10 captures`, `7 PASS / 10 captures`.

## Failure Analysis Approach

1. **Confirm repeatability and guardband**
   - Re-run with same profile, then with tighter trigger settings and larger record length.
   - Validate whether failures cluster around one edge condition (dip, overshoot, settling).

2. **Correlate fail captures with waveform signatures**
   - Compare fail vs pass waveforms for:
     - Peak current edge alignment
     - Regulator control-loop ringing pattern
     - Recovery/settling tail behavior

3. **Check measurement chain integrity**
   - Probe type, compensation, ground lead inductance, probing point.
   - Trigger stability and scope bandwidth/filter settings.
   - Exclude instrumentation artifacts first.

4. **Board-level root-cause isolation**
   - Compare BOM lot/AVL substitutions for 3.3V regulator, output caps, and inductor DCR.
   - Inspect solder quality and capacitor placement/ESR-sensitive layout nodes.
   - Thermal sensitivity check: run hot/cold transient captures.

5. **Control-loop and PDN margin checks**
   - Small-signal stability indicator from transient ringdown trend.
   - Evaluate if output capacitor effective capacitance at bias/temperature reduces margin.

## Likely Root Cause Hypotheses

- Marginal control-loop phase margin under fast load step.
- Output capacitor tolerance/aging/derating causing reduced effective capacitance.
- Layout/probing parasitics exaggerating dip in a subset of captures.
- Component variability (regulator compensation network, inductor saturation spread).

## Recommendation

- Treat `SN-017` as **marginal** and **do not release as pass** under current criteria.
- Run an expanded diagnostic lot screen (minimum 30 captures per board on 3.3V rail).
- Add production screen rule: if any intermittent fail appears in 10 captures, route board to debug bin.
- Implement corrective action based on confirmed cause:
  - If control-loop margin issue: adjust compensation/output cap network.
  - If component spread issue: tighten component tolerance or approved vendor list.
  - If measurement artifact: standardize probing fixture and trigger method.

## Disposition for SN-017

- Status: `HOLD FOR ENGINEERING REVIEW`
- Exit criteria:
  - 0 failures in 30 consecutive captures at nominal and temperature corners, or
  - documented root-cause + implemented corrective action + successful re-qualification.
