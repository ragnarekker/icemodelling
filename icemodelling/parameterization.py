# -*- coding: utf-8 -*-

import datetime as dt
import math
from icemodelling import constants as const, weatherelement as we
from utilities import doconversions as dc, getwsklima as gws
import random as random


__author__ = 'ragnarekker'


#######    Methods for arrays


def delta_snow_from_total_snow(snowTotal):
    """ Method takes a list of total snow depth and returns the daily change (derivative).

    :param snowTotal:   a list of floats representing the total snow coverage of a location
    :return:            a list of floats representing the net accumulation (only positive numbers) for the timeseries

    """

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
    """ Method makes an array of temp change from yesterday to today (derivative).

    :param temp:    [list of floats]    with the dayly avarage temperature
    :return:        [list of floats]    the change of temperature from yesterday to today

    """

    dTemp = []
    previousTemp = temp[0]

    for t in temp:
        dTemp.append(t - previousTemp)
        previousTemp = t

    return dTemp


def clouds_average_from_precipitation(prec):
    """Calculates a (constant) average cloud cover of a period based on the number of precipitation days in the period.
    It turns out this gave rms = 0.37 on a Semsvann study.

    :param clouds_inn:   [list of float]     Precipitation
    :return clouds_out:  [list of float]     Cloud cover

    """

    clouds_inn = clouds_from_precipitation(prec)
    average = sum(clouds_inn)/float(len(clouds_inn))
    average = float("{0:.2f}".format(average))
    clouds_out = [average]*len(clouds_inn)

    return clouds_out


#######    Methods for single times steps


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
    """
    This method takes shifts temperature according to cloud_cover. In theory clear nights will have a net
    out going global radiation from the surface. Here it is assumed:
    * a clear night adds to the energy balance with the equivalent of -2degC

    :param temp:        temperature [float] from met-station or equal
    :param cloud_cover:  cloud_cover as number from 0 to 1 [float] on site where temperature i measured
    :return temp:       temperature [float] radiation-corrected based on snowevents
    """

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

# untested
def irradiance_clear_sky(utm33_x, utm33_y, date_inn, time_span_in_sec=24*60*60):
    """Clear sky irradiance in J/m2/s * time_span_in_sec.

    :param utm33_x, utm33_y:    koordinat i UTM 33
    :param date_inn:            [datetime]
    :param time_span_in_sec:    [sec] Time resolution in sec

    :return I_clear_sky:        [J/m2] Energy over the time span we are looking at.
    """

    day_no = date_inn.timetuple().tm_yday
    # time given as the end of the time span
    time_hour = (date_inn + dt.timedelta(seconds=time_span_in_sec)).hour

    if time_hour == 0:
        time_hour = 24

    phi, thi, ddphi, ddthi = dc.lat_long_from_utm33(utm33_x,utm33_y, output= "both")

    theta = 0.4092*math.cos((2*math.pi/365.25)*(day_no-173))  # solar declination angleday angle, Liston 1995
    theta2 = 2*math.pi/365.25*(day_no-80)

    r = 149598000   # distance from the sun
    R = 6378        # Radius of earth

    timezone = -4 * (math.fabs(thi) % 15) * thi/math.fabs(thi)      # ang lengdegrad ikke
    epsilon = 0.4092    # rad(23.45)

    z_s = r*math.sin(theta2)*math.sin(epsilon)
    r_p = math.sqrt(r**2-z_s**2)
    nevner = (R-z_s*math.sin(phi))/(r_p*math.cos(phi))

    if(nevner > -1) and (nevner < 1):
        # acos(mÂ ha inn verdier ,(mellom-1,1) hvis <-1 sÂ er det midnattsol > 1 er det m¯rketid.
        t0 = 1440/(2*math.pi)*math.acos((R-z_s*math.sin(phi))/(r_p*math.cos(phi)))
        that = t0+5
        n = 720-10*math.sin(4*math.pi*(day_no-80)/365.25)+8*math.sin(2*math.pi*day_no/365.25)
        sr = (n-that+timezone)/60 #soloppgang
        ss = (n+that+timezone)/60 #solnedgang

    if nevner <= -1:    # Midnattsol
        sr = 0.
        ss = 24.

    if nevner >= 1:     # Mørketid
        sr = 12.
        ss = 12.

    dingom = {}         # Values for zenith angle (0 straight up)

    for tid in range(1, 24, 1):
        if (tid > sr) and (tid < ss):
            tom = tid-12    # Number of hours from solar noon. Solar noon is tom=0
            cosarg = 0.2618 * tom   # Radians pr hour
            dingom[tid] = math.acos(math.sin(phi)*math.sin(theta)+math.cos(phi)*math.cos(theta)*math.cos(cosarg))  # Dingmans zenith angle

        if (tid < sr) or (tid > ss):  # If time is outside sunrise-sunset
            dingom[tid] = math.pi/2     # Angle below horizin is set to be on the horizon.

    if time_span_in_sec == 86400:
        zenith_angle = dingom.values()          # list
    elif time_span_in_sec < 86400:              # Midler transmissvitet og solvinkel For finere tidssoppløsning
        interv = list(range(time_hour-int(time_span_in_sec/3600)+1, time_hour, 1))     # aktuelle timer
        zenith_angle = [dingom[i] for i in interv]
    else:
        print("Method doesnt work on time intervals greater than 24hrs")
        zenith_angle = None

    # Mean values
    zenith_angle = float( sum(zenith_angle) / len(zenith_angle) )

    #Solar radiation
    S0 = const.solar_constant   #[J/m2/s] Solar constant pr sec
    S0 *= time_span_in_sec      # solar constant pr time step
    S0 /=1000                   # J to kJ

    I_clear_sky = math.sin((math.pi/2)-zenith_angle) * S0

    return I_clear_sky


