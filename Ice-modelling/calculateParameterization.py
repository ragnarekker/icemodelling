__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import datetime as dt
import types
import math
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


def normal_time_from_unix_time(unixDatetime):
    """
    Takes in a date in unix datetime and returns a "normal date"

    :param unixDatetime:    Unix date time in milliseconds from 1.1.1970
    :return:                The date as datetime object

    Ex: date = unix_time_2_normal(int(p['DtObsTime'][6:-2]))
    """
    unixDatetimeInSeconds = unixDatetime/1000 # For some reason they are given in miliseconds
    dato = dt.datetime.fromtimestamp(int(unixDatetimeInSeconds))

    return dato


def lat_long_from_utm33(x, y, output="degrees"):
    '''

    konverterer til lat long.

    '''

    from math import pi, sin, cos, tan

    utmx = x-500000
    utmy = y
    k0 = 0.9996
    long0 = 15.0 * pi / 180         # 15 grader er Central meridian i sone 33  15*pi/180  gir radianer
    M = utmy/k0                     # Meridional arc
    a = 6378137                     # Eq, radius meters
    b = 6356752.3141                # Polar radius meters
    e = (1-(b**2/a**2))**0.5        # e = 0.08
    e2 = (e*a/b)**2                 # e2 = 0.007
    mu = M/(a*(1-(e**2/4)-3*(e**4/64)-5*(e**6/256)))
    e1 = (1-(1-e**2)**0.5)/(1+(1-e**2)**0.5)
    j1 = 3*(e1/2)-27*(e1**3/32)
    j2 = 21*(e1**2/16)-55*(e1**4/32)
    j3 = 151*(e1**3/96)
    j4 = (1097*e1**4)/512
    fp = mu+j1*sin(2*mu)+j2*sin(4*mu)+j3*sin(6*mu)+j4*sin(8*mu)
    C1 = e2*cos(fp)**2
    T1 = tan(fp)**2
    R1 = a*(1-e**2)/(1-e**2*sin(fp)**2)**1.5
    N1 = a/(1-e**2*sin(fp)**2)**0.5
    D = utmx/(N1*k0)
    Q1 = N1*tan(fp)/R1
    Q2 = (D**2/2)
    Q3 = (5+3*T1+10*C1-4*C1**2-9*e2)*D**4/24
    Q4 = (61+90*T1+298*C1+45*T1**2-3*C1**2-252*e2)*D**6/720
    Q5 = D
    Q6 = (1+2*T1+C1)*D**3/6
    Q7 = (5-2*C1+28*T1-3*C1**2+8*e2+24*T1**2)*D**5/120

    phi = fp-Q1*(Q2-Q3+Q4)          # latitude radianer
    thi = long0 +(Q5-Q6+Q7)/cos(fp) # longitude radianer
    phi_lat = phi*180/pi            # latitude grader
    thi_long = thi*180/pi           # longitude grader

    if output == "both":
        return phi, thi, phi_lat, thi_long

    if output == "degrees":
        return phi_lat, thi_long

    if output == "radians":
        return phi, thi


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



def get_albedo_walter(prec_snow, snow_depth, snow_density, temp_atm, albedo_prim, time_span_in_sec, time_hour):
    """
    Calculates albedo according to Todd Walters paper (2005) in journal of hydrology.
    It works for time intervals of 24hrs, 12, 6, 4 and 3hrs. That is, for albedo decay to work time_hour
    has to be 12 once a day.

    The method is derived for snow covered ground and is valid for use if snow_depth + prec_snow is
    more than swe_minimum (15-20cm snow). Less snow is treated with an interpolation with bare ground albedo.

    :param prec_snow:
    :param snow_depth:
    :param snow_density:
    :param temp_atm:
    :param albedo_prim:         primary albedo.
    :param time_span_in_sec:
    :param time_hour:
    :return:    albedo_prim:    primary albedo decayed on time step.
                albedo:         are equal in the cases where snow depth is above critical 15-20cm.

    """
    from math import exp, log

    # Method uses snow water equivalents SWE
    delta_swe = prec_snow / rho_new_snow(temp_atm)
    swe = snow_depth / snow_density
    swe += delta_swe

    albedo_max = const.alfa_max     # maximum albedo
    albedo_bare_ground = const.alfa_bare_ground
    swe_minimum = 0.05                  # Aprox 15-20cm snow height.

    A = None
    if (time_span_in_sec == 86400) or (time_hour == 12):                   # Oppdatere albedoen 1 gang i døgnet

        # case no new snow or melt. Apply albedo decay
        if delta_swe <= 0.:
            A = 0.35-(0.35-albedo_max)*exp(-(0.177+log((albedo_max-0.35)/(albedo_prim-0.35))**2.16))**0.46 #US Army corps of engineers (empirical)
            albedo_prim = A

        # Case new snow: Calculate snow density and albedo of the new snow.
        if(delta_swe > 0.):
            #rho_snow = 50 + 3.4*(temp_atm+15)       # [kg/m3] density new snow
            rho_snow = rho_new_snow(temp_atm)
            A = albedo_max-(albedo_max-albedo_prim)*exp(-((4*delta_swe*rho_snow)/0.12))
            albedo_prim = A
    else:
        A = albedo_prim                             # vi bruker forrige tidsskritts albedo

    albedo = A

    if swe < swe_minimum:
        R = (1-(swe/swe_minimum)) * exp(-(swe/(2*swe_minimum)))
        albedo = R*albedo_bare_ground + (1-R)*albedo           # interpolerer albedo til bare ground albedo

    return albedo_prim, albedo


