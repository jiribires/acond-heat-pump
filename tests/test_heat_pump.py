import unittest
from unittest.mock import patch, MagicMock, call

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
        self.mock_client.write_register.assert_called_with(0, 250, device_id=1)

    def test_set_dhw_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_dhw_temperature(45.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(4, 450, device_id=1)

    def test_set_regulation_mode(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_regulation_mode(RegulationMode.MANUAL)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(
            6, RegulationMode.MANUAL.value, device_id=1
        )

    def test_set_water_back_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_water_back_temperature(35.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(7, 350, device_id=1)

    def test_set_pool_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_pool_temperature(28.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(11, 280, device_id=1)

    def test_set_water_cool_temperature(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_water_cool_temperature(20.0)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(12, 200, device_id=1)


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
        self.mock_client.write_register.assert_called_with(5, 0b000001, device_id=1)

    def test_change_setting_off(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = False
        mock_read.registers = [0b000001]  # AUTOMATIC currently set
        self.mock_client.read_holding_registers.return_value = mock_read
        self.mock_client.write_register.return_value.isError.return_value = False

        result = self.heat_pump.change_setting(HeatPumpMode.OFF)
        self.assertTrue(result)
        # OFF = bit 3 → value 0b001000 = 8, AUTOMATIC bit cleared
        self.mock_client.write_register.assert_called_with(5, 0b001000, device_id=1)

    def test_change_setting_preserves_non_mode_bits(self):
        mock_read = MagicMock()
        mock_read.isError.return_value = False
        # Bits 5 (fault-ack), 6 (solar), 7 (pool), 8 (summer) are non-mode bits
        # that should all be preserved across a mode change.
        mock_read.registers = [0b1_11100001]  # bits 5,6,7,8 + AUTOMATIC
        self.mock_client.read_holding_registers.return_value = mock_read
        self.mock_client.write_register.return_value.isError.return_value = False

        result = self.heat_pump.change_setting(HeatPumpMode.COOLING)
        self.assertTrue(result)
        # COOLING = bit 4. Bits 5,6,7,8 preserved, AUTOMATIC (bit 0) cleared.
        expected = 0b1_11110000
        self.mock_client.write_register.assert_called_with(5, expected, device_id=1)

    def test_change_setting_manual_raises(self):
        """MANUAL is not writable via TC_set per the Acond spec (bit 5 is
        fault-ack, not a mode bit). Should raise without touching the bus."""
        with self.assertRaises(ValueError):
            self.heat_pump.change_setting(HeatPumpMode.MANUAL)
        self.mock_client.read_holding_registers.assert_not_called()
        self.mock_client.write_register.assert_not_called()

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
        self.mock_client.write_register.assert_called_with(0, 206, device_id=1)

    def test_set_indoor_temperature_circuit2(self):
        self.mock_client.write_register.return_value.isError.return_value = False
        result = self.heat_pump.set_indoor_temperature(22.0, circuit=2)
        self.assertTrue(result)
        self.mock_client.write_register.assert_called_with(2, 220, device_id=1)

    # --- read_data additional coverage ---

    def test_read_data_register_call_args(self):
        mock_result = MagicMock()
        mock_result.isError.return_value = False
        mock_result.registers = [0] * 24
        self.mock_client.read_input_registers.return_value = mock_result

        self.heat_pump.read_data()
        self.mock_client.read_input_registers.assert_called_once_with(0, count=24, device_id=1)

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

    # --- set_summer_mode tests ---

    @staticmethod
    def _mock_status(summer: bool):
        """Build a mock input-register read with TC_status bit 10 reflecting summer."""
        mock = MagicMock()
        mock.isError.return_value = False
        mock.registers = [(1 << 10) if summer else 0]
        return mock

    def _setup_summer_test(self, current_status: bool, tc_set: int, poll_results=None):
        """
        Wire up mocks for a set_summer_mode call.

        - current_status: TC_status bit 10 before the pre-check.
        - tc_set: TC_set value the holding-register read returns.
        - poll_results: list of TC_status bit 10 values returned by post-write
          polls (defaults to a single `not current_status` to flip immediately).
        """
        if poll_results is None:
            poll_results = [not current_status]
        self.mock_client.read_input_registers.side_effect = [
            self._mock_status(current_status),  # pre-check
            *(self._mock_status(v) for v in poll_results),  # polls after pulse
        ]
        holding = MagicMock()
        holding.isError.return_value = False
        holding.registers = [tc_set]
        self.mock_client.read_holding_registers.return_value = holding
        self.mock_client.write_register.return_value.isError.return_value = False

    def test_set_summer_mode_on_pulses_bit_8(self):
        # Currently winter, want summer. TC_set has only HP mode bit (1) set.
        self._setup_summer_test(current_status=False, tc_set=0b000010)

        result = self.heat_pump.set_summer_mode(True)
        self.assertTrue(result)

        # Pulse: clear bit 8, then set it. Other bits preserved.
        self.assertEqual(
            self.mock_client.write_register.call_args_list,
            [
                call(5, 0b000010, device_id=1),  # clear (bit 8 was already 0)
                call(5, 0b000010 | (1 << 8), device_id=1),  # rising edge
            ],
        )

    def test_set_summer_mode_off_pulses_bit_8(self):
        # Currently summer, want winter. Symmetric: same pulse regardless of direction.
        self._setup_summer_test(
            current_status=True, tc_set=0b000010 | (1 << 8)
        )

        result = self.heat_pump.set_summer_mode(False)
        self.assertTrue(result)

        self.assertEqual(
            self.mock_client.write_register.call_args_list,
            [
                call(5, 0b000010, device_id=1),  # clear leftover bit 8 from prior switch
                call(5, 0b000010 | (1 << 8), device_id=1),  # fresh rising edge
            ],
        )

    def test_set_summer_mode_preserves_other_bits(self):
        # Bits 1 (HP mode) + 6 + 7 + 10 set in TC_set; bit 8 currently off.
        tc_set = 0b10011000010
        self._setup_summer_test(current_status=False, tc_set=tc_set)

        result = self.heat_pump.set_summer_mode(True)
        self.assertTrue(result)

        cleared = tc_set & ~(1 << 8)
        asserted = cleared | (1 << 8)
        self.assertEqual(
            self.mock_client.write_register.call_args_list,
            [call(5, cleared, device_id=1), call(5, asserted, device_id=1)],
        )

    def test_set_summer_mode_already_in_state_is_noop(self):
        # Already in summer, requesting summer → no writes, no holding read.
        self.mock_client.read_input_registers.return_value = self._mock_status(True)

        result = self.heat_pump.set_summer_mode(True)
        self.assertTrue(result)
        self.mock_client.read_holding_registers.assert_not_called()
        self.mock_client.write_register.assert_not_called()

    def test_set_summer_mode_status_read_error(self):
        # Pre-check status read fails → bail before any write.
        bad = MagicMock()
        bad.isError.return_value = True
        self.mock_client.read_input_registers.return_value = bad

        result = self.heat_pump.set_summer_mode(True)
        self.assertFalse(result)
        self.mock_client.read_holding_registers.assert_not_called()
        self.mock_client.write_register.assert_not_called()

    def test_set_summer_mode_tc_set_read_error(self):
        # Status mismatched → proceed; but TC_set read fails → bail before write.
        self.mock_client.read_input_registers.return_value = self._mock_status(False)
        bad = MagicMock()
        bad.isError.return_value = True
        self.mock_client.read_holding_registers.return_value = bad

        result = self.heat_pump.set_summer_mode(True)
        self.assertFalse(result)
        self.mock_client.write_register.assert_not_called()

    def test_set_summer_mode_clear_write_error(self):
        # First (clear) write fails → no second write, returns False.
        self.mock_client.read_input_registers.return_value = self._mock_status(False)
        holding = MagicMock()
        holding.isError.return_value = False
        holding.registers = [0]
        self.mock_client.read_holding_registers.return_value = holding
        self.mock_client.write_register.return_value.isError.return_value = True

        result = self.heat_pump.set_summer_mode(True)
        self.assertFalse(result)
        # Only one write attempted before bailing
        self.assertEqual(self.mock_client.write_register.call_count, 1)

    @patch("acond_heat_pump.heat_pump.time.sleep")
    def test_set_summer_mode_status_does_not_propagate(self, _mock_sleep):
        # Pulse succeeds but status never flips → False after timeout.
        # Use return_value (not side_effect) so unlimited polls all see False.
        self.mock_client.read_input_registers.return_value = self._mock_status(False)
        holding = MagicMock()
        holding.isError.return_value = False
        holding.registers = [0]
        self.mock_client.read_holding_registers.return_value = holding
        self.mock_client.write_register.return_value.isError.return_value = False

        result = self.heat_pump.set_summer_mode(
            True, timeout=0.1, poll_interval=0.01
        )
        self.assertFalse(result)
        # At least pre-check + a couple of polls
        self.assertGreater(self.mock_client.read_input_registers.call_count, 2)

    @patch("acond_heat_pump.heat_pump.time.sleep")
    def test_set_summer_mode_status_propagates_after_delay(self, _mock_sleep):
        # Status flips on the third poll.
        self._setup_summer_test(
            current_status=False,
            tc_set=0,
            poll_results=[False, False, True],
        )

        result = self.heat_pump.set_summer_mode(
            True, timeout=5.0, poll_interval=0.01
        )
        self.assertTrue(result)
        # 1 pre-check + 3 polls = 4
        self.assertEqual(self.mock_client.read_input_registers.call_count, 4)

    def test_read_temp_register_at_boundary(self):
        # Exactly at min → returns value (not None)
        result = AcondHeatPump._read_temp_register(100, min=10.0, max=30.0)
        self.assertEqual(result, 10.0)
        # Exactly at max → returns value (not None)
        result = AcondHeatPump._read_temp_register(300, min=10.0, max=30.0)
        self.assertEqual(result, 30.0)


if __name__ == "__main__":
    unittest.main()
