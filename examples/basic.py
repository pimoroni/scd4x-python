#!/usr/bin/env python3
from datetime import datetime, timezone

from scd4x import SCD4X

device = SCD4X(quiet=False)
device.start_periodic_measurement()

try:
    while True:
        co2, temperature, relative_humidity, timestamp = device.measure()
        date = datetime.fromtimestamp(timestamp, timezone.utc)
        print(f"""
Time:        {date.strftime("%Y/%m/%d %H:%M:%S:%f %Z %z")}
CO2:         {co2:.2f}PPM
Temperature: {temperature:.4f}c
Humidity:    {relative_humidity:.2f}%RH""")
except KeyboardInterrupt:
    pass
