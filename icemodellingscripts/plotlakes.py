# -*- coding: utf-8 -*-
"""

"""
import os
import copy
import json
from ftplib import FTP
import datetime as dt
from icemodelling import constants as const, weatherelement as we, icethickness as it
from icemodelling import parameterization as dp
from icemodelling import ice as ice
import setenvironment as se
from utilities import getregobsdata as gro, getwsklima as gws, makeplots as pts
from utilities import getgts as gts

__author__ = 'ragnarekker'


def run_otrovann_eb(startDate, endDate):

    location_name = 'Otrøvatnet v/Nystuen 971 moh'
    wsTemp = gws.getMetData(54710, 'TAM', startDate, endDate, 0, 'list')
    wsSno  = gws.getMetData(54710, 'SA',  startDate, endDate, 0, 'list')
    wsPrec = gws.getMetData(54710, 'RR',  startDate, endDate, 0, 'list')

    utm33_y = 6802070
    utm33_x = 130513

    temp, date = we.strip_metadata(wsTemp, get_date_times=True)
    sno_tot = we.strip_metadata(wsSno)
    prec_snow = dp.delta_snow_from_total_snow(sno_tot)
    prec = we.strip_metadata(wsPrec)
    cloud_cover = dp.clouds_from_precipitation(prec)
    wind = [const.avg_wind_const] * len(date)
    rel_hum = [const.rel_hum_air] * len(date)
    pressure_atm = [const.pressure_atm] * len(date)


    # available_elements = gws.getElementsFromTimeserieTypeStation(54710, 0, 'csv')
    observed_ice = gro.get_all_season_ice_on_location(location_name, startDate, endDate)

    ice_cover, energy_balance = it.calculate_ice_cover_eb(
        utm33_x, utm33_y, date, temp, prec, prec_snow, cloud_cover, wind, rel_hum=rel_hum, pressure_atm=pressure_atm,
        inn_column=copy.deepcopy(observed_ice[0]))

    # Need datetime objects from now on
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    plot_filename = '{0}Ortovann MET EB {1}-{2}.png'.format(se.plot_folder, from_date.year, to_date.year)
    # pts.plot_ice_cover(ice_cover, observed_ice, date, temp, sno_tot, plot_filename)
    plot_filename = '{0}Ortovann MET with EB {1}-{2}.png'.format(se.plot_folder, from_date.year, to_date.year)
    pts.plot_ice_cover_eb(ice_cover, energy_balance, observed_ice, date, temp, sno_tot, plot_filename,
                       prec=prec, wind=wind, clouds=cloud_cover)


def run_semsvann_eb(startDate, endDate):
    # TODO: get coordinates from the ObsLocation in regObs
    location_name = 'Semsvannet v/Lo 145 moh'

    wsTemp = gws.getMetData(19710, 'TAM', startDate, endDate, 0, 'list')
    wsSno = gws.getMetData(19710, 'SA', startDate, endDate, 0, 'list')
    wsPrec = gws.getMetData(19710, 'RR', startDate, endDate, 0, 'list')
    wsWind = gws.getMetData(18700, 'FFM', startDate, endDate, 0, 'list')
    wsCC = gws.getMetData(18700, 'NNM', startDate, endDate, 0, 'list')

    utm33_y = 6644410
    utm33_x = 243940

    temp, date = we.strip_metadata(wsTemp, get_date_times=True)
    sno_tot = we.strip_metadata(wsSno)
    prec_snow = dp.delta_snow_from_total_snow(sno_tot)
    prec = we.strip_metadata(wsPrec)
    wind = we.strip_metadata(wsWind)
    cloud_cover = we.strip_metadata(wsCC)
    rel_hum = [const.rel_hum_air] * len(date)
    pressure_atm = [const.pressure_atm] * len(date)

    observed_ice = gro.get_all_season_ice_on_location(location_name, startDate, endDate)

    ice_cover, energy_balance = it.calculate_ice_cover_eb(
        utm33_x, utm33_y, date,
        temp, prec, prec_snow, cloud_cover=cloud_cover, wind=wind, rel_hum=rel_hum, pressure_atm=pressure_atm,
        inn_column=copy.deepcopy(observed_ice[0]))

    # Need datetime objects from now on
    from_date = dt.datetime.strptime(startDate, "%Y-%m-%d")
    to_date = dt.datetime.strptime(endDate, "%Y-%m-%d")

    plot_filename = '{0}Semsvann EB {1}-{2}.png'.format(se.plot_folder, from_date.year, to_date.year)
    # pts.plot_ice_cover(ice_cover, observed_ice, date, temp, sno_tot, plot_filename)
    plot_filename = '{0}Semsvann MET with EB {1}-{2}.png'.format(se.plot_folder, from_date.year, to_date.year)
    pts.plot_ice_cover_eb(ice_cover, energy_balance, observed_ice, date, temp, sno_tot, plot_filename, prec=prec, wind=wind, clouds=cloud_cover)
    #plot_filename = '{0}Semsvann MET with EB simple {1}-{2}.png'.format(plot_folder, from_date.year, to_date.year)
    #pts.plot_ice_cover_eb_simple(ice_cover, energy_balance, observed_ice, date, temp, sno_tot, plot_filename)


