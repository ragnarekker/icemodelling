__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import datetime
import types
import constants as const


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


#######    Works on single times teps

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

    :param temp:        temperature [float] from met-station or equal
    :param new_snow:    snowchange [float] on site where teperature i measured
    :return:            temperature [float] radiation-corrected based on snowevents
    """

    if new_snow == 0:
        temp_temp = temp - 2
    else:
        temp_temp = temp

    return temp_temp


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


def normal_time_from_unix_time(unixDatetime):
    """
    Takes in a date in unix datetime and returns a "normal date"

    :param unixDatetime:    Unix date time in milliseconds from 1.1.1970
    :return:                The date as datetime object

    Ex: date = unix_time_2_normal(int(p['DtObsTime'][6:-2]))
    """
    unixDatetimeInSeconds = unixDatetime/1000 # For some reason they are given in miliseconds
    dato = datetime.datetime.fromtimestamp(int(unixDatetimeInSeconds))

    return dato

####### Works on both


def clouds_from_precipitation(prec_inn, method='Binary'):
    '''Takes a list of precipitation and returns cloud cover.

    Method = Binary:    If precipitation the cloud cover is set to 100% and of no precipitation the cloud cover
                        is at a chosen lower threshold (now testing at 10%).

    Method = Average:   Calculates a (constant) average cloud cover of a period based on the number of
                        precipitation days in the period. It turns out this gave rms = 0.37 on a Semsvann study.

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


    # Again, if prec_inn isn't a list, return only a float.
    if not isinstance(prec_inn, types.ListType):
        clouds_out = clouds_out[0]


    return clouds_out



#######    Works on single timesteps (Energy balance)

def energy_balance_from_senorge():
    '''
    The daily energy budget of a column of snow is expressed as (Walter et al. 2005):

    λ_F * ρ_w * ΔSWE = S + L_a - L_t + H + LE + G + R - CC

    Where λ_F is the latent heat of fusion (λ_F=335 kJ〖kg〗^(-1))
    ρ_w [1000kgm^(-3)] is the density of water
    ΔSWE is the change in the snowpack’s water equivalent [m]


    :return:

    '''

def short_wave_from_senorge():
    '''
    S [kJm^(-2)]is the net incident solar (short wave) radiation
    :return:
    '''
    return

def long_wave_from_senorge(prec, temp_atm, temp_surface, snow_depth, ice_thickness, timespan_in_sec):
    '''
    Long wave radiation, both atmospheric and terrestrial, calculated from precipitation and temperature.

    We use the Stefan-Boltzmann equation: L = epsilon * sigma * temp^4
    where epsilon is emissivity and sigma is Stefan-Boltzmann constant.

    :param prec:                Precipitation (?)
    :param temp_atm:            Temperature (C)
    :param timespan_in_sec:     Time resolution gives the Boltzmann constant
    :param temp_surface:
    :param snow_depth:
    :return     L_a:            [kJm^(-2)] is the atmospheric long wave radiation
                L_t:            [kJm^(-2)] is the terrestrial long wave radiation
    '''

    cloud_cover = clouds_from_precipitation(prec, method='Binary')
    eps_atm = (0.72+0.005*temp_atm)*(1-0.84*cloud_cover)+0.84*cloud_cover    # Atmospheric emissivity from Campbell and Norman, 1998. Emissivity er dimasnjonsløs
    eps_surface = const.eps_snow                      # By default we assume snow cover
    sigma = const.sigma_pr_second * timespan_in_sec   # Stefan-Boltzmann constant over the requested time span

    if snow_depth == 0:
        eps_surface = const.eps_ice           # No snow gives ice emissivity

    if ice_thickness == 0:
        temp_surface == 0               # water at 0degC
        eps_surface = const.eps_water         # water emissivity is the same as snow emidsitivity

    L_a = eps_atm * sigma * (temp_atm + 273.2)^4            # temp_atm skal være i Celsisus. Atmosfærisk innstsåling
    L_t = eps_surface * sigma * (temp_surface + 273.2)^4    # terrestrisk utstråling emmisivity for snø er 0.97, er ogsÂ brukt for bar bakke, se Dingman p.583

    return L_a, L_t                     # Gir verdier av riktig størrelsesorden og balanserer hverandre sånn passe


def sensible_heat_from_senorge():
    '''
    H [kJm^(-2)] is the sensible heat exchange

    :return:
    '''
    return

def latent_heat_from_senorge():
    '''
    LE [kJm^(-2)] is the energy flux associated with the latent heats of vaporization and condensation at the surface

    :return:
    '''
    return

def ground_heat_conduction():
    '''
    G [kJm^(-2)] is ground heat conduction to the bottom of the snowpack
    '''
    return

def heat_by_precipitation_from_senorge():
    '''
    R [kJm^(-2)] is heat added by precipitation
    '''

    return

def change_in_snowpack_heat_storage():
    '''
    CC [kJm^(-2)] is the change of snowpack heat storage
    '''

    return

































