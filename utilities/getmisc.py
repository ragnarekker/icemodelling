# -*- coding: utf-8 -*-
"""Misc methods for making life easier."""
import datetime as dt
import numpy as np
from utilities import makelogs as ml
import requests as requests


__author__ = 'raek'


def root_mean_squared_error(predictions, targets):
    """My own root mean squared error method. Using the other libs seems like over engineering."""

    predictions = np.array(predictions)
    targets = np.array(targets)

    error = np.sqrt(((predictions - targets) ** 2).mean())

    return error


def nash_sutcliffe_efficiancy_coefficient(predictions, targets):
    """Nash Sutcliffe efficiency coefficient

    :param predictions:     [list] simulated
    :param targets:         [list] observed
    :return nsec:           [float] Nash Sutcliffe efficient coefficient

    https://en.wikipedia.org/wiki/Nash%E2%80%93Sutcliffe_model_efficiency_coefficient
    """

    predictions = np.array(predictions)
    targets = np.array(targets)

    nsec = 1 - sum((predictions - targets) ** 2) / sum((targets - np.mean(targets)) ** 2)

    return nsec


def get_season_from_date(date_inn):
    """A date belongs to a season. This method returns it.

    :param date_inn:    datetime.date object
    :return:
    """

    if date_inn >= dt.date(2020, 9, 1) and date_inn < dt.date(2021, 9, 1):
        return '2020-21'
    elif date_inn >= dt.date(2019, 9, 1) and date_inn < dt.date(2020, 9, 1):
        return '2019-20'
    elif date_inn >= dt.date(2018, 9, 1) and date_inn < dt.date(2019, 9, 1):
        return '2018-19'
    elif date_inn >= dt.date(2017, 9, 1) and date_inn < dt.date(2018, 9, 1):
        return '2017-18'
    elif date_inn >= dt.date(2016, 9, 1) and date_inn < dt.date(2017, 9, 1):
        return '2016-17'
    elif date_inn >= dt.date(2015, 9, 1) and date_inn < dt.date(2016, 9, 1):
        return '2015-16'
    elif date_inn >= dt.date(2014, 9, 1) and date_inn < dt.date(2015, 9, 1):
        return '2014-15'
    elif date_inn >= dt.date(2013, 9, 1) and date_inn < dt.date(2014, 9, 1):
        return '2013-14'
    elif date_inn >= dt.date(2012, 9, 1) and date_inn < dt.date(2013, 9, 1):
        return '2014-13'
    elif date_inn >= dt.date(2011, 9, 1) and date_inn < dt.date(2012, 9, 1):
        return '2011-12'
    else:
        return 'Requested date is before the beginning of time.'


def get_dates_from_year(year, date_format='yyyy-mm-dd'):
    """Returns start and end dates for given season. Hydrological year from 1. sept.
     Format may be specified for datetime or date or string (default).

    :param year:            [String]    E.g. '2018-19'
    :param date_format:     [String]    'yyyy-mm-dd', 'date' or 'datetime'
    :return:
    """

    log_ref = 'getregobsdata.py -> get_dates_from_year:'

    from_year = int(year[0:4])
    century = int(year[0:2]) * 100
    year_in_century = int(year[5:7])

    # We build for the future. Method will work for passing centuries.
    if year_in_century != 0:
        # Same century
        last_year = century + year_in_century
    else:
        # New century
        last_year = century + 100 + year_in_century

    from_date = str(from_year) + '-09-01'
    to_date = str(last_year) + '-09-01'

    if 'yyyy-mm-dd' in date_format:
        return from_date, to_date
    elif 'date' in date_format:
        from_date = dt.datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = dt.datetime.strptime(to_date, '%Y-%m-%d').date()
        return from_date, to_date
    elif 'datetime' in date_format:
        from_date = dt.datetime.strptime(from_date, '%Y-%m-%d')
        to_date = dt.datetime.strptime(to_date, '%Y-%m-%d')
        return from_date, to_date
    else:
        ml.log_and_print("[Error] {0} Date format not supported.".format(log_ref))
        return 'Date format not supported.'


def get_masl_from_utm33(x, y):
    """Returns the altitude of a given UTM33N coordinate.

    Method uses an NVE map service which covers only Norway. If NoData method returns None

    :param x:       [int] east
    :param y:       [int] north
    :return masl:   [int] meters above sea level
    """

    url = 'https://gis3.nve.no/arcgis/rest/services/ImageService/SK_DTM20_NSF/ImageServer/identify' \
          '?geometry={0},{1}&geometryType=esriGeometryPoint&inSR=32633&spatialRel=esriSpatialRelIntersects' \
          '&relationParam=&objectIds=&where=&time=&returnCountOnly=false&returnIdsOnly=false&returnGeometry=false' \
          '&maxAllowableOffset=&outSR=&outFields=*&f=pjson'.format(x, y)

    data = requests.get(url).json()
    masl = data['value']

    if 'NoData' in masl:
        ml.log_and_print("[warning] getmisc.py -> get_masl_from_utm33: No data elevation data for x:{} y:{}".format(x,y))
        return None
    else:
        return int(masl)


def get_lake_info(x, y, reference=4326):
    """Method looks up lake parameters from NVEs lake database at a given coordinate.

    :param x:
    :param y:
    :param reference:   [int] 4326 is lat/lon, 32633 is utm33N

    :return:
    """

    url = 'https://gis3.nve.no/map/rest/services/Innsjodatabase1/MapServer/1/query' \
          '?geometry={0}%2C{1}' \
          '&geometryType=esriGeometryPoint' \
          '&inSR={2}' \
          '&spatialRel=esriSpatialRelIntersects' \
          '&outFields=*' \
          '&returnGeometry=false' \
          '&f=json'.format(x, y, reference)

    data = requests.get(url).json()
    try:
        lake_data = data['features'][0]['attributes']
    except:
        ml.log_and_print("getmisc.py -> get_lake_info: No lake info found at x={}, y={}, ({}).".format(x, y, reference))
        lake_data = None

    return lake_data


if __name__ == "__main__":

    # height = get_masl_from_utm33(120613, 6834932)
    # from_date, to_date = get_dates_from_year('2099-00')
    # get_lake_info(x=10.7754518, y=59.9855491)
    get_lake_info(x=249607, y=6656667, reference=32633)

    pass
