# -*- coding: utf-8 -*-
"""Methods for calculating what happens to the ice_column as external forcing is applied. That is, how does
weather affect an ice column. The inner workings of the ice column is part of the IceColumn class fount in ice.py."""

import math
import copy
import numpy as np
from icemodelling import parameterization as dp, constants as const
from experimental import energybalance as deb
from icemodelling import ice as ice
from utilities import makelogs as ml


__author__ = 'raek'


def calculate_ice_cover_air_temp(inn_column_inn, date, temp, dh_sno, cloud_cover=None, time_step=60*60*24):
    """

    :param inn_column_inn:  [IceThickness] Initial ice column for modelling.
    :param date:            [] dates for plotting
    :param temp:
    :param dh_sno:          [] new snow over the period (day)
    :param cloud_cover:
    :param time_step:       [int] fixed time step of 24hrs given in seconds
    :return:
    """

    inn_column = copy.deepcopy(inn_column_inn)
    inn_column.update_water_line()
    inn_column.remove_metadata()
    inn_column.remove_time()

    ice_cover = []

    if cloud_cover is None:
        cloud_cover = [None] * len(date)

    ice_cover.append(copy.deepcopy(inn_column))

    for i in range(0, len(date), 1):

        # if date is before the initial ice column, step forward
        if date[i] < inn_column.date:
            i += 1

        # else calculate ice evolution
        else:

            # Cloudless sky gives a lower surface temperature
            if cloud_cover[i] is not None:
                temp_surf = dp.temperature_from_temperature_and_clouds(temp[i], cloud_cover[i])
            else:
                temp_surf = temp[i]

            out_column = get_ice_thickness_from_surface_temp(inn_column, time_step, dh_sno[i], temp_surf)
            inn_column = copy.deepcopy(out_column)
            ice_cover.append(out_column)

    return ice_cover


def calculate_ice_cover_eb(
        utm33_x, utm33_y, date, temp_atm, prec, prec_snow, cloud_cover, wind, rel_hum, pressure_atm, inn_column=None):
    """

    :param utm33_x:
    :param utm33_y:
    :param date:
    :param temp_atm:
    :param prec:
    :param prec_snow:
    :param cloud_cover:
    :param wind:
    :param inn_column:
    :return:
    """

    if inn_column is None:
        inn_column = ice.IceColumn(date[0], [])

    icecover = []
    time_span_in_sec = 60*60*24     # fixed timestep of 24hrs given in seconds
    inn_column.remove_metadata()
    inn_column.remove_time()
    icecover.append(copy.deepcopy(inn_column))
    energy_balance = []

    age_factor_tau = 0.
    albedo_prim = const.alfa_black_ice

    for i in range(0, len(date), 1):
        print("{0}".format(date[i]))
        if date[i] < inn_column.date:
            i = i + 1
        else:
            out_column, eb = get_ice_thickness_from_energy_balance(
                utm33_x=utm33_x, utm33_y=utm33_y, ice_column=inn_column, temp_atm=temp_atm[i],
                prec=prec[i], prec_snow=prec_snow[i], time_span_in_sec=time_span_in_sec,
                albedo_prim=albedo_prim, age_factor_tau=age_factor_tau, wind=wind[i], cloud_cover=cloud_cover[i],
                rel_hum=rel_hum[i], pressure_atm=pressure_atm[i])

            icecover.append(out_column)
            energy_balance.append(eb)
            inn_column = copy.deepcopy(out_column)

            if eb.EB is None:
                age_factor_tau = 0.
                albedo_prim = const.alfa_black_ice
            else:
                age_factor_tau = eb.age_factor_tau
                albedo_prim = eb.albedo_prim

    return icecover, energy_balance


