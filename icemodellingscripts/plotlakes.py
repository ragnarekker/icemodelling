# -*- coding: utf-8 -*-
"""

"""
import copy
import datetime as dt
from icemodelling import constants as const, weatherelement as we
from icemodelling import parameterization as dp
from icemodelling import ice as ice
from icemodellingscripts import calculateandplot as cap
import setenvironment as se
from utilities import getregobsdata as gro, getwsklima as gws, makeplots as pts
from utilities import getgts as gts

__author__ = 'ragnarekker'


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
    cloud_cover = dp.clouds_from_precipitation(prec)
    wind = [const.avg_wind_const] * len(date)
    rel_hum = [const.rel_hum_air] * len(date)
    pressure_atm = [const.pressure_atm] * len(date)


    # available_elements = gws.getElementsFromTimeserieTypeStation(54710, 0, 'csv')
    observed_ice = gro.get_all_season_ice_on_location(location_name, startDate, endDate)

    ice_cover, energy_balance = cap.calculate_ice_cover_eb(
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


def runSemsvannEB(startDate, endDate):
    # TODO: get coordinates from the ObsLocation in regObs
    location_name = 'Semsvannet v/Lo 145 moh'

    wsTemp = gws.getMetData(19710, 'TAM', startDate, endDate, 0, 'list')
    wsSno = gws.getMetData(19710, 'SA', startDate, endDate, 0, 'list')
    wsPrec = gws.getMetData(19710, 'RR', startDate, endDate, 0, 'list')
    wsWind = gws.getMetData(18700, 'FFM', startDate, endDate, 0, 'list')
    wsCC = gws.getMetData(18700, 'NNM', startDate, endDate, 0, 'list')

    utm33_y = 6644410
    utm33_x = 243940

    temp, date = we.strip_metadata(wsTemp, get_dates=True)
    sno_tot = we.strip_metadata(wsSno)
    prec_snow = dp.delta_snow_from_total_snow(sno_tot)
    prec = we.strip_metadata(wsPrec)
    wind = we.strip_metadata(wsWind)
    cloud_cover = we.strip_metadata(wsCC)
    rel_hum = [const.rel_hum_air] * len(date)
    pressure_atm = [const.pressure_atm] * len(date)

    observed_ice = gro.get_all_season_ice_on_location(location_name, startDate, endDate)

    ice_cover, energy_balance = cap.calculate_ice_cover_eb(
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


def runMosselva(from_date, to_date, observed_ice=[], make_plots=True, plot_folder=se.plot_folder):

    year = '{0}-{1}'.format(from_date[0:4], to_date[2:4])

    # Change dates to datetime. Some of the getdata modules require datetime
    from_date = dt.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = dt.datetime.strptime(to_date, '%Y-%m-%d')

    # if to_date forward in time, make sure it doesnt go to far..
    if to_date > dt.datetime.now():
        to_date = dt.datetime.now() + dt.timedelta(days=7)

    location_name = 'Mosselva'
    y = 6595744
    x = 255853

    gridTemp = gts.getgts(x, y, 'tm', from_date, to_date)
    gridSno = gts.getgts(x, y, 'sdfsw', from_date, to_date)
    gridSnoTot = gts.getgts(x, y, 'sd', from_date, to_date)

    temp, date = we.strip_metadata(gridTemp, get_date_times=True)
    sno = we.strip_metadata(gridSno)
    sno_tot = we.strip_metadata(gridSnoTot)
    cc = dp.clouds_from_precipitation(sno)

    plot_filename = '{0}_{1}.png'.format(location_name, year)
    plot_path_and_filename = '{0}{1}'.format(plot_folder, plot_filename)

    # try:
    if len(observed_ice) == 0:
        calculated_ice = cap.calculate_ice_cover_air_temp(ice.IceColumn(date[0], []), date, temp, sno, cc)
    else:
        calculated_ice = cap.calculate_ice_cover_air_temp(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

    if make_plots:
        pts.plot_ice_cover(calculated_ice, observed_ice, date, temp, sno, sno_tot, plot_path_and_filename)

    # except:
    #    # raise
    #    error_msg = sys.exc_info()[0]
    #    ml.log_and_print('calculateandplot.py -> _plot_season: {}. Could not plot {}.'.format(error_msg, location_name))
    #    calculated_ice = None

    return calculated_ice, observed_ice, plot_filename


if __name__ == "__main__":

    location_name = 'Semsvannet v/Lo 145 moh'
    cap.calculate_and_plot_location(location_name, '2016-10-01', '2017-07-01')

    runMosselva('2017-12-31', '2018-07-01')
    runMosselva('2016-12-31', '2017-07-01')
    runMosselva('2015-12-31', '2016-07-01')

    cap.plot_season_location_id(17080, '2017-18', get_new_obs=False)
    cap.plot_season_location_id(57019, '2017-18', get_new_obs=False)
    cap.plot_season_location_id(2227, '2017-18', get_new_obs=False)
    cap.plot_season_location_id(7642, '2017-18', get_new_obs=False)

    pass
