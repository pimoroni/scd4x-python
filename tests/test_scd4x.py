import time
from unittest import mock

import pytest


def test_rdwr(smbus2, scd4x):
    smbus2.i2c_msg.read().__iter__.return_value = [
        0xF8,
        0x96,
        0x31,
        0x9F,
        0x07,
        0xC2,
        0x3B,
        0xBE,
        0x89,
    ]
    sensor = scd4x.SCD4X()

    # Send Command
    smbus2.i2c_msg.write.reset_mock()
    smbus2.i2c_msg.read().__iter__.return_value = []
    assert sensor.rdwr(0xCAFE) == []
    smbus2.i2c_msg.write.assert_called_once_with(0x62, b"\xca\xfe")

    # Send Command with Delay
    smbus2.i2c_msg.write.reset_mock()
    smbus2.i2c_msg.read().__iter__.return_value = []
    start = time.monotonic()
    assert sensor.rdwr(0xCAFE, delay=500) == []
    elapsed = time.monotonic() - start
    assert elapsed > 0.5
    smbus2.i2c_msg.write.assert_called_once_with(0x62, b"\xca\xfe")

    # Read One Byte
    smbus2.i2c_msg.write.reset_mock()
    smbus2.i2c_msg.read().__iter__.return_value = [0xF8, 0x96, 0x31]
    assert sensor.rdwr(0xCAFE, response_length=1) == 0xF896
    smbus2.i2c_msg.write.assert_called_once_with(0x62, b"\xca\xfe")

    # Read Three Byte
    smbus2.i2c_msg.write.reset_mock()
    smbus2.i2c_msg.read().__iter__.return_value = [
        0xF8,
        0x96,
        0x31,
        0x9F,
        0x07,
        0xC2,
        0x3B,
        0xBE,
        0x89,
    ]
    assert sensor.rdwr(0xCAFE, response_length=3) == [0xF896, 0x9F07, 0x3BBE]
    smbus2.i2c_msg.write.assert_called_once_with(0x62, b"\xca\xfe")

    # Write
    smbus2.i2c_msg.write.reset_mock()
    smbus2.i2c_msg.read().__iter__.return_value = []
    assert sensor.rdwr(0xCAFE, value=0x4711) == []
    smbus2.i2c_msg.write.assert_called_once_with(0x62, b"\xca\xfe\x47\x11\xd4")

    # Read and Write
    smbus2.i2c_msg.write.reset_mock()
    smbus2.i2c_msg.read().__iter__.return_value = [0xF8, 0x96, 0x31]
    assert sensor.rdwr(0xCAFE, value=0x4711, response_length=1) == 0xF896
    smbus2.i2c_msg.write.assert_called_once_with(0x62, b"\xca\xfe\x47\x11\xd4")

    # Read with invalid CRC
    smbus2.i2c_msg.write.reset_mock()
    smbus2.i2c_msg.read().__iter__.return_value = [0xF8, 0x96, 0x00]
    with pytest.raises(ValueError):
        sensor.rdwr(0xCAFE, response_length=1)


