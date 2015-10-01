__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import getWSklima as gws
import getChartserverdata as gcs
import datetime as dt


def harvest_hakloa(from_string, to_string):
    """Method gathers meteorological parameters needed to run myLake and saves them to a formated file as needed
    to run myLake.

    :param from_string:     {string}    from date to acquire data
    :param to_string:       {string}    to date to acquire data
    :return:

    Columns needed
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

    utm33_x = 259942                # Hakloa (buoy)
    utm33_y = 6671218               # Hakloa (buoy)
    stnr_met_blind = 18700          # Blindern (met)
    stnr_met_bjorn = 18500          # Bjørnholt (met)
    stnr_nve = '6.24.4'             # Hakloa (NVE)

    #elems_bjorn = gws.getElementsFromTimeserieTypeStation(stnr_met_bjorn, 0, output='csv')
    #elems_blind = gws.getElementsFromTimeserieTypeStation(stnr_met_blind, 0, output='csv')

    from_date = dt.datetime.strptime(from_string, "%Y-%m-%d")
    to_date = dt.datetime.strptime(to_string, "%Y-%m-%d")

    Global_rad = None
    Cloud_cov = gws.getMetData(stnr_met_blind, 'NNM', from_date, to_date, 0)
    Air_temp = gcs.getStationdata(stnr_nve, '17.1', from_date, to_date, timeseries_type=0)
    Rel_hum = None
    Air_press = gws.getMetData(stnr_met_blind, 'POM', from_date, to_date, 0)
    Wind_speed = None
    Precipitation = gws.getMetData(stnr_met_bjorn, 'RR', from_date, to_date, 0)     # returns in SI units [m]
    #Snow_depth = gcs.getGriddata(utm33_x, utm33_y, 'sd', from_date, to_date)


    a = 1


if __name__ == "__main__":

    harvest_hakloa('2014-11-15', '2015-06-20')