def get_albedo_ueb(prec_snow, snow_depth, temp_surface, zenith_angle, age_factor_tau, time_span_in_sec):
    """
    Method estimates albedo as in the Utah energy balance Snow Accumulation and Melt Model (UEB).
    Adaption from Dickinson et al. 1993 (BATS, NCAR).

    :param prec_snow:
    :param snow_depth:
    :param temp_surface:
    :param zenith_angle:        [Radians]
    :param age_factor_tau:      [-] non-dimensional snow surface age that is incremented at each times step
                                by a quantity designed to emulate the effect of the growth of surface
                                grain sizes.
    :param time_span_in_sec:
    :return:

    """
    from math import exp, cos

    # Albedo MÅ ta med dagens snø for å regne ut albeo, ellers smelter den bare vekk
    snow_depth += prec_snow

    # Constants from Tarboton and Luce, Utah energy balance Snow Accumulation and Melt Model UEB, 1996
    albedo_bare_ground = const.alfa_black_ice     # Bare ground albedo means albedo of the ice beneath
    C_v = 0.2           # sensitivity of albedo to snow surface aging (grain size growth)
    C_ir = 0.5          # sensitivity of albedo to snow surface aging (grain size growth)
    alfa_v0 = 0.95      # fresh snow diffuse reflectances in the visible
    alfa_ir0 = 0.65     # fresh snow diffuse reflectances in the near infrared bands
    tau_0 = 1000000
    h_sd = 0.05         # Meter
    b = 2               # Dickinson et al 1993

    ##TEST VARIABLE som er input
    #prec_snow <- 0.005         # meter snøfall
    #temp_surface <- -3.2       # Snøoverflate temperatur
    #zenith_angle <- 0.6        # zenith vinkel i radianer
    #snow_depth <- 0.02         # snø i snømagasin (med prec_snow?)
    #age_factor_tau <- 0.7      # lader fra forrige tidsskritt
    #time_span_in_sec <- 10800  # 3 timer
    ####

    # The change in age_factor
    r1 = exp(5000*((1/273.16)-(1/(temp_surface+273.16))))
    r2 = min(r1**10, 1)
    r3 = 0.03
    d_tau = ((r1+r2+r3)/tau_0)*time_span_in_sec

    # In case of new snow, the age factor becomes 0.
    if prec_snow >= 0.01:
        age_factor_tau = 0.

    age_factor_tau += d_tau
    F_age = age_factor_tau/(1+age_factor_tau)

    # reflectance visible and near infra red light (< 0.7 micro-meters and > 0.7 micrometers)
    alfa_vd = (1-C_v*F_age)*alfa_v0
    alfa_ird = (1-C_ir*F_age)*alfa_ir0

    f_omg = None
    if cos(zenith_angle) < 0.5:
        f_omg = (1/b)*(((b+1)/(1+2*b*cos(zenith_angle)))-1)
    if cos(zenith_angle) > 0.5:
        f_omg = 0.

    alfa_v = alfa_vd + 0.4*f_omg*(1-alfa_vd)
    alfa_ir = alfa_ird + 0.4*f_omg*(1-alfa_ird)

    albedo_init = 0.5*alfa_v+0.5*alfa_ir        # vekter det mot visible < 0.7 mikro meter

    radiation_extinction = (1-(snow_depth/h_sd))*exp(-(snow_depth/(2*h_sd)))

    if snow_depth < h_sd:
             # interpolerer albedo til bare ground albedo
        albedo = radiation_extinction*albedo_bare_ground + (1-radiation_extinction)*albedo_init
    else:
        albedo = albedo_init

    return age_factor_tau, albedo