def test_reset(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.reset()
    sensor.rdwr.assert_called_once_with(scd4x.SOFT_RESET, delay=20)


def test_factory_reset(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.factory_reset()
    assert sensor.rdwr.call_args_list == [
        mock.call(scd4x.STOP_PERIODIC_MEASUREMENT, delay=500),
        mock.call(scd4x.FACTORY_RESET, delay=1200),
    ]


def test_self_test(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    # OK
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = 0
    sensor.self_test()
    assert sensor.rdwr.call_args_list == [
        mock.call(scd4x.STOP_PERIODIC_MEASUREMENT, delay=500),
        mock.call(scd4x.SELF_TEST, response_length=1, delay=10000),
    ]

    # Failure
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = 1
    with pytest.raises(RuntimeError):
        sensor.self_test()
    assert sensor.rdwr.call_args_list == [
        mock.call(scd4x.STOP_PERIODIC_MEASUREMENT, delay=500),
        mock.call(scd4x.SELF_TEST, response_length=1, delay=10000),
    ]


def test_measure(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    # OK
    start = time.time()
    sensor.rdwr.reset_mock(return_value=True, side_effect=True)
    sensor.rdwr.side_effect = (
        0x8000,  # No Data Ready
        0x8006,  # Data Ready
        [0x01F4, 0x6667, 0x5EB9],
    )
    co2, temperature, relative_humidity, timestamp = sensor.measure()
    end = time.time()
    assert co2 == 500
    assert round(temperature, 2) == 25.00
    assert round(relative_humidity, 2) == 37.00
    assert end > timestamp > start
    assert sensor.rdwr.call_args_list == [
        mock.call(scd4x.DATA_READY, response_length=1, delay=1),
        mock.call(scd4x.DATA_READY, response_length=1, delay=1),
        mock.call(scd4x.READ_MEASUREMENT, response_length=3, delay=1),
    ]

    # No Data, Non Blocking
    sensor.rdwr.reset_mock(return_value=True, side_effect=True)
    sensor.rdwr.side_effect = (0x8000,)  # No Data Ready
    assert sensor.measure(blocking=False) is None
    assert sensor.rdwr.call_args_list == [
        mock.call(scd4x.DATA_READY, response_length=1, delay=1),
    ]

    # No Data, Timeout
    sensor.rdwr.reset_mock(return_value=True, side_effect=True)
    sensor.rdwr.return_value = 0x8000  # No Data Ready
    start = time.monotonic()
    with pytest.raises(RuntimeError):
        sensor.measure(timeout=1)
    elapsed = time.monotonic() - start
    assert elapsed > 1
    assert (
        sensor.rdwr.call_args_list
        == [
            mock.call(scd4x.DATA_READY, response_length=1, delay=1),
        ]
        * 11
    )


def test_data_ready(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    # OK
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = 0x8006
    assert sensor.data_ready() is True
    sensor.rdwr.assert_called_once_with(scd4x.DATA_READY, response_length=1, delay=1)

    # Failure
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = 0x8000
    assert sensor.data_ready() is False
    sensor.rdwr.assert_called_once_with(scd4x.DATA_READY, response_length=1, delay=1)


def test_get_serial_number(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = [0xF896, 0x9F07, 0x3BBE]
    assert sensor.get_serial_number() == 0xF8969F073BBE
    sensor.rdwr.assert_called_once_with(scd4x.SERIAL_NUMBER, response_length=3, delay=1)


def test_start_periodic_measurement(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    # Normal
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.start_periodic_measurement()
    sensor.rdwr.assert_called_once_with(scd4x.START_PERIODIC_MEASUREMENT)

    # Low Power
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.start_periodic_measurement(low_power=True)
    sensor.rdwr.assert_called_once_with(scd4x.START_LOW_POWER_PERIODIC_MEASUREMENT)


def test_stop_periodic_measurement(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.stop_periodic_measurement()
    sensor.rdwr.assert_called_once_with(scd4x.STOP_PERIODIC_MEASUREMENT, delay=500)


def test_set_ambient_pressure(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.set_ambient_pressure(mock.sentinel.value)
    sensor.rdwr.assert_called_once_with(scd4x.SET_PRESSURE, value=mock.sentinel.value)


def test_set_temperature_offset(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.set_temperature_offset(5.4)
    sensor.rdwr.assert_called_once_with(scd4x.SET_TEMP_OFFSET, value=0x07E6)


def test_get_temperature_offset(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = 0x0912
    assert round(sensor.get_temperature_offset(), 2) == 6.2
    sensor.rdwr.assert_called_once_with(
        scd4x.GET_TEMP_OFFSET, response_length=1, delay=1
    )


def test_set_altitude(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.set_altitude(mock.sentinel.value)
    sensor.rdwr.assert_called_once_with(scd4x.SET_ALTITUDE, value=mock.sentinel.value)


def test_get_altitude(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = mock.sentinel.value
    assert sensor.get_altitude() == mock.sentinel.value
    sensor.rdwr.assert_called_once_with(scd4x.GET_ALTITUDE, response_length=1, delay=1)


def test_set_automatic_self_calibration_enabled(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    # Setting True
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.set_automatic_self_calibration_enabled(True)
    sensor.rdwr.assert_called_once_with(scd4x.SET_ASCE, value=1)

    # Setting False
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.set_automatic_self_calibration_enabled(False)
    sensor.rdwr.assert_called_once_with(scd4x.SET_ASCE, value=0)


def test_get_automatic_self_calibration_enabled(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    # Getting True
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = 1
    assert sensor.get_automatic_self_calibration_enabled() is True
    sensor.rdwr.assert_called_once_with(scd4x.GET_ASCE, response_length=1, delay=1)

    # Getting False
    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = 0
    assert sensor.get_automatic_self_calibration_enabled() is False
    sensor.rdwr.assert_called_once_with(scd4x.GET_ASCE, response_length=1, delay=1)


def test_persist_settings(smbus2, scd4x):
    scd4x.SCD4X.rdwr = mock.MagicMock()
    sensor = scd4x.SCD4X()

    sensor.rdwr.reset_mock()
    sensor.rdwr.return_value = []
    sensor.persist_settings()
    sensor.rdwr.assert_called_once_with(scd4x.PERSIST_SETTINGS, delay=800)
