# -*- coding: utf-8 -*-
import datetime as dt
import requests
from config.setenvironment import chart_server_base_url

__author__ = 'ragnarekker'


def _make_weather_element_list_from_url(url, stationID, elementID, methodReference, patch_missing_values=True):
    """Returns a list of weatherElements given the url to a request
    on Chartserver/ShowData.aspx. This is common code to the "get" methods.

    :param url [string]:                    URL for the datarequest to chartserver/ShowData
    :param stationID [string]:              Station ID in hydra. Ex: stationID  = '6.24.4'
    :param elementID [string]:              Element ID in hydra. Ex: elementID = '17.1'
    :param methodReference [dictionary]:    Reference added to the metadata. Ex: {'MethodName': 'Chartserver - getStationdata'}
    :param patch_missing_values:[bool]      Go through the list and check if som values are missing. If so, patch up.
    :return [list[WeatherElement]]:         List of WeatherElement objects.
    """

    # ml.log_and_print("getchartserverdata -> _make_weather_element_list_from_url: Requesting {0}".format(url))
    request = requests.get(url)

    if request.status_code == 500:
        if "The length of the string exceeds the value set on the maxJsonLength property." in request.content:
            return "Request less data."
        else:
            return "HTTP 500 for unknown reason."

    datareq = request.json()

    seriesPoints = datareq[0][u'SeriesPoints']
    legendText = datareq[0][u'LegendText']

    weather_element_list = []

    if len(seriesPoints) > 0:
        for sp in seriesPoints:

            value = sp[u'Value']
            if value == '':
                value = None
            date = dc.unix_time_2_normal(sp[u'Key'])

            e = we.WeatherElement(stationID, date, elementID, value)
            e.Metadata.append(methodReference)
            e.Metadata.append({'URL':url})
            e.Metadata.append({'LegendText':legendText})
            weather_element_list.append(e)

        # Chartserver/ShowData.aspx returns half hour values and on request it returns [from, to]. That is,
        # it includes the to value so if the request is nested the data will contain doublets of values
        # om the "to dates". These are therefore taken out in this method.
        del weather_element_list[-1]

    else:
        ml.log_and_print('getchartserverdata -> _make_weather_element_list_from_url: ' + legendText)

    if patch_missing_values:
        weather_element_list = we.patch_novalue_in_weather_element_list(weather_element_list)

    return weather_element_list


