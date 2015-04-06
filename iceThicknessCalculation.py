__author__  =  'raek'
# -*- coding: utf-8 -*-

import math

import numpy
from Calculations import parameterization

def getIceThickness(*args):

    '''
    :param ic:          Ice column at the beginneing of the timestep.  object containng the icolumn with metadata
    :param dh_snow:     new snow in period of timestep. Given as float in SI uniuts [m]
    :param temp:        average temerature in period of timestep. Given i C as float.
    :param timestep:    in seconds. 60*60*24 = 86400 is 24hrs
    :return:            Ice column at end of timestep
    '''

    ic = args[0]
    timestep = args[1]

    dh_snow = args[2]
    temp = args[3]


    if len(args) == 4:
        temp = temp
        # temp = parameterization.tempFromTempAndSnow(temp, dh_snow)
    elif len(args) == 5:
        cc = args[4]
        temp = parameterization.tempFromTempAndClouds(temp, cc)
    else:
        print('Unknown number of arguments.')


    ic.timestepForward(timestep)      # after the calculation we are one day further down the winter

    if len(ic.column) != 0:

        # add new snow on top if we have ice
        if dh_snow != 0.:
            ic.addLayerAtIndex(0, dh_snow, 'new_snow')

        # Update the slushlevel given new snow and that measurements can be made without ice being in equlibrium with bouancy
        ic.updateSlushLevel()

    # if air temperature is FREEZING
    if temp < ic.temp_f:

        # If no ice, freeze water to ice
        if len(ic.column) == 0:
            dh = math.sqrt(numpy.absolute(2 * ic.k_black_ice / ic.rho_black_ice / ic.L_black_ice * temp * timestep))
            ic.addLayerAtIndex(0, dh, 'black_ice')
            timestep = 0
        else:

            # Decleration of total conductance of layes above freezing layer
            U_total = 0.
            i = 0
            while timestep > 0 and i <= len(ic.column)-1:

                # If the layer is a solid it only adds to the total isolation. Unless it is the last..
                if (ic.getEnum(ic.column[i][1])) > 9:
                    U_total = addLayerConductanceToTotal(U_total, ic.getConductivity(ic.column[i][1]), ic.column[i][0])

                    # If the layer is the last layer of solids and thus at the bottom, we get freezing at the bottom
                    if i == len(ic.column)-1:

                        # The heat flux equation gives how much water will freeze
                        dh = - temp * U_total * timestep / ic.rho_water / ic.L_black_ice
                        ic.addLayerAtIndex(i+1, dh, 'black_ice')
                        timestep = 0

                # Else the layer is a slushlayer above or in the icecolumn and it will freeze fully or partially
                else:
                    timestep_used = 0
                    if i == 0: # there is slush surface whith no layers with conductance above
                        dh = math.sqrt(numpy.absolute(2 * ic.k_slush_ice / ic.rho_slush_ice / ic.L_slush_ice * temp * timestep))    # formula X?
                        timestep_used = ic.column[i][0]**2 * ic.rho_slush_ice * ic.L_slush_ice / 2 /  -temp / ic.k_slush_ice        # formula X sortet for time
                    else:
                        dh = - temp * U_total * timestep / ic.getRho(ic.column[i][1]) / ic.L_slush_ice                              # The heat flux equation gives how much slush will freeze
                        timestep_used = ic.column[i][0] * ic.rho_slush_ice * ic.L_slush_ice / -temp / U_total                       # The heat flux equation sorted for time

                    # If a layer totaly freezes during the timeperiod, the rest of the time will be used to freeze a layer further down
                    if ic.column[i][0] < dh:
                        ic.column[i][1] = 'slush_ice'
                        timestep = timestep - timestep_used
                        U_total = addLayerConductanceToTotal(U_total, ic.getConductivity(ic.column[i][1]), ic.column[i][0])

                    # Else all energy is used to freeze the layer only partially
                    else:
                        ic.column[i][0] = ic.column[i][0] - dh
                        ic.addLayerAtIndex(i, dh, 'slush_ice')
                        timestep = 0

                # Go to next icelayer
                i = i + 1


    # if air temperature is MELTING
    else:
    # all melting is made by simle degreeday model using different calibration constants for snow, slushice and blackice
    # melting only effects the topp layer (index = 0)
        meltingcoeff = -1
        while timestep > 0 and len(ic.column) > 0:
            if ic.column[0][1] == 'water':
                ic.removeLayerAtIndex(0)
            else:
                if ic.getEnum(ic.column[0][1]) >= 20: # snow
                    meltingcoeff = ic.meltingcoeff_snow
                elif ic.column[0][1] == 'slush_ice':
                    meltingcoeff = ic.meltingcoeff_slush_ice
                elif ic.column[0][1] == 'slush':
                    meltingcoeff = ic.meltingcoeff_slush
                elif ic.column[0][1] == 'black_ice':
                    meltingcoeff = ic.meltingcoeff_black_ice
                else:
                    print("Melting: Unknown layertype")

                # degreeday melting. I have sepparated the timefactor from the meltingcoefficiant.
                dh = meltingcoeff * timestep * (temp - ic.temp_f)

                # if layer is thinner than total melting the layer is removed and the rest of melting occurs
                # in the layer below for the reminder of time. melting (dh) and time are proportional in the degreeday equation
                if ic.column[0][0] < -dh:
                    timestep_used = ic.column[0][0] / -dh * timestep
                    ic.removeLayerAtIndex(0)
                    timestep = timestep - timestep_used

                # the layer is only partly melted during this timestep
                else:
                    ic.column[0][0] = ic.column[0][0] + dh
                    timestep = 0

    ic.mergeAndRemoveExcessLayers()
    ic.mergeSnowlayersAndCompress(temp)
    ic.updateWaterLine()

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