def get_energy_balance_from_senorge(utm33_x, utm33_y, ice_column, temp_atm, prec, prec_snow,
                                    age_factor_tau, albedo_prim, time_span_in_sec, cloud_cover=None):
    '''
    The daily energy budget of a column of snow is expressed as (Walter et al. 2005):

    EB = λ_F * ρ_w * ΔSWE = S + (L_a - L_t) + (H + LE) + G + R - CC

    Where λ_F is the latent heat of fusion (λ_F=335 kJ〖kg〗^(-1))
    ρ_w [1000kgm^(-3)] is the density of water
    ΔSWE is the change in the snowpack’s water equivalent [m]

    '''

    from weather import EnergyBalanceElement as ebe

    # times are given as the end of the time span
    date = ice_column.date
    day_no = (ice_column.date + dt.timedelta(seconds=time_span_in_sec)).timetuple().tm_yday
    time_hour = (ice_column.date + dt.timedelta(seconds=time_span_in_sec)).hour


    # Variables picked out from ice_column
    snow_depth = ice_column.column[0].height
    snow_density = ice_column.column[0].density
    temp_surface = ice_column.get_surface_temperature(temp_atm)
    is_ice = True
    if len(ice_column.column) == 0:
        is_ice = False


    # Calculate some parameters
    if not cloud_cover:
        cloud_cover = clouds_from_precipitation(prec, method='Binary')


    # Define an energy balance object to put it all in
    energy_balance = ebe(date)
    energy_balance.add_model_input(utm33_x, utm33_y, snow_depth, snow_density, temp_surface, is_ice,
                        temp_atm, prec, prec_snow, cloud_cover,
                        age_factor_tau, albedo_prim, day_no, time_hour, time_span_in_sec)


    # Calculate the energy balance terms
    S, s_inn, albedo, albedo_prim, age_factor_tau = \
        get_short_wave(utm33_x, utm33_y, day_no, temp_atm, cloud_cover, snow_depth, snow_density, prec_snow, time_hour,
                       time_span_in_sec, temp_surface, age_factor_tau, albedo_prim, albedo_method="ueb")

    L_a, L_t = \
        get_long_wave(cloud_cover, temp_atm, temp_surface, snow_depth, is_ice, time_span_in_sec)

    H, LE = \
         get_sensible_and_latent_heat(temp_atm, temp_surface, time_span_in_sec, pressure_atm=None, wind=None)

    G = get_ground_heat(time_span_in_sec)

    R = get_prec_heat(temp_atm, prec)

    #CC = get_cold_content(ice_column, temp_atm, prec_snow)
    CC = 0.

    EB = S + (L_a - L_t) + (H + LE) + G + R - CC

    energy_balance.add_short_wave(S, s_inn, albedo, albedo_prim, age_factor_tau)
    energy_balance.add_long_wave(L_a, L_t)
    energy_balance.add_sensible_and_latent_heat(H, LE)
    energy_balance.add_ground_heat(G)
    energy_balance.add_prec_heat(R)
    energy_balance.add_cold_content(CC)
    energy_balance.add_energy_budget(EB)

    return energy_balance