def getGriddata(UTM33X, UTM33Y, elementID, fromDate, toDate, timeseries_type=0, output='list'):
    """Method gets data from the chartserver api at NVE. Method called is ShowData.aspx.
    Future dates as well as past dates are returned. Future dates are generated from model grids from met.no

    Note that griddata is based on met data from 00 to 06 dayly values. Eg. precipitation on 17th of mai is found in
    data for 06:00 18th of mai.

    Method returns [fromDate,toDate>

    :param UTM33X:          {int} X coordinate in utm33N
    :param UTM33Y:          {int} Y coordinate in utm33N
    :param elementID:       {string} Element ID in seNorge. Ex: elementID = 'fsw' is 24hr new snow depth in [cm]
    :param fromDate:        {datetime or string YYYY-mm-dd} method returns data [fromDate, toDate]
    :param toDate:          {datetime or string YYYY-mm-dd} method returns data [fromDate, toDate]
    :param timeseries_type  {int} Works only on output='list' daily = 0 (default), no change = -1
    :param output:          {string} How to present the output.
    :return:                {list} List of WeatherElement objects with 24h resolution.

    Timeseries types:
        None                Data returned as received from service
        0                   Data made to daily average
        See also:           http://eklima.no/wsKlima/complete/cTimeserie_en.html

    Output options:
        'list':             returns a list of WeatherElement objects.
        'json':             returns NULL but saves a .json file to the working folder.

    ElementID's used:
        fws:                new snow last 24hrs in mm water equivalents
        sd:                 snow depth in cm
        tm:                 temperature avarage 24hrs
        sdfsw:              new snow last 24hrs in cm

    Example URL for getting grid data
        http://h-web01.nve.no/chartserver/ShowData.aspx?req=getchart
        &ver=1.0
        &vfmt=json
        &time=20141204T0000;20141212T0000
        &chd=ds=hgts,da=29,id=260151;6671132;fsw
    """

    if isinstance(fromDate, str):
        fromDate = dt.datetime.strptime(fromDate, '%Y-%m-%d')

    if isinstance(toDate, str):
        toDate = dt.datetime.strptime(toDate, '%Y-%m-%d')

    # include data in todate in the request
    toDate += dt.timedelta(days=1)

    url = '{0}&time={1};{2}&chd=ds=hgts,da=29,id={3};{4};{5}'.format(
        chart_server_base_url, fromDate.strftime('%Y%m%dT%H%M'), toDate.strftime('%Y%m%dT%H%M'), UTM33X, UTM33Y, elementID)

    if output == 'list':

        weatherElementList = _make_weather_element_list_from_url(
            url, 'UTM33 X{0} Y{1}'.format(UTM33X, UTM33Y), elementID, {'MethodName': 'Chartserver - getGriddata'})

        # If to much data is requested, break it down to smaller portions.
        if weatherElementList == "Request less data.":
            time_delta = toDate - fromDate
            date_in_middle = (fromDate + time_delta/2).replace(hour=0, minute=0)
            weatherElementList = \
                getGriddata(UTM33X, UTM33Y, elementID, fromDate, date_in_middle, timeseries_type=timeseries_type, output=output) \
                + getGriddata(UTM33X, UTM33Y, elementID, date_in_middle, toDate, timeseries_type=timeseries_type, output=output)
            return weatherElementList

        else:

            if elementID == 'fsw' or elementID == 'sd' or elementID == 'sdfsw':
                weatherElementList = we.meter_from_centimeter(weatherElementList)        # convert for [cm] til [m]

            if timeseries_type == -1:              # do nothing
                weatherElementList = weatherElementList
            elif timeseries_type == 0:                # make daily avaregs of hourly values
                weatherElementList = we.make_daily_average(weatherElementList)
            else:
                ml.log_and_print('getchartserverdata -> getGriddata: no valid timeseries type selected')
                weatherElementList = 'no valid timeseries type selected'
            return weatherElementList

    elif output == 'json':
        datareq = requests.get(url)
        filename = 'X{0}_Y{1}_{2}.{3}_{4}.json'.format(
            UTM33X, UTM33Y, elementID, fromDate.strftime('%Y%m%d'), toDate.strftime('%Y%m%d'))
        f = open(filename, 'w')
        f.write((datareq.text).encode('utf-8'))
        f.close()
        return

    else:
        ml.log_and_print('getchartserverdata -> getGriddata: No valid output requested.')
        return 'No valid output requested'


