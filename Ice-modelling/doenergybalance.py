__author__ = 'raek'
# -*- coding: utf-8 -*-

import datetime as dt
import constants as const
import doconversions as dc
import doparameterization as dp
from weather import EnergyBalanceElement as ebe
from math import log, exp, sin, cos, pi, fabs, sqrt, acos


def energy_balance_from_temp_sfc(
        utm33_x, utm33_y, ice_column, temp_atm, prec, prec_snow, albedo_prim, time_span_in_sec,
        temp_surface=None, age_factor_tau=None, cloud_cover=None, wind=None, pressure_atm=None):
    """
    The daily energy budget of a column of snow is expressed as (Walter et al. 2005):

    EB = λ_F * ρ_w * ΔSWE = S + (L_a - L_t) + (H + LE) + G + R - CC

    Where λ_F is the latent heat of fusion (λ_F=335 kJ (kg)^(-1))
    ρ_w [1000kgm^(-3)] is the density of water
    ΔSWE is the change in the snow pack’s water equivalent [m]

    INCOMPLETE: Need to implement shortwave attuenation in the colomn topp layers.
    Use q_s(z,t) in eq 10 in Yang et al (2012)

    Mandatory
    :param utm33_x:
    :param utm33_y:
    :param ice_column:
    :param temp_atm:
    :param prec:
    :param prec_snow:
    :param albedo_prim:
    :param time_span_in_sec:

    Optional
    :param temp_surface:        If surface temp not given, one will be estimated. Should be avoided!
    :param age_factor_tau:
    :param cloud_cover:
    :param wind:
    :param pressure_atm:
    :return:

    For reference:  1 kWh is 3600 kJ.
                    10 000 kJ can melt 30kg ice or (3cm/m2 ice).

    """


    date = ice_column.date
    day_no = ice_column.date.timetuple().tm_yday
    # time given as the end of the time span
    time_hour = (ice_column.date + dt.timedelta(seconds=time_span_in_sec)).hour


    # Variables picked out from ice_column
    is_ice = True
    snow_depth = 0.
    snow_density = const.rho_snow

    if len(ice_column.column) == 0:
        is_ice = False
        # albedo_prim = 0.10      # no ice, water absobs much of the short wave
    else:
        if ice_column.column[0].type == "snow":
            snow_density = ice_column.column[0].density
            snow_depth = ice_column.column[0].height
        if ice_column.column[0].type == "black_ice":
            albedo_prim = const.alfa_black_ice
        if ice_column.column[0].type == "slush_ice":
            albedo_prim = const.alfa_slush_ice


    # Calculate some parameters
    if cloud_cover is None:
        cloud_cover = dp.clouds_from_precipitation(prec, method='Binary')

    # This scenario should be avoided but I keep it for now because it it the method used in senorge_eb
    if temp_surface is None:
        temp_surface = ice_column.get_surface_temperature_estimate(temp_atm)


    # Define an energy balance object to put it all in
    energy_balance = ebe(date)
    energy_balance.add_model_input(
        utm33_x_inn=utm33_x, utm33_y_inn=utm33_y, snow_depth_inn=snow_depth, snow_density_inn=snow_density,
        temp_surface_inn=temp_surface, is_ice_inn=is_ice, temp_atm_inn=temp_atm,
        prec_inn=prec, prec_snow_inn=prec_snow, cloud_cover_inn=cloud_cover,
        age_factor_tau_inn=age_factor_tau, albedo_prim_inn=albedo_prim,
        day_no_inn=day_no, time_hour_inn=time_hour, time_span_in_sec_inn=time_span_in_sec)


    # Calculate the energy balance terms
    S, s_inn, albedo, albedo_prim, age_factor_tau = \
        get_short_wave(utm33_x, utm33_y, day_no, temp_atm, cloud_cover, snow_depth, snow_density, prec_snow, time_hour,
                       time_span_in_sec, temp_surface, albedo_prim, age_factor_tau=age_factor_tau, albedo_method="ueb")

    L_a, L_t = \
        get_long_wave(cloud_cover, temp_atm, temp_surface, snow_depth, is_ice, time_span_in_sec)

    H, LE = \
         get_sensible_and_latent_heat(temp_atm, temp_surface, time_span_in_sec, pressure_atm=pressure_atm, wind=wind)

    G = get_ground_heat(time_span_in_sec)

    R = get_prec_heat(temp_atm, prec)

    #CC = get_cold_content(ice_column, temp_atm, prec_snow)

    EB = S + (L_a - L_t) + (H + LE) + G + R         # - CC

    energy_balance.add_short_wave(S, s_inn, albedo, albedo_prim, age_factor_tau)
    energy_balance.add_long_wave(L_a, L_t)
    energy_balance.add_sensible_and_latent_heat(H, LE)
    energy_balance.add_ground_heat(G)
    energy_balance.add_prec_heat(R)
    #energy_balance.add_cold_content(CC)
    energy_balance.add_energy_budget(EB)

    return energy_balance


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
    # Method uses snow water equivalents SWE
    delta_swe = prec_snow / dp.rho_new_snow(temp_atm)
    swe = snow_depth / snow_density
    swe += delta_swe

    albedo_max = const.alfa_max     # maximum albedo
    albedo_bare_ground = const.alfa_bare_ground
    swe_minimum = 0.05                  # Aprox 15-20cm snow height.

    A = None
    if (time_span_in_sec == 86400) or (time_hour == 12):                   # Oppdatere albedoen 1 gang i døgnet

        # case no new snow or melt. Apply albedo decay
        if delta_swe <= 0.:
            if albedo_prim <= 0.35:
                print "get_albedo_walter: albedo_prim <= 0.35 (value: [0]). Forced to 0.355."
                albedo_prim = 0.355

            A = 0.35-(0.35-albedo_max)*exp(-(0.177+log((albedo_max-0.35)/(albedo_prim-0.35))**2.16))**0.46 #US Army corps of engineers (empirical)
            albedo_prim = A

        # Case new snow: Calculate snow density and albedo of the new snow.
        if(delta_swe > 0.):
            #rho_snow = 50 + 3.4*(temp_atm+15)       # [kg/m3] density new snow
            rho_snow = dp.rho_new_snow(temp_atm)
            A = albedo_max-(albedo_max-albedo_prim)*exp(-((4*delta_swe*rho_snow)/0.12))
            albedo_prim = A
    else:
        A = albedo_prim                             # vi bruker forrige tidsskritts albedo

    albedo = A

    if swe < swe_minimum:
        R = (1-(swe/swe_minimum)) * exp(-(swe/(2*swe_minimum)))
        albedo = R*albedo_bare_ground + (1-R)*albedo           # interpolerer albedo til bare ground albedo

    return albedo_prim, albedo