def get_short_wave(utm33_x, utm33_y, day_no, temp_atm, cloud_cover,snow_depth, snow_density, prec_snow, time_hour,
                   time_span_in_sec, temp_surface, age_factor_tau, albedo_prim, albedo_method="ueb"):
    '''
    S [kJm^(-2)]is the net incident solar (short wave) radiation
    Method calculates albedo in two different ways for comparison and testing. In the end one is chose based on
    the method chosen.

    :param utm33_x, utm33_y:    koordinat i UTM 33
    :param day_no:              Dagnummer
    :param temp_atm:            [C] Air temperature
    :param SWE:                 snø i snømagasin
    :param prec_rain:           [m] precipitation as liquid
    :param time_hour:           [0-23] Hour of the day the time_span_in_sec ends
    :param time_span_in_sec:    [sec] Time resolution in sec
    :param temp_surface:        [C] Snøoverflate temperatur
    :param prec_snow:           [m] Meter snøfall
    :param albedo_prim:         Primary albedo from last timestep. Used in the albedo_walters routine.
    :param age_factor_tau:      [?] Age factor in the UEB albedo routine.

    :return:    S, s_inn, albedo, albedo_prim, age_factor_tau


    '''
    from math import sin, cos, pi, fabs, sqrt, acos

    if time_hour == 0:
        time_hour = 24

    phi, thi, ddphi, ddthi = lat_long_from_utm33(utm33_x,utm33_y, output= "both")

    thetaW = 0.4102*sin((2*pi/365)*(day_no-80))     # solar declination angleday angle, Walter 2005
    print("sol.decl.angle={0} on daynumber={1}".format(thetaW, day_no))

    #theta <- vector("numeric", 365)
    #theta2 <- vector("numeric", 365)
    #for (day_no in 1:365)theta[day_no] <- 0.4092*cos((2*pi/365)*(day_no-173))#solar declination angleday angle, Liston 1995
    #for (day_no in 1:365)theta2[day_no] <- 0.4102*sin((2*pi/365)*(day_no-80))#solar declination angleday angle

    theta = 0.4092*cos((2*pi/365.25)*(day_no-173))  # solar declination angleday angle, Liston 1995
    print(theta)

    theta2 = 2*pi/365.25*(day_no-80)
    print(theta2)

    r = 149598000   # distance from the sun
    R = 6378        # Radius of earth

    timezone = -4 * (fabs(thi) % 15) * thi/fabs(thi)      # ang lengdegrad ikke
    epsilon = 0.4092    # rad(23.45)

    z_s = r*sin(theta2)*sin(epsilon)
    r_p = sqrt(r**2-z_s**2)
    nevner = (R-z_s*sin(phi))/(r_p*cos(phi))

    if(nevner > -1) and (nevner < 1):

        # acos(mÂ ha inn verdier ,(mellom-1,1) hvis <-1 sÂ er det midnattsol > 1 er det m¯rketid.
        t0 = 1440/(2*pi)*acos((R-z_s*sin(phi))/(r_p*cos(phi)))
        that = t0+5
        n = 720-10*sin(4*pi*(day_no-80)/365.25)+8*sin(2*pi*day_no/365.25)
        sr = (n-that+timezone)/60 #soloppgang
        ss = (n+that+timezone)/60 #solnedgang

        #sunhrs = ss-sr# antall soltimer
        #time_hour er tidsvariabel
        #Trise = -(1/0.2618)*cos(-tan(theta)*tan(phi))**-1
        #Tset = (1/0.2618)*cos(-tan(theta)*tan(phi))**-1
        #Trise = round(-sunhrs/2)
        #Tset = round(sunhrs/2)

    if nevner <= -1:    # Midnattsol
        sr = 0.
        ss = 24.

    if nevner >= 1:     # Mørketid
        sr = 12.
        ss = 12.

    #time_hour <- 22
    TTList = {}         # Values for transmissivity for every hr
    dingom = {}         # Values for zenith angle (0 straight up)

    for tid in range(1, 24, 1):

        if (tid > sr) and (tid < ss):

            tom = tid-12    # Number of hours from solar noon. Solar noon is tom=0
            cosarg = 0.2618 * tom   # Radians pr hour

            dingom[tid] = acos(sin(phi)*sin(theta)+cos(phi)*cos(theta)*cos(cosarg))  # Dingmans zenith angle
            TTList[tid] = (0.6 + 0.2*sin((0.5*pi)-dingom[tid]))*(1.0-0.5*cloud_cover)         # Inspirert av G. Liston 1995 transmissivitet

            # TTList[tid] = (0.6-0.2*sin(dingom[tid]))*(1.0-0.5*cloud_cover) #Inspirert av G. Liston 1995 transmissivitet
            # TTList[tid] = (0.6-0.2*sin(dingom[tid]))*(1.0-0.5*cloud_cover) #Inspirert av G. Liston 1995 transmissivitet

        if (tid < sr) or (tid > ss):  # If time is outside sunrise-sunset

            TTList[tid] = 0.       # Transmissivity = 0 when sun is below horizon.
            dingom[tid] = pi/2     # Angle below horizin is set to be on the horizon.

    # pi/2 minus zenith angle, initielt, ikke helt sikker. Blir veldig lav med init dingom lik pi/2
    # blir på den annen side høy med init dingom lik 0. Albedo ser ganske fornuftig ut.

    if time_span_in_sec == 86400:
        Trans = TTList.values()                 # list
        zenith_angle = dingom.values()          # list

    elif time_span_in_sec < 86400:              # Midler transmissvitet og solvinkel For finere tidssoppløsning
        interv = list(range(time_hour-int(time_span_in_sec/3600)+1, time_hour, 1))     # aktuelle timer
        Trans = [TTList[i] for i in interv]     # selection of transmisions in intervall
        zenith_angle = [dingom[i] for i in interv]

    else:
        print("Method doesnt work on time intervals greater than 24hrs")
        Trans = None
        zenith_angle = None

    # Mean values
    Trans = float( sum(Trans) / len(Trans) )
    zenith_angle = float( sum(zenith_angle) / len(zenith_angle) )

    S0 = (117.6*10**3)/86400    # [kJ/m2*s] Solar constant pr sec
    S0 *= time_span_in_sec      # solar constant pr time step
    print("Solar constant={0}, time resolution = {1}".format(S0, time_span_in_sec))

    # UEB albedo
    age_factor_tau, albedo_ueb \
        = get_albedo_ueb(prec_snow, snow_depth, temp_surface, zenith_angle, age_factor_tau, time_span_in_sec)

    # Todd Walters albedo
    albedo_prim, albedo_walter \
        = get_albedo_walter(prec_snow, snow_depth, snow_density, temp_atm, albedo_prim, time_span_in_sec, time_hour)

    # At this point I choose which albedo variant to use in calculating short wave radiation
    if albedo_method == "ueb":
        albedo = albedo_ueb
    elif albedo_method == "walter":
        albedo = albedo_walter
    else:
        print("No valid albedo method selected.")
        albedo = None

    #Solar radiation
    s_inn = Trans * sin((pi/2)-zenith_angle) * S0   #
    S = (1-albedo) * s_inn           # se likning Liston 1995, eq. 26 (Nett SW-radiation)

    return S, s_inn, albedo, albedo_prim, age_factor_tau


