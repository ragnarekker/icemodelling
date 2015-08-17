__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-


import copy
import datetime as dt

import doicethickness as dit
import doparameterization as dp
import doenergybalance as deb

import ice as ice
import weather as we

import getRegObsdata as gro
import getFiledata as gfd
import getWSklima as gws
import getChartserverdata as gcsd

import makePlots as pts

import constants as const
from setEnvironment import data_path, plot_folder


def calculateIceCoverSimple(inn_column, date, temp, sno, cloudcover=None):

    icecover = []
    timestep = 60*60*24     # fixed timestep of 24hrs given in seconds
    icecover.append(copy.deepcopy(inn_column))

    for i in range(0, len(date), 1):
        if date[i] < inn_column.date:
            i = i + 1
        else:
            if cloudcover != None:
                out_column = dit.get_ice_thickness_from_conductivity(inn_column, timestep, sno[i], temp[i], cloudcover[i])
            else:
                out_column = dit.get_ice_thickness_from_conductivity(inn_column, timestep, sno[i], temp[i])
            icecover.append(out_column)
            inn_column = copy.deepcopy(out_column)

    return icecover

def calculateIceCoverEB(utm33_x, utm33_y, inn_column, date, temp_atm, prec, prec_snow, cloud_cover):

    icecover = []
    time_span_in_sec = 60*60*24     # fixed timestep of 24hrs given in seconds
    icecover.append(copy.deepcopy(inn_column))
    energy_balance = []

    age_factor_tau = 0.
    albedo_prim = const.alfa_black_ice

    for i in range(0, len(date), 1):

        out_column = dit.get_ice_thickness_from_conductivity(inn_column, time_span_in_sec,
                                                             prec_snow[i], temp_atm[i], cloud_cover[i])
        eb = deb.get_energy_balance_from_senorge(utm33_x, utm33_y, inn_column,
                            temp_atm[i], prec[i], prec_snow[i], age_factor_tau, albedo_prim,
                            time_span_in_sec, cloud_cover=cloud_cover[i])

        icecover.append(out_column)
        energy_balance.append(eb)
        inn_column = copy.deepcopy(out_column)

        age_factor_tau = eb.age_factor_tau
        albedo_prim = eb.albedo_prim



    return icecover, energy_balance


def runOrovannNVE(startDate, endDate):

    # Need datetime objects from now on
    LocationName = 'Otrøvatnet v/Nystuen 971 moh'
    startDate = dt.datetime.strptime(startDate, "%Y-%m-%d")
    endDate = dt.datetime.strptime(endDate, "%Y-%m-%d")

    weather_data_filename = '{0}kyrkjestoelane_vaerdata.csv'.format(data_path)
    date, temp, sno, snotot = gfd.read_weather(startDate, endDate, weather_data_filename)

    #observed_ice_filename = '{0}Otroevann observasjoner 2011-2012.csv'.format(data_path)
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = gro.get_all_season_ice(LocationName, startDate, endDate)

    icecover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno)

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

    sno = dp.delta_snow_from_total_snow(snotot)

    #observed_ice_filename = '{0}Otroevann observasjoner {1}-{2}.csv'.format(data_path, startDate.year, endDate.year)
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = gro.get_all_season_ice(location_name, startDate, endDate)

    if len(observed_ice) == 0:
        icecover = calculateIceCoverSimple(ice.IceColumn(date[0], []), date, temp, sno)
    else:
        icecover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno)

    # Need datetime objects from now on
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    plot_filename = '{0}Ortovann MET {1}-{2}.png'.format(plot_folder, from_date.year, to_date.year)
    pts.plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)