def get_ice_thickness_from_surface_temp(ic, time_step, dh_snow, temp, melt_energy=None):
    """Given surface temperature and new snow on an ice-column, ice evolution is estimated. In the simplest case
    the surface temp is estimated from air temperature. More advances approaches calculates surface temperature
    by solving er energy balance equation.

    :param ic:          Ice column at the beginning of the time step. Object containing the ice column with metadata
    :param dh_snow:     New snow in period of time step. Given as float in SI units [m]
    :param temp:        Average temperature in period of time step. Given i C as float.
    :param time_step:   In seconds. 60*60*24 = 86400 is 24hrs
    :return:            Ice column at end of time step
    """

    dh_snow = float(dh_snow)

    # step the date forward one time step. We do it initially because the variable is also used and subtracted in the following calculations.
    ic.time_step_forward(time_step)

    # Add new snow on top of the column if we have ice and snow
    # and update the slush level/buoyancy given new snow
    if len(ic.column) != 0:
        if dh_snow != 0.:
            ic.add_layer_at_index(0, ice.IceLayer(dh_snow, 'new_snow'))
        ic.update_slush_level()

    # if surface or air temperature is FREEZING
    if temp < const.temp_f:

        # If no ice, freeze water to ice
        if len(ic.column) == 0:
            # The heat flux equation gives how much water will freeze. U_total for the equation is estimated.
            U_total = ice.add_layer_conductance_to_total(None, const.k_black_ice, 0, 10)
            dh = - temp * U_total * time_step / const.rho_water / const.L_fusion
            ic.add_layer_at_index(0, ice.IceLayer(dh, 'black_ice'))
            pass

        else:
            # Declaration of total conductance of layers above freezing layer
            U_total = None
            i = 0
            while time_step > 0 and i <= len(ic.column)-1:

                # If the layer is a solid, it only adds to the total isolation. Unless it is the last and water is frozen to ice.
                if (ic.column[i].get_enum()) > 9:
                    U_total = ice.add_layer_conductance_to_total(U_total, ic.column[i].conductivity, ic.column[i].height, ic.column[i].get_enum())

                    # If the layer is the last layer of solids and thus at the bottom, we get freezing at the bottom
                    if i == len(ic.column)-1:

                        # The heat flux equation gives how much water will freeze
                        dh = - temp * U_total * time_step / const.rho_water / const.L_fusion
                        ic.add_layer_at_index(i+1, ice.IceLayer(dh, 'black_ice'))
                        time_step = 0

                # Else the layer is a slush layer above or in the ice column and it will freeze fully or partially
                else:
                    # time_step_used = 0
                    L_slush_ice = const.part_ice_in_slush*const.L_fusion
                    if i == 0:    # there is slush surface with no layers with conductance above
                        dh = math.sqrt(np.absolute(2 * const.k_slush_ice / const.rho_slush_ice / L_slush_ice * temp * time_step))    # formula X?
                        time_step_used = ic.column[i].height**2 * const.rho_slush_ice * L_slush_ice / 2 / -temp / const.k_slush_ice  # formula X sorted for time
                    else:
                        dh = - temp * U_total * time_step / ic.column[i].density / L_slush_ice                       # The heat flux equation gives how much slush will freeze
                        time_step_used = ic.column[i].height * const.rho_slush_ice * L_slush_ice / -temp / U_total   # The heat flux equation sorted for time

                    # If a layer totaly freezes during the timeperiod, the rest of the time will be used to freeze a layer further down
                    if ic.column[i].height < dh:
                        ic.column[i].type = 'slush_ice'
                        time_step = time_step - time_step_used
                        U_total = ice.add_layer_conductance_to_total(U_total, ic.column[i].conductivity, ic.column[i].height, ic.column[i].get_enum())

                    # Else all energy is used to freeze the layer only partially
                    else:
                        ic.column[i].height = ic.column[i].height - dh
                        ic.add_layer_at_index(i, ice.IceLayer(dh, 'slush_ice'))
                        time_step = 0

                # Go to next ice layer
                i += 1

    # if surface or air temperature is MELTING
    else:
        # In case surface temperatures are above 0C (when air temp is used to calculate ice evolution) there
        # should not be submitted a energy term from the energy balance calculations (melt_energy = None).
        if temp > 0.:
            # all melting is made by simple degree day model using different calibration constants for snow,
            # slush ice and black ice melting only effects the top layer (index = 0)
            while time_step > 0 and len(ic.column) > 0:
                if ic.column[0].type == 'water':
                    ic.remove_layer_at_index(0)
                else:
                    if ic.column[0].get_enum() >= 20: # snow
                        meltingcoeff = const.meltingcoeff_snow
                    elif ic.column[0].type == 'slush_ice':
                        meltingcoeff = const.meltingcoeff_slush_ice
                    elif ic.column[0].type == 'slush':
                        meltingcoeff = const.meltingcoeff_slush
                    elif ic.column[0].type == 'black_ice':
                        meltingcoeff = const.meltingcoeff_black_ice
                    else:
                        ml.log_and_print("[info] icethickness.py -> get_ice_thickness_from_surface_temp: Melting on unknown layer type: {0}. Using slush_ice coeff.".format(ic.column[0].type))
                        meltingcoeff = const.meltingcoeff_slush_ice

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

        # In case surface temp is calculated from energy balance, surface temp is never above 0C, but if we have
        # melting and thus melt_energy is not None and temp == 0.
        elif melt_energy is not None:
            while time_step > 0 and len(ic.column) > 0:
                if ic.column[0].type == 'water':
                    ic.remove_layer_at_index(0)
                else:
                    # energy available to melt used with latent heat of fusion (delta_h = Q/L/rho)
                    L_ice = const.L_fusion/1000.    # Joule to Kilo Joule
                    dh = melt_energy / L_ice / ic.column[0].density * time_step/24/60/60

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

        else:
            ml.log_and_print("[info] icethickness.py -> get_ice_thickness_from_surface_temp: Need either energy or positive temperatures in model to melt snow and ice.")

    ic.merge_and_remove_excess_layers()
    ic.merge_snow_layers_and_compress(temp)
    ic.update_draft_thickness()
    ic.update_water_line()
    ic.update_column_temperatures(temp)
    ic.update_total_column_height()
    ic.set_surface_temperature(temp)

    return ic


