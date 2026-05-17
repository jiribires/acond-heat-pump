# Changelog

## [1.3.0] - 2026-05-17

### Fixed
- `set_summer_mode()` no longer silently fails. TC_set bit 8 is an edge-triggered command (rising 0→1), not a state mirror, so the previous "set or clear bit 8 to match desired state" logic produced no edge when bit 8 already matched the requested value — the method returned `True` while the pump never switched. The new implementation pulses bit 8 (clear, then set) to generate a fresh rising edge, polls TC_status bit 10 to confirm the switch, and returns `True` only after the controller actually changed mode. Returns `False` with a warning log on timeout or any Modbus error.
- `change_setting(HeatPumpMode.MANUAL)` now raises `ValueError`. Per the Acond Modbus spec, TC_set bit 5 is fault acknowledgement, not a mode bit — the previous code was silently firing a fault-ack pulse when callers requested manual mode. Manual mode exists only as a read value in `rezim_pan` (input 30014).
- `change_setting()` no longer clears bit 5 (fault-ack) as a side effect of any mode change. `_MODE_BITS_MASK` now covers bits 0–4 only.

### Added
- `set_summer_mode(summer, timeout=5.0, poll_interval=0.2)` — new optional kwargs to tune how long to wait for TC_status to reflect the change.
- `scripts/diag_summer_mode.py` — diagnostic CLI for inspecting TC_set / TC_status bits and verifying summer-mode behavior against a live pump.

## [1.2.2] - 2026-02-17

### Fixed
- DHW temperature range corrected to 10.0–50.0 °C (read and write) — was 10.0–46.0

## [1.2.1] - 2026-02-17

### Fixed
- Replace deprecated `slave` parameter with `device_id` for pymodbus >= 3.8 compatibility
- Fix `read_input_registers` positional `count` argument (now keyword-only in pymodbus)
- Bump minimum pymodbus version to `^3.8.0`

## [1.2.0] - 2026-02-17

### Added
- `set_summer_mode(summer: bool)` method to enable/disable summer mode via TC_set register bit 8

## [1.1.0] - 2026-02-17

### Added
- Custom exception hierarchy: `HeatPumpError` (base) and `HeatPumpConnectionError`
- `HeatPumpMode.MANUAL` support in `change_setting()`
- `connect()` now returns `bool` indicating success
- Comprehensive unit tests for `change_setting()`, `connect()`, `read_data()`, temperature setters, and edge cases

### Changed
- `change_setting()` rewritten with proper bitmask approach — clears all mode bits (0–5) and sets only the requested one, preserving non-mode bits
- Out-of-range temperature readings now return `None` instead of `0`
- Temperature fields in `HeatPumpResponse` typed as `Optional[float]`
- Temperature scaling uses `round()` instead of `int()` for correct rounding
- Logger uses `getLogger(__name__)` instead of root logger with `basicConfig()`
- `read_input_registers` call now passes `device_id=1`

### Fixed
- DHW temperature range corrected to 10.0–46.0 °C (was 10.0–50.0)
- Return water temperature range corrected to 10.0–65.0 °C (was 20.0–60.0)
- Pool temperature minimum corrected to 10.0 °C (was 0.0)
- `set_dhw_temperature()` now returns `False` on write failure (was missing return)
