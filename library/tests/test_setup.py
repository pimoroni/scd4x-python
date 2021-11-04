import pytest


def test_setup(smbus2, scd4x):
    smbus2.i2c_msg.read().__iter__.return_value = [1, 72, 241, 1, 72, 241, 1, 72, 241]

    sensor = scd4x.SCD4X()
    del sensor


def test_setup_invalid_crc8(smbus2, scd4x):
    smbus2.i2c_msg.read().__iter__.return_value = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    with pytest.raises(ValueError):
        sensor = scd4x.SCD4X()
        del sensor