def run_semsvann(from_date, to_date, make_plots=True, plot_folder=se.plot_folder, forcing='grid'):
    """

    :param from_date:
    :param to_date:
    :param make_plots:
    :param plot_folder:
    :return:
    """

    location_name = 'Semsvann'
    regobs_location_id = 2227

    x = 243655
    y = 6644286
    altitude = 145

    met_stnr = 19710        # Asker (Sem)
    met_stnr_NNM = 18700    # Blindern

    year = '{0}-{1}'.format(from_date[0:4], to_date[2:4])

    observed_ice = gro.get_observations_on_location_id(regobs_location_id, year)
    first_ice = observed_ice[0]

    # Change dates to datetime. Some of the getdata modules require datetime
    from_date = dt.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = dt.datetime.strptime(to_date, '%Y-%m-%d')

    # if to_date forward in time, make sure it doesnt go to far..
    if to_date > dt.datetime.now():
        to_date = dt.datetime.now() + dt.timedelta(days=7)

    if forcing == 'eKlima':

        wsTemp = gws.getMetData(met_stnr, 'TAM', from_date, to_date, 0, 'list')
        wsSnoTot = gws.getMetData(met_stnr, 'SA', from_date, to_date, 0, 'list')
        wsCC = gws.getMetData(met_stnr_NNM, 'NNM', from_date, to_date, 0, 'list')

        temp, date = we.strip_metadata(wsTemp, get_date_times=True)
        sno_tot = we.strip_metadata(wsSnoTot)
        sno = dp.delta_snow_from_total_snow(sno_tot)
        cc = we.strip_metadata(wsCC)

        plot_filename = '{0}_{1}_eklima.png'.format(location_name, year)

    elif forcing == 'grid':

        gridTemp = gts.getgts(x, y, 'tm', from_date, to_date)
        gridSno = gts.getgts(x, y, 'sdfsw', from_date, to_date)
        gridSnoTot = gts.getgts(x, y, 'sd', from_date, to_date)

        # Grid altitude and lake at same elevations.
        gridTempNewElevation = we.adjust_temperature_to_new_altitude(gridTemp, altitude)

        temp, date = we.strip_metadata(gridTempNewElevation, get_date_times=True)
        sno = we.strip_metadata(gridSno)
        sno_tot = we.strip_metadata(gridSnoTot)
        cc = dp.clouds_from_precipitation(sno)

        plot_filename = '{0}_{1}_grid.png'.format(location_name, year)

    else:
        temp, date = None, None
        sno = None
        sno_tot = None
        cc = None

        plot_filename = '{0}_{1}_no_forcing.png'.format(location_name, year)

    calculated_ice = it.calculate_ice_cover_air_temp(copy.deepcopy(first_ice), date, temp, sno, cloud_cover=cc)

    if make_plots:
        plot_path_and_filename = '{0}{1}'.format(plot_folder, plot_filename)
        pts.plot_ice_cover(calculated_ice, observed_ice, date, temp, sno, sno_tot, plot_path_and_filename)


