# -*- coding: utf-8 -*-
"""Classes for handling ice Thickness and Ice Cover. Much of the ice model is in the methods in these classes."""

import math
import datetime as dt
from icemodelling import parameterization as pz, constants as const
from utilities import getregobsdata as gro, getfiledata as gfd

__author__ = 'ragnarekker'


class IceLayer:
    """Each layer in the ice column is given its own IceLayer object. The constructor takes as minimum
    height and type and sets conductivity and density from constants.
    """

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

    def set_temperature_top(self, temperature_top_inn):
        self.temperature_top = temperature_top_inn

    def set_temperature_bottom(self, temperature_bottom_inn):
        self.temperature_bottom = temperature_bottom_inn

    def set_conductivity(self):
        # sets conductivity for a given snow or ice type
        # Method should only be used when initialising a new IceLayer
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
        # Method should only be used when initialising a new IceLayer
        if self.type == 'new_snow':     self.density = const.rho_new_snow
        elif self.type == 'snow':       self.density = const.rho_snow
        elif self.type == 'drained_snow': self.density = const.rho_drained_snow
        elif self.type == 'slush':      self.density = const.rho_slush
        elif self.type == 'slush_ice':  self.density = const.rho_slush_ice
        elif self.type == 'black_ice':  self.density = const.rho_black_ice
        elif self.type == 'water':      self.density = const.rho_water
        elif self.type == 'unknown':    self.density = const.rho_slush_ice

    def add_metadata(self, key, value):
        self.metadata[key] = value

    def get_colour(self):
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

    def get_norwegian_name(self):
        # returns the norwegian name of the ice layer type. Used for legend in plots.
        if self.type == 'new_snow': return 'Nysnø'
        elif self.type == 'snow': return 'Snø'
        elif self.type == 'drained_snow': return 'Tørket snø'
        elif self.type == 'slush': return 'Sørpe'
        elif self.type == 'slush_ice': return 'Sørpeis'
        elif self.type == 'black_ice': return 'Stålis'
        elif self.type == 'water': return 'Vann'
        elif self.type == 'unknown': return 'Ukjent istype'
        else: return 'Ukjent forespørsel'

    def get_enum(self):
        # returns the get_enum used for a given snow or ice type
        # LayerTypes given as enums. Values 0-9 are liquids, 10-19 are ice, 20-29 are snow
        if self.type == 'new_snow': return 20
        elif self.type == 'snow': return 21
        elif self.type == 'drained_snow': return 22
        elif self.type == 'slush': return 2
        elif self.type == 'slush_ice': return 11
        elif self.type == 'black_ice': return 10
        elif self.type == 'water': return 1
        elif self.type == 'unknown': return 11      # unknown icetype is treated as slush_ice
        else: return -1

    def get_heat_capacity(self):
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

    def get_surface_roughness(self):
        # Surface roughness [m] as used to calculate turbulent fluxes
        if self.type == 'new_snow': return const.z_new_snow
        elif self.type == 'snow': return const.z_snow
        elif self.type == 'drained_snow': return const.z_drained_snow
        elif self.type == 'slush': return const.z_slush
        elif self.type == 'slush_ice': return const.z_slush_ice
        elif self.type == 'black_ice': return const.z_black_ice
        elif self.type == 'water': return const.z_water
        elif self.type == 'unknown': return const.z_black_ice
        else: return -1

    def get_thermal_diffusivity(self):
        """returns Thermal diffusivity given the type of layer
        Thermal diffusivity (alpha) [m^2/sek]

            alpha = k / rho / c

            k   is thermal conductivity (W/(m·K))
            rho is density (kg/m³)
            c   is specific heat capacity (J/(kg·K))

        From https://en.wikipedia.org/wiki/Thermal_diffusivity
        """

        if self.type == 'new_snow':         return const.k_new_snow     /self.density/   const.c_snow
        elif self.type == 'snow':           return const.k_snow         /self.density/   const.c_snow
        elif self.type == 'drained_snow':   return const.k_drained_snow /self.density/   const.c_snow
        elif self.type == 'slush':          return const.k_slush        /self.density/   const.c_slush
        elif self.type == 'slush_ice':      return const.k_slush_ice    /self.density/   const.c_ice
        elif self.type == 'black_ice':      return const.k_black_ice    /self.density/   const.c_ice
        elif self.type == 'water':          return const.k_water        /self.density/   const.c_water
        elif self.type == 'unknown':        return const.k_black_ice    /self.density/   const.c_ice
        else: return -1


