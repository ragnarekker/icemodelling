#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'ragnarekker'

'''Setup work environment

@var :
@var :

'''

# Emissivities
eps_snow        = 0.97
eps_ice         = eps_snow
eps_water       = eps_snow

# Boltzmans constant pr day and second.
sigma_day       = 4.89*10**-6                # [kJ/m^2/day/K^4]
sigma_pr_second = (sigma_day/(24*60*60))    # [kJ/m^2/s/K^4]

# Thermal Conductivities
k_snow_max = 0.25               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
k_new_snow = 0.05               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
k_snow = 0.11                   # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
k_drained_snow = k_snow
k_slush = 0.561                 # from Vehvilainen (2008) and again Saloranta (2000)
k_black_ice = 2.24              # from Vehvilainen (2008) and again Saloranta (2000)
k_slush_ice = 0.5 * k_black_ice # from Vehvilainen (2008) and again Saloranta (2000)
k_water = 0.58                  # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html