####### Works on both

# untested
def clouds_from_short_wave(utm33_x, utm33_y, short_wave_inn, date_inn, time_span_in_sec=24*60*60):
    """Clouds defined by: clouds = 1 - measured solar irradiance / clear-sky irradiance

    :param utm33_x:             []
    :param utm33_y:
    :param short_wave_inn:      [float] in J/m2/time_step
    :param date_inn:
    :param time_span_in_sec:    [int] Is necessary if used on non-list calculations and not on daily values.
    :return cloud_cover_out:
    """

    # If resources isn't list, make it so
    input_is_list = False
    if isinstance(short_wave_inn, list):
        input_is_list = True

    if input_is_list:
        short_wave_list = short_wave_inn
        date_list = date_inn
        time_span_in_sec = (date_list[1] - date_list[0]).total_seconds()
    else:
        short_wave_list = [short_wave_inn]
        date_list = [date_inn]


    cloud_cover_list = []
    for i in range(0, len(short_wave_list), 1):

        I_clear_sky = irradiance_clear_sky(utm33_x, utm33_y, date_list[i], time_span_in_sec)
        I_measured = short_wave_list[i]

        cloud_cover = 1 - I_measured/I_clear_sky
        cloud_cover_list.append(cloud_cover)


    # If resources aren't lists, return only float.
    if input_is_list:
        cloud_cover_out = cloud_cover_list
    else:
        cloud_cover_out = cloud_cover_list[0]

    return cloud_cover_out

# untested
def atmospheric_emissivity(temp_atm_inn, cloud_cover_inn, method="2005 WALTER"):
    """Its a start.. Incomplete

    :param temp_atm:
    :param cloud_cover:
    :return:
    """

    # If resources aren't lists, make them so
    if not isinstance(temp_atm_inn, list):
        temp_atm_list = [temp_atm_inn]
        cloud_cover_list = [cloud_cover_inn]
    else:
        temp_atm_list = temp_atm_inn
        cloud_cover_list = cloud_cover_inn

    eps_atm_list = []

    for i in range(0, len(temp_atm_list), 1):
        temp_atm = temp_atm_list[i]
        cloud_cover = cloud_cover_list[i]

        if method=="1998 CAMPBELL":
            # Atmospheric emissivity from Campbell and Norman, 1998. Emissivity er dimasnjonsløs
            eps_atm = (0.72+0.005*temp_atm)*(1-0.84*cloud_cover)+0.84*cloud_cover
        elif method=="2005 WALTER":
            # From THS og 2005 WALTER
            eps_atm = (1.0+0.0025*temp_atm)-(1-cloud_cover)*(0.25*(1.0+0.0025*temp_atm))
        elif method=="1963 SWINBANK":
            # From 1998 TODD eq 13
            eps_atm = cloud_cover + (1-cloud_cover) * (9.36 * 10**-6 * temp_atm**2)
        elif method=="1969 Idso and Jackson":
            # From 1998 TODD eq 14
            eps_atm = (cloud_cover + (1-cloud_cover) * (1 - (0.261 * math.exp(-7.77 * 10**-4) * (273.15 - temp_atm)**2 )))
        else:
            eps_atm = None
            print('parameterization.py --> atmospheric_emissivity: Unknown method.')

        eps_atm_list.append(eps_atm)

    # Again, if resources aren't lists, return only float.
    if not isinstance(temp_atm_inn, list):
        eps_atm_out = eps_atm_list[0]
    else:
        eps_atm_out = eps_atm_list

    return eps_atm_out


