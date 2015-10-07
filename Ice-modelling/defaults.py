#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'ragnarekker'


# doenergybalance.py
# energy_balance_from_temp_sfc
default_cloud_cover_method = "Binary"

# temp_surface_from_eb
default_iteration_method = "Newton_Raphson"
default_iteration_error = 10.

# temp_surface_from_eb --> method == "Delta_T"
delta_t_eb_fraction = 10000.

# temp_surface_from_eb --> method == "Newton_Raphson"
init_d_t_eb_fraction = 50000.
d_t_eb_fraction = 10000.
num_iterations_cut_of = 50
d_temp_max = 10.
num_iterations_max = 20

# get_short_wave
default_albedo_method = "ueb"

# get_turbulent_flux
#default_turbulent_flux_method = "YOU 2014"
default_turbulent_flux_method = "MARTIN 1998"

