#! /usr/bin/python
# -*- coding: utf-8 -*-
"""Describe the universe! All constants for modelling."""

__author__ = 'Ragnar Ekker'


# Misc constants
sigma_pr_second = 5.6704*10**-8  # Boltzmann constants pr second [J/s/m2/K4]
temp_f = 0.                     # [degC] freezing temp for fresh water
absolute_zero = -273.15         # [degC] 0K is -273.15C
temp_rain_snow = 0.5            # [degC] Threshold where precipitation falls as snow or rain.
von_karmans_const = 0.41        # [-] von Karmans constant
solar_constant = 1.3608 *10**3  # [J/s/m2] https://en.wikipedia.org/wiki/Solar_constant
g = 9.81                        # [m/s2] Acceleration of gravity


# Weather data if otherwise not given
avg_wind_const = 3.74           # [m/s] if nothing else is given. From TVEDALEN 2015
pressure_atm = 101.1            # [kPa] if nothing else is given.
rel_hum_air = 0.8349            # [-] if nothing else is given. From TVEDALEN 2015


# Thermal Conductivities [W/m/K]
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
L_fusion = 333.5 * 10**3        # latent heat of fusion
L_vapour = 2260. * 10**3        # latent heat of vapoour
L_0to100C = 41.8                # heat in warming 1kg water from 0 to 100 C
L_sublimation = L_fusion + L_vapour + L_0to100C  # Latent heat of sublimation


# Molecular wights
molecular_weight_dry_air = 28.966   # [g/mol]
molecular_weight_water = 18.016     # [g/mol]
molecular_weight_ratio = 0.622      # [-] The ratio of the molecular weights of water and dry air


# Specific heat capacities [J/kg/K]
c_air = 1.01 * 10**3            # heat capacity of air
c_water = 4.19 * 10**3          # heat capacity of water
c_snow = 2.102 * 10**3          # heat capacity of snow from Dingman p. 189
c_ice = c_snow                  # at 0C. http://www.engineeringtoolbox.com/ice-thermal-properties-d_576.html
c_slush = (c_water + c_ice)/2   # Assume slush is half/half water and ice


# Surface roughness as used to calculate turbulent fluxes.
# Surface roughness defined as height where wind field becomes zero
z_snow = 2*10**-3               # [m] surface roughness for snow
z_new_snow = z_snow             # [m] surface roughness for
z_drained_snow = z_snow         # [m] surface roughness for
z_black_ice = 10**-4            # [m] surface roughness for
z_slush_ice = z_black_ice       # [m] surface roughness for
z_water = z_black_ice           # [m] surface roughness for
z_slush = z_water               # [m] surface roughness for


# Albedo in values [0,1]
alfa_black_ice = 0.5            #
alfa_snow_new = 0.85            # from http://en.wikipedia.org/wiki/Albedo
alfa_snow_old = 0.45            #
alfa_slush_ice = 0.75           #
alfa_max = 0.95                 #
alfa_bare_ground = 0.25         # Generic albedo for snow less ground (Campell, 1977)


# Emissivities are dimensionless
eps_snow = 0.97                 #
eps_ice = eps_snow              #
eps_water = eps_snow            #


# The melting coefficients for the degree-day formula [m s-1 degC-1]
meltingcoeff_snow = -0.10 /(60*60*24) / 5       # 10cm melting pr day at 5degC
meltingcoeff_slush_ice = -0.04 /(60*60*24) / 5  # 4cm melting pr day at 5degC
meltingcoeff_slush = meltingcoeff_slush_ice*2   # slush is partly melted
meltingcoeff_black_ice = -0.02 /(60*60*24) / 5  # 2cm melting pr day at 5degC


# Conductance = thermal conductivity over height (k/h) [W/K/m2]
U_surface = k_snow/0.01          # surface conductance defined by the active part of column during 24hrs temperature oscylations


# On the energy used to freeze slush
part_ice_in_slush = 0.5         # How big part of sluh is frozen? This number is probably to low. Slush is probably 20-30% ice only?


# Constants affecting how surface water interacts with snow on an ice cover
snow_pull_on_water = 0.05       # [m] The length water is pulled upp into the snow by capillary forces
min_slush_change = 0.05         # [m] If slush level change is lower than this value the no new slush level is made
snow_to_slush_ratio = 0.33      # [-] When snow becomes slush when water is pulled up it also is compressed