def clouds_from_precipitation(prec_inn, method='Binary'):
    """Takes a list of precipitation and returns cloud cover.

    Method = Binary:    If precipitation the cloud cover is set to 100% and of no precipitation the cloud cover
                        is at a chosen lower threshold (now testing at 10%).

    Method = Average:   Calculates a (constant) average cloud cover of a period based on the number of
                        precipitation days in the period. It turns out this gave rms = 0.37 on a Semsvann study.

    Method = Binary and average: Method combines the above. If there is no rain one day, the average precipitation
                        in the period is used and if there is precipitation 100% cloud cover is used.

    Method = Random Thomas: Thomas Skaugen suggests to choose random numbers in a interval based on
                        precipitation amount to estimate clouds. Method returns different Nash-Sutcliffe every
                        run but the seem to circle around the results from "Binary and average" method.


    :param prec_inn:        [list or single value]     Precipitation
    :return clouds_out:     [list or single value]     Cloud cover

    """

    # If prec_inn isn't a list, make it so.
    if not isinstance(prec_inn, list):
        prec = [prec_inn]
    else:
        prec = prec_inn

    clouds_out = []

    if method == 'Binary':
        for p in prec:
            if p == 0:
                # clouds.append(0.)
                clouds_out.append(0.1)      # THS suggests a lower threshold
            else:
                clouds_out.append(1.)

    if method == 'Average':
        clouds = []
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
        # Thomas Skaugen suggests to choose random numbers in a interval based on precipitation amount
        # to estimate clouds.
        for p in prec:
            if p > 5./1000:
                clouds_out.append(1.)
            elif 0. < p <= 5./1000:
                clouds_out.append(0.8+random.random()/5.)       # random numbers between 0.8 an 1.0
            if p == 0.:
                clouds_out.append(0.4+random.random()*3./10.)   # random numbers between 0.4 and 0.7

    # Again, if prec_inn isn't a list, return only a float.
    if not isinstance(prec_inn, list):
        clouds_out = clouds_out[0]

    return clouds_out


def __test_clouds_from_short_wave():

    date_list = [dt.date.today() - dt.timedelta(days=x) for x in range(0, 365)]
    date_list = [dt.datetime.combine(d, dt.datetime.min.time()) for d in date_list]
    date_list.reverse()

    # test Nordnesfjellet i Troms
    station_id = 91500
    short_wave_id = 'QSI'
    long_wave_id = 'QLI'
    temperature_id = 'TA'
    timeseries_type = 2
    utm_e = 711075
    utm_n = 7727719

    short_wave = gws.getMetData(station_id, short_wave_id, date_list[0], date_list[-1], timeseries_type)
    long_wave = gws.getMetData(station_id, long_wave_id, date_list[0], date_list[-1], timeseries_type)
    temperature = gws.getMetData(station_id, temperature_id, date_list[0], date_list[-1], timeseries_type)

    short_wave = we.fix_data_quick(short_wave)
    long_wave = we.fix_data_quick(long_wave)
    temperature_daily = we.fix_data_quick(temperature)

    short_wave_daily = we.make_daily_average(short_wave)
    short_wave_daily = we.multiply_constant(short_wave_daily, 24 * 3600 / 1000)  # Wh/m2 * 3600 s/h * kJ/1000J (energy) over 24hrs
    long_wave_daily = we.make_daily_average(long_wave)
    long_wave_daily = we.multiply_constant(long_wave_daily, 24 * 3600 / 1000)
    temperature_daily = we.make_daily_average(temperature)

    Short_wave_list = we.strip_metadata(short_wave_daily)
    I_clear_sky_list = [irradiance_clear_sky(utm_e, utm_n, d) for d in date_list]
    Cloud_cover = clouds_from_short_wave(utm_e, utm_n, Short_wave_list, date_list)

    import matplotlib.pyplot as plt

    plt.plot(date_list, Short_wave_list)
    plt.plot(date_list, I_clear_sky_list)
    plt.plot(date_list, Cloud_cover)
    plt.ylim(0, 50000)
    plt.show()


if __name__ == "__main__":

    __test_clouds_from_short_wave()

    a = 1











