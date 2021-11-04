# SCD4X C02 Sensor

[![Build Status](https://shields.io/github/workflow/status/pimoroni/scd4x-python/Python%20Tests.svg)](https://github.com/pimoroni/scd4x-python/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/scd4x-python/badge.svg?branch=master)](https://coveralls.io/github/pimoroni/scd4x-python?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/scd4x.svg)](https://pypi.python.org/pypi/scd4x)
[![Python Versions](https://img.shields.io/pypi/pyversions/scd4x.svg)](https://pypi.python.org/pypi/scd4x)

# Pre-requisites

You must enable:

* i2c: `sudo raspi-config nonint do_i2c 0`

You can optionally run `sudo raspi-config` or the graphical Raspberry Pi Configuration UI to enable interfaces.

# Installing

Stable library from PyPi:

* Just run `pip3 install scd4x`

In some cases you may need to use `sudo` or install pip with: `sudo apt install python3-pip`

Latest/development library from GitHub:

* `git clone https://github.com/pimoroni/scd4x-python`
* `cd scd4x-python`
* `sudo ./install.sh`


# Changelog
0.0.1
-----

* Initial Release
