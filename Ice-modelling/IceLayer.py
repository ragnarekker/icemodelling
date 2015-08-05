__author__ = 'ragnarekker'

import constants as const

class IceLayer:
    '''
    height      float in m
    type       string
    temp        float in C
    '''

    def __init__(self, height_inn, type_inn):

        self.height = height_inn        # Case where height_inn is None
        if height_inn:
            self.height = float(height_inn)

        self.type = type_inn

        self.set_conductivity()
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
        elif self.type == 'water':      self.conductivity =  const.k_water
        elif self.type == 'unknown':    self.conductivity =  const.k_slush_ice

