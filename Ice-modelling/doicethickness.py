__author__  =  'raek'
# -*- coding: utf-8 -*-

import math
import numpy as np
import doparameterization as dp
import doenergybalance as deb
import ice as ice
import constants as const


def get_ice_thickness_from_energy_balance(utm33_x, utm33_y, ice_column,
                                          temp_atm, prec, prec_snow, prec_rain,  albedo_prim,
                                          time_span_in_sec,
                                          age_factor_tau=None, cloud_cover=None, wind=None,  pressure_atm=None):

    out_column = get_ice_thickness_from_conductivity(ice_column, time_span_in_sec, prec_snow, temp_atm, cloud_cover)

    energy_balance = deb.energy_balance_from_temp_sfc(utm33_x, utm33_y, ice_column, temp_atm, prec, prec_snow, prec_rain,
                                                         albedo_prim, time_span_in_sec, age_factor_tau=age_factor_tau,
                                                         cloud_cover=cloud_cover, wind=wind, pressure_atm=pressure_atm)

    return out_column, energy_balance

def get_ice_thickness_from_conductivity(ic, time_step, dh_snow, temp, cloud_cover=None):

    '''
    :param ic:          Ice column at the beginning of the time step. Object containing the ice column with metadata
    :param dh_snow:     New snow in period of time step. Given as float in SI units [m]
    :param temp:        Average temperature in period of time step. Given i C as float.
    :param time_step:   In seconds. 60*60*24 = 86400 is 24hrs
    :return:            Ice column at end of time step
    '''

    # temp = dp.temperature_from_temperature_and_snow(temp, dh_snow)
    if cloud_cover != None:
        temp = dp.temperature_from_temperature_and_clouds(temp, cloud_cover)

     # step the date forward on time step. We do it initially because the variable is also used and subtracted
     # in the following calculations.
    ic.time_step_forward(time_step)

    # add new snow on top if we have ice and snow
    if len(ic.column) != 0:

        if dh_snow != 0.:
            ic.add_layer_at_index(0, ice.IceLayer(dh_snow, 'new_snow'))

        # Update the slush level/buoyancy given new snow
        ic.update_slush_level()

    # if air temperature is FREEZING
    if temp < const.temp_f:

        # If no ice, freeze water to ice
        if len(ic.column) == 0:
            dh = math.sqrt(np.absolute(2 * const.k_black_ice / const.rho_black_ice / const.L_black_ice * temp * time_step))
            ic.add_layer_at_index(0, ice.IceLayer(dh, 'black_ice'))
            time_step = 0
        else:

            # Declaration of total conductance of layers above freezing layer
            U_total = 0.
            i = 0
            while time_step > 0 and i <= len(ic.column)-1:

                # If the layer is a solid it only adds to the total isolation. Unless it is the last..
                if (ic.column[i].enum()) > 9:
                    U_total = addLayerConductanceToTotal(U_total, ic.column[i].conductivity, ic.column[i].height)

                    # If the layer is the last layer of solids and thus at the bottom, we get freezing at the bottom
                    if i == len(ic.column)-1:

                        # The heat flux equation gives how much water will freeze
                        dh = - temp * U_total * time_step / const.rho_water / const.L_black_ice
                        ic.add_layer_at_index(i+1, ice.IceLayer(dh, 'black_ice'))
                        time_step = 0

                # Else the layer is a slush layer above or in the ice column and it will freeze fully or partially
                else:
                    time_step_used = 0
                    if i == 0: # there is slush surface with no layers with conductance above
                        dh = math.sqrt(np.absolute(2 * const.k_slush_ice / const.rho_slush_ice / const.L_slush_ice * temp * time_step))    # formula X?
                        time_step_used = ic.column[i].height**2 * const.rho_slush_ice * const.L_slush_ice / 2 / -temp / const.k_slush_ice             # formula X sortet for time
                    else:
                        dh = - temp * U_total * time_step / ic.column[i].density / const.L_slush_ice                              # The heat flux equation gives how much slush will freeze
                        time_step_used = ic.column[i].height * const.rho_slush_ice * const.L_slush_ice / -temp / U_total                       # The heat flux equation sorted for time

                    # If a layer totaly freezes during the timeperiod, the rest of the time will be used to freeze a layer further down
                    if ic.column[i].height < dh:
                        ic.column[i].type = 'slush_ice'
                        time_step = time_step - time_step_used
                        U_total = addLayerConductanceToTotal(U_total, ic.column[i].conductivity, ic.column[i].height)

                    # Else all energy is used to freeze the layer only partially
                    else:
                        ic.column[i].height = ic.column[i].height - dh
                        ic.add_layer_at_index(i, ice.IceLayer(dh, 'slush_ice'))
                        time_step = 0

                # Go to next ice layer
                i += 1


    # if air temperature is MELTING
    else:
    # all melting is made by simple degree day model using different calibration constants for snow, slushice and blackice
    # melting only effects the top layer (index = 0)
        meltingcoeff = -1
        while time_step > 0 and len(ic.column) > 0:
            if ic.column[0].type == 'water':
                ic.remove_layer_at_index(0)
            else:
                if ic.column[0].enum() >= 20: # snow
                    meltingcoeff = const.meltingcoeff_snow
                elif ic.column[0].type == 'slush_ice':
                    meltingcoeff = const.meltingcoeff_slush_ice
                elif ic.column[0].type == 'slush':
                    meltingcoeff = const.meltingcoeff_slush
                elif ic.column[0].type == 'black_ice':
                    meltingcoeff = const.meltingcoeff_black_ice
                else:
                    print("Melting: Unknown layer type.")

                # degree day melting. I have separated the time factor from the melting coefficiant.
                dh = meltingcoeff * time_step * (temp - const.temp_f)

                # if layer is thinner than total melting the layer is removed and the rest of melting occurs
                # in the layer below for the reminder of time. melting (dh) and time are proportional in the degreeday equation
                if ic.column[0].height < -dh:
                    time_step_used = ic.column[0].height / -dh * time_step
                    ic.remove_layer_at_index(0)
                    time_step = time_step - time_step_used

                # the layer is only partly melted during this time_step
                else:
                    ic.column[0].height = ic.column[0].height + dh
                    time_step = 0

    ic.merge_and_remove_excess_layers()
    ic.merge_snow_layers_and_compress(temp)
    ic.update_draft_thickness()
    ic.update_water_line()
    ic.update_column_average_temperature(temp)
    ic.update_column_temperatures(temp)

    return ic


def addLayerConductanceToTotal(U_total, k, h):
    # Adds a layers conductance to a total conductance
    # Conductance is conductivity pr unit lenght. I.e. U = k/h where k is conductivity and h is height of icelayer
    # Sum of conductance follows the rule 1/U = 1/U1 + 1/U2 + ... + 1/Un
    if U_total == 0.:
        U_total = k/h
    else:
        U_total = 1/(1/U_total+h/k)
    return U_total

