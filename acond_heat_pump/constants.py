from enum import Enum


class RegulationMode(Enum):
    """
    Regulation mode affects how is calculated back water temperature setpoint.
    """

    ACOND_THERM = 0
    EQUITHERMAL = 1
    MANUAL = 2


class HeatPumpMode(Enum):
    """
    Enumeration for different operational modes of the heat pump.

    Attributes:
        AUTOMATIC: The heat pump operates automatically based on the system's requirements.
        HEAT_PUMP_ONLY: The heat pump operates without auxiliary bivalent heating.
        BIVALENT_ONLY: The heat pump operates only with an auxiliary bivalent system.
        OFF: The heat pump is turned off.
        MANUAL: The heat pump operates in manual mode, allowing user defined settings.
        COOLING: The heat pump operates in cooling mode.
    """

    AUTOMATIC = 0
    HEAT_PUMP_ONLY = 1
    BIVALENT_ONLY = 3
    OFF = 4
    MANUAL = 5
    COOLING = 6
