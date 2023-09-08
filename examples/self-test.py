#!/usr/bin/env python3
from scd4x import SCD4X

device = SCD4X(quiet=False)
device.self_test()

print("Self test successful!")