def getYrdata(stationID, elementID, fromDate, toDate, timeseries_type=0, output='list'):
    """
    Gets data form yr.no though the chartserver api at NVE. Method called is ShowData.aspx.
    Does not return historical values. Seems only to return +48 hrs even though more is requested.

    :param stationID:   {string} Station ID in hydra. Ex: stationID  = '6.24.4'
    :param elementID:   {string} Element ID in hydra. Ex: elementID = '17.1'
    :param fromDate:    {datetime} method returns data including fromDate
    :param toDate:      {datetime} method returns data including toDate
    :param output:      {string} How to present the output.
    :return:            List of WeatherElement objects with 24h resolution.


    Timeseries types:
        None                Data returned as received from service
        0                   Data made to daily average
        See also:           http://eklima.no/wsKlima/complete/cTimeserie_en.html

    Output options:
        'list':         returns a list of WeatherElement objects.
        'json':         returns NULL but saves a .json file til the working folder.

    URL for getting stationdata from Hakkloa 6.24.4.17.1

        http://h-web01.nve.no/chartserver/ShowData.aspx
        ?req=getchart
        &ver=1.0
        &vfmt=json
        &time=20141204T0000;20141212T0000
        &chd=ds=htsry,id=hydx[6;24;4;17;1].6000

    """

    url = "{0}&time={1};{2}&chd=ds=htsry,id=hydx[{3};{4}].6000"\
        .format(chart_server_base_url,
                fromDate.strftime('%Y%m%dT%H%M'),
                toDate.strftime('%Y%m%dT%H%M'),
                stationID.replace('.',';'),
                elementID.replace('.',';'))

    if output == 'list':

        weatherElementList = _make_weather_element_list_from_url(url, stationID, elementID, {'MethodName': 'Chartserver - getYrdata'})

        # If to much data is requested, break it down to smaller portions.
        if weatherElementList == "Request less data.":
            time_delta = toDate - fromDate
            date_in_middle = (fromDate + time_delta/2).replace(hour=0, minute=0)
            weatherElementList = getYrdata(stationID, elementID, fromDate, date_in_middle, timeseries_type=timeseries_type, output=output) \
                                 + getYrdata(stationID, elementID, date_in_middle, toDate, timeseries_type=timeseries_type, output=output)
            return weatherElementList

        else:

            if timeseries_type == -1:              # do nothing
                weatherElementList = weatherElementList
            elif timeseries_type == 0:                # make dailyavaregs of hourly values
                weatherElementList = we.make_daily_average(weatherElementList)
            else:
                ml.log_and_print('getchartserverdata -> getYrdata: no valid timeseries type selected')
                weatherElementList = 'no valid timeseries type selected'
            return weatherElementList

    elif output == 'json':
        datareq = requests.get(url)
        filename = '{0}.{1}_{2}_{3}.json'\
            .format(stationID, elementID, dt.date.today().strftime('%Y%m%d'), toDate.strftime('%Y%m%d'))
        f = open(filename, 'w')
        f.write((datareq.text).encode('utf-8'))
        f.close()
        return

    else:
        ml.log_and_print('getchartserverdata -> getYrdata: No valid output requested.')
        return 'No valid output requested'


def getStationdata(stationID, elementID, fromDate, toDate, timeseries_type=0, output='list'):
    """Method gets data from the chartserver api at NVE. Method called is ShowData.aspx.
    The data returned from the api are 30min values but they may be recalculated to daily average in this method
    if timeseries_type=0. Method returns [fromDate,toDate>. Future dates are truncated in this method,
    but dataset may be complemented with the getYrdata in this class.

    :param stationID:   {string} Station ID in hydra. Ex: stationID  = '6.24.4'
    :param elementID:   {string} Element ID in hydra. Ex: elementID = '17.1'
    :param fromDate:    {datetime} method returns [fromDate ,toDate>
    :param toDate:      {datetime} method returns [fromDate ,toDate>
    :param output:      {string} How to present the output.
    :return:            {list} List of WeatherElement objects.


    Timeseries types:
        None                Data returned as received from service
        0                   Data made to daily average
        See also:           http://eklima.no/wsKlima/complete/cTimeserie_en.html

    Output options:
        'list':         returns a list of WeatherElement objects.
        'json':         returns NULL but saves a .json file til the working folder.

    URL for getting stationdata from Hakkloa 6.24.4.17.1

        http://h-web01.nve.no/chartserver/ShowData.aspx
        ?req=getchart
        &ver=1.0
        &vfmt=json
        &time=20141204T0000;20141212T0000
        &chd=ds=htsr,da=29,id=6.24.4.17.1

    """


    # if not datetime objects, make them so
    if isinstance(fromDate, str):
        fromDate = dt.datetime.strptime(fromDate, "%Y-%m-%d")
    if isinstance(toDate, str):
        toDate = dt.datetime.strptime(toDate, "%Y-%m-%d")


    url = "{0}&time={1};{2}&chd=ds=htsr,da=29,id={3}.{4}"\
        .format(chart_server_base_url, fromDate.strftime('%Y%m%dT%H%M'), toDate.strftime('%Y%m%dT%H%M'), stationID, elementID)

    if output == 'list':
        weatherElementList = _make_weather_element_list_from_url(url, stationID, elementID, {'MethodName': 'Chartserver - getStationdata'})

        # If to much data is requested, break it down to smaller portions.
        if weatherElementList == "Request less data.":
            time_delta = toDate - fromDate
            date_in_middle = (fromDate + time_delta/2).replace(hour=0, minute=0)
            weatherElementList = getStationdata(stationID, elementID, fromDate, date_in_middle, timeseries_type=timeseries_type, output=output) \
                                 + getStationdata(stationID, elementID, date_in_middle, toDate, timeseries_type=timeseries_type, output=output)
            return weatherElementList

        else:
            if timeseries_type == -1:              # do nothing
                weatherElementList = weatherElementList
            elif timeseries_type == 0:                # make daily averages of hourly values
                weatherElementList = we.make_daily_average(weatherElementList)
            else:
                ml.log_and_print('getchartserverdata -> getYrdata: no valid timeseries type selected')
                weatherElementList = 'no valid timeseries type selected'
            return weatherElementList

    elif output == 'json':
        datareq = requests.get(url)
        filename = '{0}.{1}_{2}_{3}.json'\
            .format(stationID, elementID, fromDate.strftime('%Y%m%d'), dt.date.today().strftime('%Y%m%d'))
        f = open(filename, 'w')
        f.write((datareq.text).encode('utf-8'))
        f.close()
        return

    else:
        ml.log_and_print('getchartserverdata -> getYrdata: No valid output requested.')
        return 'No valid output requested'


