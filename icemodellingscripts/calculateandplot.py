# -*- coding: utf-8 -*-
"""Module contains methods for handlig modelling and plotting.

General process procedure:
* gather data from regobs
* structure them as lists of IceThickness
* get weather data from somewhere
* calculate with icemodelling module
* plot data (optional)
"""

import sys as sys
import os as os
import json as json
import copy
import datetime as dt
from icemodelling import icethickness as dit, constants as const, weatherelement as we
from icemodelling import parameterization as dp
from icemodelling import ice as ice
import setenvironment as se
from utilities import fencoding as fe, makepickle as mp, makelogs as ml, makeplots as pts
from utilities import getregobsdata as gro, getwsklima as gws
from utilities import setlocationparameters as slp
from utilities import getgts as gts, getfiledata as gfd, getchartserverdata as gcsd

__author__ = 'ragnarekker'


def calculate_ice_cover_air_temp(inn_column_inn, date, temp, sno, cloud_cover=None):
    """

    :param inn_column_inn:
    :param date:    [] dates for plotting
    :param temp:
    :param sno:     []  new snow over the period (day)
    :param cloud_cover:
    :return:
    """

    inn_column = copy.deepcopy(inn_column_inn)
    inn_column.update_water_line()
    inn_column.remove_metadata()
    inn_column.remove_time()

    icecover = []
    timestep = 60*60*24     # fixed timestep of 24hrs given in seconds

    icecover.append(copy.deepcopy(inn_column))

    for i in range(0, len(date), 1):
        if date[i] < inn_column.date:
            i = i + 1
        else:
            if cloud_cover != None:
                out_column = dit.get_ice_thickness_from_surface_temp(inn_column, timestep, sno[i], temp[i], cloud_cover=cloud_cover[i])
            else:
                out_column = dit.get_ice_thickness_from_surface_temp(inn_column, timestep, sno[i], temp[i])
            icecover.append(out_column)
            inn_column = copy.deepcopy(out_column)

    return icecover


def calculate_ice_cover_eb(
        utm33_x, utm33_y, date, temp_atm, prec, prec_snow, cloud_cover, wind, rel_hum, pressure_atm, inn_column=None):
    """

    :param utm33_x:
    :param utm33_y:
    :param date:
    :param temp_atm:
    :param prec:
    :param prec_snow:
    :param cloud_cover:
    :param wind:
    :param inn_column:
    :return:
    """

    if inn_column is None:
        inn_column = ice.IceColumn(date[0], [])

    icecover = []
    time_span_in_sec = 60*60*24     # fixed timestep of 24hrs given in seconds
    inn_column.remove_metadata()
    inn_column.remove_time()
    icecover.append(copy.deepcopy(inn_column))
    energy_balance = []

    age_factor_tau = 0.
    albedo_prim = const.alfa_black_ice

    for i in range(0, len(date), 1):
        print("{0}".format(date[i]))
        if date[i] < inn_column.date:
            i = i + 1
        else:
            out_column, eb = dit.get_ice_thickness_from_energy_balance(
                utm33_x=utm33_x, utm33_y=utm33_y, ice_column=inn_column, temp_atm=temp_atm[i],
                prec=prec[i], prec_snow=prec_snow[i], time_span_in_sec=time_span_in_sec,
                albedo_prim=albedo_prim, age_factor_tau=age_factor_tau, wind=wind[i], cloud_cover=cloud_cover[i],
                rel_hum=rel_hum[i], pressure_atm=pressure_atm[i])

            icecover.append(out_column)
            energy_balance.append(eb)
            inn_column = copy.deepcopy(out_column)

            if eb.EB is None:
                age_factor_tau = 0.
                albedo_prim = const.alfa_black_ice
            else:
                age_factor_tau = eb.age_factor_tau
                albedo_prim = eb.albedo_prim

    return icecover, energy_balance


