__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

# http://learntofish.wordpress.com/2011/12/06/tutorial-object-oriented-programming-in-python-part-2/
# http://www.python-course.eu/object_oriented_programming.php
#

import math
import datetime

from Calculations import parameterization


class IceColumn:

    # parameters to be initialized in constructor
    date = 0                        # date not initiallized
    column = 0                      # icecolumn with [layer thickness, layer type].
    water_line = -1                 # distance from bottom of ice column to the water surface. Negative number meens not initiallized
    draft_height = -1

    # constants that follow ice ans snow types.
    # They are not protected so they can be updated outside the class

    # LayerTypes given as enums. Values 0-9 are liquids, 10-19 are ice, 20-29 are snow
    enum_new_snow = 20
    enum_snow = 21
    enum_drained_snow = 22
    enum_slush = 2
    enum_slush_ice = 11
    enum_black_ice = 10
    enum_water = 1
    enum_NA = -1

    # Material temperatures [degC]
    temp_f = 0                      # freezing temp

    # Desities [kg m-3]
    rho_snow_max = 450.             # maximum snow density (kg m-3)
    rho_new_snow = 250.             # new-snow density (kg m-3)
    rho_snow = 350.                 # average snowdensity.
    rho_drained_snow = rho_snow
    rho_slush = 0.920*10**3         # from Vehvilainen (2008) and again Saloranta (2000)
    rho_slush_ice = 0.875*10**3     # from Vehvilainen (2008) and again Saloranta (2000)
    rho_black_ice = 0.917*10**3     # ice (incl. snow ice) density [kg m-3]
    rho_water = 1000.               # density of freshwater (kg m-3)
    rho_NA = -1.                    # value to return if desity is not available.

    # ice heat conduction coefficient/thermal conductivity [W K-1 m-1]
    k_snow_max = 0.25               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
    k_new_snow = 0.05               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
    k_snow = 0.11                   # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
    k_drained_snow = k_snow
    k_slush = 0.561                 # from Vehvilainen (2008) and again Saloranta (2000)
    k_black_ice = 2.24              # from Vehvilainen (2008) and again Saloranta (2000)
    k_slush_ice = 0.5 * k_black_ice # from Vehvilainen (2008) and again Saloranta (2000)
    k_water = 0.58                  # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
    k_NA = -1

    # Latent heat of fusion [J kg-1]
    L_black_ice = 333500            # latent heat of freezing water to black ice
    L_slush_ice = 0.5 * L_black_ice # freezing slush to slushice

    alfa_black_ice = 35             # albedo in % from http://en.wikipedia.org/wiki/Albedo
    alfa_snow_new = 85              # albedo in % from http://en.wikipedia.org/wiki/Albedo
    alfa_snow_old = 45              # albedo in % from http://en.wikipedia.org/wiki/Albedo

    # The meltingcoeficients for the degreeday formula [m s-1 degC-1]
    meltingcoeff_snow = -0.10 /(60*60*24) / 5           # 10cm melting pr day at 5degC
    meltingcoeff_slush_ice = -0.04 /(60*60*24) / 5      #  4cm melting pr day at 5degC
    meltingcoeff_slush = meltingcoeff_slush_ice * 2     #  slush is partlymelted
    meltingcoeff_black_ice = -0.02 /(60*60*24) / 5      #  2cm melting pr day at 5degC

    # The more quaziscientific constants
    snow_pull_on_water = 0.05          # The length watrer is pulled upp into the snow by capillary fources [m]
    min_slush_change = 0.05         # If slushlevelchange is lower than this value the no new slushlevel is made
    snow_to_slush_ratio = 0.33          # when snow becomes slush when water is pulled up it also is compressed

    # Constructor-like-thingy
    # an empty column is initiallized as iceColumn(dateobject, 0)
    def __init__(self, date_inn, column_inn):
        self.date = date_inn
        if column_inn == 0:         # the case of no ice
            self.column = list()
            self.water_line = -1
        else:
            self.column = column_inn
            self.water_line = -1

            ### initialize waterline better
            ### calculate old height of draft better with use of density? and the old snow layers?

    # Adds a new layer at a given index in icecolumn. Subsequent layers are added after the new layer.
    def addLayerAtIndex(self, index, height, layertype):
        if index == -1:
            self.column.append([height, layertype])
        else:
            self.column.insert(index, [height, layertype])

    # Removes a layer at a given index
    def removeLayerAtIndex(self, index):
        self.column.pop(index)

    # Step the date forward the timedelta of "timestep"
    def timestepForward(self, timestep):
        self.date = self.date + datetime.timedelta(seconds = timestep)

    # Cleans up the icecolumn a bit. Removes layers of zero height if they occur and merges layers of equal type if the exist
    def mergeAndRemoveExcessLayers(self):

        # If no colum there is nothing to merge
        if len(self.column) != 0:

            # Goes through the icecolumn to find layes of zero heigh and removes them
            i = 0
            condition = 0   # The condition for looping through the column. Couldnt use i since the list is shortend while i the loop..

            while condition == 0:
                if self.column[i][0] == 0.:
                    self.column.pop(i)
                i = i + 1
                if i >= len(self.column):
                    condition = 1

            # Find neihbouring layers of equal type and merges them
            last_checked_layertype = 'NA'
            i = 0
            condition = 0
            while condition == 0 :
                if self.column[i][1] == last_checked_layertype:
                    self.column[i-1][0] = self.column[i-1][0] + self.column[i][0]
                    self.column.pop(i)
                    i = i - 1   # the current layer was removed so the index must be moved back one step
                last_checked_layertype = self.column[i][1]
                i = i + 1
                if i >= len(self.column):
                    condition = 1

    # Updates slushlevel by balancing bouyency of icelayers with weight of snow
    def updateSlushLevel(self):

        self.updateDraftHeight()
        self.updateWaterLine()

        # We get more slush if pressure from snow is great enough to push all ice below the water dh_slush > 0.
        dh_slush = self.water_line - self.draft_height

        # We also have a constant regulating the minimum change before we get a slush event
        if dh_slush > self.min_slush_change:

            # Cappilary forces pull water up past the eqlibriumline
            dh_slush = dh_slush + self.snow_pull_on_water

            # find index of deepest snow layer. Slush forms at the bottom of this layer.
            index = 0
            for i in range(len(self.column)):
                if self.getEnum(self.column[i][1]) >= 20:       # material types >= 20 are snow
                    index = i                   # keep counting the index until we reach bottom of the snow.

            # reduce the deepest snow layer with the dh_slush and if snowlayer isnt big enough go to the
            # abowe and make this layer wet aswell (and so on).
            while dh_slush > 0 and index >= 0:
                # if the layer is to shalow all is flodded with water and made to slush. Note that the layer is compressed as a result of adding water to snow.
                if dh_slush > self.column[index][0] * self.snow_to_slush_ratio:
                    self.column[index][1] = 'slush'
                    self.column[index][0] = self.column[index][0] * self.snow_to_slush_ratio
                    dh_slush = dh_slush - self.column[index][0]     # remember that this layer has been uppdated to the new layer height on the previous line
                    index = index - 1
                # take a part of the layer and make a new snushlayer under it.
                else:
                    self.column[index][0] = self.column[index][0] - dh_slush / self.snow_to_slush_ratio
                    self.addLayerAtIndex(index+1,dh_slush,'slush')
                    index = -1


        # reduse slushlevel if pressure from snow goes away (e.g. windtransport, melting etc).
        # The result is slush drained back to snow. (Probably only a theoretical posibility?)
        # elif dh_slush < 0.01:
        #
        #     # find the topmost slushlayer
        #     i_start = 0
        #     for i in range (len(self.column)):
        #         if self.column[i][1] == 'slush':
        #             i_start = i
        #             break
        #
        #     # Drain it with dh_slush (negative number)
        #     for i in range(i_start, len(self.column), 1):
        #         # if we have slush layer and need a change in slush level
        #         if self.column[i][1] == 'slush' and dh_slush < 0:
        #             if self.column[i][0] >= -dh_slush:               # if layer is thick enought to only be partly drained
        #                 self.column[i][0] = self.column[i][0] + dh_slush
        #                 self.addLayerAtIndex(i, -dh_slush, 'drained_snow')
        #                 dh_slush = 0                                # we have equlibrium in the icecoulumn
        #             else:                                           # slushlayer is shalower than the change in slushlayer
        #                 self.column[i][1] = 'drained_snow'          # Slush layer is completely drained. We set layertype to drained_snow.
        #                 dh_slush = dh_slush + self.column[i][0]     # updated slush level change which will effect the next slushlayer
        #         # if we dont have a slush layer but still need change
        #         elif self.column[i][1] != 'slush' and dh_slush < 0:
        #             dh_slush = dh_slush + self.column[i][0]
        #         elif dh_slush >= 0:
        #             break

        # Remove layers of height = 0 and merge neighbouring layers of equal type
        self.mergeAndRemoveExcessLayers()
        self.updateWaterLine()     # due to the snow pulling water up in the snow the waterline is shifted since before uppdatig the slushlevel

    # method updates the iceColumns draft height variable. This is ice, slushice and slush layers. I.e. not snow layers
    def updateDraftHeight(self):

        # the draft height given by summing ice, slushice and slush layers. I.e. not snow layers
        thickness_ice = 0
        for i in range(len(self.column)):
            if self.getEnum(self.column[i][1]) < 20:       # material types >= 20 are snow
                thickness_ice = thickness_ice + self.column[i][0]
        self.draft_height = thickness_ice

    # method updates the iceColumns water line variable. This is the distance from the botom of the ice to the waterline.
    def updateWaterLine(self):
        # the height of the draft submerged under the water line given by arkimedes law
        h_draft = 0
        for i in range(len(self.column)):
            h_draft = h_draft + self.column[i][0]*self.getRho(self.column[i][1])     # height*density = [kg/m2]
        h_draft = h_draft/self.rho_water        # [kg/m2]*[m3/kg]
        self.water_line = h_draft

    # merges the snowlayers and compresses the snow. This method updates the snow denity in the object and the conductivity of the snow in the object
    def mergeSnowlayersAndCompress(self, temp):

        # If no layers, compacation of snow is not needed
        if len(self.column) > 0:
            # declare the new snow layer (index = 0) as normal snowlayer
            if self.column[0][1] == 'new_snow':
                self.column[0][1] = 'snow'
                if len(self.column) > 1:
                    # If more snow layers merge the snowlayer to one with the old snowlayer beneeth (index = 1)
                    if self.column[1][1] == 'snow':
                        # New density becomes avarage og snow densities
                        self.rho_snow = ( self.column[0][0]*self.rho_new_snow + self.column[1][0]*self.rho_snow ) / (self.column[0][0] + self.column[1][0])
                    # Else the new density is that of new snow
                    else:
                        self.rho_snow = self.rho_new_snow

            self.mergeAndRemoveExcessLayers()

            # we use a formula for compactation only if air temperature is below freezing and there is snow on top
            if temp < self.temp_f and self.column[0][1] == 'snow':

                # ice & snow parameter values
                C1=7.0*1e-3*12      #snow compaction coefficient #1
                C2=-21.0*1e-3       #snow compaction coefficient #2
                C3=-0.04            #snow compaction coefficient #3

                # this is one strange fromula. Would be good to change it with something more familiar..
                delta_rho_snow = self.rho_snow**2 * C1 * self.column[0][0] * math.exp(C2*self.rho_snow) * math.exp(C3*temp)

                rho_snow_old = self.rho_snow
                rho_snow_new = rho_snow_old + delta_rho_snow
                k_snow_new = parameterization.k_snow_from_rho_snow(rho_snow_new)

            # Else we have meltingconditions and the snow conductivuty and density is sett to max
            else:
                rho_snow_old = self.rho_snow
                rho_snow_new = self.rho_snow_max
                k_snow_new = self.k_snow_max

            self.rho_snow = min([rho_snow_new, self.rho_snow_max])
            self.k_snow = min([k_snow_new, self.k_snow_max])

            h_snow_new = self.column[0][0] / self.rho_snow * rho_snow_old    # Asume a inverse linear correlation between density and the height (preservation og mass?)
            self.column[0][0] = h_snow_new

    # returns the conductivity for a given snow or ice type
    def getConductivity(self, type):

        if type == 'new_snow': return self.k_new_snow
        elif type == 'snow': return self.k_snow
        elif type == 'drained_snow': return self.k_drained_snow
        elif type == 'slush': return self.k_slush
        elif type == 'slush_ice': return self.k_slush_ice
        elif type == 'black_ice': return self.k_black_ice
        elif type == 'water': return self.k_water
        else: return self.k_NA

    # returns the density for a given snow or ice type
    def getRho(self, type):

        if type == 'new_snow': return self.rho_new_snow
        elif type == 'snow': return self.rho_snow
        elif type == 'drained_snow': return self.rho_drained_snow
        elif type == 'slush': return self.rho_slush
        elif type == 'slush_ice': return self.rho_slush_ice
        elif type == 'black_ice': return self.rho_black_ice
        elif type == 'water': return self.rho_water
        else: return self.rho_NA

    # returns the density for a given snow or ice type
    def getEnum(self, type):

        if type == 'new_snow': return self.enum_new_snow
        elif type == 'snow': return self.enum_snow
        elif type == 'drained_snow': return self.enum_drained_snow
        elif type == 'slush': return self.enum_slush
        elif type == 'slush_ice': return self.enum_slush_ice
        elif type == 'black_ice': return self.enum_black_ice
        elif type == 'water': return self.enum_water
        else: return self.enum_NA

    # returns the density for a given snow or ice type
    def getColour(self, type):

        if type == 'new_snow': return "0.9"
        elif type == 'snow': return "0.8"
        elif type == 'drained_snow': return "0.7"
        elif type == 'slush': return "blue"
        elif type == 'slush_ice': return "0.4"
        elif type == 'black_ice': return "0.1"
        elif type == 'water': return "red"
        else: return "yellow"

# some tests of the functions in the IceColumn.py file
def tests():

    date = datetime.datetime.strptime("2011-10-05", "%Y-%m-%d")
    icecol = IceColumn(date, 0)
    #icecol.addLayerAtIndex(0, 0.1, 'new_snow')
    #icecol.updateSlushLevel()
    #icecol.mergeAndRemoveExcessLayers()
    icecol.mergeSnowlayersAndCompress(-5)


