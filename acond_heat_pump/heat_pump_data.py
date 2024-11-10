from dataclasses import dataclass

from acond_heat_pump.constants import HeatPumpMode, RegulationMode


@dataclass
class HeatPumpStatus:
    on: bool  # Bit 0 - Heat Pump On
    running: bool  # Bit 1 - Heat Pump Running
    fault: bool  # Bit 2 - Heat Pump Fault
    heating_dhw: bool  # Bit 3 - Heating TUV
    pump_circuit1: bool  # Bit 4 - Pump Circuit 1
    pump_circuit2: bool  # Bit 5 - Pump Circuit 2
    solar_pump: bool  # Bit 6 - Solar Pump
    pool_pump: bool  # Bit 7 - Pool Pump
    defrost: bool  # Bit 8 - Defrost
    bivalence_running: bool  # Bit 9 - Bivalence Running
    summer_mode: bool  # Bit 10 - Summer Mode
    brine_pump: bool  # Bit 11 - Brine Pump
    cooling_running: bool  # Bit 12 - Cooling Running


@dataclass
class HeatPumpResponse:
    """
    Data class representing the response from the heat pump unit.
    """

    indoor1_temp_set: float
    """Desired indoor temperature, circuit 1 [°C]"""
    indoor1_temp_actual: float
    """Actual indoor temperature, circuit 1 [°C]"""
    indoor2_temp_set: float
    """Desired indoor temperature, circuit 2 [°C]"""
    indoor2_temp_actual: float
    """Actual indoor temperature, circuit 2 [°C]"""
    dhw_temp_set: float
    """Desired domestic hot water temperature [°C]"""
    dhw_temp_actual: float
    """Actual domestic hot water temperature [°C]"""
    status: HeatPumpStatus
    """Heat pump status"""
    water_back_temp_set: float
    """Desired return water temperature [°C]"""
    water_back_temp_actual: float
    """Actual return water temperature [°C]"""
    outdoor_temp_actual: float
    """Actual outdoor temperature [°C]"""
    solar_temp_actual: float
    """Solar temperature [°C]"""
    pool_temp_actual: float
    """Pool temperature [°C]"""
    pool_temp_set: float
    """Desired pool temperature [°C]"""
    heat_pump_mode: HeatPumpMode
    regulation_mode: RegulationMode
    brine_temp: float
    """Brine temperature at the outlet from collector [°C]"""
    heart_beat: int
    """Communication verification counter"""
    water_outlet_temp_actual: float
    """Actual water outlet temperature [°C]"""
    water_outlet_temp_set: float
    """Desired water outlet temperature for cooling [°C]"""
    compressor_capacity_max: int
    """Max heat pump capacity [W]. Only for PRO units"""
    compressor_capacity_actual: int
    """Actual heat pump capacity (heating/cooling) [W]. Only for PRO units"""
    err_number: int
    """Basic error number"""
    err_number_SECMono: int
    """SECMono error number"""
    err_number_driver: int
    """Driver error number"""