def calculate_and_plot_location(location_name, from_date, to_date, sub_plot_folder='', make_plots=True, return_values=False):
    """ due to get_all_season_ice returns data grouped be location_id
    For a given LocationName in regObs calculate the ice cover between two dates. Optional, make plots
    and/or return the calculations and observations for this location. Different sources for weather data
    may be given, chartserver grid is default.

    :param location_name:
    :param from_date:               [String] 'yyyy-mm-dd'
    :param to_date:                 [String] 'yyyy-mm-dd'
    :param sub_plot_folder:
    :param make_plots:
    :param return_values:           [bool]  If true the calculated and observed data is returned
    """

    loc = slp.get_for_location(location_name)
    year = '{0}-{1}'.format(from_date[0:4], to_date[2:4])
    lake_file_name = '{0} {1}'.format(fe.make_standard_file_name(loc.file_name), year)
    observed_ice = gro.get_observations_on_location(loc.regobs_location_id, year)

    # Change dates to datetime. Some of the getdata modules require datetime
    from_date = dt.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = dt.datetime.strptime(to_date, '%Y-%m-%d')

    # special rule for this season.
    if year == '2018-19':
        from_date = dt.datetime(2017, 10, 15)

    # if to_date forward in time, make sure it doesnt go to far..
    if to_date > dt.datetime.now():
        to_date = dt.datetime.now() + dt.timedelta(days=7)

    if loc.weather_data_source == 'eKlima':
        wsTemp = gws.getMetData(loc.eklima_TAM, 'TAM', from_date, to_date, 0, 'list')
        temp, date = we.strip_metadata(wsTemp, True)

        wsSno = gws.getMetData(loc.eklima_SA, 'SA', from_date, to_date, 0, 'list')
        snotot = we.strip_metadata(wsSno)
        sno = dp.delta_snow_from_total_snow(snotot)

        # Clouds. If not from met.no it is parametrised from precipitation.
        if loc.eklima_NNM:
            wsCC = gws.getMetData(loc.eklima_NNM, 'NNM', from_date, to_date, 0, 'list')
            cc = we.strip_metadata(wsCC)
        else:
            cc = dp.clouds_from_precipitation(sno)

        plot_filename = '{0}{1} eklima.png'.format(se.plot_folder + sub_plot_folder, lake_file_name)

    elif loc.weather_data_source == 'chartserver grid':
        x, y = loc.utm_east, loc.utm_north

        gridTemp = gcsd.getGriddata(x, y, 'tm', from_date, to_date)
        gridSno = gcsd.getGriddata(x, y, 'fsw', from_date, to_date)
        gridSnoTot = gcsd.getGriddata(x, y, 'sd', from_date, to_date)

        gridTemp = we.patch_weather_element_list(gridTemp, from_date, to_date)
        gridSno = we.patch_weather_element_list(gridSno, from_date, to_date)
        gridSnoTot = we.patch_weather_element_list(gridSnoTot, from_date, to_date)

        temp, date = we.strip_metadata(gridTemp, get_dates=True)
        sno = we.strip_metadata(gridSno, False)
        snotot = we.strip_metadata(gridSnoTot, False)

        if loc.eklima_NNM:
            wsCC = gws.getMetData(loc.eklima_NNM, 'NNM', from_date, to_date, 0, 'list')
            cc = we.strip_metadata(wsCC)
        else:
            cc = dp.clouds_from_precipitation(sno)

        plot_filename = '{0}{1} grid.png'.format(se.plot_folder + sub_plot_folder, lake_file_name)

    elif loc.weather_data_source == 'nve':
        x, y = loc.utm_east, loc.utm_north

        # Temp from NVE station or grid if not.
        if loc.nve_temp:
            temp_obj = gcsd.getStationdata(loc.nve_temp, '17.1', from_date, to_date, timeseries_type=0)
        else:
            temp_obj = gcsd.getGriddata(x, y, 'tm', from_date, to_date)
        temp, date = we.strip_metadata(temp_obj, get_dates=True)

        # Snow from NVE station or grid if not.
        if loc.nve_snow:
            snotot_obj = gcsd.getStationdata(loc.nve_snow, '2002.1', from_date, to_date, timeseries_type=0)
            snotot = we.strip_metadata(snotot_obj)
            sno = dp.delta_snow_from_total_snow(snotot_obj)
        else:
            snotot_obj = gcsd.getGriddata(x, y, 'sd', from_date, to_date, timeseries_type=0)
            sno_obj = gcsd.getGriddata(x, y, 'fsw', from_date, to_date, timeseries_type=0)
            snotot = we.strip_metadata(snotot_obj)
            sno = we.strip_metadata(sno_obj)

        # Clouds. If not from met.no it is parametrised from precipitation.
        if loc.eklima_NNM:
            cc_obj = gws.getMetData(18700, 'NNM', from_date, to_date, 0, 'list')
        else:
            cc_obj = dp.clouds_from_precipitation(sno)
        cc = we.strip_metadata(cc_obj)

        plot_filename = '{0}{1} nve.png'.format(se.plot_folder + sub_plot_folder, lake_file_name)

    elif loc.weather_data_source == 'file':
        date, temp, sno, snotot = gfd.read_weather(from_date, to_date, loc.input_file)
        cc = dp.clouds_from_precipitation(sno)

        plot_filename = '{0}{1} file.png'.format(se.plot_folder + sub_plot_folder, lake_file_name)

    else:
        ml.log_and_print("runicethickness -> calculate_and_plot_location: Invalid scource for weather data.")
        return

    try:
        if len(observed_ice) == 0:
            calculated_ice = calculate_ice_cover_air_temp(ice.IceColumn(date[0], []), date, temp, sno, cc)
        else:
            calculated_ice = calculate_ice_cover_air_temp(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

        if make_plots:
            pts.plot_ice_cover(calculated_ice, observed_ice, date, temp, sno, snotot, plot_filename)

    except:
        error_msg = sys.exc_info()[0]
        ml.log_and_print("calculateandplot.py -> calculate_and_plot_location: {}. Could not plot {}.".format(error_msg, location_name))
        calculated_ice = None

    if return_values:
        return calculated_ice, observed_ice


def plot_season_location_id(location_id, year, get_new_obs=True):
    """For a given location_id get all observations, calculate cover and plot for full season.

    Observed ice is retrieved from get_all_season_ice. Thus, all season ice for all location ids is requested
    even though only one location id is requested. Weather data from GTS.

    :param location_id:
    :param year:
    :param get_new_obs:
    :return:
    """

    all_observations = gro.get_all_season_ice(year, get_new=get_new_obs)
    observed_ice = all_observations[location_id]

    from_date, to_date = gro.get_dates_from_year(year)
    _plot_season(location_id, from_date, to_date, observed_ice, make_plots=True)


def _plot_season(location_id, from_date, to_date, observed_ice, make_plots=True, plot_folder=se.plot_folder):
    """Given a location id, a time period and some observations on this location id and this method
    calculates and optionally plots the ice evolution that season. Weather data from GTS.

    It is a sub method of plot_season_location_id and plot_season_regobs_observations.

    :param location_id:
    :param from_date:
    :param to_date:
    :param observed_ice:
    :param make_plots:
    :param plot_folder:     [string]        Path of folder for plots.

    :return calculated_ice, observed_ice:   [list of Ice.IceColumn] observed_ice is returned as given inn.

    TODO: should accept observerd_ice=None and then query for the observations. If still missing, set icecover on to start date.
    """

    year = '{0}-{1}'.format(from_date[0:4], to_date[2:4])

    # Change dates to datetime. Some of the get data modules require datetime
    from_date = dt.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = dt.datetime.strptime(to_date, '%Y-%m-%d')

    # special rule for this season.
    if year == '2018-19':
        from_date = dt.datetime(2018, 10, 15)

    # if to_date forward in time, make sure it doesnt go to far..
    if to_date > dt.datetime.now():
        to_date = dt.datetime.now() + dt.timedelta(days=7)

    x, y = observed_ice[0].metadata['UTMEast'], observed_ice[0].metadata['UTMNorth']

    # get weather data
    gridTemp = gts.getgts(x, y, 'tm', from_date, to_date)
    gridSno = gts.getgts(x, y, 'sdfsw', from_date, to_date)
    gridSnoTot = gts.getgts(x, y, 'sd', from_date, to_date)

    # strip metadata
    temp, date = we.strip_metadata(gridTemp, get_date_times=True)
    sno = we.strip_metadata(gridSno, False)
    snotot = we.strip_metadata(gridSnoTot, False)
    cc = dp.clouds_from_precipitation(sno)

    plot_filename = '{0}_{1}.png'.format(location_id, year)
    plot_path_and_filename = '{0}{1}'.format(plot_folder, plot_filename)

    try:
        if len(observed_ice) == 0:
            calculated_ice = calculate_ice_cover_air_temp(ice.IceColumn(date[0], []), date, temp, sno, cc)
        else:
            calculated_ice = calculate_ice_cover_air_temp(copy.deepcopy(observed_ice[0]), date, temp, sno, cc)

        if make_plots:
            pts.plot_ice_cover(calculated_ice, observed_ice, date, temp, sno, snotot, plot_path_and_filename)

    except:
        # raise
        error_msg = sys.exc_info()[0]
        ml.log_and_print("calculateandplot.py -> _plot_season: {}. Could not plot {}.".format(error_msg, location_id))
        calculated_ice = None

    return calculated_ice, observed_ice, plot_filename


def plot_season_regobs_observations(year='2018-19', calculate_new=False, get_new_obs=False, make_plots=False, delete_old_plots=False):
    """Method specialized for scheduled plotting for iskart.no.
    Method makes a season plot for all ObsLocations in regObs where we have a first ice date.

    It may take 3hrs to plot one full season. 250 lakes for a season and 1000 observations for 9 days.
    For each plot weather params are requested from the GTS.

    The workings of the method:
    1.  get all locations ids and belonging observations where we have first ice.
    2.1 if calculate new, empty sesong folder and pickle in local storage and calculate (and make plots if requested).
    2.2 Make metadata json for showing files on iskart.no
    3.  All calculations are compared to observed data in scatter plot.

    :param year:                [String] Season for plotting. eg: '2016-17'
    :param calculate_new:       [bool] Calculate new ice thicks. If false only make the seasonal scatter.
    :param get_new_obs:         [bool]
    :param make_plots:          [bool]  If False all calculations are made, but only the scatter comparison against observatiosn is ploted
    :param delete_old_plots:    [bool]  If True all former plots and pickles are removed.
    """

    pickle_file_name_and_path = '{0}all_calculated_ice_{1}.pickle'.format(se.local_storage, year)
    location_id_metadata_json = '{}location_id_metadata.json'.format(se.sesong_plots_folder)

    if calculate_new:
        if delete_old_plots:
            # Empty the sesong plot folder
            for file in os.listdir(se.sesong_plots_folder):
                file_path = os.path.join(se.sesong_plots_folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except OSError:
                    pass

            # remove pickle old data - because we are getting new
            try:
                os.remove(pickle_file_name_and_path)
            except OSError:
                pass

        all_observations = gro.get_all_season_ice(year, get_new=get_new_obs)
        from_date, to_date = gro.get_dates_from_year(year)
        all_calculated = {}
        all_observed = {}
        location_id_metadata = {}

        for location_id, observed_ice in all_observations.items():
            try:
                calculated, observed, plot_filename = _plot_season(
                    location_id, from_date, to_date, observed_ice, make_plots=make_plots, plot_folder=se.sesong_plots_folder)
                all_calculated[location_id] = calculated
                all_observed[location_id] = observed
            except:
                error_msg = sys.exc_info()[0]
                ml.log_and_print("calculateandplot.py -> plot_season_regobs_observations: Error making plot for {}".format(error_msg, location_id))

            # Make the json with metadata needed for iskart.no. Add only if the plot was made and thus file exists.
            if os.path.isfile(se.sesong_plots_folder + plot_filename):

                region_name = observed_ice[0].metadata['OriginalObject']['ForecastRegionName']
                if not region_name:
                    region_name = 'Ukjent region'
                lake_id = observed_ice[0].metadata['LocationID']
                x, y = observed_ice[0].metadata['UTMEast'], observed_ice[0].metadata['UTMNorth']
                lake_name = observed_ice[0].metadata['LocationName']
                if not lake_name:
                    lake_name = 'E{} N{}'.format(x, y)

                location_id_metadata[location_id] = {'RegionName': region_name,
                                                     'LakeID': lake_id,
                                                     'LakeName': lake_name,
                                                     'PlotFileName': plot_filename}

        mp.pickle_anything([all_calculated, all_observed], pickle_file_name_and_path)

        try:
            json_string = json.dumps(location_id_metadata, ensure_ascii=False).encode('utf-8')
            with open(location_id_metadata_json, 'wb') as f:
                f.write(json_string)
        except:
            error_msg = sys.exc_info()[0]
            ml.log_and_print("calculateandplot.py -> plot_season_regobs_observations: Cant write json. {}".format(error_msg))

    else:
        [all_calculated, all_observed] = mp.unpickle_anything(pickle_file_name_and_path)

    try:
        pts.scatter_calculated_vs_observed(all_calculated, all_observed, year)
    except:
        error_msg = sys.exc_info()[0]
        ml.log_and_print("calculateandplot.py -> plot_season_regobs_observations: {}. Could not plot scatter {}.".format(error_msg, year))


def calculate_and_plot9d_regid(regid, plot_folder=se.plot_folder, observed_ice=None):
    """For an ice thickness on a given regObs RegID, a plot of will be made of the following 9 days development.
    If observed_ice is not given, it is looked up on regObs api by using its RegID. If observation is older
    than 11 days, no plot is made. Weather data is from GTS.

    1.1 If observed ice is none, get some on this regid
    1.2 Else use what is provided, but it has to be a list.
    2.  Get weather data.
    3.  Plot file if it is missing or it is newer than 11 days.

    :param regid:           [Int]           RegID as defined in regObs.
    :param plot_folder:     [string]        Path of folder for plots.
    :param observed_ice:    [ice.IceColumn] Optional. If not given, one will be looked up.
    """

    # if no observed ice is given, get it. Also, observed ice in the plotting routine is a list, so make it so.
    if not observed_ice:
        observed_ice = [gro.get_ice_thickness_on_regid(regid)]
    else:
        observed_ice = [observed_ice]

    x, y = observed_ice[0].metadata['UTMEast'], observed_ice[0].metadata['UTMNorth']

    from_date = observed_ice[0].date.date()
    to_date = from_date + dt.timedelta(days=9)

    # Get weather and snow data
    gridTemp = gts.getgts(x, y, 'tm', from_date, to_date)
    gridSno = gts.getgts(x, y, 'sdfsw', from_date, to_date)
    gridSnoTot = gts.getgts(x, y, 'sd', from_date, to_date)

    temp, date_times = we.strip_metadata(gridTemp, get_date_times=True)
    dates = [d.date() for d in date_times]
    sno = we.strip_metadata(gridSno)
    snotot = we.strip_metadata(gridSnoTot)
    cc = dp.clouds_from_precipitation(sno)

    # Define file name and tests for modelling and plotting
    plot_filename = '{0}{1}.png'.format(plot_folder, regid)

    try:
        icecover = calculate_ice_cover_air_temp(observed_ice[0], date_times, temp, sno, cc)
        pts.plot_ice_cover_9dogn(icecover, observed_ice[0], dates, temp, sno, snotot, plot_filename)
    except:
        # raise
        error_msg = sys.exc_info()[0]
        ml.log_and_print('calculateandplot.py -> calculate_and_plot9d_regid: {}. Could not plot {}.'.format(error_msg, regid))


def plot9d_regobs_observations(period='2018-19'):
    """Calculate ice columns for 9 days and make plots of all ice thickness for a given season or optionally 'Today'.

    The inner workings:
    1.1 Retrieves ice thickness observations from regObs. If period is given as a season, all observations for
        this season will be requested. All previous plots and local storage will be deleted.
    1.2 If period='Today' ice thickness observations from today will be requested and plotted. Older plots will be
        in the folder. Metadata dict will be merged.
    2.  Calculate the 9 day prognosis from the observation time and plots the result.
    3.  Make a metadata json for handling files on iskart.no. Only confirmed files in folder will be
        added to metadata json.

    :param period:    [String] Default is current season (2017-18).
    :return:
    """

    log_referance = 'calculateandplot.py -> plot9d_regobs_observations'

    # File names
    regid_metadata_json = '{}regid_metadata.json'.format(se.ni_dogn_plots_folder)
    regid_metadata_pickle = '{}regid_metadata.pickle'.format(se.local_storage)

    if period == 'Today':
        ice_thicks = gro.get_ice_thickness_today()

    else:
        # Empty the 9dogn folder
        # for file in os.listdir(se.ni_dogn_plots_folder):
        #     file_path = os.path.join(se.ni_dogn_plots_folder, file)
        #     try:
        #         if os.path.isfile(file_path):
        #             os.unlink(file_path)
        #     except OSError:
        #         pass

        # remove pickle with metadata
        try:
            os.remove(regid_metadata_pickle)
        except OSError:
            pass

        # Get new observations
        ice_thicks = gro.get_ice_thickness_observations(period, reset_and_get_new=True)

    # Calculate and plot
    for k, v in ice_thicks.items():

        # If file is missing, make it. If observation is older than 11 days it is based on gridded data for sure and no plot file needed.
        make_plot = False
        max_file_age = 11
        date_limit = dt.datetime.now() - dt.timedelta(days=max_file_age)
        file_names = os.listdir(se.ni_dogn_plots_folder)
        plot_filename = '{0}.png'.format(k)
        if plot_filename not in file_names:
            make_plot = True
        else:
            if v.date.date() > date_limit.date():
                make_plot = True

        if make_plot:
            try:
                calculate_and_plot9d_regid(k, plot_folder=se.ni_dogn_plots_folder, observed_ice=v)
            except:
                error_msg = sys.exc_info()[0]
                ml.log_and_print('{} Error making plot for {} {}'.format(log_referance, k, error_msg))

    # Make json with metadata for using files on iskart.no. Load metadata from pickle if available and
    # new observations where a plot is available will be made.
    if not os.path.exists(regid_metadata_pickle):
        regid_metadata = {}
    else:
        regid_metadata = mp.unpickle_anything(regid_metadata_pickle)

    list_of_plots = os.listdir(se.ni_dogn_plots_folder)

    for k, v in ice_thicks.items():
        # only add metadata on files that are in the folder
        if '{0}.png'.format(k) in list_of_plots:
            date = v.date.date()

            region_name = v.metadata['OriginalObject']['ForecastRegionName']
            if not region_name:
                region_name = 'Ukjent region'
            x, y = v.metadata['UTMEast'], v.metadata['UTMNorth']
            lake_id = v.metadata['LocationID']
            lake_name = v.metadata['LocationName']
            if not lake_name:
                lake_name = 'E{} N{}'.format(x,y)

            regid_metadata[k] = {'RegionName':region_name,'LakeID':lake_id,'LakeName':lake_name,'Date':'{}'.format(date)}

    mp.pickle_anything(regid_metadata, regid_metadata_pickle)

    json_string = json.dumps(regid_metadata, ensure_ascii=False).encode('utf-8')
    with open(regid_metadata_json, 'wb') as f:
        f.write(json_string)


if __name__ == "__main__":

    # plot9d_regobs_observations(period='Today')

    # ------ One full season may take 3-4 hours to plot since weatherdata is in each case requested ------
    # plot9d_regobs_observations(period='2018-19')
    # plot_season_regobs_observations(year='2018-19', calculate_new=True, get_new_obs=True, make_plots=True)
    # plot9d_regobs_observations(period='2017-18')
    # plot_season_regobs_observations(year='2017-18', calculate_new=True, get_new_obs=True, make_plots=True)
    # plot9d_regobs_observations(period='2016-17')
    # plot_season_regobs_observations(year='2016-17', calculate_new=True, get_new_obs=True, make_plots=True)
    # plot9d_regobs_observations(period='2015-16')
    # plot_season_regobs_observations(year='2015-16', calculate_new=True, get_new_obs=True, make_plots=True)
    # plot9d_regobs_observations(period='2014-15')
    # plot_season_regobs_observations(year='2014-15', calculate_new=True, get_new_obs=True, make_plots=True)

    # ------ Test some lakes plotted for a season ------
    # plot_season_location_id(17080, '2017-18', get_new_obs=False)
    # plot_season_location_id(57019, '2017-18', get_new_obs=False)
    # plot_season_location_id(2227, '2017-18', get_new_obs=False)
    # plot_season_location_id(7642, '2017-18', get_new_obs=False)

    # ------ Test some 9day plots on a give ice thickness observation -----
    calculate_and_plot9d_regid(138105)
    calculate_and_plot9d_regid(137767)
    calculate_and_plot9d_regid(131390)
    calculate_and_plot9d_regid(95811)         # has warm temps that fall behind
    calculate_and_plot9d_regid(136868)        # Burudvann lille julaften
    calculate_and_plot9d_regid(130979)        # Uskeput tidlig høst
    calculate_and_plot9d_regid(112366)
    calculate_and_plot9d_regid(130988)
    calculate_and_plot9d_regid(132133)
    calculate_and_plot9d_regid(133488)
    calculate_and_plot9d_regid(131705)        # has newsnow on first day and there is a frame

    pass
