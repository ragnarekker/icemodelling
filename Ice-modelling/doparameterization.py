__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import datetime as dt
import types
import math
import constants as const
from doconversions import *
import random as random


#######    Works on arrays


def delta_snow_from_total_snow(snowTotal):
    ''' Method takes a list of total snow depth and returns the daily change (derivative).

    :param snowTotal:   a list of floats representing the total snow coverage of a location
    :return:            a list of floats representing the net accumulation (only positive numbers) for the timeseries

    '''

    snowChange = []
    snowChange.append(snowTotal[0])

    for i in range(1, len(snowTotal), 1):
        delta = (snowTotal[i]-snowTotal[i-1])
        if delta > 0:
            snowChange.append(delta)    # the model uses only change where it accumulates
        else:
            snowChange.append(0)

    return snowChange


def delta_temperature_from_temperature(temp):
    ''' Method makes an array of temp change from yesterday to today (derivative).

    :param temp:    [list of floats]    with the dayly avarage temperature
    :return:        [list of floats]    the change of temperature from yesterday to today

    '''

    dTemp = []
    previousTemp = temp[0]

    for t in temp:
        dTemp.append(t - previousTemp)
        previousTemp = t

    return dTemp


def clouds_average_from_precipitation(prec):
    '''Calculates a (constant) average cloud cover of a period based on the number of precipitation days in the period.
    It turns out this gave rms = 0.37 on a Semsvann study.

    :param clouds_inn:   [list of float]     Precipitation
    :return clouds_out:  [list of float]     Cloud cover

    '''

    clouds_inn = clouds_from_precipitation(prec)
    average = sum(clouds_inn)/float(len(clouds_inn))
    average = float("{0:.2f}".format(average))
    clouds_out = [average]*len(clouds_inn)

    return clouds_out


#######    Works on single times steps


def albedo_from_net_short_wave(SW_inn, SW_out):
    """
    SW_out = SW_inn * albedo

    :param SW_inn:      [float][kJ/m2]
    :param SW_out:      [float][kJ/m2]
    :return albedo:     [float][-]
    """

    albedo = SW_out/SW_inn

    return albedo


def surface_temp_from_long_wave(L_t, eps_surface=const.eps_snow, time_span_in_sec=24*60*60):
    """
    Tss = (L_t/(eps*sigma))^1/4 - 273.15

    :param L_t:                 [float] [kJ/m2/day] but other time period can be set.
    :param eps_surface:         Optional [float]
    :param time_span_in_sec:    Optional [int]

    :return temp_surface:       [degC]
    """

    temp_surface = ( L_t*time_span_in_sec / const.sigma_day/eps_surface )**(1/4) - const.absolute_zero

    return temp_surface


def temperature_from_temperature_and_clouds(temp, cloud_cover):
    '''
    This method takes shifts temperature according to cloud_cover. In theory clear nights will have a net
    out going global radiation from the surface. Here it is assumed:
    * a clear night adds to the energy balance with the equivalent of -2degC

    :param temp:        temperature [float] from met-station or equal
    :param cloud_cover:  cloud_cover as number from 0 to 1 [float] on site where temperature i measured
    :return temp:       temperature [float] radiation-corrected based on snowevents
    '''

    temp = temp + 2*(cloud_cover - 1)
    return temp


def temperature_from_temperature_and_snow(temp, new_snow):
    """
    This method is a special case of the temperature_from_temperature_and_clouds method.

    This method takes shifts temperature according to snow events. In theory clear nights will have a net
    global radialtion outgouing from the surface. Here it is assumed:
    * a clear night adds to the energybalace with the equivalent of -2degC
    * a snow event has a cloudcover CC = 100% and no new snow is assumed a clear night (CC = 0%)

    :param temp:        Temperature [float] from met-station or equal
    :param new_snow:    Snow change [float] on site where temperature i measured
    :return:            Temperature [float] radiation-corrected based on snow events
    """

    if new_snow == 0:
        temp_temp = temp - 2
    else:
        temp_temp = temp

    return temp_temp


def rho_new_snow(temp):
    """
    Method found in THS archives. Must investigate...

    Note, there is a different formula used in the albedo_walter() method:
    rho_snow = 50 + 3.4*(temp_atm + 15)

    :param temp:
    :return:

    """
    new_snow_density = 0.05
    temp = temp * 9.0/5.0 + 32.0      # Celsius to Fahrenhet

    if(temp > 0.):
        new_density = new_snow_density + (temp/100)**2
    else:
        new_density = new_snow_density

    return new_density


