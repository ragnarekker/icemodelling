__author__  =  'raek'
""""""

import math

rho_fw = 1000.        # density of freshwater (kg m-3)
temp_f = 0            # freezing temp
rho_new_snow=250   #new-snow density (kg m-3)
max_rho_snow=450   #maximum snow density (kg m-3)
rho_si = rho_ice
rho_slush = rho_fw



k_ice = 2.24            # ice heat conduction coefficient [W K-1 m-1]
rho_ice = 0.917*10**3   # ice (incl. snow ice) density [kg m-3]
L_ice=333500            # latent heat of freezing (J kg-1)
alfa_ice = 35           # albedo (%) from http://en.wikipedia.org/wiki/Albedo
alfa_snow_new = 85      # albedo (%) from http://en.wikipedia.org/wiki/Albedo
alfa_snow_old = 45      # albedo (%) from http://en.wikipedia.org/wiki/Albedo

# ice & snow parameter values
C1=7.0             #snow compaction coefficient #1
C2=21.0            #snow compaction coefficient #2


# h_ice
# h_si
# h_snow
# h_snow_new
# temp
# rho_snow
# Q_sw      energy from shortwave
# Q_lw      heat form longwave
# Q_l       latent heat of snowsnowmelting (icemelting also?)
# timetep   60*60*24 is 24hrs

def getIceThickness(h_ice, h_si, h_snow, dh_snow, h_slush, temp, rho_snow, Q_sw, Q_lw, Q_l, timestep):

    # uppdate the snowvariables with the new snow
    rho_snow = (h_snow*rho_snow + dh_snow*rho_new_snow)/(h_snow+dh_snow)
    h_snow = h_snow + dh_snow

    # the height of the draft (the waterlevel) given by arkimedes law?
    h_draft = ( h_ice*rho_ice + h_si*rho_si + h_slush*rho_slush + h_snow*rho_snow )/rho_fw
    # utdate slushlevel if preassure from snow is great enough
    if h_draft > h_ice+h_si+h_slush:
        h_slush = h_draft-h_ice-h_si

    # if air temperature is FREEZING
    if temp < temp_f:

        # Calculate ice surface temperature (temp_ice) and height of slush ice (h_si + dh_si)
        if dh_snow == 0:                    # if no new snow
            alfa = 1/10/h_ice               # what is alfa? Something to do with icetemperature? [m-1]
            dh_si = 0                       # no new snow gives no aditional snow ice
        else:
            k_snow = 2.22362 * (rho_snow/1000)**1.885                     # Yen (1981)
            alfa = (k_ice/k_snow)*(h_snow/h_ice)                        # dimensjonsløs? []
            dh_si = max([0, h_ice * ( rho_ice/rho_fw - 1 ) + h_snow ])  # Slush/snow ice formation (directly to ice) always growth when teperatures below freezing

        temp_ice = ( alfa * temp_f + temp )/( 1 + alfa )

        h_si = h_si + dh_si
        #Ice growth by Stefan's law
        h_ice_new = math.sqrt( (h_ice+dh_si)**2 + (2*k_ice/(rho_ice*L_ice)) * timestep*(temp_f - temp_ice) )

        #subtract snow-to-snow-ice formation from new snow
        h_snow_new = dh_snow - h_si*(rho_ice/rho_fw)                 # new precipitation minus snow-to-snow-ice in snow water equivalent
        dh_si = 0                                                       # reset new snow-ice formation

    # if air temperature is MELTING
    else:
        q = (1-lambda_si)*Q_sw + Q_lw + Q_l             # heat flux
        temp_ice = temp_f                               # ice surface at freezing point
        swe_snow_new = 0                                # No new snow
        if (swe_snow > 0):                              # snow melting in water equivalents
            dswe_snow = -max([0, timestep*q/rho_fw/L_ice])
            if ((swe_snow+dswe_snow) < 0):       #if more than all snow melts...
                h_ice_new = h_ice+(swe_snow+dswe_snow)*(rho_fw/rho_ice) #...take the excess melting from ice thickness
            else:
                h_ice_new = h_ice #ice does not melt until snow is melted away
        else:
            #total ice melting
            dswe_snow = 0
            h_ice_new = h_ice - max([0, timestep*q/rho_ice/L_ice])
            #snow ice part melting
            h_si = h_si - max([0, timestep*q/rho_ice/L_ice])
            if (h_si <= 0):
                h_si = 0

    # Update ice and snow thicknesses
    h_ice = h_ice_new               # new ice thickness
    h_si = h_si
    h_snow = h_snow + h_snow_new

    #Update snow density as weighed average of old and new snow densities
    rho_snow = rho_snow_new

    #snow compaction
    if (temp<temp_f) : #if air temperature is below freezing
        rhos = 1e-3*rho_snow #from kg/m3 to g/cm3
        delta_rhos = 24*rhos*C1*(0.5*swe_snow)*exp(-C2*rhos)*exp(-0.08*(temp_f-0.5*(temp_ice+temp)))
        rho_snow = min([rho_snow+1e+3*delta_rhos, max_rho_snow])  #from g/cm3 back to kg/m3
    else:
       rho_snow = max_rho_snow

