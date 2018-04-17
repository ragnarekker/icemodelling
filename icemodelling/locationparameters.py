#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'ragnarekker'

from icemodelling import setenvironment as se
from icemodelling import getregobsdata as gro
from icemodelling import makelogs as ml


class Location():

    def __init__(self, location_name_inn):

        self.location_name = location_name_inn

        self.eklima_TAM = None
        self.eklima_SA = None
        self.eklima_NNM = None

        self.nve_temp = None                # param 17.1
        self.nve_snow = None                # param 2002.1

        self.utm_east = None
        self.utm_north = None
        self.utm_zone = None

        self.lake_size_class = None
        self.lake_elevation_range = None

        self.input_file = None
        self.file_name = None


def get_for_location(location_name):

    if location_name == 'Semsvannet v/Lo 145 moh':
        location = Location(location_name)

        location.eklima_TAM = 19710
        location.eklima_SA = 19710
        location.eklima_NNM = 18700

        location.utm_north = 6644286
        location.utm_east = 243655
        location.utm_zone = 33

        location.file_name = 'Semsvann'
        return location

    elif location_name == 'Hakkloa nord 372 moh':
        location = Location(location_name)

        location.eklima_NNM = 18700
        location.nve_temp = '6.24.4'

        location.utm_north = 6671401
        location.utm_east = 259900
        location.utm_zone = 33

        location.file_name = 'Hakkloa nord'
        return location

    # elif location_name == 'Otrøvatnet v/Nystuen 971 moh':
    #     location = Location(location_name)
    #
    #     location.eklima_TAM = 54710
    #     location.eklima_SA = 54710
    #
    #     location.utm_north = 6801955
    #     location.utm_east = 132994
    #     location.utm_zone = 33
    #
    #     # Data in range 2011.10.01 til 2013.07.19
    #     location.input_file = '{0}Kyrkjestølane værdata.csv'.format(se.data_path)
    #
    #     location.file_name = 'Otrøvatnet'
    #     return location

    elif location_name == 'Skoddebergvatnet - nord 101 moh':
        location = Location(location_name)

        # location.eklima_NNM = 87640         # Harstad Stadion
        location.nve_temp = '189.3.0'

        location.utm_north = 7612469
        location.utm_east = 593273
        location.utm_zone = 33

        location.file_name = 'Skoddebergvatnet nord'
        return location

    elif location_name == 'Giljastølsvatnet 412 moh':
        location = Location(location_name)

        #location.eklima_NNM = 43010, # Gone? Eik - Hove. Ligger lenger sør og litt inn i landet.
        location.eklima_NNM = 44560  # Sola er et alternativ

        location.utm_east = -1904
        location.utm_north = 6553573
        location.utm_zone = 33

        location.file_name = 'Giljastølsvatnet'
        return location


    elif location_name == 'Baklidammen 200 moh':
        location = Location(location_name)

        #location.eklima_NNM = 68860   # TRONDHEIM - VOLL

        location.utm_east = 266550
        location.utm_north = 7040812
        location.utm_zone = 33

        location.file_name = 'Baklidammen'
        return location


    elif location_name == 'Storvannet, 7 moh':
        location = Location(location_name)

        #location.eklima_NNM = 95350    # BANAK - østover innerst i fjorden

        location.utm_east = 821340
        location.utm_north = 7862497
        location.utm_zone = 33

        location.file_name = 'Storvannet'
        return location

    else:
        location = Location(location_name)
        try:
            odata_call = gro.get_obs_location(location_name)

            location.utm_east = odata_call['UTMEast']
            location.utm_north = odata_call['UTMNorth']
            location.utm_zone = odata_call['UTMZone']

            location.file_name = '{0}'.format(location_name.replace(",","").replace("/","").replace("\"", ""))

            return location

        except:
            ml.log_and_print('locationparameters.py -> get_for_location: No such location.')




