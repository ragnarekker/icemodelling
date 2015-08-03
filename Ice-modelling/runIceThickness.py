__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-


import copy
import datetime as dt

import calculateIceThickness as itc
import calculateParameterization as pz
import IceColumn as ic
import WeatherElement as we
import getRegObsdata as gro
import getFiledata as gfd
import getWSklima as gws
import getChartserverdata as gcsd
import makePlots as pts
from setEnvironment import data_path, plot_folder


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
                out_column = itc.getIceThickness(inn_column, timestep, sno[i], temp[i])
            elif len(args) == 5:
                cloudcover = args[4]
                out_column = itc.getIceThickness(inn_column, timestep, sno[i], temp[i], cloudcover[i])
            icecover.append(out_column)
            inn_column = copy.deepcopy(out_column)

    return icecover


def runOrovannNVE(startDate, endDate):

    # Need datetime objects from now on
    LocationName = 'Otrøvatnet v/Nystuen 971 moh'
    startDate = dt.datetime.strptime(startDate, "%Y-%m-%d")
    endDate = dt.datetime.strptime(endDate, "%Y-%m-%d")

    weather_data_filename = '{0}kyrkjestoelane_vaerdata.csv'.format(data_path)
    date, temp, sno, snotot = gfd.readWeather(startDate, endDate, weather_data_filename)

    #observed_ice_filename = '{0}Otroevann observasjoner 2011-2012.csv'.format(data_path)
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = gro.getAllSeasonIce(LocationName, startDate, endDate)

    icecover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno)

    plot_filename = '{0}Ortovann {1}-{2}.png'.format(plot_folder, startDate.year, endDate.year)
    pts.plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)


def runOrovannMET(startDate, endDate):

    location_name = 'Otrøvatnet v/Nystuen 971 moh'
    wsTemp = gws.getMetData(54710, 'TAM', startDate, endDate, 0, 'list')
    wsSno  = gws.getMetData(54710, 'SA',  startDate, endDate, 0, 'list')

    date = []
    snotot = []
    temp = []

    for e in wsTemp:
        date.append(e.Date)
        temp.append(e.Value)
    for e in wsSno:
        snotot.append(e.Value)

    sno = pz.makeSnowChangeFromSnowTotal(snotot)

    #observed_ice_filename = '{0}Otroevann observasjoner {1}-{2}.csv'.format(data_path, startDate.year, endDate.year)
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = gro.getAllSeasonIce(location_name, startDate, endDate)

    if len(observed_ice) == 0:
        icecover = calculateIceCover(ic.IceColumn(date[0], []), date, temp, sno)
    else:
        icecover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno)

    # Need datetime objects from now on
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    plot_filename = '{0}Ortovann MET {1}-{2}.png'.format(plot_folder, from_date.year, to_date.year)
    pts.plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)


