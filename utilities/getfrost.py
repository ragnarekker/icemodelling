# -*- coding: utf-8 -*-
import requests
import setenvironment as se

__author__ = 'ragnarekker'


def get_observations():
    """

    :return:
    """
    # Define endpoint and parameters
    endpoint = 'https://frost.met.no/observations/v0.jsonld'

    parameters = {
        'sources': 'SN18700,SN90450',
        'elements': 'mean(air_temperature P1D),sum(precipitation_amount P1D),mean(wind_speed P1D)',
        'referencetime': '2010-04-01/2010-04-03',
    }

    parameters = {
        'sources': '*',
        'elements': 'SA',
        'referencetime': 'latest'
    }

    # Issue an HTTP GET request
    r = requests.get(endpoint, parameters, auth=(se.frost_client_id, ''))
    # Extract JSON data
    json = r.json()

    return


def get_available_time_series():
    """

    :return:
    """
    # Define endpoint and parameters
    endpoint = 'https://frost.met.no/observations/availableTimeSeries/v0.jsonld'

    parameters = {
        'elements': 'surface_snow_thickness'
    }

    # Issue an HTTP GET request
    r = requests.get(endpoint, parameters, auth=(se.frost_client_id, ''))
    # Extract JSON data
    data = r.json()['data']

    current_data = []
    for d in data:
        if 'validTo' not in d.keys():
            current_data.append(d)

    return


def get_locations():
    """
    """

    endpoint = 'https://frost.met.no/locations/v0.jsonld'
    r = requests.get(endpoint, auth=(se.frost_client_id, ''))
    json = r.json()

    return


def get_elements():

    endpoint = 'https://frost.met.no/elements/v0.jsonld'
    parameters = {
        'oldElementCodes': 'SA'         # Snow depth
    }

    r = requests.get(endpoint, parameters, auth=(se.frost_client_id, ''))
    json = r.json()
    data = json['data']

    # snow_data = []
    # for d in data:
    #     if 'snow' in d['name'].lower():
    #         snow_data.append(d)


    return


def get_sources():

    endpoint = 'https://frost.met.no/sources/v0.jsonld'
    parameters = {
        'country': 'Norge'
    }

    r = requests.get(endpoint, parameters, auth=(se.frost_client_id, ''))
    json = r.json()
    data = json['data']

    return


if __name__ == "__main__":

    get_available_time_series()
    # get_observations()
    get_elements()

    get_sources()
    get_locations()
