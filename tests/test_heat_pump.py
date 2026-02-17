import unittest
from unittest.mock import patch, MagicMock

from acond_heat_pump import AcondHeatPump
from acond_heat_pump import HeatPumpMode
from acond_heat_pump import HeatPumpStatus
from acond_heat_pump import HeatPumpConnectionError
from acond_heat_pump import RegulationMode


class TestAcondHeatPump(unittest.TestCase):
    @patch("acond_heat_pump.heat_pump.ModbusTcpClient")
    def setUp(self, MockModbusTcpClient):
        self.mock_client = MockModbusTcpClient.return_value
        self.heat_pump = AcondHeatPump("192.168.1.16")

    def test_connect(self):
        self.heat_pump.connect()
        self.mock_client.connect.assert_called_once()

    def test_close(self):
        self.heat_pump.close()
        self.mock_client.close.assert_called_once()

    def test_read_data(self):
        mock_result = MagicMock()
        mock_result.isError.return_value = False
        mock_result.registers = [
            190,
            205,
            150,
            65516,
            450,
            465,
            3,
            400,
            290,
            65503,
            0,
            0,
            300,
            0,
            2,
            65146,
            17,
            343,
            200,
            6061,
            0,
            0,
            0,
            5200,
        ]
        self.mock_client.read_input_registers.return_value = mock_result

        response = self.heat_pump.read_data()
        self.assertEqual(response.indoor1_temp_set, 19.0)
        self.assertEqual(response.indoor1_temp_actual, 20.5)
        self.assertEqual(response.indoor2_temp_set, 15.0)
        self.assertIsNone(response.indoor2_temp_actual)
        self.assertEqual(response.dhw_temp_set, 45.0)
        self.assertEqual(response.dhw_temp_actual, 46.5)
        self.assertEqual(response.regulation_mode, RegulationMode.MANUAL)
        self.assertEqual(
            response.status,
            HeatPumpStatus(
                on=True,
                running=True,
                fault=False,
                heating_dhw=False,
                pump_circuit1=False,
                pump_circuit2=False,
                solar_pump=False,
                pool_pump=False,
                defrost=False,
                bivalence_running=False,
                summer_mode=False,
                brine_pump=False,
                cooling_running=False,
            ),
        )
        self.assertEqual(response.water_back_temp_set, 40.0)
        self.assertEqual(response.water_back_temp_actual, 29.0)
        self.assertEqual(response.outdoor_temp_actual, -3.3)
        self.assertEqual(response.solar_temp_actual, 0.0)
        self.assertEqual(response.pool_temp_actual, 0.0)
        self.assertEqual(response.pool_temp_set, 30.0)
        self.assertIsNone(response.brine_temp)
        self.assertEqual(response.heart_beat, 17)
        self.assertEqual(response.water_outlet_temp_actual, 34.3)
        self.assertEqual(response.water_outlet_temp_set, 20.0)
        self.assertEqual(response.compressor_capacity_max, 6061)
        self.assertEqual(response.err_number, 0)
        self.assertEqual(response.err_number_SECMono, 0)
        self.assertEqual(response.err_number_driver, 0)
        self.assertEqual(response.compressor_capacity_actual, 5200)

    def test_set_indoor_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_indoor_temperature(25.0, circuit=1)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(0, 250, slave=1)

    def test_set_dhw_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_dhw_temperature(45.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(4, 450, slave=1)

    def test_set_regulation_mode(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_regulation_mode(RegulationMode.MANUAL)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(
            6, RegulationMode.MANUAL.value, slave=1
        )

    def test_set_water_back_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_water_back_temperature(35.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(7, 350, slave=1)

    def test_set_pool_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_pool_temperature(28.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(11, 280, slave=1)

    def test_set_water_cool_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_water_cool_temperature(20.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(12, 200, slave=1)


    # --- change_setting tests ---

    def test_change_setting_automatic(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = False
        mock_read.registers = [0]
        self.mock_client.read_holding_registers.return_value = mock_read
        self.mock_client.write_register.return_value.isError.return_value = False

        result = self.heat_pump.change_setting(HeatPumpMode.AUTOMATIC)
        self.assertTrue(result)
        # AUTOMATIC = bit 0 → value 0b000001 = 1
        self.mock_client.write_register.assert_called_with(5, 0b000001, slave=1)

    def test_change_setting_off(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = False
        mock_read.registers = [0b000001]  # AUTOMATIC currently set
        self.mock_client.read_holding_registers.return_value = mock_read
        self.mock_client.write_register.return_value.isError.return_value = False

        result = self.heat_pump.change_setting(HeatPumpMode.OFF)
        self.assertTrue(result)
        # OFF = bit 3 → value 0b001000 = 8, AUTOMATIC bit cleared
        self.mock_client.write_register.assert_called_with(5, 0b001000, slave=1)

    def test_change_setting_preserves_non_mode_bits(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = False
        # Bits 6+ are non-mode bits that should be preserved
        mock_read.registers = [0b11000000_00000001]  # bits 6,7 set + AUTOMATIC
        self.mock_client.read_holding_registers.return_value = mock_read
        self.mock_client.write_register.return_value.isError.return_value = False

        result = self.heat_pump.change_setting(HeatPumpMode.COOLING)
        self.assertTrue(result)
        # COOLING = bit 4, non-mode bits preserved
        expected = 0b11000000_00010000
        self.mock_client.write_register.assert_called_with(5, expected, slave=1)

    def test_change_setting_manual(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = False
        mock_read.registers = [0]
        self.mock_client.read_holding_registers.return_value = mock_read
        self.mock_client.write_register.return_value.isError.return_value = False

        result = self.heat_pump.change_setting(HeatPumpMode.MANUAL)
        self.assertTrue(result)
        # MANUAL = bit 5 → value 0b100000 = 32
        self.mock_client.write_register.assert_called_with(5, 0b100000, slave=1)

    def test_change_setting_read_error(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = True
        self.mock_client.read_holding_registers.return_value = mock_read

        result = self.heat_pump.change_setting(HeatPumpMode.AUTOMATIC)
        self.assertFalse(result)
        self.mock_client.write_register.assert_not_called()

    def test_change_setting_write_error(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = False
        mock_read.registers = [0]
        self.mock_client.read_holding_registers.return_value = mock_read
        self.mock_client.write_register.return_value.isError.return_value = True

        result = self.heat_pump.change_setting(HeatPumpMode.AUTOMATIC)
        self.assertFalse(result)

    # --- connect return value tests ---

    def test_connect_returns_true(self):
        self.mock_client.connect.return_value = True
        self.assertTrue(self.heat_pump.connect())

    def test_connect_returns_false(self):
        self.mock_client.connect.return_value = False
        self.assertFalse(self.heat_pump.connect())

    # --- read_data exception test ---

    def test_read_data_raises_on_error(self):
        mock_result = MagicMock()
        mock_result.isError.return_value = True
        self.mock_client.read_input_registers.return_value = mock_result

        with self.assertRaises(HeatPumpConnectionError):
            self.heat_pump.read_data()

    # --- set_indoor_temperature edge cases ---

    def test_set_indoor_temperature_write_error(self):
        self.mock_client.write_register.return_value.isError.return_value = True
        result = self.heat_pump.set_indoor_temperature(25.0, circuit=1)
        self.assertFalse(result)

    def test_set_indoor_temperature_invalid_circuit(self):
        with self.assertRaises(ValueError):
            self.heat_pump.set_indoor_temperature(25.0, circuit=3)

    def test_set_indoor_temperature_out_of_range(self):
        with self.assertRaises(ValueError):
            self.heat_pump.set_indoor_temperature(50.0, circuit=1)

    def test_set_indoor_temperature_rounding(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        self.heat_pump.set_indoor_temperature(20.55, circuit=1)
        # 20.55 * 10 = 205.5 → round() = 206, not int() = 205
        self.mock_client.write_register.assert_called_with(0, 206, slave=1)

    def test_set_indoor_temperature_circuit2(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_indoor_temperature(22.0, circuit=2)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(2, 220, slave=1)

    # --- read_data additional coverage ---

    def test_read_data_register_call_args(self):
        mock_result = MagicMock()
        mock_result.isError.return_value = False
        mock_result.registers = [0] * 24
        self.mock_client.read_input_registers.return_value = mock_result

        self.heat_pump.read_data()
        self.mock_client.read_input_registers.assert_called_once_with(0, 24, slave=1)

    def test_read_data_status_bits_varied(self):
        """Verify field-to-bit mapping with bits 3,6,9,12 set (0x1248)."""
        mock_result = MagicMock()
        mock_result.isError.return_value = False
        mock_result.registers = [
            200, 200, 200, 200, 200, 200,
            0x1248,  # bits 3,6,9,12
            200, 200, 0, 0, 0, 200, 0, 0, 0, 0, 200, 200, 0, 0, 0, 0, 0,
        ]
        self.mock_client.read_input_registers.return_value = mock_result

        status = self.heat_pump.read_data().status
        self.assertFalse(status.on)
        self.assertFalse(status.running)
        self.assertFalse(status.fault)
        self.assertTrue(status.heating_dhw)       # bit 3
        self.assertFalse(status.pump_circuit1)
        self.assertFalse(status.pump_circuit2)
        self.assertTrue(status.solar_pump)         # bit 6
        self.assertFalse(status.pool_pump)
        self.assertFalse(status.defrost)
        self.assertTrue(status.bivalence_running)  # bit 9
        self.assertFalse(status.summer_mode)
        self.assertFalse(status.brine_pump)
        self.assertTrue(status.cooling_running)    # bit 12

    def test_read_temp_register_at_boundary(self):
        # Exactly at min → returns value (not None)
        result = AcondHeatPump._read_temp_register(100, min=10.0, max=30.0)
        self.assertEqual(result, 10.0)
        # Exactly at max → returns value (not None)
        result = AcondHeatPump._read_temp_register(300, min=10.0, max=30.0)
        self.assertEqual(result, 30.0)


if __name__ == "__main__":
    unittest.main()
