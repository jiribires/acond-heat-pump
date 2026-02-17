# Changelog

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