def runSemsvann(startDate, endDate):

    LocationName = 'Semsvannet v/Lo 145 moh'

    wsTemp = gws.getMetData(19710, 'TAM', startDate, endDate, 0, 'list')
    wsSno = gws.getMetData(19710, 'SA', startDate, endDate, 0, 'list')
    wsCC = gws.getMetData(18700, 'NNM', startDate, endDate, 0 , 'list')

    temp, date = we.stripMetadata(wsTemp, True)
    snotot = we.stripMetadata(wsSno, False)
    cc = we.stripMetadata(wsCC, False)

    sno = pz.makeSnowChangeFromSnowTotal(snotot)

    #observed_ice_filename = '{0}Semsvann observasjoner {1}-{2}.csv'.format(data_path, startDate[0:4], endDate[0:4])
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = gro.getAllSeasonIce(LocationName, startDate, endDate)
    if len(observed_ice) == 0:
        icecover = calculateIceCover(ic.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        icecover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Semsvann {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)


def runHakkloa(startDate, endDate):

    LocationName = 'Hakkloa nord 372 moh'
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    cs_temp = we.makeDailyAvarage(gcsd.getStationdata('6.24.4','17.1', from_date, to_date, 'list'))
    cs_sno = we.makeDailyAvarage(gcsd.getGriddata(260150, 6671135, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.makeDailyAvarage(gcsd.getGriddata(260150, 6671135, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(18700, 'NNM', startDate, endDate, 0, 'list')

    temp, date = we.stripMetadata(cs_temp, True)
    sno = we.stripMetadata(cs_sno, False)
    snotot = we.stripMetadata(cs_snotot, False)
    cc = we.stripMetadata(wsCC, False)

    observed_ice = gro.getAllSeasonIce(LocationName, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCover(ic.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Hakkloa {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runSkoddebergvatnet(startDate, endDate):

    LocationName = 'Skoddebergvatnet - nord 101 moh'
    # Skoddebergvatnet - sør 101 moh
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    #cs_temp = makeDailyAvarage(gcsd.getStationdata('189.3.0','17.1', from_date, to_date, 'list'))
    cs_temp = we.makeDailyAvarage(gcsd.getGriddata(593273, 7612469, 'tm', from_date, to_date, 'list'))
    cs_sno = we.makeDailyAvarage(gcsd.getGriddata(593273, 7612469, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.makeDailyAvarage(gcsd.getGriddata(593273, 7612469, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(87640, 'NNM', startDate, endDate, 0, 'list')  # Harstad Stadion

    temp, date = we.stripMetadata(cs_temp, True)
    sno = we.stripMetadata(cs_sno, False)
    snotot = we.stripMetadata(cs_snotot, False)
    cc = we.stripMetadata(wsCC, False)

    observed_ice = gro.getAllSeasonIce(LocationName, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCover(ic.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Skoddebergvatnet {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runGiljastolsvatnet(startDate, endDate):

    LocationNames = ['Giljastølsvatnet 412 moh', 'Giljastølvatnet sør 412 moh']
    x = -1904
    y = 6553573

    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    #cs_temp = makeDailyAvarage(gcsd.getStationdata('189.3.0','17.1', from_date, to_date, 'list'))
    cs_temp = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'tm', from_date, to_date, 'list'))
    cs_sno = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(43010, 'NNM', startDate, endDate, 0, 'list')  # Eik - Hove. Ligger lenger sør men er litt inn i landet.
    #wsCC = getMetData(43010, 'NNM', startDate, endDate, 0, 'list') # Sola (44560) er et alternativ

    temp, date = we.stripMetadata(cs_temp, True)
    sno = we.stripMetadata(cs_sno, False)
    snotot = we.stripMetadata(cs_snotot, False)
    cc = we.stripMetadata(wsCC, False)

    observed_ice = gro.getAllSeasonIce(LocationNames, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCover(ic.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Giljastolsvatnet {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runBaklidammen(startDate, endDate):

    LocationNames = ['Baklidammen 200 moh']
    x = 266550
    y = 7040812

    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    cs_temp = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'tm', from_date, to_date, 'list'))
    cs_sno = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(68860, 'NNM', startDate, endDate, 0, 'list')  # TRONDHEIM - VOLL

    temp, date = we.stripMetadata(cs_temp, True)
    sno = we.stripMetadata(cs_sno, False)
    snotot = we.stripMetadata(cs_snotot, False)
    cc = we.stripMetadata(wsCC, False)

    observed_ice = gro.getAllSeasonIce(LocationNames, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCover(ic.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Baklidammen {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runStorvannetHammerfest(startDate, endDate):

    LocationNames = ['Storvannet, 7 moh']
    x = 821340
    y = 7862497

    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    cs_temp = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'tm', from_date, to_date, 'list'))
    cs_sno = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.makeDailyAvarage(gcsd.getGriddata(x, y, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(95350, 'NNM', startDate, endDate, 0, 'list')  # BANAK - østover innerst i fjorden

    temp, date = we.stripMetadata(cs_temp, True)
    sno = we.stripMetadata(cs_sno, False)
    snotot = we.stripMetadata(cs_snotot, False)
    cc = we.stripMetadata(wsCC, False)

    observed_ice = gro.getAllSeasonIce(LocationNames, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCover(ic.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCover(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}StorvannetHammerfest {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


if __name__ == "__main__":
    '''
    #runSemsvann('2011-11-01', '2012-05-01')
    #runSemsvann('2012-11-01', '2013-06-01')
    #runSemsvann('2013-11-01', '2014-04-15')
    #runSemsvann('2014-11-01', '2015-05-15')

    #runOrovannNVE('2011-11-15', '2012-06-20')
    runOrovannMET('2011-11-15', '2012-06-20')
    runOrovannMET('2012-11-15', '2013-06-20')
    runOrovannMET('2013-11-15', '2014-06-20')
    runOrovannMET('2014-11-15', '2015-03-27')

    '''
    runHakkloa('2011-11-01', '2012-06-01')
    runHakkloa('2012-11-01', '2013-06-01')
    runHakkloa('2013-11-01', '2014-06-01')
    runHakkloa('2014-11-01', '2015-06-01')
    '''
    runSkoddebergvatnet('2006-11-01', '2007-06-01')
    runSkoddebergvatnet('2007-11-01', '2008-06-01')
    runSkoddebergvatnet('2008-11-01', '2009-06-01')
    runSkoddebergvatnet('2009-11-01', '2010-06-01')
    runSkoddebergvatnet('2010-11-01', '2011-06-01')
    runSkoddebergvatnet('2011-11-01', '2012-06-01')
    runSkoddebergvatnet('2012-11-01', '2013-06-01')
    runSkoddebergvatnet('2013-11-01', '2014-06-01')
    runSkoddebergvatnet('2014-11-01', '2015-06-01')

    runGiljastolsvatnet('2012-11-01', '2013-06-01')
    runGiljastolsvatnet('2013-11-01', '2014-06-01')
    runGiljastolsvatnet('2014-11-01', '2015-06-01')

    runBaklidammen('2006-11-01', '2007-06-01')
    runBaklidammen('2007-11-01', '2008-06-01')
    runBaklidammen('2008-11-01', '2009-06-01')
    runBaklidammen('2009-11-01', '2010-06-01')
    runBaklidammen('2010-11-01', '2011-06-01')
    runBaklidammen('2011-11-01', '2012-06-01')
    runBaklidammen('2012-11-01', '2013-06-01')
    runBaklidammen('2013-11-01', '2014-06-01')
    runBaklidammen('2014-11-01', '2015-06-01')

    runStorvannetHammerfest('2008-11-01', '2009-06-01')
    runStorvannetHammerfest('2009-11-01', '2010-06-01')
    runStorvannetHammerfest('2010-11-01', '2011-06-01')
    runStorvannetHammerfest('2011-11-01', '2012-06-01')
    runStorvannetHammerfest('2012-11-01', '2013-06-01')
    runStorvannetHammerfest('2013-11-01', '2014-06-01')
    runStorvannetHammerfest('2014-11-01', '2015-06-01')
    '''
    # cleanupp otrøvann
    # plott CC i plott
    # figurtext med hva som brukes og plottes
    # set environment fil som kmunve har i senorge koden sin
