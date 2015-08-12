__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-


import math
import datetime
import doparameterization as pz
import constants as const
import getRegObsdata as gro


class IceColumn:
    def __init__(self, date_inn, column_inn):
        '''
        This initializes the object
        An empty column is initialized as iceColumn(date as datetime, 0)
        Column_inn includes new snow layer on index 0.

        :param date_inn:        [datetime]
        :param column_inn:      list[IceLayers]
        :return:
        '''

        self.date = date_inn  # Date
        self.column = 0  # Ice column with [IceLayers].
        self.water_line = -1  # Distance from bottom of ice column to the water surface. Negative number meens not initiallized
        self.draft_thickness = -1  # This is ice, slush ice and slush layers. I.e. not snow layers
        self.metadata = {}  # Metadata given as dictionary {key:value , key:value, ... }
        self.top_layer_is_slush = None  # [Bool] True if top layer is slush. False if not.
        self.column_average_temperature = 0  # avg temperature used in energy balance calculations
        self.last_days_temp_atm = [0, 0, 0, 0, 0]  # index zero is current and 1 is yesterday etc.

        if column_inn == 0:  # the case of no ice
            self.column = list()
            self.water_line = -1
            self.draft_thickness = -1
        else:
            self.column = column_inn
            self.water_line = -1
            self.draft_thickness = -1


    def add_metadata(self, key, value):
        """

        :param key:
        :param value:
        """
        self.metadata[key] = value


    def set_water_line(self, water_line_inn):
        self.water_line = water_line_inn


    def add_layer_at_index(self, index, layer):
        '''
        Adds a new layer at a given index in ice column. Subsequent layers are added after the new layer.
        If layer.height is None nothing is done.

        :param index:           -1 is last index
        :param layer:
        :return:                no return
        '''

        if layer.height != None:
            if index == -1:
                self.column.append(layer)
            else:
                self.column.insert(index, layer)


    def remove_layer_at_index(self, index):
        # Removes a layer at a given index
        self.column.pop(index)


    def time_step_forward(self, time_step):
        '''
        Step the date forward the timedelta of "timestep"
        :param timestep:
        :return:
        '''
        self.date = self.date + datetime.timedelta(seconds=time_step)


    def merge_and_remove_excess_layers(self):
        '''
        Cleans up the icecolumn a bit. Removes layers of zero height if they occur and merges layers of equal type
        if the exist

        :return:
        '''

        # If no column there is nothing to merge
        if len(self.column) != 0:

            # Goes through the ice column to find layers of zero height and removes them
            i = 0
            condition = True  # The condition for looping through the column.
            while condition:
                if self.column[i].height == 0.:
                    self.column.pop(i)
                    i = i - 1  # poping one shortens the list an thus the index counter should go back with it
                i = i + 1
                if i >= len(self.column):
                    condition = False


            # Find neighbouring layers of equal type and merges them
            last_checked_layer_type = 'NA'
            i = 0
            condition = True
            while condition:
                if self.column[i].type == last_checked_layer_type:

                    # average the temperatures
                    if (self.column[i - 1].temperature != None) and (self.column[i].temperature != None):
                        self.column[i - 1].temperature = (self.column[i - 1].height * self.column[i - 1].temperature
                                                          + self.column[i].height * self.column[i].temperature) \
                                                         / (self.column[i - 1].height + self.column[i].height)

                    # average densities
                    if (self.column[i - 1].density != None) and (self.column[i].density != None):
                        self.column[i - 1].density = (self.column[i - 1].height * self.column[i - 1].density
                                                      + self.column[i].height * self.column[i].density) \
                                                     / (self.column[i - 1].height + self.column[i].height)

                    # average thermal conductivities
                    if (self.column[i - 1].conductivity != None) and (self.column[i].conductivity != None):
                        self.column[i - 1].conductivity = (self.column[i - 1].height * self.column[i - 1].conductivity
                                                           + self.column[i].height * self.column[i].conductivity) \
                                                          / (self.column[i - 1].height + self.column[i].height)

                    # merge the two metadata dictionaries
                    z = self.column[i - 1].metadata.copy()
                    z.update(self.column[i].metadata)
                    self.column[i - 1].metadata = z

                    # new layer is sum of the two prior layers
                    self.column[i - 1].height = self.column[i - 1].height + self.column[i].height

                    self.column.pop(i)

                    # the current layer was removed so the index must be moved back one step
                    i = i - 1

                last_checked_layer_type = self.column[i].type
                i = i + 1
                if i >= len(self.column):
                    condition = False

    ## incomplete
    def get_surface_temperature(self, temp_atm, effective_depth=0.5):
        """
        Surface temperature

        :param temp_atm:
        :param effective_depth:
        :return:
        """

        temp_surface = (self.column_average_temperature + temp_atm)/2

        # THS approach
        #temp_surface = self.column_average_temperature * 2

        if temp_surface > 0.:
            temp_surface = 0.

        return temp_surface

    ## incomplete
    def update_column_temperatures(self, temp_atm):
        '''INCOMPLETE
        Temperatures are given as a wheighted (lamda_n) sum of the last N days.

        temp_i = sum_N(temp_(i-1) * lamda_n)

        Lambda_n is dependant of layer thickness. As refferance I estimate a snow/icepack of 1 meter to
        reach equlibrium after 3 days with the same temperature.

        Columntemperatures should hold the condition that bottom layer is 0C and that material conductivities shold
        reflect the temperature gradient.

        :param temp_atm:
        :return:
        '''

        N = 3

        for layer in self.column:
            if len(layer) < 3:
                layer.append(0.)
            weight = 1 / layer[0] / N
            layer[2] = (layer[2] * weight + temp_atm) / 2
            a = 1


    def update_column_average_temperature(self, temp_atm):
        '''Average temperature of the column. The theory is:

                temp_avg = ( sum_n(temp_atm * weight_n) / sum_n(weight_n) )/2

        We devide by 2 from the asumption that there is a linear temperature gradient in the column and
        at thte botonm it is water at 0C.

        Method takes into account column thickness to how quick its temperature shifts according to
        the atmospheric temperature.

        I do calculations in Kelvin so that days with 0C in are taken into account.

        :param temp_atm:
        :return:

        '''

        max_h_thin_layer = 0.3  # in meter
        medium_weights = [5, 2]
        max_h_medium_layer = 1.  # in meter
        thick_weighs = [5, 3, 2, 1]

        # first index is avg temp. The next indexes are todays temperature, yesturdays temp, etc.
        self.last_days_temp_atm.insert(0, temp_atm)
        self.last_days_temp_atm.pop(-1)

        # effect of temperature o column is depending on column thickness
        total_thick = 0
        for layer in self.column:
            total_thick = total_thick + layer.height

        avg_temp = 0

        # no sno or ice
        if total_thick == 0:
            avg_temp = 0 # feezing temp in water

        # Thin layer case
        elif total_thick < max_h_thin_layer:
            avg_temp = temp_atm - const.absolute_zero

        # Medium layer case
        elif (total_thick >= max_h_thin_layer) and (total_thick < max_h_medium_layer):
            weight = medium_weights
            weight_sum = sum(weight)
            for i in range(0, len(weight), 1):
                w_i = weight[i]
                temp_i = self.last_days_temp_atm[i] - const.absolute_zero
                avg_temp = avg_temp + temp_i * w_i
            avg_temp = avg_temp / weight_sum

        # Thick layer case
        else:
            weight = thick_weighs
            weight_sum = sum(weight)
            for i in range(0, len(weight), 1):
                w_i = weight[i]
                temp_i = self.last_days_temp_atm[i] - const.absolute_zero
                avg_temp = avg_temp + temp_i * w_i
            avg_temp = avg_temp / weight_sum

        # avg_temp is also effected by water temp (0C)
        avg_temp_out = (avg_temp + const.absolute_zero) / 2

        # snow and ice isnt above 0C
        if avg_temp_out > 0.:
            avg_temp_out = 0.

        self.column_average_temperature = avg_temp_out

        return


    def update_slush_level(self):
        '''
        Updates slush level by balancing bouyency of icelayers with weight of snow

        :return:
        '''

        self.update_draft_thickness()
        self.update_water_line()

        # We get more slush if pressure from snow is great enough to push all ice below the water dh_slush > 0.
        dh_slush = self.water_line - self.draft_thickness

        # We also have a constant regulating the minimum change before we get a slush event
        if dh_slush > const.min_slush_change:

            # Cappilary forces pull water up past the equlibrium line
            dh_slush = dh_slush + const.snow_pull_on_water

            # find index of deepest snow layer. Slush forms at the bottom of this layer.
            index = 0
            for i in range(len(self.column)):
                if self.column[i].enum() >= 20:  # material types >= 20 are snow
                    index = i  # keep counting the index until we reach bottom of the snow.

            # reduce the deepest snow layer with the dh_slush and if snowlayer isnt big enough go to the
            # abowe and make this layer wet aswell (and so on).
            while dh_slush > 0 and index >= 0:
                # if the layer is to shallow all is flooded with water and made to slush.
                # Note that the layer is compressed as a result of adding water to snow.
                if dh_slush > self.column[index].height * const.snow_to_slush_ratio:
                    self.column[index].type = 'slush'
                    self.column[index].height = self.column[index].height * const.snow_to_slush_ratio
                    dh_slush = dh_slush - self.column[
                        index].height  # remember that this layer has been updated to the new layer height on the previous line
                    index = index - 1
                # take a part of the layer and make a new slush layer under it.
                else:
                    self.column[index].height = self.column[index].height - dh_slush / const.snow_to_slush_ratio
                    self.add_layer_at_index(index + 1, IceLayer(dh_slush, 'slush'))
                    index = -1


        # reduse slushlevel if pressure from snow goes away (e.g. windtransport, melting etc).
        # The result is slush drained back to snow. (Probably only a theoretical posibility?)
        # elif dh_slush < 0.01:
        #
        # # find the topmost slushlayer
        #     i_start = 0
        #     for i in range (len(self.column)):
        #         if self.column[i].type == 'slush':
        #             i_start = i
        #             break
        #
        #     # Drain it with dh_slush (negative number)
        #     for i in range(i_start, len(self.column), 1):
        #         # if we have slush layer and need a change in slush level
        #         if self.column[i].type == 'slush' and dh_slush < 0:
        #             if self.column[i].height >= -dh_slush:               # if layer is thick enought to only be partly drained
        #                 self.column[i].height = self.column[i].height + dh_slush
        #                 self.add_layer_at_index(i, -dh_slush, 'drained_snow')
        #                 dh_slush = 0                                # we have equlibrium in the icecoulumn
        #             else:                                           # slushlayer is shalower than the change in slushlayer
        #                 self.column[i].type[1] = 'drained_snow'          # Slush layer is completely drained. We set layertype to drained_snow.
        #                 dh_slush = dh_slush + self.column[i].height     # updated slush level change which will effect the next slushlayer
        #         # if we dont have a slush layer but still need change
        #         elif self.column[i].type != 'slush' and dh_slush < 0:
        #             dh_slush = dh_slush + self.column[i].height
        #         elif dh_slush >= 0:
        #             break

        # Remove layers of height = 0 and merge neighbouring layers of equal type
        self.merge_and_remove_excess_layers()
        self.update_water_line()  # due to the snow pulling water up in the snow the waterline is shifted since before uppdatig the slushlevel


    def update_draft_thickness(self):
        '''
        Method updates the iceColumns draft_thickness variable. The draft height given by summing ice, slush ice and
        slush layers. I.e. not snow layers (and not the surface slush layer)
        '''

        draft_thickness = 0

        for layer in self.column:
            if draft_thickness == 0 and layer.enum() > 20:  # material types >= 20 are snow
                continue
            # elif draft_thickness == 0 and layer.enum() == 2:    # slush over the ice does not count
            #    continue
            else:
                draft_thickness = draft_thickness + layer.height

        self.draft_thickness = draft_thickness


    def update_water_line(self):
        '''
        Method updates the iceColumns water line variable. This is the distance from the bottom of the ice to the
        waterline. The height of the draft submerged under the water line given by Arkimedes law.

        :return:
        '''

        column_mass = 0
        for layer in self.column:
            column_mass = column_mass + layer.height * layer.density  # height*density = [kg/m2]
        water_line = column_mass / const.rho_water  # [kg/m2]*[m3/kg]
        self.water_line = water_line


    def update_top_layer_is_slush(self):
        '''
        Tests if the top most ice column layer is slush. Updates the objects top_layer_is_slush prameter.
        Returns true if it is.

        :return: [Bool] True if topp layer is slush. False if not.
        '''

        for layer in self.column:
            if layer.enum() > 20:  # material types >= 20 are snow
                continue
            elif layer.enum() == 2:  # slush over the ice does not count
                self.top_layer_is_slush = True
                return True
            else:
                self.top_layer_is_slush = False
                return False


    def merge_snow_layers_and_compress(self, temp_atm):
        '''
        Merges the snow layers and compresses the snow. This method updates the snow density in the object and the
        conductivity of the snow in the object.

        Snow compaction may be referenced in article in literature folder or evernote.

        :param temp_atm: [float] Temperature in Celsius used in the compaction routine.
        :return:
        '''

        # If no layers, compaction of snow is not needed
        if len(self.column) > 0:
            # declare the new snow layer (index = 0) as normal snow layer
            if self.column[0].type == 'new_snow':
                self.column[0].type = 'snow'

            self.merge_and_remove_excess_layers()

            # if no snow, no compaction
            if self.column[0].type == 'snow':
                # we use a formula for compaction only if air temperature is below freezing and there is snow on top
                if temp_atm < const.temp_f:

                    # ice & snow parameter values
                    C1 = 7.0 * 1e-3 * 12  # snow compaction coefficient #1
                    C2 = -21.0 * 1e-3  # snow compaction coefficient #2
                    C3 = -0.04  # snow compaction coefficient #3

                    # this is one strange fromula. Would be good to change it with something more familiar..
                    delta_rho_snow = self.column[0].density ** 2 * C1 * self.column[0].height * math.exp(
                        C2 * self.column[0].density) * math.exp(C3 * temp_atm)

                    rho_snow_old = self.column[0].density
                    rho_snow_new = rho_snow_old + delta_rho_snow
                    k_snow_new = pz.k_snow_from_rho_snow(rho_snow_new)

                # Else we have melting conditions and the snow conductivity and density is sett to max
                else:
                    rho_snow_old = self.column[0].density
                    rho_snow_new = const.rho_snow_max
                    k_snow_new = const.k_snow_max

                self.column[0].density = min([rho_snow_new, const.rho_snow_max])
                self.column[0].conductivity = min([k_snow_new, const.k_snow_max])

                h_snow_new = self.column[0].height / self.column[
                    0].density * rho_snow_old  # Asume a inverse linear correlation between density and the height (preservation og mass?)
                self.column[0].height = h_snow_new

        return


