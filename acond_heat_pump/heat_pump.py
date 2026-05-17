from typing import Optional
import time

from pymodbus.client.tcp import ModbusTcpClient
import logging

from acond_heat_pump.constants import RegulationMode, HeatPumpMode
from acond_heat_pump.exceptions import HeatPumpConnectionError
from acond_heat_pump.heat_pump_data import HeatPumpStatus, HeatPumpResponse

log = logging.getLogger(__name__)


class AcondHeatPump:
    """
    A class to represent and interact with an Acond heat pump system.

    Usage:
        heat_pump = AcondHeatPump("192.168.1.16")
        heat_pump.connect()
        response = heat_pump.read_data()
        heat_pump.set_indoor_temperature(25.0, circuit=1)
        heat_pump.close()
    """

    def __init__(self, host: str, port: int = 502):
        """
        Initialize the heat pump object.
        :param host: IP or hostname of the heat pump.
        :param port: Port number of the Modbus TCP server. Default is 502.
        """
        self.client = ModbusTcpClient(host, port=port)

    def connect(self) -> bool:
        """
        Connect to the heat pump.
        """
        return self.client.connect()

    def close(self):
        """
        Close the connection to the heat pump.
        """
        self.client.close()

    def read_data(self) -> HeatPumpResponse:
        """
        Read all input registers and parse them into a HeatPumpResponse object.

        Returns:
            HeatPumpResponse: An object containing the parsed data from the heat pump.

        Raises:
            Exception: If there is an error reading the input registers.
        """

        # Reading 24 registers from 30001 to 30024
        result = self.client.read_input_registers(0, count=24, device_id=1)
        if result.isError():
            log.error("Error reading input registers")
            raise HeatPumpConnectionError("Error reading input registers")

        return HeatPumpResponse(
            indoor1_temp_set=self._read_temp_register(
                result.registers[0], min=10.0, max=30.0
            ),
            indoor1_temp_actual=self._read_temp_register(
                result.registers[1], min=0.0, max=50.0
            ),
            indoor2_temp_set=self._read_temp_register(
                result.registers[2], min=10.0, max=30.0
            ),
            indoor2_temp_actual=self._read_temp_register(
                result.registers[3], min=0.0, max=50.0
            ),
            dhw_temp_set=self._read_temp_register(
                result.registers[4], min=10.0, max=50.0
            ),
            dhw_temp_actual=self._read_temp_register(
                result.registers[5], min=0.0, max=90.0
            ),
            status=self._parse_status_bits(result.registers[6]),
            water_back_temp_set=self._read_temp_register(
                result.registers[7], min=20.0, max=60.0
            ),
            water_back_temp_actual=self._read_temp_register(
                result.registers[8], min=-10.0, max=90.0
            ),
            outdoor_temp_actual=self._read_temp_register(
                result.registers[9], min=-50.0, max=50.0
            ),
            solar_temp_actual=self._read_temp_register(
                result.registers[10], min=-50.0, max=300.0
            ),
            pool_temp_actual=self._read_temp_register(
                result.registers[11], min=0.0, max=50.0
            ),
            pool_temp_set=self._read_temp_register(result.registers[12]),
            heat_pump_mode=HeatPumpMode(result.registers[13]),
            regulation_mode=RegulationMode(result.registers[14]),
            brine_temp=self._read_temp_register(
                result.registers[15], min=-30.0, max=50.0
            ),
            heart_beat=result.registers[16],
            water_outlet_temp_actual=self._read_temp_register(
                result.registers[17], min=-10.0, max=90.0
            ),
            water_outlet_temp_set=self._read_temp_register(
                result.registers[18], min=10.0, max=25.0
            ),
            compressor_capacity_max=result.registers[19],
            err_number=result.registers[20],
            err_number_SECMono=result.registers[21],
            err_number_driver=result.registers[22],
            compressor_capacity_actual=result.registers[23],
        )

    def set_indoor_temperature(self, temperature: float, circuit: int = 1) -> bool:
        """
        Set the desired indoor temperature for a given circuit (1 or 2).

        Parameters:
        - temperature (float): The temperature to set in °C. Must be between 10.0 and 30.0 °C.
        - circuit (int): The circuit number (1 or 2). Default is 1.

        Returns:
        - bool: True if the temperature was set successfully, False otherwise.
        """
        # Choose the appropriate register based on the circuit number
        if circuit == 1:
            register_address = 0  # 40001 offset
        elif circuit == 2:
            register_address = 2  # 40003 offset
        else:
            raise ValueError("Invalid circuit number. Use 1 or 2.")

        if not 10.0 <= temperature <= 30.0:
            raise ValueError("Temperature must be between 10.0 and 30.0 °C")

        # Scale the temperature by 10 for the Modbus register
        scaled_temperature = round(temperature * 10)

        # Write to the register
        result = self.client.write_register(
            register_address, scaled_temperature, device_id=1
        )
        if not result.isError():
            log.info(f"Temperature for circuit {circuit} set to {temperature} °C")
            return True
        else:
            log.info(f"Failed to set temperature for circuit {circuit}")
            return False

    def set_dhw_temperature(self, temperature: float) -> bool:
        """
        Set the desired domestic hot water temperature.

        Parameters:
        - temperature (float): The temperature to set in °C. Must be between 10.0 and 50.0 °C.

        Returns:
        - bool: True if the temperature was set successfully, False otherwise.
        """
        if not 10.0 <= temperature <= 50.0:
            raise ValueError("Temperature must be between 10.0 and 50.0 °C")

        # Scale the temperature by 10 for the Modbus register
        scaled_temperature = round(temperature * 10)

        # Write to the register
        result = self.client.write_register(4, scaled_temperature, device_id=1)
        if not result.isError():
            log.info(f"Domestic hot water temperature set to {temperature} °C")
            return True
        else:
            log.info("Failed to set domestic hot water temperature")
            return False

    def set_regulation_mode(self, mode: RegulationMode) -> bool:
        """
        Set the regulation mode.

        Parameters:
        - mode: The regulation mode to set.

        Returns:
        - bool: True if the mode was set successfully, False otherwise.
        """
        result = self.client.write_register(6, mode.value, device_id=1)
        if not result.isError():
            log.info(f"Regulation mode set to {mode.name}")
            return True
        else:
            log.info("Failed to set regulation mode")
            return False

    # Bit position in TC_set register for each heat pump mode.
    # HeatPumpMode.MANUAL is intentionally absent: per the Acond Modbus spec,
    # TC_set bit 5 is "fault acknowledgement", not a mode bit. Manual mode
    # exists only as a read value in rezim_pan (input 30014).
    _MODE_BIT_POSITION = {
        HeatPumpMode.AUTOMATIC: 0,
        HeatPumpMode.HEAT_PUMP_ONLY: 1,
        HeatPumpMode.BIVALENT_ONLY: 2,
        HeatPumpMode.OFF: 3,
        HeatPumpMode.COOLING: 4,
    }

    # Bitmask covering all mode bits (bits 0–4).
    _MODE_BITS_MASK = sum(1 << pos for pos in _MODE_BIT_POSITION.values())

    # Bit position in TC_set register for summer mode
    _SUMMER_MODE_BIT = 8

    # TC_status (input register 30007 / offset 6), bit 10 = summer operation
    _STATUS_REGISTER = 6
    _SUMMER_STATUS_BIT = 10

    def change_setting(self, mode: HeatPumpMode) -> bool:
        """
        Set the heat pump operating mode by writing to the TC_set register.

        Only one mode bit (bits 0–4) is set at a time; non-mode bits
        (including bit 5 fault-ack, bits 6–7 solar/pool, bit 8 summer) are
        preserved.

        HeatPumpMode.MANUAL is not settable via Modbus per the Acond spec —
        it appears only as a read value in rezim_pan. Passing it raises
        ValueError.

        Parameters:
        - mode (HeatPumpMode): The operating mode to set.

        Returns:
        - bool: True if the mode was set successfully, False otherwise.
        """
        if mode not in self._MODE_BIT_POSITION:
            settable = ", ".join(m.name for m in self._MODE_BIT_POSITION)
            raise ValueError(
                f"{mode.name} is not settable via TC_set. "
                f"Settable modes: {settable}."
            )

        register_address = 5  # Modbus address for TC_set (40006)

        result = self.client.read_holding_registers(
            register_address, count=1, device_id=1
        )
        if result.isError():
            log.error("Failed to read TC_set register")
            return False

        current_value = result.registers[0]

        # Clear all mode bits, then set the one for the requested mode
        bit_value = (current_value & ~self._MODE_BITS_MASK) | (
            1 << self._MODE_BIT_POSITION[mode]
        )

        # Write the updated value to the TC_set register
        write_result = self.client.write_register(
            register_address, bit_value, device_id=1
        )
        if write_result.isError():
            log.error("Failed to update TC_set register")
            return False

        log.info(f"Heat pump mode set to {mode.name}")
        return True

    def set_summer_mode(
        self,
        summer: bool,
        timeout: float = 5.0,
        poll_interval: float = 0.2,
    ) -> bool:
        """
        Switch the heat pump between summer and winter mode.

        TC_set bit 8 ("summer/winter switching", holding 40006) is an
        edge-triggered command, not a state mirror: only a rising edge
        (0 → 1) tells the controller to switch. Its value in TC_set does
        not correspond to the current mode — that lives in TC_status bit 10
        (input 30007). This method pulses bit 8 (clear, then set) to
        generate a fresh rising edge, then polls TC_status to confirm.

        Parameters:
        - summer (bool): True for summer, False for winter.
        - timeout (float): Max seconds to wait for TC_status to reflect the
          requested state.
        - poll_interval (float): Seconds between status polls.

        Returns:
        - bool: True if TC_status reached the requested state within timeout
          (including the no-op case where it was already there), False on
          any Modbus error or if the controller did not switch.
        """
        register_address = 5  # Modbus address for TC_set (40006)

        # No-op fast path: don't touch the bus if we're already in the
        # requested state. Avoids generating spurious edges on the pump.
        status = self.client.read_input_registers(
            self._STATUS_REGISTER, count=1, device_id=1
        )
        if status.isError():
            log.error("Failed to read TC_status register")
            return False
        if bool(status.registers[0] & (1 << self._SUMMER_STATUS_BIT)) == summer:
            log.info(
                f"Summer mode already {'enabled' if summer else 'disabled'}"
            )
            return True

        result = self.client.read_holding_registers(
            register_address, count=1, device_id=1
        )
        if result.isError():
            log.error("Failed to read TC_set register")
            return False

        current_value = result.registers[0]
        cleared = current_value & ~(1 << self._SUMMER_MODE_BIT)
        asserted = cleared | (1 << self._SUMMER_MODE_BIT)

        # Pulse: clear bit 8 first so the next write is always a fresh
        # rising edge, regardless of whether bit 8 was already set from a
        # prior switch.
        if self.client.write_register(
            register_address, cleared, device_id=1
        ).isError():
            log.error("Failed to clear TC_set bit 8")
            return False
        if self.client.write_register(
            register_address, asserted, device_id=1
        ).isError():
            log.error("Failed to assert TC_set bit 8")
            return False

        deadline = time.monotonic() + timeout
        while True:
            status = self.client.read_input_registers(
                self._STATUS_REGISTER, count=1, device_id=1
            )
            if not status.isError():
                actual = bool(
                    status.registers[0] & (1 << self._SUMMER_STATUS_BIT)
                )
                if actual == summer:
                    log.info(
                        f"Summer mode {'enabled' if summer else 'disabled'}"
                    )
                    return True
            if time.monotonic() >= deadline:
                log.warning(
                    f"TC_set bit 8 pulsed but TC_status bit "
                    f"{self._SUMMER_STATUS_BIT} did not reach {summer} "
                    f"within {timeout}s"
                )
                return False
            time.sleep(poll_interval)

    def set_water_back_temperature(self, temperature: float) -> bool:
        """
        Set the desired return water temperature.

        Parameters:
        - temperature (float): The temperature to set in °C. Must be between 10.0 and 65.0 °C.

        Returns:
        - bool: True if the temperature was set successfully, False otherwise.
        """
        if not 10.0 <= temperature <= 65.0:
            raise ValueError("Temperature must be between 10.0 and 65.0 °C")

        # Scale the temperature by 10 for the Modbus register
        scaled_temperature = round(temperature * 10)

        # Write to the register
        result = self.client.write_register(7, scaled_temperature, device_id=1)
        if not result.isError():
            log.info(f"Return water temperature set to {temperature} °C")
            return True
        else:
            log.info("Failed to set return water temperature")
            return False

    def set_pool_temperature(self, temperature: float) -> bool:
        """
        Set the desired pool water temperature.

        Parameters:
        - temperature (float): The temperature to set in °C. Must be between 10.0 and 50.0 °C.

        Returns:
        - bool: True if the temperature was set successfully, False otherwise.
        """
        if not 10.0 <= temperature <= 50.0:
            raise ValueError("Temperature must be between 10.0 and 50.0 °C")

        # Scale the temperature by 10 for the Modbus register
        scaled_temperature = round(temperature * 10)

        # Write to the register
        result = self.client.write_register(11, scaled_temperature, device_id=1)
        if not result.isError():
            log.info(f"Pool water temperature set to {temperature} °C")
            return True
        else:
            log.info("Failed to set pool water temperature")
            return False

    def set_water_cool_temperature(self, temperature: float) -> bool:
        """
        Set the desired water outlet temperature in cooling mode.

        Parameters:
        - temperature (float): The temperature to set in °C. Must be between 15.0 and 30.0 °C.

        Returns:
        - bool: True if the temperature was set successfully, False otherwise.
        """
        if not 15.0 <= temperature <= 30.0:
            raise ValueError("Temperature must be between 15.0 and 30.0 °C")

        # Scale the temperature by 10 for the Modbus register
        scaled_temperature = round(temperature * 10)

        # Write to the register
        result = self.client.write_register(12, scaled_temperature, device_id=1)
        if not result.isError():
            log.info(f"Water cool temperature set to {temperature} °C")
            return True
        else:
            log.info("Failed to set water cool temperature")
            return False

    @staticmethod
    def _read_temp_register(
        value: int, min: Optional[float] = None, max: Optional[float] = None
    ) -> Optional[float]:
        """
        Read temperature register and convert it to float.
        """
        signed = int.from_bytes(int(value).to_bytes(length=2), signed=True)
        temp = signed / 10.0
        if min is not None and temp < min:
            return None
        if max is not None and temp > max:
            return None
        return temp

    @staticmethod
    def _parse_status_bits(status: int) -> HeatPumpStatus:
        """
        Extract status bits from TC_status register.
        """

        status_bits = [bool(status & (1 << bit)) for bit in range(16)]
        return HeatPumpStatus(
            on=status_bits[0],
            running=status_bits[1],
            fault=status_bits[2],
            heating_dhw=status_bits[3],
            pump_circuit1=status_bits[4],
            pump_circuit2=status_bits[5],
            solar_pump=status_bits[6],
            pool_pump=status_bits[7],
            defrost=status_bits[8],
            bivalence_running=status_bits[9],
            summer_mode=status_bits[10],
            brine_pump=status_bits[11],
            cooling_running=status_bits[12],
        )
