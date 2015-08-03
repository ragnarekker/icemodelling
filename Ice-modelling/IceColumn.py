__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

# http://learntofish.wordpress.com/2011/12/06/tutorial-object-oriented-programming-in-python-part-2/
# http://www.python-course.eu/object_oriented_programming.php

import math
import datetime
import calculateParameterization as pz


class IceColumn:

    def __init__(self, date_inn, column_inn):
        '''
        This initializes the object
        An empty column is initiallized as iceColumn(dateobject, 0)
        Column_inn includes new snow layer on index 0.

        :param date_inn:        [datetime]
        :param column_inn:      list[float, string] as [[height, layertype], [height, layertype], ...]
        :return:
        '''

        self.set_constants()

        self.date = date_inn                 # date
        self.column = 0                      # icecolumn with [layer thickness, layer type].
        self.water_line = -1                 # distance from bottom of ice column to the water surface. Negative number meens not initiallized
        self.draft_thickness = -1            # This is ice, slushice and slush layers. I.e. not snow layers
        self.metadata = {}                   # Metadata given as dictionary {key:value , key:value, ... }
        self.top_layer_is_slush = None

        ### initialize waterline better
        ### calculate old height of draft better with use of density? and the old snow layers?

        if column_inn == 0:         # the case of no ice
            self.column = list()
            self.water_line = -1
            self.draft_thickness = -1
        else:
            self.column = column_inn
            self.water_line = -1
            self.draft_thickness = -1

    def set_constants(self):
        '''
        Listed constants that assosiated with ice and snow types. These are defaults.
        The constants follow the object and can intentionally be updated for every icecolumn.

        :return:
        '''

        #Constants that assosiated with ice and snow types.

        # LayerTypes given as enums. Values 0-9 are liquids, 10-19 are ice, 20-29 are snow
        self.enum_new_snow = 20
        self.enum_snow = 21
        self.enum_drained_snow = 22
        self.enum_slush = 2
        self.enum_slush_ice = 11
        self.enum_black_ice = 10
        self.enum_water = 1
        self.enum_NA = -1

        # Material temperatures [degC]
        self.temp_f = 0                      # freezing temp

        # Desities [kg m-3]
        self.rho_snow_max = 450.             # maximum snow density (kg m-3)
        self.rho_new_snow = 250.             # new-snow density (kg m-3)
        self.rho_snow = 350.                 # average snowdensity.
        self.rho_drained_snow = self.rho_snow
        self.rho_slush = 0.920*10**3         # from Vehvilainen (2008) and again Saloranta (2000)
        self.rho_slush_ice = 0.875*10**3     # from Vehvilainen (2008) and again Saloranta (2000)
        self.rho_black_ice = 0.917*10**3     # ice (incl. snow ice) density [kg m-3]
        self.rho_water = 1000.               # density of freshwater (kg m-3)

        # ice heat conduction coefficient/thermal conductivity [W K-1 m-1]
        self.k_snow_max = 0.25               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
        self.k_new_snow = 0.05               # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
        self.k_snow = 0.11                   # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
        self.k_drained_snow = self.k_snow
        self.k_slush = 0.561                 # from Vehvilainen (2008) and again Saloranta (2000)
        self.k_black_ice = 2.24              # from Vehvilainen (2008) and again Saloranta (2000)
        self.k_slush_ice = 0.5 * self.k_black_ice # from Vehvilainen (2008) and again Saloranta (2000)
        self.k_water = 0.58                  # from http://www.engineeringtoolbox.com/thermal-conductivity-d_429.html

        # Latent heat of fusion [J kg-1]
        self.L_black_ice = 333500                   # latent heat of freezing water to black ice
        self.L_slush_ice = 0.5 * self.L_black_ice   # freezing slush to slushice

        self.alfa_black_ice = 35             # albedo in % from http://en.wikipedia.org/wiki/Albedo
        self.alfa_snow_new = 85              # albedo in % from http://en.wikipedia.org/wiki/Albedo
        self.alfa_snow_old = 45              # albedo in % from http://en.wikipedia.org/wiki/Albedo

        # The meltingcoeficients for the degreeday formula [m s-1 degC-1]
        self.meltingcoeff_snow = -0.10 /(60*60*24) / 5              # 10cm melting pr day at 5degC
        self.meltingcoeff_slush_ice = -0.04 /(60*60*24) / 5         #  4cm melting pr day at 5degC
        self.meltingcoeff_slush = self.meltingcoeff_slush_ice * 2   #  slush is partlymelted
        self.meltingcoeff_black_ice = -0.02 /(60*60*24) / 5         #  2cm melting pr day at 5degC

        # The more quaziscientific constants
        self.snow_pull_on_water = 0.05       # The length watrer is pulled upp into the snow by capillary fources [m]
        self.min_slush_change = 0.05         # If slushlevelchange is lower than this value the no new slushlevel is made
        self.snow_to_slush_ratio = 0.33      # when snow becomes slush when water is pulled up it also is compressed

    def add_metadata(self, key, value):
        self.metadata[key] = value

    def set_water_line(self, water_line_inn):
        self.water_line = water_line_inn

    def addLayerAtIndex(self, index, height, layertype):
        '''
        Adds a new layer at a given index in icecolumn. Subsequent layers are added after the new layer.
        If height is None nothing is done.

        :param index:
        :param height:          Should be float but variable is parsed to float so string is acceted
        :param layertype:
        :return:                no return
        '''

        if height != None:
            height = float(height) # cast to int
            if index == -1:
                self.column.append([height, layertype])
            else:
                self.column.insert(index, [height, layertype])

    def removeLayerAtIndex(self, index):
        # Removes a layer at a given index
        self.column.pop(index)

    def timestepForward(self, timestep):
        '''
        Step the date forward the timedelta of "timestep"
        :param timestep:
        :return:
        '''
        self.date = self.date + datetime.timedelta(seconds = timestep)

    def mergeAndRemoveExcessLayers(self):
        '''
        Cleans up the icecolumn a bit. Removes layers of zero height if they occur and merges layers of equal type
        if the exist

        :return:
        '''

        # If no column there is nothing to merge
        if len(self.column) != 0:

            # Goes through the ice column to find layers of zero height and removes them
            i = 0
            condition = True        # The condition for looping through the column.

            while condition:
                if self.column[i][0] == 0.:
                    self.column.pop(i)
                    i = i - 1   # poping one shortens the list an thus the index counter should go back with it
                i = i + 1
                if i >= len(self.column):
                    condition = False

            # Find neighbouring layers of equal type and merges them
            last_checked_layer_type = 'NA'
            i = 0
            condition = True
            while condition:
                if self.column[i][1] == last_checked_layer_type:
                    self.column[i-1][0] = self.column[i-1][0] + self.column[i][0]
                    self.column.pop(i)
                    i = i - 1   # the current layer was removed so the index must be moved back one step
                last_checked_layer_type = self.column[i][1]
                i = i + 1
                if i >= len(self.column):
                    condition = False

    def update_slush_level(self):
        '''
        Updates slushlevel by balancing bouyency of icelayers with weight of snow

        :return:
        '''

        self.update_draft_thickness()
        self.update_water_line()

        # We get more slush if pressure from snow is great enough to push all ice below the water dh_slush > 0.
        dh_slush = self.water_line - self.draft_thickness

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
        self.update_water_line()     # due to the snow pulling water up in the snow the waterline is shifted since before uppdatig the slushlevel

    def update_draft_thickness(self):
        '''
        Method updates the iceColumns draft_thickness variable. The draft height given by summing ice, slush ice and
        slush layers. I.e. not snow layers (and not the surface slush layer)
        '''

        draft_thickness = 0

        for l in self.column:
            if draft_thickness == 0 and self.getEnum(l[1]) > 20:      # material types >= 20 are snow
                continue
            #elif draft_thickness == 0 and self.getEnum(l[1]) == 2:    # slush over the ice does not count
            #    continue
            else:
                draft_thickness = draft_thickness + l[0]

        self.draft_thickness = draft_thickness

    def update_water_line(self):
        '''
        Method updates the iceColumns water line variable. This is the distance from the bottom of the ice to the
        waterline. The height of the draft submerged under the water line given by arkimedes law.

        :return:
        '''

        column_mass = 0
        for l in self.column:
            column_mass = column_mass + l[0]*self.getRho(l[1])     # height*density = [kg/m2]
        water_line = column_mass/self.rho_water        # [kg/m2]*[m3/kg]
        self.water_line = water_line

    def update_top_layer_is_slush(self):
        '''
        Tests if the top most ice column layer is slush. Updates the objects top_layer_is_slush prameter.
        Returns true if it is.

        :return: [Bool] True if topp layer is slush. False if not.
        '''

        for l in self.column:
            if self.getEnum(l[1]) > 20:      # material types >= 20 are snow
                continue
            elif self.getEnum(l[1]) == 2:    # slush over the ice does not count
                self.top_layer_is_slush = True
                return True
            else:
                self.top_layer_is_slush = False
                return False

    def mergeSnowlayersAndCompress(self, temp):
        '''
        Merges the snow layers and compresses the snow. This method updates the snow density in the object and the
        conductivity of the snow in the object.

        Snow compactation may be referenced in article in literature folder or evernote.

        :param temp: [float] Temperature in celcuis used in the compactation routine.
        :return:
        '''

        # If no layers, compacation of snow is not needed
        if len(self.column) > 0:
            # declare the new snow layer (index = 0) as normal snow layer
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
                k_snow_new = pz.k_snow_from_rho_snow(rho_snow_new)

            # Else we have meltingconditions and the snow conductivuty and density is sett to max
            else:
                rho_snow_old = self.rho_snow
                rho_snow_new = self.rho_snow_max
                k_snow_new = self.k_snow_max

            self.rho_snow = min([rho_snow_new, self.rho_snow_max])
            self.k_snow = min([k_snow_new, self.k_snow_max])

            h_snow_new = self.column[0][0] / self.rho_snow * rho_snow_old    # Asume a inverse linear correlation between density and the height (preservation og mass?)
            self.column[0][0] = h_snow_new

    def getConductivity(self, type):
        # returns the conductivity for a given snow or ice type

        if type == 'new_snow': return self.k_new_snow
        elif type == 'snow': return self.k_snow
        elif type == 'drained_snow': return self.k_drained_snow
        elif type == 'slush': return self.k_slush
        elif type == 'slush_ice': return self.k_slush_ice
        elif type == 'black_ice': return self.k_black_ice
        elif type == 'water': return self.k_water
        elif type == 'unknown': return self.k_slush_ice
        else: return self.k_slush_ice

    def getRho(self, type):
        # returns the density for a given snow or ice type

        if type == 'new_snow': return self.rho_new_snow
        elif type == 'snow': return self.rho_snow
        elif type == 'drained_snow': return self.rho_drained_snow
        elif type == 'slush': return self.rho_slush
        elif type == 'slush_ice': return self.rho_slush_ice
        elif type == 'black_ice': return self.rho_black_ice
        elif type == 'water': return self.rho_water
        elif type == 'unknown': return self.rho_slush_ice
        else: return self.rho_slush_ice

    def getEnum(self, type):
        # returns the enum used for a given snow or ice type

        if type == 'new_snow': return self.enum_new_snow
        elif type == 'snow': return self.enum_snow
        elif type == 'drained_snow': return self.enum_drained_snow
        elif type == 'slush': return self.enum_slush
        elif type == 'slush_ice': return self.enum_slush_ice
        elif type == 'black_ice': return self.enum_black_ice
        elif type == 'water': return self.enum_water
        elif type == 'unknown': return self.enum_slush_ice
        else: return self.enum_NA

    def getColour(self, type):
        # returns the color used for plotting a given snow or ice type

        if type == 'new_snow': return "0.9"
        elif type == 'snow': return "0.8"
        elif type == 'drained_snow': return "0.7"
        elif type == 'slush': return "blue"
        elif type == 'slush_ice': return "0.4"
        elif type == 'black_ice': return "0.1"
        elif type == 'water': return "red"
        elif type == 'unknown': return "orange"
        else: return "yellow"

def tests():
    # some tests of the functions in the IceColumn.py file

    date = datetime.datetime.strptime("2011-10-05", "%Y-%m-%d")
    icecol = IceColumn(date, 0)
    #icecol.addLayerAtIndex(0, 0.1, 'new_snow')
    #icecol.update_slush_level()
    #icecol.mergeAndRemoveExcessLayers()
    icecol.mergeSnowlayersAndCompress(-5)