def get_long_wave(cloud_cover, temp_atm, temp_surface, snow_depth, is_ice, time_span_in_sec):
    '''
    Long wave radiation, both atmospheric and terrestrial, calculated from precipitation and temperature.

    We use the Stefan-Boltzmann equation: L = epsilon * sigma * temp^4
    where epsilon is emissivity and sigma is Stefan-Boltzmann constant.

    :param prec:                Precipitation (?)
    :param temp_atm:            Temperature (C)
    :param time_span_in_sec:     Time resolution gives the Boltzmann constant
    :param is_ice:              [Bool]  It there ice or not?
    :param temp_surface:
    :param snow_depth:
    :return     L_a:            [kJm^(-2)] is the atmospheric long wave radiation over the given time span
                L_t:            [kJm^(-2)] is the terrestrial long wave radiation over the given time span

    Notes:      W = J / s
    '''

    eps_atm = (0.72+0.005*temp_atm)*(1-0.84*cloud_cover)+0.84*cloud_cover    # Atmospheric emissivity from Campbell and Norman, 1998. Emissivity er dimasnjonsløs
    eps_surface = const.eps_snow                       # By default we assume snow cover
    sigma = const.sigma_pr_second * time_span_in_sec   # Stefan-Boltzmann constant over the requested time span

    if snow_depth == 0:
        eps_surface = const.eps_ice           # No snow gives ice emissivity

    if is_ice == False:
        temp_surface == 0                     # water at 0degC
        eps_surface = const.eps_water         # water emissivity is the same as snow emidsitivity

    L_a = eps_atm * sigma * (temp_atm + 273.2)**4            # temp_atm skal være i Celsisus. Atmosfærisk innstsåling
    L_t = eps_surface * sigma * (temp_surface + 273.2)**4    # terrestrisk utstråling emmisivity for snø er 0.97, er ogsÂ brukt for bar bakke, se Dingman p.583

    return L_a, L_t                     # Gir verdier av riktig størrelsesorden og balanserer hverandre sånn passe


