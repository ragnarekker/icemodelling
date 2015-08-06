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


# Desities [kg m-3]
rho_snow_max = 450.             # maximum snow density (kg m-3)
rho_new_snow = 250.             # new-snow density (kg m-3)
rho_snow = 350.                 # average snowdensity.
rho_drained_snow = rho_snow
rho_slush = 0.920*10**3         # from Vehvilainen (2008) and again Saloranta (2000)
rho_slush_ice = 0.875*10**3     # from Vehvilainen (2008) and again Saloranta (2000)
rho_black_ice = 0.917*10**3     # ice (incl. snow ice) density [kg m-3]
rho_water = 1000.               # density of freshwater (kg m-3)

# Material temperatures [degC]
temp_f = 0                      # freezing temp

# Latent heat of fusion [J kg-1]
L_black_ice = 333500                   # latent heat of freezing water to black ice
L_slush_ice = 0.5 * L_black_ice   # freezing slush to slushice