def get_albedo_ueb(prec_snow, snow_depth, temp_surface, zenith_angle, time_span_in_sec, age_factor_tau=None):
    """
    Method estimates albedo as in the Utah energy balance Snow Accumulation and Melt Model (UEB).
    Adaption from Dickinson et al. 1993 (BATS, NCAR).

    :param prec_snow:
    :param snow_depth:
    :param temp_surface:
    :param zenith_angle:        [Radians]
    :param age_factor_tau:      [-] non-dimensional snow surface age that is incremented at each times step
                                by a quantity designed to emulate the effect of the growth of surface
                                grain sizes. Defalt 0. as for new snow
    :param time_span_in_sec:
    :return:

    """


    # Albedo MÅ ta med dagens snø for å regne ut albeo, ellers smelter den bare vekk
    snow_depth += prec_snow

    # Constants from Tarboton and Luce, Utah energy balance Snow Accumulation and Melt Model UEB, 1996
    albedo_bare_ground = const.alfa_black_ice   # Bare ground albedo means albedo of the ice beneath
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

    if not age_factor_tau:
        age_factor_tau = 0.

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


def get_short_wave(
        utm33_x, utm33_y, day_no, temp_atm, cloud_cover, snow_depth, snow_density, prec_snow, time_hour,
        time_span_in_sec, temp_surface, albedo_prim, age_factor_tau=None, albedo_method="ueb"):
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
    :param prec_snow:           [m] New snow in meter
    :param albedo_prim:         Primary albedo from last time step. Used in the albedo_walters routine.
    :param age_factor_tau:      [-] Age factor in the UEB albedo routine.

    :return:    S, s_inn, albedo, albedo_prim, age_factor_tau


    '''
    if time_hour == 0:
        time_hour = 24

    phi, thi, ddphi, ddthi = dc.lat_long_from_utm33(utm33_x,utm33_y, output= "both")

    thetaW = 0.4102*sin((2*pi/365)*(day_no-80))     # solar declination angleday angle, Walter 2005
    # print("sol.decl.angle={0} on daynumber={1}".format(thetaW, day_no))

    #theta <- vector("numeric", 365)
    #theta2 <- vector("numeric", 365)
    #for (day_no in 1:365)theta[day_no] <- 0.4092*cos((2*pi/365)*(day_no-173))#solar declination angleday angle, Liston 1995
    #for (day_no in 1:365)theta2[day_no] <- 0.4102*sin((2*pi/365)*(day_no-80))#solar declination angleday angle

    theta = 0.4092*cos((2*pi/365.25)*(day_no-173))  # solar declination angleday angle, Liston 1995
    theta2 = 2*pi/365.25*(day_no-80)

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
    # print("Solar constant={0}, time resolution = {1}".format(S0, time_span_in_sec))

    if snow_depth == 0.:
        albedo = albedo_prim
        age_factor_tau = 0.

    else:
        # UEB albedo
        age_factor_tau, albedo_ueb \
            = get_albedo_ueb(prec_snow, snow_depth, temp_surface, zenith_angle, time_span_in_sec, age_factor_tau=age_factor_tau)

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
        temp_surface = 0                      # water at 0degC
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

    if pressure_atm is None:
        pressure_atm = const.pressure_atm
    if wind is None:
        wind = const.avg_wind_const

    c_air = const.c_air         # specific heatcapacity air
    rho_air = const.rho_air     # density of air
    zu = 2                      # Høyde på vind målinger
    zt = 2                      # Høyde på lufttemperatur målinger
    zm = 0.001                  # ruhetsparameter for snø
    d = 0                       # Zeroplane displecement for snow
    zh = 0.0002                 # varme og damp ruhets
    k = const.von_karmans_const  # von Karmans konstant

    common = k**2/( log( (zu-d)/zm ,10) )**2

    # Sensible heat exchange
    H = c_air*rho_air*common*wind*(temp_atm-temp_surface) # Sensible heat. Positivt hvis temp_surface < temp_atm
    H = H * time_span_in_sec

    # Latent heat exchange
    # e_a and e_s [kPa] are saturation vapor pressure in the atmosphere and at the surface respectively.
    # Can be estimated as (Dingman, 2002, p. 586, see also Walter et al. 2005))
    ea = 0.611 * exp( (17.3*temp_atm)/(temp_atm+273.3) )           # alltid positivt
    es = 0.611 * exp( (17.3*temp_surface)/(temp_surface+273.3) )   # alltid positivt

    # Where λ_F and λ_V are the latent heats involved in fusion and vaporization-condensation respectively
    lambda_V = 2470     # kJkg-1 latent varme fra fordampning
    lambda_F = 334      # kJkg-1 latent varme fra fusjon

    LE = None       # Latent varme. Positivt hvis temp_surface < temp_atm
    if temp_surface < 0.:
        LE = (lambda_V+lambda_F)*0.622*(rho_air/pressure_atm)*common*wind*(ea-es)
    elif temp_surface == 0.:
        LE = lambda_V * 0.622 * (rho_air/pressure_atm) * common * wind *(ea-es)
    else:
        print('get_sensible_and_latent_heat: Surface temperature above 0C not possible for snow and ice. Forcing temp_surface = 0')
        LE = lambda_V * 0.622 * (rho_air/pressure_atm) * common * wind *(ea-es)

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

    if temp_atm >= const.temp_rain_snow:
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


def temp_surface_from_eb(
        utm33_x, utm33_y, ice_column, temp_atm, prec, prec_snow, albedo_prim, time_span_in_sec,
        error=100., age_factor_tau=None, cloud_cover=None, wind=None, pressure_atm=None):
    """Solves surface temperature from the criteria that the energy budget has to be zero.
    This method iterates surface temperatures so that the error goes below a requested threshold.

    INCOMPLETE: method needs iterations in the case that surface temp is at melting temp (0C)

    :param utm33_x:
    :param utm33_y:
    :param ice_column:
    :param temp_atm:
    :param prec:
    :param prec_snow:
    :param albedo_prim:
    :param time_span_in_sec:
    :param age_factor_tau:
    :param error:
    :param cloud_cover:
    :param wind:
    :param pressure_atm:
    :return:
    """

    temp_sfc = temp_atm     # initail value
    eb = error + 1.         # initial value to start while loop
    num_iterations = 0
    eb_obj = None
    melting = False

    while abs(eb) > error:
        if temp_sfc > 0.:
            # in this case EB(T_sfc = 0) = Q_melt
            if melting is True:     # if the melting condition is true already (from previous iteration)
                break
            temp_sfc = 0.
            melting = True      # condition to avoid calculating EB at surf_temp multiple times-

        eb_obj = energy_balance_from_temp_sfc(
            utm33_x, utm33_y, ice_column, temp_atm, prec, prec_snow, albedo_prim, time_span_in_sec,
            temp_surface=temp_sfc, age_factor_tau=age_factor_tau, cloud_cover=cloud_cover, wind=wind, pressure_atm=pressure_atm)

        eb = eb_obj.EB
        delta_t = 0.01 * abs(eb)/100

        if eb > 0.:   # to much energy coming inn.
            temp_sfc += delta_t

        if eb < 0.:   # to much energy going out.
            temp_sfc -= delta_t
            # The melting condition is no longer valid and surface temp can be lowered
            if melting:
                melting = False

        num_iterations += 1

    eb_obj.add_iterations(num_iterations)

    return eb_obj



if __name__ == "__main__":

    import getFiledata as gfd
    from setEnvironment import data_path

    icecols = gfd.importColumns("{0}Semsvann observasjoner 2012-2013.csv".format(data_path))
    icecol = icecols[6]

    eb = temp_surface_from_eb(utm33_x=130513, utm33_y=6802070, ice_column=icecol, temp_atm=5,
                                    prec=0.01,prec_snow=0.1,time_span_in_sec=24*60*60,albedo_prim=0.37)

    S, s_inn, albedo, albedo_prim, age_factor_tau\
           = get_short_wave(utm33_x=130513, utm33_y=6802070, day_no=180, temp_atm= -1.5, cloud_cover=0.5,
                            snow_depth=1., snow_density=0.3, prec_snow=0.01,
                            time_hour=0, time_span_in_sec=24*60*60, temp_surface=-2.,
                            age_factor_tau=None, albedo_prim=0.30, albedo_method="ueb")

    a = 1