def run_mosselva(from_date, to_date, make_plots=True, plot_folder=se.plot_folder, forcing='grid'):
    """

    :param from_date:
    :param to_date:
    :param make_plots:
    :param plot_folder:
    :return:
    """

    location_name = 'Mosselva'
    y = 6595744
    x = 255853
    altitude = 25

    met_stnr = 17150    # Rygge målestasjon (met.no)

    first_ice = ice.IceColumn(dt.datetime(int(from_date[0:4]), 12, 31), [])
    first_ice.add_metadata('LocationName', location_name)       # used when plotting
    observed_ice = [first_ice]

    year = '{0}-{1}'.format(from_date[0:4], to_date[2:4])

    # Change dates to datetime. Some of the getdata modules require datetime
    from_date = dt.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = dt.datetime.strptime(to_date, '%Y-%m-%d')

    # if to_date forward in time, make sure it doesnt go to far..
    if to_date > dt.datetime.now():
        to_date = dt.datetime.now() + dt.timedelta(days=7)

    if forcing == 'eKlima':

        wsTemp = gws.getMetData(met_stnr, 'TAM', from_date, to_date, 0, 'list')
        gridSno = gts.getgts(x, y, 'sdfsw', from_date, to_date)
        gridSnoTot = gts.getgts(x, y, 'sd', from_date, to_date)

        temp, date = we.strip_metadata(wsTemp, get_date_times=True)
        sno = we.strip_metadata(gridSno)
        sno_tot = we.strip_metadata(gridSnoTot)
        cc = dp.clouds_from_precipitation(sno)

        plot_filename = '{0}_{1}_eklima.png'.format(location_name, year)

    elif forcing == 'grid':

        gridTemp = gts.getgts(x, y, 'tm', from_date, to_date)
        gridSno = gts.getgts(x, y, 'sdfsw', from_date, to_date)
        gridSnoTot = gts.getgts(x, y, 'sd', from_date, to_date)

        gridTempNewElevation = we.adjust_temperature_to_new_altitude(gridTemp, altitude)

        temp, date = we.strip_metadata(gridTempNewElevation, get_date_times=True)
        sno = we.strip_metadata(gridSno)
        sno_tot = we.strip_metadata(gridSnoTot)
        cc = dp.clouds_from_precipitation(sno)

        plot_filename = '{0}_{1}_grid.png'.format(location_name, year)

    else:
        temp, date = None, None
        sno = None
        sno_tot = None
        cc = None

        plot_filename = '{0}_{1}_no_forcing.png'.format(location_name, year)

    calculated_ice = it.calculate_ice_cover_air_temp(copy.deepcopy(first_ice), date, temp, sno, cloud_cover=cc)

    if make_plots:
        plot_path_and_filename = '{0}{1}'.format(plot_folder, plot_filename)
        pts.plot_ice_cover(calculated_ice, observed_ice, date, temp, sno, sno_tot, plot_path_and_filename)


if __name__ == "__main__":

    #run_semsvann('2017-11-01', '2018-06-01')
    #run_semsvann('2016-11-01', '2017-06-01')
    #run_semsvann('2015-11-01', '2016-06-01')
    #run_semsvann('2014-11-01', '2015-06-01')

    #run_semsvann('2017-11-01', '2018-06-01', forcing='eKlima')
    #run_semsvann('2016-11-01', '2017-06-01', forcing='eKlima')
    #run_semsvann('2015-11-01', '2016-06-01', forcing='eKlima')

    #run_mosselva('2017-11-01', '2018-06-01')
    #run_mosselva('2016-11-01', '2017-06-01')
    #run_mosselva('2015-11-01', '2016-06-01')

    #run_mosselva('2017-11-01', '2018-06-01', forcing='eKlima')
    #run_mosselva('2016-11-01', '2017-06-01', forcing='eKlima')
    #run_mosselva('2015-11-01', '2016-06-01', forcing='eKlima')

    # cap.calculate_and_plot_location('Semsvannet v/Lo 145 moh', '2016-10-01', '2017-07-01')

    pass
