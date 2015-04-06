__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-


import copy

import iceThicknessCalculation
from TimeseriesIO import getMetData, readWeather, plotIcecover, stripMetadata, getStationdata, makeDailyAvarage, getGriddata, \
    IceColumn, getAllSeasonIce
from Calculations.parameterization import *


#plot_folder = "C:\\Users\\raek\\Documents\\GitHub\\Ice-modelling\\Plots\\"
#data_path = "C:\\Users\\raek\\Documents\\GitHub\\Ice-modelling\\TimeseriesData\\"

plot_folder = "/Users/ragnarekker/Documents/GitHub/Ice-modelling/Plots/"
data_path = "/Users/ragnarekker/Documents/GitHub/Ice-modelling/TimeseriesData/"

def calculateIceCover(*args):

    inn_column = args[0]
    date = args[1]
    temp = args[2]
    sno = args[3]

    icecover = []
    timestep = 60*60*24     # fixed timestep of 24hrs given in seconds
    icecover.append(copy.deepcopy(inn_column))

    for i in range(0, len(date), 1):
        if date[i] < inn_column.date:
            i = i + 1
        else:
            if len(args) == 4:
                out_column = iceThicknessCalculation.getIceThickness(inn_column, timestep, sno[i], temp[i])
            elif len(args) == 5:
                cloudcover = args[4]
                out_column = iceThicknessCalculation.getIceThickness(inn_column, timestep, sno[i], temp[i], cloudcover[i])
            icecover.append(out_column)
            inn_column = copy.deepcopy(out_column)

    return icecover

def runOrovannNVE(startDate, endDate):

    # Need datetime objects from now on
    LocationName = 'Otrøvatnet v/Nystuen 971 moh'
    startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d")

    weather_data_filename = '{0}kyrkjestoelane_vaerdata.csv'.format(data_path)
    date, temp, sno, snotot = readWeather(startDate, endDate, weather_data_filename)

    #observed_ice_filename = '{0}Otroevann observasjoner 2011-2012.csv'.format(data_path)
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = getAllSeasonIce(LocationName, startDate, endDate)

    icecover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno)

    plot_filename = '{0}Ortovann {1}-{2}.png'.format(plot_folder, startDate.year, endDate.year)
    plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)

def runOrovannMET(startDate, endDate):

    LocationName = 'Otrøvatnet v/Nystuen 971 moh'
    wsTemp = getMetData(54710, 'TAM', startDate, endDate, 0, 'list')
    wsSno  = getMetData(54710, 'SA',  startDate, endDate, 0, 'list')

    date = []
    snotot = []
    temp = []

    for e in wsTemp:
        date.append(e.Date)
        temp.append(e.Value)
    for e in wsSno:
        snotot.append(e.Value)

    sno = makeSnowChangeFromSnowTotal(snotot)

    #observed_ice_filename = '{0}Otroevann observasjoner {1}-{2}.csv'.format(data_path, startDate.year, endDate.year)
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = getAllSeasonIce(LocationName, startDate, endDate)

    if len(observed_ice) == 0:
        icecover = calculateIceCover(IceColumn.IceColumn(date[0], []), date, temp, sno)
    else:
        icecover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno)

    # Need datetime objects from now on
    from_date = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = datetime.datetime.strptime(endDate, "%Y-%m-%d")

    plot_filename = '{0}Ortovann MET {1}-{2}.png'.format(plot_folder, from_date.year, to_date.year)
    plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)

def runSemsvann(startDate, endDate):

    LocationName = 'Semsvannet v/Lo 145 moh'

    wsTemp = getMetData(19710, 'TAM', startDate, endDate, 0, 'list')
    wsSno = getMetData(19710, 'SA', startDate, endDate, 0, 'list')
    wsCC = getMetData(18700, 'NNM', startDate, endDate, 0 , 'list')

    temp, date = stripMetadata(wsTemp, True)
    snotot = stripMetadata(wsSno, False)
    cc = stripMetadata(wsCC, False)

    sno = makeSnowChangeFromSnowTotal(snotot)

    #observed_ice_filename = '{0}Semsvann observasjoner {1}-{2}.csv'.format(data_path, startDate[0:4], endDate[0:4])
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = getAllSeasonIce(LocationName, startDate, endDate)
    if len(observed_ice) == 0:
        icecover = calculateIceCover(IceColumn.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        icecover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Semsvann {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)

def runHakkloa(startDate, endDate):

    LocationName = 'Hakkloa nord 372 moh'
    from_date = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = datetime.datetime.strptime(endDate, "%Y-%m-%d")

    cs_temp = makeDailyAvarage(getStationdata('6.24.4','17.1', from_date, to_date, 'list'))
    cs_sno = makeDailyAvarage(getGriddata(260150, 6671135, 'fsw', from_date, to_date, 'list'))
    cs_snotot = makeDailyAvarage(getGriddata(260150, 6671135, 'sd', from_date, to_date, 'list'))
    wsCC = getMetData(18700, 'NNM', startDate, endDate, 0, 'list')

    temp, date = stripMetadata(cs_temp, True)
    sno = stripMetadata(cs_sno, False)
    snotot = stripMetadata(cs_snotot, False)
    cc = stripMetadata(wsCC, False)

    observed_ice = getAllSeasonIce(LocationName, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCover(IceColumn.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Hakkloa {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)

if __name__ == "__main__":

    #runSemsvann('2011-11-01', '2012-05-01')
    #runSemsvann('2012-11-01', '2013-06-01')
    #runSemsvann('2013-11-01', '2014-04-15')
    #runSemsvann('2014-11-01', '2015-03-27')

    #runOrovannNVE('2011-11-15', '2012-06-20')
    #runOrovannMET('2011-11-15', '2012-06-20')
    runOrovannMET('2012-11-15', '2013-06-20')
    runOrovannMET('2013-11-15', '2014-06-20')
    #runOrovannMET('2014-11-15', '2015-03-27')

    '''
    runHakkloa('2011-11-01', '2012-06-01')
    runHakkloa('2012-11-01', '2013-06-01')
    runHakkloa('2013-11-01', '2014-06-01')
    runHakkloa('2014-11-01', '2015-03-27')
    '''