class IceColumn:

    def __init__(self, date_inn, column_inn):
        """This initializes the object.
        An empty column is initialized as iceColumn(date as datetime, 0)
        Column_inn includes new snow layer on index 0.

        :param date_inn:        [datetime]
        :param column_inn:      list[IceLayers]
        :return:
        """

        self.date = date_inn                # Date
        self.column = 0                     # Ice column with [IceLayers].
        self.water_line = -1                # Distance from bottom of ice column to the water surface. Negative number meens not initiallized
        self.draft_thickness = -1           # This is ice, slush ice and slush layers. I.e. not snow layers
        self.total_column_height = None
        self.metadata = {}                  # Metadata given as dictionary {key:value , key:value, ... }
        self.top_layer_is_slush = None      # [Bool] True if top layer is slush. False if not.

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

    def remove_metadata(self):
        self.metadata.clear()

    def set_water_line(self, water_line_inn):
        self.water_line = water_line_inn

    def set_surface_temperature(self, surface_temperature_inn):
        self.temp_surface = surface_temperature_inn

    def add_layer_at_index(self, index, layer):
        """Adds a new layer at a given index in ice column. Subsequent layers are added after the new layer.
        If layer.height is None nothing is done.

        :param index:           -1 is last index
        :param layer:
        :return:                no return
        """

        if layer.height != None:
            if index == -1:
                self.column.append(layer)
            else:
                self.column.insert(index, layer)

    def remove_layer_at_index(self, index):
        """Removes a layer at a given index."""
        self.column.pop(index)

    def time_step_forward(self, time_step):
        """Step the date forward the timedelta of "timestep"

        :param timestep:
        :return:
        """
        self.date = self.date + dt.timedelta(seconds=time_step)

    def remove_time(self):
        """When using observations as initial values the observations normally have date and time .
        For further modelling the daily values are calculatet so the hour and minutes can be removed.
        """

        new_time = self.date.replace(hour=00, minute=0)
        self.date = new_time

        return

    def merge_and_remove_excess_layers(self):
        """Cleans up the icecolumn a bit. Removes layers of zero height if they occur and merges layers of equal type
        if the exist"""

        # If no column there is nothing to merge
        if self.column is not None and len(self.column) > 0:

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
        if self.column is not None and len(self.column) > 0:

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

    def merge_snow_layers_and_compress(self, temp_atm):
        """Merges the snow layers and compresses the snow. This method updates the snow density in the object and the
        conductivity of the snow in the object.

        Snow compaction may be referenced in article in literature folder or evernote.

        :param temp_atm: [float] Temperature in Celsius used in the compaction routine.
        :return:
        """

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

    def get_snow_height(self):

        snow_height = 0.

        if self.column[0].type == "snow":
            snow_height = self.column[0].height

        return snow_height

    def get_layer_at_z(self, depth_inn):
        """

        :param depth_inn: [m]
        :return layer_out:          the actual laye object
                depth_layer_top:    the depth of the topp of the layer
                rest_height:        to the requested depth, ho far is it from the top of the layer?
        """

        current_depth = 0.
        layer_out = None
        depth_layer_top = None
        rest_height  = None

        for l in self.column:
            if current_depth < depth_inn:
                if current_depth + l.height > depth_inn:
                    layer_out = l
                    depth_layer_top = current_depth
                    rest_height = depth_inn-current_depth
                    break
                current_depth += l.height

        return layer_out, depth_layer_top, rest_height

    def get_surface_temperature(self):
        """
        Retruns surface temperature if on exists.
        :return:
        """
        try:
            return self.temp_surface
        except Exception as e:
            print(e)
            print("No surface temperature on object. Try using the get_surface_temperature_estimate function.")

    def update_column_temperatures(self, temp_sfc=None):
        """Column temperatures calculated under the assumption that over 24hrs temperature
        reaches steady state. Calculation hold the boundary conditions of bottom at 0C and
        top at temperature of atmosphere.

        For multiple dry layers the set of equations is solves with matrix linear algebra:

            AA * xx = bb

        Possible extension: Effect of temp from precious days weight inn, in the end.

        :param temp_sfc:        Temp in atmosphere
        :return:
        """

        import numpy as np

        if temp_sfc is None:
            temp_sfc = self.temp_surface

        # only continuous dry layers from surface can be below freezing (0C)
        num_dry_layers = 0
        for l in self.column:
            if l.get_enum() > 9:
                num_dry_layers += 1
            else:
                break

        num_boundaries = num_dry_layers - 1
        temp_top = temp_sfc
        temp_bottom = const.temp_f      # freezing temp

        # case surface layer is wet, we assume all is 0C
        if num_boundaries == -1:
            for l in self.column:
                l.set_temperature_top(0.)
                l.set_temperature_bottom(0.)
                l.set_temperature(0.)

        # case only one layer or only the top layer is dry, this layer is avg of surface temp and 0C
        elif num_boundaries == 0:
            self.column[0].set_temperature((temp_top+temp_bottom)/2)
            self.column[0].set_temperature_top(temp_top)
            self.column[0].set_temperature_bottom(temp_bottom)
            # the rest is 0C
            for l in self.column[1:]:
                l.set_temperature_top(0.)
                l.set_temperature_bottom(0.)
                l.set_temperature(0.)

        # case more dry layers, solve numerically
        elif num_boundaries > 0:
            AA = np.zeros([num_boundaries, num_boundaries])

            for i in range(num_boundaries):
                AA[i,i] = self.column[i].conductivity * self.column[i].height \
                        + self.column[i+1].conductivity * self.column[i+1].height

            for i in range(num_boundaries-1):
                AA[i, i+1] = -1 * self.column[i+1].conductivity * self.column[i+1].height
                AA[i+1, i] = -1 * self.column[i+1].conductivity * self.column[i+1].height

            bb = np.zeros([num_boundaries])
            bb[0] = temp_top * self.column[0].conductivity * self.column[0].height
            if num_boundaries > 1:
                bb[num_boundaries-1] = temp_bottom * self.column[num_boundaries].conductivity \
                                     * self.column[num_boundaries].height

            xx = np.linalg.solve(AA, bb)

            #print (AA)
            #print (xx)
            #print (bb)

            # add the outer boundary conditions to the solution
            boundary_temps = xx
            boundary_temps = np.insert(boundary_temps, 0, temp_top)
            boundary_temps = np.insert(boundary_temps, len(boundary_temps), temp_bottom)

            # layer temp is average of the boundary temps
            for i in range(0, len(boundary_temps)-1, 1):
                self.column[i].set_temperature((boundary_temps[i]+boundary_temps[i+1])/2)
                self.column[i].set_temperature_top(boundary_temps[i])
                self.column[i].set_temperature_bottom(boundary_temps[i+1])

            # the lower layers are 0C
            for i in range(len(boundary_temps)-1, len(self.column), 1):
                self.column[i].set_temperature(0.)
                self.column[i].set_temperature_top(0.)
                self.column[i].set_temperature_bottom(0.)

        return

    def update_slush_level(self):
        """Updates slush level by balancing bouyency of icelayers with weight of snow

        :return:
        """

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
                if self.column[i].get_enum() >= 20:  # material types >= 20 are snow
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
        """Method updates the iceColumns draft_thickness variable.
        The draft height given by summing ice, slush ice and
        slush layers. I.e. not snow layers (and not the surface slush layer)
        """

        draft_thickness = 0

        for layer in self.column:
            if draft_thickness == 0 and layer.get_enum() > 20:  # material types >= 20 are snow
                continue
            # elif draft_thickness == 0 and layer.get_enum() == 2:    # slush over the ice does not count
            #    continue
            else:
                draft_thickness = draft_thickness + layer.height

        self.draft_thickness = draft_thickness

    def update_total_column_height(self):
        """Sum  of all layers in column. also snow.
        :return:
        """
        total_height = 0.

        for l in self.column:
            total_height += l.height

        self.total_column_height = total_height

    def update_water_line(self):
        """
        Method updates the iceColumns water line variable. This is the distance from the bottom of the ice to the
        waterline. The height of the draft submerged under the water line given by Arkimedes law.

        :return:
        """

        column_mass = 0
        for layer in self.column:
            column_mass = column_mass + layer.height * layer.density  # height*density = [kg/m2]
        water_line = column_mass / const.rho_water  # [kg/m2]*[m3/kg]
        self.water_line = water_line

    def update_top_layer_is_slush(self):
        """Tests if the top most ice column layer is slush. Updates the objects top_layer_is_slush prameter.
        Returns true if it is.

        :return: [Bool] True if topp layer is slush. False if not.
        """

        for layer in self.column:
            if layer.get_enum() > 20:  # material types >= 20 are snow
                continue
            elif layer.get_enum() == 2:  # slush over the ice does not count
                self.top_layer_is_slush = True
                return True
            else:
                self.top_layer_is_slush = False
                return False

    def get_conductance_at_z(self, depth_inn=None):
        """Retruns conductance from surface to a certain depth.

        Conductance is conductivity pr unit lenght.
        I.e. U = k/h where k is conductivity and h is height of icelayer
        Sum of conductance follows the rule 1/U = 1/U1 + 1/U2 + ... + 1/Un

        From https://en.wikipedia.org/wiki/Thermal_conductivity:
        thermal conductivity = k,           measured in W/(m·K)
        thermal conductance = kA/L,         measured in W·K−1
        thermal resistance = L/(kA),        measured in K·W−1 (equivalent to: °C/W)
        heat transfer coefficient = k/L,    measured in W·K−1·m−2
        thermal insulance = L/k, measured in K·m2·W−1.

        where k is thermal conductivity, A is area and L is thickness.


        :param depth_inn: [m] If None total column height is used. I.e. No water conductance below
        :return:
        """

        current_depth = 0.
        U_total = 0.

        if depth_inn is None:
            if self.total_column_height is None:
                self.update_total_column_height()
            depth_inn = self.total_column_height

        for l in self.column:
            if U_total == 0.: # case for the first layer
                if l.height > depth_inn:
                    U_total = l.conductivity / (depth_inn-current_depth)
                    current_depth = depth_inn
                    break
                U_total = l.conductivity/l.height
                current_depth += l.height
                continue
            if current_depth < depth_inn:
                if current_depth + l.height > depth_inn:
                    U_total = 1/ (1/U_total+(depth_inn-current_depth)/l.conductivity)
                    current_depth = depth_inn
                    break
                U_total = 1/ (1/U_total+l.height/l.conductivity)
                current_depth += l.height
            else:
                break


        # if requested depth is deeper than the column, add water conductance
        if current_depth < depth_inn:
            U_total = 1/ (1/U_total+(depth_inn-current_depth)/const.k_water)

        return U_total

    def get_depth_at_conductance(self, conductance_limit):
        """Given a desired conductance, this method returns the height from the surface to get this
        conductance

        :param conductance_limit:
        :return:
        """

        current_depth = 0.
        resistivity_limit = 1/conductance_limit
        current_resistivity = 0.

        for l in self.column:
            if current_resistivity < resistivity_limit:
                # if were not at the limit, keep adding
                delta_resistivity = l.height / l.conductivity
                if current_resistivity + delta_resistivity > resistivity_limit:
                    # if only part of the layer is added
                    rest_depth = l.height * (resistivity_limit - current_resistivity)/delta_resistivity
                    current_depth += rest_depth
                    current_resistivity = resistivity_limit
                else:
                    current_depth += l.height
                    current_resistivity += delta_resistivity
            else:
                # else stop
                break

        # if not enough heigt in the ice column make sure water contributes
        if current_resistivity < resistivity_limit:
            rest_depth_in_water = (resistivity_limit - current_resistivity) * const.k_water
            current_depth += rest_depth_in_water
            current_resistivity = resistivity_limit

        self.active_depth = current_depth

        return current_depth


