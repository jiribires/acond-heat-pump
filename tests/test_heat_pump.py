import unittest
from unittest.mock import patch, MagicMock

from acond_heat_pump import AcondHeatPump
from acond_heat_pump import HeatPumpStatus
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
        self.assertEqual(response.indoor2_temp_actual, 0)
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
        self.assertEqual(response.solar_temp_actual, 0)
        self.assertEqual(response.pool_temp_actual, 0)
        self.assertEqual(response.pool_temp_set, 30.0)
        self.assertEqual(response.brine_temp, 0)
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


if __name__ == "__main__":
    unittest.main()
