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
sigma_day       = 4.89*10^-6                # [kJ/m^2/day/K^4]
sigma_pr_second = (sigma_day/(24*60*60))    # [kJ/m^2/s/K^4]