def runOrovannEB(startDate, endDate):

    location_name = 'Otrøvatnet v/Nystuen 971 moh'
    wsTemp = gws.getMetData(54710, 'TAM', startDate, endDate, 0, 'list')
    wsSno  = gws.getMetData(54710, 'SA',  startDate, endDate, 0, 'list')
    wsPrec = gws.getMetData(54710, 'RR',  startDate, endDate, 0, 'list')

    utm33_y = 6802070
    utm33_x = 130513

    temp, date = we.strip_metadata(wsTemp, get_dates=True)
    sno_tot = we.strip_metadata(wsSno)
    prec_snow = dp.delta_snow_from_total_snow(sno_tot)
    prec = we.strip_metadata(wsPrec)
    cloud_cover = dp.clouds_average_from_precipitation(prec)

    # available_elements = gws.getElementsFromTimeserieTypeStation(54710, 0, 'csv')
    observed_ice = gro.get_all_season_ice(location_name, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover, energy_balance = calculateIceCoverEB(utm33_x, utm33_y, ice.IceColumn(date[0], []), date, temp,
                                        prec, prec_snow, cloud_cover)
    else:
        ice_cover, energy_balance = calculateIceCoverEB(utm33_x, utm33_y, copy.deepcopy(observed_ice[0]), date, temp,
                                        prec, prec_snow, cloud_cover)

    # Need datetime objects from now on
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    plot_filename = '{0}Ortovann MET {1}-{2}.png'.format(plot_folder, from_date.year, to_date.year)
    pts.plotIcecover(ice_cover, observed_ice, date, temp, sno_tot, plot_filename)


def runSemsvann(startDate, endDate):

    LocationName = 'Semsvannet v/Lo 145 moh'

    wsTemp = gws.getMetData(19710, 'TAM', startDate, endDate, 0, 'list')
    wsSno = gws.getMetData(19710, 'SA', startDate, endDate, 0, 'list')
    wsCC = gws.getMetData(18700, 'NNM', startDate, endDate, 0 , 'list')

    temp, date = we.strip_metadata(wsTemp, True)
    snotot = we.strip_metadata(wsSno, False)
    cc = we.strip_metadata(wsCC, False)

    sno = dp.delta_snow_from_total_snow(snotot)

    #observed_ice_filename = '{0}Semsvann observasjoner {1}-{2}.csv'.format(data_path, startDate[0:4], endDate[0:4])
    #observed_ice = importColumns(observed_ice_filename)
    observed_ice = gro.get_all_season_ice(LocationName, startDate, endDate)
    if len(observed_ice) == 0:
        icecover = calculateIceCoverSimple(ice.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        icecover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Semsvann {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(icecover, observed_ice, date, temp, snotot, plot_filename)


def runHakkloa(startDate, endDate):

    LocationName = 'Hakkloa nord 372 moh'
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    cs_temp = we.make_daily_average(gcsd.getStationdata('6.24.4','17.1', from_date, to_date, 'list'))
    cs_sno = we.make_daily_average(gcsd.getGriddata(260150, 6671135, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.make_daily_average(gcsd.getGriddata(260150, 6671135, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(18700, 'NNM', startDate, endDate, 0, 'list')

    temp, date = we.strip_metadata(cs_temp, True)
    sno = we.strip_metadata(cs_sno, False)
    snotot = we.strip_metadata(cs_snotot, False)
    cc = we.strip_metadata(wsCC, False)

    observed_ice = gro.get_all_season_ice(LocationName, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCoverSimple(ice.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Hakkloa {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runSkoddebergvatnet(startDate, endDate):

    LocationName = 'Skoddebergvatnet - nord 101 moh'
    # Skoddebergvatnet - sør 101 moh
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    #cs_temp = make_daily_average(gcsd.getStationdata('189.3.0','17.1', from_date, to_date, 'list'))
    cs_temp = we.make_daily_average(gcsd.getGriddata(593273, 7612469, 'tm', from_date, to_date, 'list'))
    cs_sno = we.make_daily_average(gcsd.getGriddata(593273, 7612469, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.make_daily_average(gcsd.getGriddata(593273, 7612469, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(87640, 'NNM', startDate, endDate, 0, 'list')  # Harstad Stadion

    temp, date = we.strip_metadata(cs_temp, True)
    sno = we.strip_metadata(cs_sno, False)
    snotot = we.strip_metadata(cs_snotot, False)
    cc = we.strip_metadata(wsCC, False)

    observed_ice = gro.get_all_season_ice(LocationName, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCoverSimple(ice.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Skoddebergvatnet {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runGiljastolsvatnet(startDate, endDate):

    LocationNames = ['Giljastølsvatnet 412 moh', 'Giljastølvatnet sør 412 moh']
    x = -1904
    y = 6553573

    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    #cs_temp = make_daily_average(gcsd.getStationdata('189.3.0','17.1', from_date, to_date, 'list'))
    cs_temp = we.make_daily_average(gcsd.getGriddata(x, y, 'tm', from_date, to_date, 'list'))
    cs_sno = we.make_daily_average(gcsd.getGriddata(x, y, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.make_daily_average(gcsd.getGriddata(x, y, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(43010, 'NNM', startDate, endDate, 0, 'list')  # Eik - Hove. Ligger lenger sør men er litt inn i landet.
    #wsCC = getMetData(43010, 'NNM', startDate, endDate, 0, 'list') # Sola (44560) er et alternativ

    temp, date = we.strip_metadata(cs_temp, True)
    sno = we.strip_metadata(cs_sno, False)
    snotot = we.strip_metadata(cs_snotot, False)
    cc = we.strip_metadata(wsCC, False)

    observed_ice = gro.get_all_season_ice(LocationNames, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCoverSimple(ice.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Giljastolsvatnet {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runBaklidammen(startDate, endDate):

    LocationNames = ['Baklidammen 200 moh']
    x = 266550
    y = 7040812

    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    cs_temp = we.make_daily_average(gcsd.getGriddata(x, y, 'tm', from_date, to_date, 'list'))
    cs_sno = we.make_daily_average(gcsd.getGriddata(x, y, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.make_daily_average(gcsd.getGriddata(x, y, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(68860, 'NNM', startDate, endDate, 0, 'list')  # TRONDHEIM - VOLL

    temp, date = we.strip_metadata(cs_temp, True)
    sno = we.strip_metadata(cs_sno, False)
    snotot = we.strip_metadata(cs_snotot, False)
    cc = we.strip_metadata(wsCC, False)

    observed_ice = gro.get_all_season_ice(LocationNames, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCoverSimple(ice.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}Baklidammen {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


def runStorvannetHammerfest(startDate, endDate):

    LocationNames = ['Storvannet, 7 moh']
    x = 821340
    y = 7862497

    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    cs_temp = we.make_daily_average(gcsd.getGriddata(x, y, 'tm', from_date, to_date, 'list'))
    cs_sno = we.make_daily_average(gcsd.getGriddata(x, y, 'fsw', from_date, to_date, 'list'))
    cs_snotot = we.make_daily_average(gcsd.getGriddata(x, y, 'sd', from_date, to_date, 'list'))
    wsCC = gws.getMetData(95350, 'NNM', startDate, endDate, 0, 'list')  # BANAK - østover innerst i fjorden

    temp, date = we.strip_metadata(cs_temp, True)
    sno = we.strip_metadata(cs_sno, False)
    snotot = we.strip_metadata(cs_snotot, False)
    cc = we.strip_metadata(wsCC, False)

    observed_ice = gro.get_all_season_ice(LocationNames, startDate, endDate)

    if len(observed_ice) == 0:
        ice_cover = calculateIceCoverSimple(ice.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        ice_cover = calculateIceCoverSimple(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    plot_filename = '{0}StorvannetHammerfest {1}-{2}.png'.format(plot_folder, startDate[0:4], endDate[0:4])
    pts.plotIcecover(ice_cover, observed_ice, date, temp, snotot, plot_filename)


if __name__ == "__main__":

    #runOrovannEB('2014-11-15', '2015-06-20')

    #runSemsvann('2011-11-01', '2012-05-01')
    #runSemsvann('2012-11-01', '2013-06-01')
    #runSemsvann('2013-11-01', '2014-04-15')
    #runSemsvann('2014-11-01', '2015-05-15')

    #runOrovannNVE('2011-11-15', '2012-06-20')
    #runOrovannMET('2011-11-15', '2012-06-20')
    #runOrovannMET('2012-11-15', '2013-06-20')
    #runOrovannMET('2013-11-15', '2014-06-20')
    #runOrovannMET('2014-11-15', '2015-06-20')

    runHakkloa('2011-11-01', '2012-06-01')
    runHakkloa('2012-11-01', '2013-06-01')
    runHakkloa('2013-11-01', '2014-06-01')
    runHakkloa('2014-11-01', '2015-06-01')

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