class IceCover:

    def __init__(self, date_inn, iceCoverName_inn, iceCoverBeforeName_inn, locationName_inn):
        self.date = date_inn
        self.iceCoverName = iceCoverName_inn
        self.iceCoverTID = gro.get_tid_from_name('IceCoverKDV', iceCoverName_inn)
        self.iceCoverBeforeName = iceCoverBeforeName_inn
        self.iceCoverBeforeTID = gro.get_tid_from_name('IceCoverBeforeKDV', iceCoverBeforeName_inn)
        self.locationName = locationName_inn

        self.RegID = None
        self.LocationID = None
        # self.UTMNorth = None
        # self.UTMEast = None
        # self.UTMZone = None
        self.iceCoverAfterName = 'Ikke gitt'
        self.iceCoverAfterTID = 0
        self.first_ice = False
        self.ice_cover_lost = False

        self.metadata = {}
        # self.original_object = None

    def add_metadata(self, key, value):
        """

        :param key:
        :param value:
        """
        self.metadata[key] = value

    def set_regid(self, regid_inn):
        self.RegID = int(regid_inn)

    def set_locationid(self, locationid_inn):
        self.LocationID = int(locationid_inn)

    def set_utm(self, utm_north_inn, utm_east_inn, utm_zone_inn):
        self.metadata['UTMNorth'] = int(utm_north_inn)
        self.metadata['UTMEast'] = int(utm_east_inn)
        self.metadata['UTMZone'] = int(utm_zone_inn)

    def set_cover_after(self, cover_after_name_inn, cover_after_tid_inn):
        self.iceCoverAfterName = cover_after_name_inn
        self.iceCoverAfterTID = cover_after_tid_inn

    def mark_as_first_ice(self):
        self.first_ice = True

    def mark_as_ice_cover_lost(self):
        self.ice_cover_lost = True

    def add_original_object(self, original_object_inn):
        self.metadata['OriginalObject'] = original_object_inn


if __name__ == "__main__":

    from setenvironment import data_path

    # some tests of the functions in the IceColumn file
    # date = dt.datetime.strptime("2011-10-05", "%Y-%m-%d")
    # icecol = IceColumn(date, 0)
    # icecol.add_layer_at_index(0, 0.1, 'new_snow')
    # icecol.update_slush_level()
    # icecol.merge_and_remove_excess_layers()
    # icecol.merge_snow_layers_and_compress(-5)

    icecols = gfd.importColumns("{0}test ice columns.csv".format(data_path))
    icecol = icecols[4]
    icecol.update_column_temperatures(-15)
    icecol.update_total_column_height()
    layer = icecol.get_layer_at_z(0.9)

    conductance = icecol.get_conductance_at_z()
    height = icecol.get_depth_at_conductance(const.U_surface)

    R13 = 0.3/0.11+0.18/1.12+0.28/2.24
    U11 = 0.11/0.30
    U12 = 1 / (1/0.3667 + 0.18/1.12)
    U13 = 1 / (1/0.346 + 0.28/2.24)
    R13_2 = 1/U13

    pass
