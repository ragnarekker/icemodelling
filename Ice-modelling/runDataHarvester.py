__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import getWSklima as gws
import weather as we
import getChartserverdata as gcs
import datetime as dt
import setEnvironment as env


def harvest_hakloa(from_string, to_string):
    """Method gathers meteorological parameters needed to run myLake and saves them to a formated file as needed
    to run myLake. For columns needed se MyLakeInput class.

    :param from_string:     {string}    from date to acquire data
    :param to_string:       {string}    to date to acquire data
    :return:

    HydraII parameters:
        Wind                15
        Temperature         17
        Relative humidity    2
    """

    utm33_x = 259942                # Hakloa (buoy)
    utm33_y = 6671218               # Hakloa (buoy)
    stnr_met_blind = 18700          # Blindern (met)
    stnr_met_bjorn = 18500          # Bjørnholt (met)
    stnr_nve = '6.24.4'             # Hakloa (NVE)

    #elems_bjorn = gws.getElementsFromTimeserieTypeStation(stnr_met_bjorn, 0, output='csv')
    #elems_blind = gws.getElementsFromTimeserieTypeStation(stnr_met_blind, 0, output='csv')

    from_date = dt.datetime.strptime(from_string, "%Y-%m-%d")
    to_date = dt.datetime.strptime(to_string, "%Y-%m-%d")

    data = MyLakeInput()
    '''
    data.Global_rad = None
    data.Cloud_cov = gws.getMetData(stnr_met_blind, 'NNM', from_date, to_date, 0)
    data.Air_temp = gcs.getStationdata(stnr_nve, '17.1', from_date, to_date)
    data.Rel_hum = gcs.getStationdata(stnr_nve, '2.1', from_date, to_date)
    data.Air_press = gws.getMetData(stnr_met_blind, 'POM', from_date, to_date, 0)
    data.Wind_speed = gcs.getStationdata(stnr_nve, '15.1', from_date, to_date)
    data.Precipitation = we.millimeter_from_meter(gws.getMetData(stnr_met_bjorn, 'RR', from_date, to_date, 0))
    '''
    data.Inflow = we.constant_weather_element_list('Hakloa', from_date, to_date, 'Inflow', 10.)

    return data

class MyLakeInput():
    """
    Year
    Month
    Day

    Global_rad (MJ/m2)
    Cloud_cov (-)
    Air_temp (deg C)
    Relat_hum (%)
    Air_press (hPa)
    Wind_speed (m/s)
    Precipitation (mm/day)

    Inflow (m3/day)
    Inflow_T (deg C)
    Inflow_C
    Inflow_S (kg/m3)
    Inflow_TP (mg/m3)
    Inflow_DOP (mg/m3)
    Inflow_Chla (mg/m3)
    Inflow_DOC (mg/m3)
    """

    def __init__(self):

        Global_rad = None    # (MJ/m2)
        Cloud_cov = None    # (-)
        Air_temp = None    # (deg C)
        Relat_hum = None    # (%)
        Air_press = None    # (hPa)
        Wind_speed = None    # (m/s)
        Precipitation = None    # (mm/day)

        Inflow = None    # (m3/day)
        Inflow_T = None    # (deg C)
        Inflow_C = None    #
        Inflow_S = None    # (kg/m3)
        Inflow_TP = None    # (mg/m3)
        Inflow_DOP = None    # (mg/m3)
        Inflow_Chla = None    # (mg/m3)
        Inflow_DOC = None    # (mg/m3)


def make_mylake_inputfile(file_path, custom_text, data):
    """

    :param file_path:
    :return:

    E.g.:
    -999;MyLake model input data time series for Vansjoen, from PGS data, 1984-2000, Last modified 28.02.2005;;;;;;;;;;;;;;;;
    Year;Month;Day;Global_rad (MJ/m2);Cloud_cov (-);Air_temp (deg C);Relat_hum (%);Air_press (hPa);Wind_speed (m/s);Precipitation (mm/day);Inflow (m3/day);Inflow_T (deg C);Inflow_C;Inflow_S (kg/m3);Inflow_TP (mg/m3);Inflow_DOP (mg/m3);Inflow_Chla (mg/m3);Inflow_DOC (mg/m3)
    1984;1;1;NaN;0.375;4.95;64.25;971.4;7.6;0.1;325161.29;3.01;0;0.001;1;0;0;0
    1984;1;2;NaN;0.21875;0.95;73.25;977.575;6.95;0;325161.29;2.08;0;0.001;1;0;0;0
    """

    f = open(file_path, 'w')

    # Write header
    first_line = '-999;{0}, Last modified {1};;;;;;;;;;;;;;;;'.format(custom_text, dt.date.today())
    second_line = 'Year;Month;Day;Global_rad (MJ/m2);Cloud_cov (-);Air_temp (deg C);Relat_hum (%);Air_press (hPa):' \
                  'Wind_speed (m/s);Precipitation (mm/day);Inflow (m3/day);Inflow_T (deg C);Inflow_C;' \
                  'Inflow_S (kg/m3);Inflow_TP (mg/m3);Inflow_DOP (mg/m3);Inflow_Chla (mg/m3);Inflow_DOC (mg/m3)'
    f.write(first_line + '\n' + second_line + '\n')

    a = 1

    '''
    for m in main_messages:

        # sort the keys according to which is used most
        danger_levels = sorted(m.danger_levels.items(), key=operator.itemgetter(1), reverse=True)
        main_causes = sorted(m.main_causes.items(), key=operator.itemgetter(1), reverse=True)
        cause_names = sorted(m.cause_names.items(), key=operator.itemgetter(1), reverse=True)
        aval_types = sorted(m.aval_types.items(), key=operator.itemgetter(1), reverse=True)

        # join (the now after sorting, lists) to strings
        danger_levels = ', '.join("{!s} ({!r})".format(key,val) for (key,val) in danger_levels)
        main_causes = ', '.join("{!s} ({!r})".format(key,val) for (key,val) in main_causes)
        cause_names = ', '.join("{!s} ({!r})".format(key,val) for (key,val) in cause_names)
        aval_types = ', '.join("{!s} ({!r})".format(key,val) for (key,val) in aval_types)

        use_encoding = 'utf8'
        #use_encoding = 'latin-1'

        # add norwegian letters
        danger_levels = fe.add_norwegian_letters(danger_levels, use_encoding=use_encoding)
        main_causes = fe.add_norwegian_letters(main_causes, use_encoding=use_encoding)
        cause_names = fe.add_norwegian_letters(cause_names, use_encoding=use_encoding)
        aval_types = fe.add_norwegian_letters(aval_types, use_encoding=use_encoding)

        main_message_no = fe.add_norwegian_letters(m.main_message_no, use_encoding=use_encoding)
        main_message_en = fe.add_norwegian_letters(m.main_message_en, use_encoding=use_encoding)

        s = u'{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'.format(
            m.occurrences,
            danger_levels,
            main_causes,
            cause_names,
            aval_types,
            main_message_no,
            main_message_en)

        l.write(s.encode(use_encoding))
    '''

    f.close()

if __name__ == "__main__":

    data = harvest_hakloa('2014-11-15', '2015-06-20')
    file_path = '{0}HAK_input.csv'.format(env.data_path)
    custom_text = 'MyLake model input data for Hakloa from Hakloa (NVE), Bjørnholt (met) and Blindern (met) stations'
    make_mylake_inputfile(file_path, custom_text, data)