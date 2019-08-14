#!/usr/bin/env python3

import math

reactors = int(input("Reactors: "))

if not reactors % 2:
	megawatts = 160 * reactors - 160
	mwpr = 160 - 160 / reactors
else:
	megawatts = 160 * reactors - 200
	mwpr = 160 - 200 / reactors

turbines = math.ceil(megawatts / 5.82)
pumps = math.ceil(turbines / 20)

if not reactors % 2:
	heaters = 16 * reactors - 16
else:
	heaters = 16 * reactors - 20

print("{0:<17} {1}".format("MW (total):", megawatts))
print("{0:<17} {1}".format("MW (per reactor):", mwpr))
print("{0:<17} {1}".format("Heaters:", heaters))
print("{0:<17} {1}".format("Turbines:", turbines))
print("{0:<17} {1}".format("Offshore pumps:", pumps))