class IceLayer:
    '''
    height      float in m
    type       string
    temp        float in C
    '''

    def __init__(self, height_inn, type_inn):

        self.type = type_inn

        self.height = height_inn
        if height_inn: self.height = float(height_inn)  # If height_inn has value make sure it is a float

        self.set_conductivity()
        self.set_density()

        self.temperature = None
        self.metadata = {} # Metadata given as dictionary {key:value , key:value, ... }


    def set_temperature(self, temperature_inn):
        # Avarage temp of layer
        self.temperature = temperature_inn


    def add_metadata(self, key, value):
        self.metadata[key] = value


    def colour(self):
        # returns the color used for plotting a given snow or ice type
        if self.type == 'new_snow': return "0.9"
        elif self.type == 'snow': return "0.8"
        elif self.type == 'drained_snow': return "0.7"
        elif self.type == 'slush': return "blue"
        elif self.type == 'slush_ice': return "0.4"
        elif self.type == 'black_ice': return "0.1"
        elif self.type == 'water': return "red"
        elif self.type == 'unknown': return "orange"
        else: return "yellow"


    def set_conductivity(self):
        # sets conductivity for a given snow or ice type
        # Method should only be used when initiallizing a new IceLayer
        if self.type == 'new_snow':     self.conductivity = const.k_new_snow
        elif self.type == 'snow':       self.conductivity = const.k_snow
        elif self.type == 'drained_snow': self.conductivity = const.k_drained_snow
        elif self.type == 'slush':      self.conductivity = const.k_slush
        elif self.type == 'slush_ice':  self.conductivity = const.k_slush_ice
        elif self.type == 'black_ice':  self.conductivity = const.k_black_ice
        elif self.type == 'water':      self.conductivity = const.k_water
        elif self.type == 'unknown':    self.conductivity = const.k_slush_ice


    def set_density(self):
        # Desities [kg m-3]
        # Method should only be used when initiallizing a new IceLayer
        if self.type == 'new_snow':     self.density = const.rho_new_snow
        elif self.type == 'snow':       self.density = const.rho_snow
        elif self.type == 'drained_snow': self.density = const.rho_drained_snow
        elif self.type == 'slush':      self.density = const.rho_slush
        elif self.type == 'slush_ice':  self.density = const.rho_slush_ice
        elif self.type == 'black_ice':  self.density = const.rho_black_ice
        elif self.type == 'water':      self.density = const.rho_water
        elif self.type == 'unknown':    self.density = const.rho_slush_ice


    def enum(self):
        # returns the enum used for a given snow or ice type
        # LayerTypes given as enums. Values 0-9 are liquids, 10-19 are ice, 20-29 are snow
        if self.type == 'new_snow': return 20
        elif self.type == 'snow': return 21
        elif self.type == 'drained_snow': return 22
        elif self.type == 'slush': return 2
        elif self.type == 'slush_ice': return 11
        elif self.type == 'black_ice': return 10
        elif self.type == 'water': return 1
        elif self.type == 'unknown': return 11
        else: return -1


    def heat_capacity(self):
        # returns heat capacity given the type of layer
        if self.type == 'new_snow': return const.c_snow
        elif self.type == 'snow': return const.c_snow
        elif self.type == 'drained_snow': return const.c_snow
        elif self.type == 'slush': return const.c_slush
        elif self.type == 'slush_ice': return const.c_ice
        elif self.type == 'black_ice': return const.c_ice
        elif self.type == 'water': return const.c_water
        elif self.type == 'unknown': return const.c_ice
        else: return -1


class IceCover:

    def __init__(self, date_inn, iceCoverName_inn, iceCoverBeforeName_inn, locationName_inn):
        self.date = date_inn
        self.iceCoverName = iceCoverName_inn
        self.iceCoverTID = gro.get_tid_from_name('IceCoverKDV', iceCoverName_inn)
        self.iceCoverBeforeName = iceCoverBeforeName_inn
        self.iceCoverBeforeTID = gro.get_tid_from_name('IceCoverBeforeKDV', iceCoverBeforeName_inn)
        self.locationName = locationName_inn

        self.RegID = None

    def set_regid(self, regid_inn):
        self.RegID = regid_inn


def tests_IceColumn():
    # some tests of the functions in the IceColumn file

    date = datetime.datetime.strptime("2011-10-05", "%Y-%m-%d")
    icecol = IceColumn(date, 0)
    # icecol.add_layer_at_index(0, 0.1, 'new_snow')
    #icecol.update_slush_level()
    #icecol.merge_and_remove_excess_layers()
    icecol.merge_snow_layers_and_compress(-5)


