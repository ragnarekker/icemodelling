__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-
# In this file methods for calulating/estimating physical parameters WITHIN THE CURRENT TIMESTEP

import datetime


#######    Works on arrays

def makeSnowChangeFromSnowTotal(snowTotal):
    '''
    Method takes a list of total snowdeapth and returns the dayly change (derivative).

    :param snowTotal:   a list of floats representing the total snowcoverage of a locaton
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


def makeTempChangeFromTemp(temp):
    '''
    Method makes an array of temp change from yesterday to today
    :param temp:    a list of floats with the dayly avarage temperature
    :return:        a list of the change of temperature from yesterday to today
    '''

    dTemp = []
    previousTemp = temp[0]
    for t in temp:
        dTemp.append(t - previousTemp)
        previousTemp = t

    return dTemp


# Needs coments
def ccFromPrec(prec):

    clouds = []

    for e in prec:
        if e == 0:
            clouds.append(0.)
        else:
            clouds.append(1.)

    return clouds


# needs comments
def ccFromAvaragePrecDays(prec):


    """
    Maade to test the precision og just unsin the avarage of precipitation days.
    Turns out it gave rms = 0.37

    :param cloudsInn:
    :return: cloudsOut
    """

    cloudsInn = ccFromPrec(prec)

    average = sum(cloudsInn)/float(len(cloudsInn))
    average = float("{0:.2f}".format(average))
    cloudsOut = [average]*len(cloudsInn)

    return cloudsOut


#######    Works on single timesteps

def tempFromTempAndClouds(temp, cloudcover):
    '''
    This method takes shifts temperature according to cloudcover. In theory clear nights will have a net
    global radialtion outgouing from the surface. Here it is assumed:
    * a clear night adds to the energybalace with the equivalent of -2degC

    :param temp:        temprature [float] from met-station or equal
    :param cloudcover:  cloudcover as number from 0 to 1 [float] on site where temperature i measured
    :return:            temperature [float] radiation-corrected based on snowevents
    '''

    temp = temp + 2*(cloudcover - 1)
    return temp


def tempFromTempAndSnow(temp, new_snow):
    """
    This method is a special case of the tempFromTempAndClouds method.

    This method takes shifts temperature according to snow events. In theory clear nights will have a net
    global radialtion outgouing from the surface. Here it is assumed:
    * a clear night adds to the energybalace with the equivalent of -2degC
    * a snow event has a cloudcover CC = 100% and no new snow is assumed a clear night (CC = 0%)

    :param temp:        temprature [float] from met-station or equal
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


def unixTime2Normal(unixDatetime):
    """
    Takes in a date in unix datetime and returns a "normal date"

    :param unixDatetime:    Unix date time in milliseconds from 1.1.1970
    :return:                The date as datetime object

    Ex: date = unix_time_2_normal(int(p['DtObsTime'][6:-2]))
    """
    unixDatetimeInSeconds = unixDatetime/1000 # For some reason they are given in miliseconds
    dato = datetime.datetime.fromtimestamp(int(unixDatetimeInSeconds))

    return dato