def __runHakkloaTemp():
    # Hakkloa temp data
    stationID  = '6.24.4'
    elementID = '17.1'
    #fromDate = dt.datetime.strptime('2011-01-01', "%Y-%m-%d")
    #toDate   = dt.datetime.strptime('2015-01-01', "%Y-%m-%d")
    fromDate = dt.datetime.combine(dt.date.today() - dt.timedelta(days=400), dt.datetime.min.time())
    toDate =   dt.datetime.combine(dt.date.today() + dt.timedelta(days=4), dt.datetime.min.time())

    return getStationdata(stationID, elementID, fromDate, toDate)


def __runHakkloaSnow():

    # Hakkloa snow data
    UTM33X = 260151
    UTM33Y = 6671132
    elementID = 'fsw'

    #fromDate = dt.datetime.strptime('2017-02-10', "%Y-%m-%d")
    #toDate   = dt.datetime.strptime('2017-02-20', "%Y-%m-%d")
    fromDate = dt.datetime.combine(dt.date.today() - dt.timedelta(days=100), dt.datetime.min.time())
    toDate =   dt.datetime.combine(dt.date.today() + dt.timedelta(days=10), dt.datetime.min.time())

    return getGriddata(UTM33X, UTM33Y, elementID, fromDate, toDate)


def __runHakkloaTempYr():
    # Hakkloa temp data
    stationID  = '6.24.4'
    elementID = '17.1'
    fromDate = dt.datetime.combine(dt.date.today() - dt.timedelta(days=10), dt.datetime.min.time())
    toDate =   dt.datetime.combine(dt.date.today() + dt.timedelta(days=10), dt.datetime.min.time())

    return getYrdata(stationID, elementID, fromDate, toDate)


if __name__ == "__main__":

    # Examples
    #station = __runHakkloaTemp()
    grid =__runHakkloaSnow()
    #yr = __runHakkloaTempYr()

    from utilities import makefiledata as mfd, makelogs as ml, doconversions as dc, weatherelementlistoperations as we

    #mfd.write_weather_element_list(station)
    mfd.write_weather_element_list(grid)
    #mfd.write_weather_element_list(yr)

    a = 1