def get_ice_thickness_from_energy_balance(
        utm33_x, utm33_y, ice_column, temp_atm, prec, prec_snow, time_span_in_sec,
        albedo_prim=None, age_factor_tau=None, cloud_cover=None, wind=None, rel_hum=None, pressure_atm=None):
    """

    :param utm33_x:
    :param utm33_y:
    :param ice_column:
    :param temp_atm:
    :param prec:
    :param prec_snow:
    :param albedo_prim:
    :param time_span_in_sec:
    :param age_factor_tau:
    :param cloud_cover:
    :param wind:
    :param pressure_atm:
    :return:
    """

    out_column = None
    energy_balance = None

    # No ice?, dont do EB and use air temp as surface temp
    if len(ice_column.column) == 0:
        energy_balance = deb.EnergyBalanceElement(ice_column.date)
        energy_balance.add_no_energy_balance(is_ice_inn=False)
        out_column = get_ice_thickness_from_surface_temp(ice_column, time_span_in_sec, prec_snow, temp_atm)
    else:
        energy_balance = deb.temp_surface_from_eb(
            utm33_x, utm33_y, ice_column, temp_atm, prec, prec_snow, albedo_prim, time_span_in_sec,
            age_factor_tau=age_factor_tau,
            cloud_cover=cloud_cover, wind=wind, rel_hum=rel_hum, pressure_atm=pressure_atm)

        surface_temp = energy_balance.temp_surface
        out_column = None

        if surface_temp < 0.:
            out_column = get_ice_thickness_from_surface_temp(
                ice_column, time_span_in_sec, prec_snow, surface_temp)
        elif surface_temp == 0.:
            melt_energy = energy_balance.SM
            out_column = get_ice_thickness_from_surface_temp(
                ice_column, time_span_in_sec, prec_snow, surface_temp, melt_energy=melt_energy)
        else:
            print("doicethicckness --> get_ice_thickness_from_energy_balance: Surface temp cant be above 0C in the method get_ice_thickness_from_energy_balance")

    return out_column, energy_balance
