__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import datetime
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
    :param temp:
    :return:

    """
    new_snow_density = 0.05
    temp = temp * 9.0/5.0 + 32.0      # Celsius to Fahrenhet

    if(temp >0.0):
        new_density = new_snow_density + (temp/100)^2
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
    dato = datetime.datetime.fromtimestamp(int(unixDatetimeInSeconds))

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

def energy_balance_from_senorge():
    '''
    The daily energy budget of a column of snow is expressed as (Walter et al. 2005):

    λ_F * ρ_w * ΔSWE = S + (L_a - L_t) + (H + LE) + G + R - CC

    Where λ_F is the latent heat of fusion (λ_F=335 kJ〖kg〗^(-1))
    ρ_w [1000kgm^(-3)] is the density of water
    ΔSWE is the change in the snowpack’s water equivalent [m]
    '''

    return


def short_wave_from_senorge(x=130513, y=6802070, DN=180,thr=12,PS=10.):
#def short_wave_from_senorge(x,y,DN,Ta,Aprim,taux,SWE,regn,thr,Timeresinsec,TSS,PS):
    '''

    solrad_trans_albedo
    S [kJm^(-2)]is the net incident solar (short wave) radiation

    :param x, y:    koordinat i UTM 33
    :param DN:      Dagnummer
    :param Ta:
    :param Aprim:
    :param taux:
    :param SWE:
    :param regn:
    :param thr:
    :param Timeresinsec:
    :param TSS:
    :param PS:
    :return:

    # maximums temperatur
    # minimums temperatur
    # Døgnmiddel temperatur

    # Albedo fra dagen før
    # Sprim og Albedo er daglige bestemt for daglige verdier verdier Temoral oppløsning er bestemt av


    :return:


    '''
    from math import sin, cos, tan, pi, e, fabs

    deltaSWE = PS/1000.
    thrx = thr
    if thr == 0:
        thrx = 24   # 1.2.2013

    phi, thi, ddphi, ddthi = lat_long_from_utm33(x,y, output= "both")


    thetaW = 0.4102*sin((2*pi/365)*(DN-80))#solar declination angleday angle, Walter 2005
    print("sol.decl.angle={0} on daynumber={1}".format(thetaW, DN))

    #theta <- vector("numeric", 365)
    #theta2 <- vector("numeric", 365)
    #for (DN in 1:365)theta[DN] <- 0.4092*cos((2*pi/365)*(DN-173))#solar declination angleday angle, Liston 1995
    #for (DN in 1:365)theta2[DN] <- 0.4102*sin((2*pi/365)*(DN-80))#solar declination angleday angle

    theta = 0.4092*cos((2*pi/365.25)*(DN-173)) #solar declination angleday angle, Liston 1995
    print(theta)

    theta2 = 2*pi/365.25*(DN-80)
    print(theta2)

    r = 149598000   # distance from the sun
    R = 6378        # Radius of earth

    #timezone = -4 * (fabs(thi)%%15) * thi/fabs(thi)      # ang lengdegrad ikke
    epsilon = 0.4092    # rad(23.45)
    '''
    z.s <-r*sin(theta2)*sin(epsilon)
    r.p <- sqrt(r^2-z.s^2)   #her
    nevner <- (R-z.s*sin(phi))/(r.p*cos(phi))
    if((nevner > -1) && (nevner < 1)):
        {
        # acos(mÂ ha inn verdier ,(mellom-1,1) hvis <-1 sÂ er det midnattsol > 1 er det m¯rketid.
        t0 <-1440/(2*pi)*acos((R-z.s*sin(phi))/(r.p*cos(phi)))
        that <- t0+5
        n <-720-10*sin(4*pi*(DN-80)/365.25)+8*sin(2*pi*DN/365.25)
        sr <-(n-that+timezone)/60 #soloppgang
        ss <- (n+that+timezone)/60 #solnedgang
        #sunhrs <- ss-sr# antall soltimer
        #thr er tidsvariabel
        #Trise <- -(1/0.2618)*cos(-tan(theta)*tan(phi))^-1
        #Tset <- (1/0.2618)*cos(-tan(theta)*tan(phi))^-1
        #Trise <-round(-sunhrs/2)
        #Tset <- round(sunhrs/2)
        }

    if (nevner <= -1) #Midnattsol
        {
        sr <-0.0
        ss <-24.0
        }

    if (nevner >= 1) #M¯skjetid
        {
        sr <-12.0
        ss <-12.0
        }


    #thr <- 22
    TTList <- vector("numeric",24) #vektor for Transmissivity
    dingom <- vector("numeric",24) #vektor for Transmissivity

    for (tid in 1:24)
    {
      if((tid > sr) && (tid < ss))
      {
      ifelse(regn > 0, Cl <- 1.0, Cl <-0.1) #Cloudcover 100 % if precipitation, zero otherwise Litt brutal, ganske mange skyete dager
      #Noter at Cl = 0.1 hvis skyfritt, min justering

      tom <-  -(12-(tid)) #gir antall timer fra solar noon, som gir tom=0.0
      #print(tom)
       cosarg <-0.2618 *tom #radianer pr time
      #dingom<- vector("numeric", 365)
       dingom[tid] <- acos(sin(phi)*sin(theta)+cos(phi)*cos(theta)*cos(cosarg))  #Dingmans zenith angle
       TTList[tid] <- (0.6 + 0.2*sin((0.5*pi)-dingom[tid]))*(1.0-0.5*Cl) #Inspirert av G. Liston 1995 transmissivitet
    #    TTList[tid] <- (0.6-0.2*sin(dingom[tid]))*(1.0-0.5*Cl) #Inspirert av G. Liston 1995 transmissivitet
       #TTList[tid] <- (0.6-0.2*sin(dingom[tid]))*(1.0-0.5*Cl) #Inspirert av G. Liston 1995 transmissivitet
      }
      if((tid < sr) || (tid > ss))  #Hvis klokken er utenfor sunrise-sunset
      {
         TTList[tid] <-0.0 #Transmissivity Disse settes lik null hvis solen er under horisonten
         dingom[tid] <-pi*0.5 #pi/2 minus zenith angle, initielt, ikke hel¯t sikker. Blir veldig lav med init dingom lik pi/2
         #blir pÂ den annen side h¯y med init dingom lik 0 . Albedo ser ganske fornuftig ut
      }
    }
    if(Timeresinsec == 86400)
    {
    Trans <- mean(TTList)
    zen_ang <- mean(dingom)
    }
    if(Timeresinsec < 86400)#Midler transmissvitet og solvinkel For finere tidssoppl¯sning
    {
    interv <-as.integer(Timeresinsec/3600) #hvor mange timer
    Trans <- mean(TTList[(thrx-interv+1):thrx])
    zen_ang <- mean(dingom[(thrx-interv+1):thrx])
    }
    #th30 <- 0.4102*sin((2*pi/365)*((DN-30)-80))
    #Sprim <-117.6*10^3 #[kJ/m^2*day]Sola constant
    S0 <- (117.6*10^3)/86400 #kJ/m2*s

    S0 <- S0*Timeresinsec #solar constant pr timeunit
    print(paste("Solar constant=", S0,Timeresinsec))

    #Albedo MÂ ta med dagens sn¯ for Â regne ut albeo, eller smelter den bare vekk
    SD <- (1000/300)*(SWE+deltaSWE) #[m] bruker 300 kg/m3 som fast tetthet for utregning av albedo i UEB SDi [m]
    #UEB albedo
    albUEB <- AlbedoUEB(PS,SD,TSS,zen_ang,taux,Timeresinsec)
    A_UEB <- albUEB$albedo
    #print(paste("Albedo=",A,"SD=",SD,"taux=",round(taux,3)))
    taux <- albUEB$taux

    #Todd Walters albedo
    print(paste("deltaSWE=",deltaSWE,"SWE=",SWE,"taux=",round(taux,3)))
    albW <- AlbedoWalter(deltaSWE,SWE,Ta,Aprim,Timeresinsec,thrx)
    A_Walter <- albW$albedo
    Aprim <-albW$Aprim
    #Abedo decay
    #if((Timeresinsec ==86400) || (thrx==12))#Oppdatere albedoen
    #{
    # if (deltaSWE ==0.0)
    # {
    #   A <-0.35-(0.35-AX)*exp(-(0.177+log((AX-0.35)/(Aprim-0.35))^2.16))^0.46 #US Army corps of engineers (empirical)
    #   Aprim <- A
    # }
    #Albedo new snow
    #snow density
    #deltaSWe i meter
    # if(deltaSWE > 0.0)
    # {
    #   Srho <-50 +3.4*(Ta+15) #kg/m3, density new snow
    #   A <- AX-(AX-Aprim)*exp(-((4*deltaSWE*Srho)/0.12))
    #   Aprim <- A
    # }
    #}
    #else #vi bruker forrige tidsskritts albedo
    #{
    # A <- Aprim
    #}

    #her velger jeg hvilken albedo variant
    A <-A_UEB
    #A <-A_Walter

    #Solar radiation
    S <-(1-A)*Trans*sin((pi/2)-zen_ang)*S0 #se likning Liston 1995, eq. 26 (NettoSWstrÂling)
    Sinn <-Trans*sin((pi/2)-zen_ang)*S0

    resultsolrad_trans_albedo<- NULL
    resultsolrad_trans_albedo$S<- S
    resultsolrad_trans_albedo$Sinn<- Sinn
    resultsolrad_trans_albedo$A<- A
    resultsolrad_trans_albedo$Aprim<- Aprim
    resultsolrad_trans_albedo$taux<- taux
    resultsolrad_trans_albedo
    }


    '''
    return


def long_wave_from_senorge(prec, temp_atm, temp_surface, snow_depth, ice_thickness, time_span_in_sec):
    '''
    Long wave radiation, both atmospheric and terrestrial, calculated from precipitation and temperature.

    We use the Stefan-Boltzmann equation: L = epsilon * sigma * temp^4
    where epsilon is emissivity and sigma is Stefan-Boltzmann constant.

    :param prec:                Precipitation (?)
    :param temp_atm:            Temperature (C)
    :param time_span_in_sec:     Time resolution gives the Boltzmann constant
    :param temp_surface:
    :param snow_depth:
    :return     L_a:            [kJm^(-2)] is the atmospheric long wave radiation over the given time span
                L_t:            [kJm^(-2)] is the terrestrial long wave radiation over the given time span

    Notes:      W = J / s
    '''

    cloud_cover = clouds_from_precipitation(prec, method='Binary')
    eps_atm = (0.72+0.005*temp_atm)*(1-0.84*cloud_cover)+0.84*cloud_cover    # Atmospheric emissivity from Campbell and Norman, 1998. Emissivity er dimasnjonsløs
    eps_surface = const.eps_snow                       # By default we assume snow cover
    sigma = const.sigma_pr_second * time_span_in_sec   # Stefan-Boltzmann constant over the requested time span

    if snow_depth == 0:
        eps_surface = const.eps_ice           # No snow gives ice emissivity

    if ice_thickness == 0:
        temp_surface == 0                     # water at 0degC
        eps_surface = const.eps_water         # water emissivity is the same as snow emidsitivity

    L_a = eps_atm * sigma * (temp_atm + 273.2)^4            # temp_atm skal være i Celsisus. Atmosfærisk innstsåling
    L_t = eps_surface * sigma * (temp_surface + 273.2)^4    # terrestrisk utstråling emmisivity for snø er 0.97, er ogsÂ brukt for bar bakke, se Dingman p.583

    return L_a, L_t                     # Gir verdier av riktig størrelsesorden og balanserer hverandre sånn passe


def sensible_and_latent_heat_from_senorge(temp_atm, temp_surface, time_span_in_sec,
                                          pressure_atm=None, wind=None):
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


def ground_heat_from_senorge(temp_span_in_sec):
    """
    G [kJm^(-2)] is ground heat conduction to the bottom of the snowpack

    :param temp_span_in_sec:
    :return:
    """

    # Ground heat
    G = 173./86400               # [kJ / second]
    G = G * temp_span_in_sec     # desired resolution

    return G


def prec_heat_from_senorge(temp_atm, prec_rain):
    """
    Heat from liquid precipitation. We assume rainwater has the same temperature as air and that heat is added to the
    snowpack when the rain’s temperature is lowered to zero degrees.

    :param temp_atm:    [C] Air temperature.
    :param prec_rain:   [m] Precipitation as liquid water.
    :return R:          [kJm^-2] Heat added by precipitation
    """


    if prec_rain > 0.:
        R = const.rho_water * const.c_water * prec_rain * temp_atm
    else:
        R = 0.

    return R


def cold_content_from_senorge(ice_column, temp_atm, prec_snow):
    """
    Heat storage (cold content) of the snow and ice.

    :param ice_column:  From previous time step. The column variable has layers with layer.density, layer.height and layer.temp.
    :param prec_snow:   [m] Prec as snow from this time step (new snow)
    :param temp_atm:    [C] air temperature. We assume the new snow has this temp.

    :return CC:         [kJm^-2]

    Dimensions:     kg m^-3 * kJ kg^-1 K^-1 * m * K = kJm^-2
    """

    CC = 0      # kan kun bli negativ eller 0.

    for layer in ice_column.column:
        CC += layer.rho * layer.heat_capacity * layer.height * layer.temperature

    # Add also the new snow
    CC += const.rho_new_snow * const.c_snow * prec_snow * temp_atm

    return  CC


if __name__ == "__main__":

    # Test koordinater i tana
    x_tana = 988130
    y_tana = 7844353
    lat_tana, long_tana = lat_long_from_utm33(x_tana, y_tana)


    # Test Filefjell
    y_file = 6802070
    x_file = 130513
    lat_file, long_file = lat_long_from_utm33(x_file, y_file)

    short_wave_from_senorge()

    a = 1

























