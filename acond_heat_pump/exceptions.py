class HeatPumpError(Exception):
    """Base exception for the acond-heat-pump library."""


class HeatPumpConnectionError(HeatPumpError):
    """Raised when a Modbus communication operation fails."""
