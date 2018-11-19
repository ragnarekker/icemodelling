# -*- coding: utf-8 -*-
import datetime as dt
import requests as rq
from icemodelling import weatherelement as we
from utilities import makeplots as mplot

__author__ = 'ragnarekker'


def getgts(utm33x, utm33y, element_id, from_date, to_date, timeseries_type=0, patch_missing_values=True):
    """Retrieves data from the grid time series application (GTS) and maps it to a list of WeatherElements.

    Values in WeatherElements are given in meters, i.e in some cases they are converted from cm to m.
    Optionally the data is patched up if data is missing and daily averages from 00-24 are calculated.

    GTS data is given as 24hour avarages from 0600-0600. If timeseries_type=0 is requested, data
    is converted to daily average from 00-24hrs, time stamped at the end of the period (23:59:59).

    :param utm33x:              [int] X coordinate in utm33N
    :param utm33y:              [int] Y coordinate in utm33N
    :param element_id:          [string] Element ID in seNorge. Ex: elementID = 'fsw' is 24hr new snow depth in [cm]
    :param from_date:           [datetime or string YYYY-mm-dd] method returns data [fromDate, toDate]
    :param to_date:             [datetime or string YYYY-mm-dd] method returns data [fromDate, toDate]
    :param timeseries_type      [int] daily = 0 (default), no change = -1
    :param patch_missing_values:[bool] Go through the list and check if som values are missing. If so, patch up.
    :param output:              [list of WeatherElements]
    :return:

    http://h-web02.nve.no:8080/api/GridTimeSeries/gridtimeserie?theme=tm&startdate=2017-11-20&enddate=2017-11-22&x=109190&y=6817490

    timeseries_type's:
        -1                  Data returned as received from service
        0                   Data made to daily average from 00-24hrs
        See also:           http://eklima.no/wsKlima/complete/cTimeserie_en.html

    element_id's used:
        fws:                new snow last 24hrs in mm water equivalents
        sd:                 snow depth in cm
        tm:                 temperature average 24hrs
        sdfsw:              new snow last 24hrs in cm
    """

    url = 'http://h-web02.nve.no:8080/api/GridTimeSeries/gridtimeserie?theme={0}&startdate={1}&enddate={2}&x={3}&y={4}'.format(element_id, from_date, to_date, utm33x, utm33y)

    responds = rq.get(url)

    full_data = responds.json()
    data = full_data['Data']

    weather_element_list = []
    date = dt.datetime.strptime(full_data['StartDate'], '%d.%m.%Y %H:%M:%S')

    # the assigned NoDataValue if one data element is missing.
    no_data_value = int(full_data['NoDataValue'])

    for d in data:
        value = float(d)
        if value == no_data_value:
            value = None
        weather_element = we.WeatherElement('UTM33 X{0} Y{1}'.format(utm33x, utm33y), date, element_id, value)
        weather_element.Metadata['DataSource'] = 'GTS'
        weather_element.Metadata['TimeResolution'] = full_data['TimeResolution']
        weather_element.Metadata['FullName'] = full_data['FullName']
        weather_element.Metadata['WeatherDataAltitude'] = full_data['Altitude']
        weather_element_list.append(weather_element)
        date += dt.timedelta(minutes=full_data['TimeResolution'])

    if patch_missing_values:
        weather_element_list = we.patch_novalue_in_weather_element_list(weather_element_list)

    if element_id == 'fsw' or element_id == 'sd' or element_id == 'sdfsw':
        weather_element_list = we.meter_from_centimeter(weather_element_list)  # convert for [cm] til [m]

    if timeseries_type == 0:
        weather_element_list = we.make_daily_average(weather_element_list)

        # fist element after doing daily avarage represents the day before the requested time period
        del weather_element_list[0]

    return weather_element_list


if __name__ == "__main__":

    weather_pr_day = getgts(109190, 6817490, 'tm', '2017-12-20', '2017-12-30')
    gts_weather = getgts(109190, 6817490, 'tm', '2017-12-20', '2017-12-30', timeseries_type=-1)

    mplot.plot_weather_elements([weather_pr_day, gts_weather])

    pass