def k_snow_from_rho_snow(rho_snow):
    """
    The heat conductivity of the snow can be calculated from its density using the equation:

                                k_s = 2.85 * 10E-6 * ρ_s^2

    where minimum value of ρ_s is 100 kg/m3. This relation is found in [2008 Vehvilainen
    ice model]. Note all constans are given in SI values.

                                [k] = W K-1 m-1
                                [ρ] = kg m-3
                           konstant = W m5 K-1 kg-2

    :param rho_snow:    density of snow
    :return:            estimated conductivity of snow
    """

    rho_snow = max(100, rho_snow)
    konstant = 2.85*10**-6
    k_snow = konstant*rho_snow*rho_snow

    return k_snow


####### Works on both


def atmospheric_emissivity(temp_atm, cloud_cover, method="2005 WALTER"):
    """Its a start.. Incomplete

    :param temp_atm:
    :param cloud_cover:
    :return:
    """

    eps_atm_list = []

    if method=="1998 CAMPBELL":
        # Atmospheric emissivity from Campbell and Norman, 1998. Emissivity er dimasnjonsløs
        eps_atm = (0.72+0.005*temp_atm)*(1-0.84*cloud_cover)+0.84*cloud_cover

    if method=="2005 WALTER":
        # From THS og 2005 WALTER
        eps_atm = (1.0+0.0025*temp_atm)-(1-cloud_cover)*(0.25*(1.0+0.0025*temp_atm))


def clouds_from_precipitation(prec_inn, method='Binary'):
    '''Takes a list of precipitation and returns cloud cover.

    Method = Binary:    If precipitation the cloud cover is set to 100% and of no precipitation the cloud cover
                        is at a chosen lower threshold (now testing at 10%).

    Method = Average:   Calculates a (constant) average cloud cover of a period based on the number of
                        precipitation days in the period. It turns out this gave rms = 0.37 on a Semsvann study.

    Method = Binary and average: Method combines the above. If there is no rain one day, the average precipitation
                        in the period is used and if there is precipitation 100% cloud cover is used.

    :param prec_inn:        [list or single value]     Precipitation
    :return clouds_out:     [list or single value]     Cloud cover

    '''

    # If prec_inn isn't a list, make it so.
    if not isinstance(prec_inn, types.ListType):
        prec = [prec_inn]
    else:
        prec = prec_inn

    clouds = []
    clouds_out = []

    if method == 'Binary':
        for p in prec:
            if p == 0:
                # clouds.append(0.)
                clouds.append(0.1)      # THS suggests a lower threshold
            else:
                clouds.append(1.)
        clouds_out = clouds


    if method == 'Average':
        for p in prec:
            if p == 0:
                clouds.append(0.)
            else:
                clouds.append(1.)
        average = sum(clouds)/float(len(clouds))
        average = float("{0:.2f}".format(average))
        clouds_out = [average]*len(clouds)


    if method == 'Binary and average':
        clouds_out_1 = clouds_from_precipitation(prec, method='Binary')
        clouds_out_2 = clouds_from_precipitation(prec, method='Average')
        for i in range(0, len(clouds_out_1), 1):
            clouds_out.append(min(clouds_out_1[i]+clouds_out_2[i], 1))


    if method == 'Random Thomas':
        '''
        Mange takk, dette blir bra å  forske videre på. Jeg må tenke på andre snø ting nå, men dette er så
        langt jeg kom, kanskje det er bra nok! Da beregnes skyer slik:

        if(P >5)Cl <-1.0
        if(P>0.0&& P <=5) Cl <- runif(1,0.80,1.0)
        if(P==0) Cl<-runif(1,0.4,0.7)

        og emmisivitet slik:
        epsa <- (1.0+0.0025*Ta)-(1-Cl)*(0.25*(1.0+0.0025*Ta))

        Tilfeldigvis ble dette uttrykket ganske ryddig. Hvis helt skyfritt reduseres epsa med 25 %. Litt
        pussig at emmisiviteten kan bli over en (med Cl = 1.0),  på den annen side tillates aldri
        dettet i beregningen av skyer.

        '''
        for p in prec:
            if p > 5./1000:
                clouds.append(1.)
            elif 0. < p <= 5./1000:
                clouds.append(0.8+random.random()/5.)       # random numbers between 0.8 an 1.0
            if p == 0.:
                clouds.append(0.4+random.random()*3./10.)   # random numbers between 0.4 and 0.7


    # Again, if prec_inn isn't a list, return only a float.
    if not isinstance(prec_inn, types.ListType):
        clouds_out = clouds_out[0]

    return clouds_out


if __name__ == "__main__":

    # Test koordinater i tana
    x_tana = 988130
    y_tana = 7844353
    lat_tana, long_tana = lat_long_from_utm33(x_tana, y_tana)


    # Test Filefjell
    y_file = 6802070
    x_file = 130513
    lat_file, long_file = lat_long_from_utm33(x_file, y_file)



    a = 1











