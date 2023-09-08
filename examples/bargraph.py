#!/usr/bin/env python3
import sys

from scd4x import SCD4X

BAR_CHAR = u'\u2588'

ANSI_COLOR_RED = '\x1b[31m'
ANSI_COLOR_GREEN = '\x1b[32m'
ANSI_COLOR_YELLOW = '\x1b[33m'
ANSI_COLOR_BLUE = '\x1b[34m'
ANSI_COLOR_MAGENTA = '\x1b[35m'
ANSI_COLOR_BLACK = '\x1b[30m'
ANSI_COLOR_RESET = '\x1b[0m'


colours = [ANSI_COLOR_BLUE, ANSI_COLOR_GREEN, ANSI_COLOR_YELLOW, ANSI_COLOR_RED, ANSI_COLOR_MAGENTA]

BAR_WIDTH = 80

min_co2 = 1 << 32
max_co2 = 0

min_temperature = 1 << 32
max_temperature = 0

device = SCD4X()
device.start_periodic_measurement()

try:
    while True:
        co2, temperature, relative_humidity, timestamp = device.measure()

        min_co2 = min(co2 - 100, min_co2)
        max_co2 = max(co2 + 100, max_co2)
        min_temperature = min(temperature - 5, min_temperature)
        max_temperature = max(temperature + 5, max_temperature)

        if max_co2 - min_co2 == 0 or max_temperature - min_temperature == 0:
            continue

        t_scale = min((temperature - min_temperature) / (max_temperature - min_temperature), 1.0)
        p_scale = min((co2 - min_co2) / (max_co2 - min_co2), 1.0)
        t_colour = colours[int((len(colours) - 1) * t_scale)]
        p_colour = colours[int((len(colours) - 1) * p_scale)]
        t_bar = BAR_CHAR * int(BAR_WIDTH * t_scale)
        c_bar = BAR_CHAR * int(BAR_WIDTH * p_scale)

        t_bar += ANSI_COLOR_BLACK + (BAR_CHAR * (BAR_WIDTH - len(t_bar)))
        c_bar += ANSI_COLOR_BLACK + (BAR_CHAR * (BAR_WIDTH - len(c_bar)))

        t_bar = t_colour + t_bar + ANSI_COLOR_RESET
        c_bar = p_colour + c_bar + ANSI_COLOR_RESET

        t_reading = "{:.4f}c".format(temperature).ljust(BAR_WIDTH + 14)
        c_reading = "{:.0f}PPM".format(co2).ljust(BAR_WIDTH + 14)

        sys.stdout.write('\x1b[0;1H')
        sys.stdout.write(u"""{title}
{blank}
Temperature: {t_bar}
{t_reading}
CO2:         {c_bar}
{c_reading}
{blank}
""".format(
            title="SCD4X Sensor".ljust(BAR_WIDTH + 14, " "),
            t_bar=t_bar,
            c_bar=c_bar,
            t_reading=t_reading,
            c_reading=c_reading,
            blank=" " * (BAR_WIDTH + 14)
        ))
        sys.stdout.flush()

except KeyboardInterrupt:
    pass
