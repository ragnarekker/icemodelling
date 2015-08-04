__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import datetime

import requests

import calculateParameterization as pz
from WeatherElement import WeatherElement, makeDailyAvarage, cm2m

# URL to the chartserver/ShowData service
baseURL = "http://h-web01.nve.no/chartserver/ShowData.aspx?req=getchart&ver=1.0&vfmt=json"

def __makeWeatherElementListFromURL(url, stationID, elementID, methodReference):
    """
    Internal method that returns a list of weatherElements given the url to a request on Chartserver/ShowData.aspx. This
    is common code to the public "get" methods.

    :param url [string]:                    URL for the datarequest to chartserver/ShowData
    :param stationID [string]:              Station ID in hydra. Ex: stationID  = '6.24.4'
    :param elementID [string]:              Element ID in hydra. Ex: elementID = '17.1'
    :param methodReference [dictionary]:    Referance added to the metadata. Ex: {'MethodName': 'Chartserver - getStationdata'}
    :return [list[WeatherElement]]:         List of WeatherElement objects.
    """
    datareq = requests.get(url).json()

    seriesPoints = datareq[0][u'SeriesPoints']
    legendText = datareq[0][u'LegendText']

    weatherElementList = []

    for sp in seriesPoints:

        value = sp[u'Value']
        date = pz.normal_time_from_unix_time(int(sp[u'Key'][6:-2]))

        we = WeatherElement(stationID, date, elementID, value)
        we.Metadata.append(methodReference)
        we.Metadata.append({'URL':url})
        we.Metadata.append({'LegendText':legendText})
        weatherElementList.append(we)

    return weatherElementList

def getGriddata(UTM33X, UTM33Y, elementID, fromDate, toDate, output):
    """
    Method gets data from the chartserverapi at NVE. Method called is ShowData.aspx.
    Future dates as well as past dates are returned. Future dates are generated from modellgrids from met.no

    Note that griddata is based on met data from 00 to 06 dayly values. Eg. precipitation on 17th of mai is found in
    data for 06:00 18th of mai.

    :param UTM33X:      {int} X coordinate in utm33N
    :param UTM33Y:      {int} Y coordinate in utm33N
    :param elementID:   {string} Element ID in seNorge. Ex: elementID = 'fsw' is 24hr new snow depth in [cm]
    :param fromDate:    {datetime} method returns [fromDate ,toDate>
    :param toDate:      {datetime} method returns [fromDate ,toDate>
    :param output:      {string} How to present the output.
    :return:            {list} List of WeatherElement objects with 24h resolution.

    Output options:
        'list':         returns a list of WeatherElement objects.
        'json':         returns NULL but saves a .json file til the working folder.


    ElementID's used:
        fws:            new snow last 24hrs
        sd:             snow depth
        tm:             temperature avarage 24hrs


    Example URL for getting grid data
        http://h-web01.nve.no/chartserver/ShowData.aspx?req=getchart
        &ver=1.0
        &vfmt=json
        &time=20141204T0000;20141212T0000
        &chd=ds=hgts,da=29,id=260151;6671132;fsw

    """

    url = '{0}&time={1};{2}&chd=ds=hgts,da=29,id={3};{4};{5}'\
        .format(baseURL, fromDate.strftime('%Y%m%dT%H%M'), toDate.strftime('%Y%m%dT%H%M'), UTM33X, UTM33Y, elementID)

    if output == 'list':
        weatherElementList = __makeWeatherElementListFromURL(url , 'UTM33 X{0} Y{1}'.format(UTM33X, UTM33Y), elementID, {'MethodName': 'Chartserver - getGriddata'})
        if elementID == 'fsw' or elementID == 'sd':
            weatherElementList = cm2m(weatherElementList)        # convert for [cm] til [m]
        return weatherElementList

    elif output == 'json':
        datareq = requests.get(url)
        filename = 'X{0}_Y{1}_{2}.{3}_{4}.json'\
            .format(UTM33X, UTM33Y, elementID, fromDate.strftime('%Y%m%d'), toDate.strftime('%Y%m%d'))
        f = open(filename, 'w')
        f.write((datareq.text).encode('utf-8'))
        f.close()
        return

    else:
        print('No valid output requested.')
        return 'No valid output requested'