def get_sensible_and_latent_heat(temp_atm, temp_surface, time_span_in_sec, pressure_atm=None, wind=None):
    '''
    Turbulent fluxes:
    Theory for calculations found in Dingman, 2002, p. 197.

    :param temp_atm:            døgnmiddeltemperatur/aktuell temperatur
    :param temp_surface:        snøtemperatur
    :param time_span_in_sec:    Tidsoppløsning i sekunder
    :param wind:                Vind set constnstant if not given
    :param pressure_atm:        atmopheric presure set constnstant if not given

    :return:    H   [kJm^(-2)] Sensible heat exchange.
                LE  [kJm^(-2)] Energy flux associated with the latent heats of vaporization and condensation at the surface.

    :return:
    '''

    if not pressure_atm:
        pressure_atm = const.pressure_atm
    if not wind:
        wind = const.avg_wind_const

    c_air = const.c_air         # specific heatcapacity air
    rho_air = const.rho_air     # density of air
    zu = 2                      # Høyde på vind målinger
    zt = 2                      # Høyde på lufttemperatur målinger
    zm = 0.001                  # ruhetsparameter for snø
    d = 0                       # Zeroplane displecement for snow
    zh = 0.0002                 # varme og damp ruhets
    k =const.von_karmans_const  # von Karmans konstant

    common = k**2/(  math.log( (zu-d)/zm ,10)  )**2

    # Sensible heat exchange
    H = c_air*rho_air*common*wind*(temp_atm-temp_surface) # Sensible heat. Positivt hvis temp_surface < temp_atm
    H = H * time_span_in_sec

    # Latent heat exchange
    # e_a and e_s [kPa] are saturation vapor pressure in the atmosphere and at the surface respectively.
    # Can be estimated as (Dingman, 2002, p. 586, see also Walter et al. 2005))
    ea = 0.611 * math.exp( (17.3*temp_atm)/(temp_atm+273.3) )           # alltid positivt
    es = 0.611 * math.exp( (17.3*temp_surface)/(temp_surface+273.3) )   # alltid positivt

    # Where λ_F and λ_V are the latent heats involved in fusion and vaporization-condensation respectively
    lambda_V = 2470     # kJkg-1 latent varme fra fordampning
    lambda_F = 334      # kJkg-1 latent varme fra fusjon

    LE = None       # Latent varme. Positivt hvis temp_surface < temp_atm
    if temp_surface < 0.:
        LE = (lambda_V+lambda_F)*0.622*(rho_air/pressure_atm)*common*wind*(ea-es)
    if temp_surface == 0.:
        LE = lambda_V * 0.622 * (rho_air/pressure_atm) * common * wind *(ea-es)
    else:
        print('Surface temperature above 0C not possible.')

    LE = LE * time_span_in_sec

    return H, LE


def get_ground_heat(time_span_in_sec):
    """
    G [kJm^(-2)] is ground heat conduction to the bottom of the snowpack

    :param time_span_in_sec:
    :return:
    """

    # Ground heat
    G = 173./86400               # [kJ / second]
    G = G * time_span_in_sec     # desired resolution

    return G


def get_prec_heat(temp_atm, prec):
    """
    Heat from liquid precipitation. We assume rainwater has the same temperature as air and that heat is added to the
    snowpack when the rain’s temperature is lowered to zero degrees.

    :param temp_atm:    [C] Air temperature.
    :param prec_rain:   [m] Precipitation as liquid water.
    :return R:          [kJm^-2] Heat added by precipitation
    """

    if temp_atm > const.temp_rain_snow:
        prec_rain = prec
    else:
        prec_rain = 0.

    if prec_rain > 0.:
        R = const.rho_water * const.c_water * prec_rain * temp_atm
    else:
        R = 0.

    return R


def get_cold_content(ice_column, temp_atm, prec_snow):
    """
    Heat storage (cold content) of the snow and ice.

    :param ice_column:  From previous time step. The column variable has layers with layer.density, layer.height and layer.temp.
    :param prec_snow:   [m] Prec as snow from this time step (new snow)
    :param temp_atm:    [C] air temperature. We assume the new snow has this temp.

    :return CC:         [kJm^-2]

    Dimensions:     kg m^-3 * kJ kg^-1 K^-1 * m * K = kJm^-2
    """

    CC = 0.      # kan kun bli negativ eller 0.

    for layer in ice_column.column:
        CC += layer.rho * layer.heat_capacity * layer.height * layer.temperature

    # Add also the new snow
    CC += const.rho_new_snow * const.c_snow * prec_snow * temp_atm

    return CC


if __name__ == "__main__":

    # Test koordinater i tana
    x_tana = 988130
    y_tana = 7844353
    lat_tana, long_tana = lat_long_from_utm33(x_tana, y_tana)


    # Test Filefjell
    y_file = 6802070
    x_file = 130513
    lat_file, long_file = lat_long_from_utm33(x_file, y_file)

    get_short_wave(utm33_x=130513, utm33_y=6802070, day_no=10, temp_atm= -1.5, cloud_cover=0.5,
                            snow_depth=1., snow_density=0.3, prec_snow=0.01,
                            time_hour=0, time_span_in_sec=24*60*60, temp_surface=-2.,
                            age_factor_tau=None, albedo_prim=0.30, albedo_method="ueb")

    a = 1

























