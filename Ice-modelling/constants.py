#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'ragnarekker'

'''Setup work environment

@var :
@var :

'''



# Emissivities are dimensionless
eps_snow = 0.97
eps_ice = eps_snow
eps_water = eps_snow


# Boltzmann constants
sigma_day = 4.89*10**-6                         # pr day [kJ/m^2/day/K^4]
sigma_pr_second = (sigma_day/(24*60*60))        # pr second [kJ/m^2/s/K^4]


# Misc constants
temp_f = 0                      # [degC] freezing temp for fresh water
absolute_zero = -273.15         # [degC] 0K is -273.15C
von_karmans_const = 0.41        # [-] von Karmans constant
avg_wind_const = 1.5            # [m/s] if nothing else is given
pressure_atm = 101.1            # [kPa] if nothing else is given


# Thermal Conductivities
k_snow_max = 0.25               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
k_new_snow = 0.05               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
k_snow = 0.11                   # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
k_drained_snow = k_snow         #
k_slush = 0.561                 # from Vehvilainen (2008) and again Saloranta (2000)
k_black_ice = 2.24              # from Vehvilainen (2008) and again Saloranta (2000)
k_slush_ice = 0.5*k_black_ice   # from Vehvilainen (2008) and again Saloranta (2000)
k_water = 0.58                  # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html


# Densities [kg m^-3]
rho_snow_max = 450.             # maximum snow density (kg m-3)
rho_new_snow = 250.             # new-snow density (kg m-3)
rho_snow = 350.                 # average of max and min densities.
rho_drained_snow = rho_snow     #
rho_slush = 0.920*10**3         # from Vehvilainen (2008) and again Saloranta (2000)
rho_slush_ice = 0.875*10**3     # from Vehvilainen (2008) and again Saloranta (2000)
rho_black_ice = 0.917*10**3     # ice (incl. snow ice) density [kg m-3]
rho_water = 1000.               # density of freshwater (kg m-3)
rho_air = 1.29                  # kg/m3


# Latent heat of fusion [J kg-1]
L_black_ice = 333500            # latent heat of freezing water to black ice
L_slush_ice = 0.5*L_black_ice   # freezing slush to slush ice


# Specific heat capacities [kJ/kg/K]
c_air = 1.01                    # heat capacity of air
c_water = 4.19                  # heat capacity of water
c_snow = 2.102                  # heat capacity of snow from Dingman p. 189
c_ice = c_snow            # at 0C. http://www.engineeringtoolbox.com/ice-thermal-properties-d_576.html
c_slush = (c_water + c_ice)/2  # Assume slush is half/half water and ice


# Albedo in %
alfa_black_ice = 35             # from http://en.wikipedia.org/wiki/Albedo
alfa_snow_new = 85              # from http://en.wikipedia.org/wiki/Albedo
alfa_snow_old = 45              # from http://en.wikipedia.org/wiki/Albedo


# The melting coefficients for the degree-day formula [m s-1 degC-1]
meltingcoeff_snow = -0.10 /(60*60*24) / 5       # 10cm melting pr day at 5degC
meltingcoeff_slush_ice = -0.04 /(60*60*24) / 5  # 4cm melting pr day at 5degC
meltingcoeff_slush = meltingcoeff_slush_ice*2   # slush is partly melted
meltingcoeff_black_ice = -0.02 /(60*60*24) / 5  # 2cm melting pr day at 5degC


# Constants affecting how surface water interacts with snow on an ice cover
snow_pull_on_water = 0.05       # [m] The length water is pulled upp into the snow by capillary forces
min_slush_change = 0.05         # [m] If slush level change is lower than this value the no new slush level is made
snow_to_slush_ratio = 0.33      # [-] When snow becomes slush when water is pulled up it also is compressed