def getYrdata(stationID, elementID, fromDate, toDate, output):
    """
    Gets data form yr.no though the chartserverapi at NVE. Method called is ShowData.aspx.
    Does not return historical values. Seems only to return +48 hrs even though more is requested.

    :param stationID:   {string} Station ID in hydra. Ex: stationID  = '6.24.4'
    :param elementID:   {string} Element ID in hydra. Ex: elementID = '17.1'
    :param fromDate:    {datetime} method returns data including fromDate
    :param toDate:      {datetime} method returns data including toDate
    :param output:      {string} How to present the output.
    :return:            List of WeatherElement objects with 24h resolution.

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
        .format(baseURL,
                fromDate.strftime('%Y%m%dT%H%M'),
                toDate.strftime('%Y%m%dT%H%M'),
                stationID.replace('.',';'),
                elementID.replace('.',';'))

    if output == 'list':
        weatherElementList = __makeWeatherElementListFromURL(url, stationID, elementID, {'MethodName': 'Chartserver - getYrdata'})
        weatherElementList = makeDailyAvarage(weatherElementList)        # make dailyavaregs of hourly values

    elif output == 'json':
        datareq = requests.get(url)
        filename = '{0}.{1}_{2}_{3}.json'\
            .format(stationID, elementID, datetime.date.today().strftime('%Y%m%d'), toDate.strftime('%Y%m%d'))
        f = open(filename, 'w')
        f.write((datareq.text).encode('utf-8'))
        f.close()
        return

    else:
        print('No valid output requested.')
        return 'No valid output requested'



    return weatherElementList

def getStationdata(stationID, elementID, fromDate, toDate, output):
    """
    Method gets data from the chartserverapi at NVE. Method called is ShowData.aspx.
    The data returned from the api are 30min values but they recalculated to daily average in this method.
    Future dates are truncated in this method, but dataset may be complemented with the getYrdata in this class.

    :param stationID:   {string} Station ID in hydra. Ex: stationID  = '6.24.4'
    :param elementID:   {string} Element ID in hydra. Ex: elementID = '17.1'
    :param fromDate:    {datetime} method returns [fromDate ,toDate]
    :param toDate:      {datetime} method returns [fromDate ,toDate]
    :param output:      {string} How to present the output.
    :return:            {list} List of WeatherElement objects with 24h resolution.

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

    url = "{0}&time={1};{2}&chd=ds=htsr,da=29,id={3}.{4}"\
        .format(baseURL, fromDate.strftime('%Y%m%dT%H%M'), toDate.strftime('%Y%m%dT%H%M'), stationID, elementID)

    if output == 'list':
        weatherElementList = __makeWeatherElementListFromURL(url, stationID, elementID, {'MethodName': 'Chartserver - getStationdata'})
        weatherElementList = makeDailyAvarage(weatherElementList)               # daily avarages
        return weatherElementList

    elif output == 'json':
        datareq = requests.get(url)
        filename = '{0}.{1}_{2}_{3}.json'\
            .format(stationID, elementID, fromDate.strftime('%Y%m%d'), datetime.date.today().strftime('%Y%m%d'))
        f = open(filename, 'w')
        f.write((datareq.text).encode('utf-8'))
        f.close()
        return

    else:
        print('No valid output requested.')
        return 'No valid output requested'


def __runHakkloaTemp():
    # Hakkloa temp data
    stationID  = '6.24.4'
    elementID = '17.1'
    #fromDate = datetime.datetime.strptime('2013-10-01', "%Y-%m-%d")
    #toDate   = datetime.datetime.strptime('2014-06-01', "%Y-%m-%d")
    fromDate = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=4), datetime.datetime.min.time())
    toDate =   datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=4), datetime.datetime.min.time())
    output = 'list'

    return getStationdata(stationID, elementID, fromDate, toDate, output)

def __runHakkloaSnow():

    # Hakkloa snow data
    UTM33X = 260151
    UTM33Y = 6671132
    elementID = 'fsw'

    #fromDate = datetime.datetime.strptime('2013-10-01', "%Y-%m-%d")
    #toDate   = datetime.datetime.strptime('2014-06-01', "%Y-%m-%d")
    fromDate = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=4), datetime.datetime.min.time())
    toDate =   datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=4), datetime.datetime.min.time())
    output = 'list'

    return getGriddata(UTM33X, UTM33Y, elementID,fromDate, toDate, output)

def __runHakkloaTempYr():
    # Hakkloa temp data
    stationID  = '6.24.4'
    elementID = '17.1'
    fromDate = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=4), datetime.datetime.min.time())
    toDate =   datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=4), datetime.datetime.min.time())
    output = 'list'

    return getYrdata(stationID, elementID, fromDate, toDate, output)


if __name__ == "__main__":

    # Examples
    station = __runHakkloaTemp()
    grid    =__runHakkloaSnow()
    yr      = __runHakkloaTempYr()

    a = 1