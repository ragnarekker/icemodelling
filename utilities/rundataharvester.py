# -*- coding: utf-8 -*-
"""Module for gathering and saving to file, meteorological parameters needed to run myLake. Module may be
expanded for preparing other data sets if needed."""
import datetime as dt
import setenvironment as env
from utilities import makepickle as mp, makefiledata as mfd, getwsklima as gws
from icemodelling import weatherelement as we
from utilities import getfiledata as gfd, getchartserverdata as gcs

__author__ = 'ragnarekker'


def harvest_for_mylake_hakkloa(from_string, to_string):
    """Method gathers meteorological parameters needed to run myLake on Hakkloa and saves them to a
    formatted file as needed to run myLake. For columns needed se MyLakeInput class.

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

    hydraii_temperature = '{0}6.24.4.17.1 Hakkloa temperatur 20110101-20151009.txt'.format(env.data_path)
    hydraii_wind = '{0}6.24.4.15.1 Hakkloa vind 20110101-20151009.txt'.format(env.data_path)
    hydraii_relative_humidity = '{0}6.24.4.2.1 Hakkloa relativ fuktighet 20110101-20151009.txt'.format(env.data_path)

    from_date = dt.datetime.strptime(from_string, "%Y-%m-%d")
    to_date = dt.datetime.strptime(to_string, "%Y-%m-%d")
    data = MyLakeInput(from_date, to_date)
    data.output_file_path = '{0}HAK_input'.format(env.data_path)
    data.output_header = 'MyLake model resources data for Hakkloa from Hakkloa (NVE), Bjørnholt (met) and Blindern (met) stations'

    data.add_Global_rad(we.constant_weather_element('Hakkloa', from_date, to_date, 'Global_rad', None))
    data.add_Cloud_cov(gws.getMetData(stnr_met_blind, 'NNM', from_date, to_date, 0))
    data.add_Air_temp(gfd.read_hydra_time_value(stnr_nve, '17.1', hydraii_temperature, from_date, to_date))
    data.add_Relat_hum(gfd.read_hydra_time_value(stnr_nve, '2.1', hydraii_relative_humidity, from_date, to_date))
    data.add_Air_press(gws.getMetData(stnr_met_blind, 'POM', from_date, to_date, 0))
    data.add_Wind_speed(gfd.read_hydra_time_value(stnr_nve, '15.1', hydraii_wind, from_date, to_date))
    data.add_Precipitation(we.millimeter_from_meter(gws.getMetData(stnr_met_bjorn, 'RR', from_date, to_date, 0)))

    # Inflow is water shed area * precipitation
    Inflow = []
    precipitation = data.Precipitation # precipitation in [mm]
    water_shed_area = 6.49 * 10**6 # [m2]
    for p in precipitation:
        value =  p.Value/1000*water_shed_area
        Inflow.append(we.WeatherElement('Hakkloa', p.Date, 'Inflow', value))
    data.add_Inflow(Inflow)

    # Inflow temperature is assumed air temp but never below 0C and if snow always 0C
    snow = gcs.getGriddata(utm33_x, utm33_y, 'sd', from_date, to_date)
    temperature = data.Air_temp

    #mfd.write_weather_element_list(temperature)
    #mfd.write_weather_element_list(snow)
    #mfd.write_weather_element_list(data.Relat_hum)
    #mfd.write_weather_element_list(data.Wind_speed)

    Inflow_T = []
    for i in range(0, len(snow), 1):
        date = temperature[i].Date
        value = max(0., temperature[i].Value)       # water never below 0C
        if snow[i].Value > 0. and value > 0.:       # if snow, water never over 0C
            value = 0.
        Inflow_T.append(we.WeatherElement('Hakkloa', date, 'Inflow_T', value))
    data.add_Inflow_T(Inflow_T)

    data.add_Inflow_C(we.constant_weather_element('Hakkloa', from_date, to_date, 'Inflow_C', .5))
    data.add_Inflow_S(we.constant_weather_element('Hakkloa', from_date, to_date, 'Inflow_S', .01))
    data.add_Inflow_TP(we.constant_weather_element('Hakkloa', from_date, to_date, 'Inflow_TP', 44.))
    data.add_Inflow_DOP(we.constant_weather_element('Hakkloa', from_date, to_date, 'Inflow_DOP', 7.))
    data.add_Inflow_Chla(we.constant_weather_element('Hakkloa', from_date, to_date, 'Inflow_Chla', .1))
    data.add_Inflow_DOC(we.constant_weather_element('Hakkloa', from_date, to_date, 'Inflow_DOC', 3000.))

    return data


def harvest_and_save_blindern(from_string, to_string):

    stnr_met_blind = 18700          # Blindern (met)
    from_date = dt.datetime.strptime(from_string, "%Y-%m-%d")
    to_date = dt.datetime.strptime(to_string, "%Y-%m-%d")
    #elems_blind = gws.getElementsFromTimeserieTypeStation(stnr_met_blind, 2, output='csv')

    rr = gws.getMetData(stnr_met_blind, 'RR', from_date, to_date, 0, output='raw list')
    rr = we.millimeter_from_meter(rr)
    rr_test_message = we.test_for_missing_elements(rr, from_date, to_date)

    tam = gws.getMetData(stnr_met_blind, 'TAM', from_date, to_date, 0, output='raw list')
    tam_test_message = we.test_for_missing_elements(tam, from_date, to_date)

    nnm = gws.getMetData(stnr_met_blind, 'NNM', from_date, to_date, 0, output='raw list')
    nnm_test_message = we.test_for_missing_elements(nnm, from_date, to_date)

    file_name = '{2}RR TAM NNM Blindern 18700 {0} to {1}.txt'.format(from_string, to_string, env.data_path)

    WSYS = "github/Ice-modelling/rundataharvester.py"
    OPER = "Ragnar Ekker"
    DCHA = ['RR  [mm/day]          on Blindern 18700 from eklima.met.no',
            'TAM [C]     daily avg on Blindern 18700 from eklima.met.no',
            'NNM [%/100] daily avg on Blindern 18700 from eklima.met.no']

    mfd.write_vardat2(file_name, [rr, tam, nnm], WSYS, OPER, DCHA)

    return


def harvest_and_save_nordnesfjelet(from_string, to_string):

    stnr = 91500          # Nordnesfjellet (met)
    from_date = dt.datetime.strptime(from_string, "%Y-%m-%d")
    to_date = dt.datetime.strptime(to_string, "%Y-%m-%d")
    #elems_blind = gws.getElementsFromTimeserieTypeStation(stnr, 2, output='csv')

    qli = gws.getMetData(stnr, 'QLI', from_date, to_date, 2, output='raw list')
    qli_test_message = we.test_for_missing_elements(qli, from_date, to_date, time_step=60*60)

    ta = gws.getMetData(stnr, 'ta', from_date, to_date, 2, output='raw list')
    ta_test_message = we.test_for_missing_elements(ta, from_date, to_date, time_step=3600)

    rr_1 = gws.getMetData(stnr, 'rr_1', from_date, to_date, 2, output='raw list')
    rr_1 = we.millimeter_from_meter(rr_1)
    rr_test_message = we.test_for_missing_elements(rr_1, from_date, to_date, time_step=3600)

    file_name = '{2}QLI TA RR Nordnesfjellet 91500 {0} to {1}.txt'.format(from_string, to_string, env.data_path)

    WSYS = "github/Ice-modelling/rundataharvester.py"
    OPER = "Ragnar Ekker"
    DCHA = ['QLI  [Wh/m2] avg pr hr on Nordnesfjellet 91500 from eklima.met.no',
            'TA   [C]     avg pr hr on Nordnesfjellet 91500 from eklima.met.no',
            'RR_1 [mm/hr]           on Nordnesfjellet 91500 from eklima.met.no']

    mfd.write_vardat2(file_name, [qli, ta, rr_1], WSYS, OPER, DCHA)

    return


class MyLakeInput:
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

    def __init__(self, from_date_inn, to_date_inn):

        self.from_date = from_date_inn
        self.to_date = to_date_inn

        self.output_file_path = None
        self.output_header = None

        self.metadata = []

        self.Global_rad = None    # (MJ/m2)
        self.Cloud_cov = None    # (-)
        self.Air_temp = None    # (deg C)
        self.Relat_hum = None    # (%)
        self.Air_press = None    # (hPa)
        self.Wind_speed = None    # (m/s)
        self.Precipitation = None    # (mm/day)

        self.Inflow = None    # (m3/day)
        self.Inflow_T = None    # (deg C)
        self.Inflow_C = None    #
        self.Inflow_S = None    # (kg/m3)
        self.Inflow_TP = None    # (mg/m3)
        self.Inflow_DOP = None    # (mg/m3)
        self.Inflow_Chla = None    # (mg/m3)
        self.Inflow_DOC = None    # (mg/m3)


    def add_Global_rad(self, Global_rad_inn):
        if Global_rad_inn is None:
            self.Global_rad = None
        else:
            messages = we.test_for_missing_elements(Global_rad_inn, self.from_date, self.to_date)
            self.metadata += messages
            self.Global_rad = Global_rad_inn


    def add_Cloud_cov(self, Cloud_cov_inn):
        messages = we.test_for_missing_elements(Cloud_cov_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Cloud_cov = Cloud_cov_inn


    def add_Air_temp(self, Air_temp_inn):
        messages = we.test_for_missing_elements(Air_temp_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Air_temp = Air_temp_inn


    def add_Relat_hum(self, Relat_hum_inn):
        messages = we.test_for_missing_elements(Relat_hum_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Relat_hum = Relat_hum_inn


    def add_Air_press(self, Air_press_inn):
        messages = we.test_for_missing_elements(Air_press_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Air_press = Air_press_inn


    def add_Wind_speed(self, Wind_speed_inn):
        messages = we.test_for_missing_elements(Wind_speed_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Wind_speed = Wind_speed_inn


    def add_Precipitation(self, Precipitation_inn):
        messages = we.test_for_missing_elements(Precipitation_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Precipitation = Precipitation_inn


    def add_Inflow(self, Inflow_inn):
        messages = we.test_for_missing_elements(Inflow_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow = Inflow_inn


    def add_Inflow_T(self, Inflow_T_inn):
        messages = we.test_for_missing_elements(Inflow_T_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow_T = Inflow_T_inn


    def add_Inflow_C(self, Inflow_C_inn):
        messages = we.test_for_missing_elements(Inflow_C_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow_C = Inflow_C_inn


    def add_Inflow_S(self, Inflow_S_inn):
        messages = we.test_for_missing_elements(Inflow_S_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow_S = Inflow_S_inn


    def add_Inflow_TP(self, Inflow_TP_inn):
        messages = we.test_for_missing_elements(Inflow_TP_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow_TP = Inflow_TP_inn


    def add_Inflow_DOP(self, Inflow_DOP_inn):
        messages = we.test_for_missing_elements(Inflow_DOP_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow_DOP = Inflow_DOP_inn


    def add_Inflow_Chla(self, Inflow_Chla_inn):
        messages = we.test_for_missing_elements(Inflow_Chla_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow_Chla = Inflow_Chla_inn


    def add_Inflow_DOC(self, Inflow_DOC_inn):
        messages = we.test_for_missing_elements(Inflow_DOC_inn, self.from_date, self.to_date)
        self.metadata += messages
        self.Inflow_DOC = Inflow_DOC_inn


if __name__ == "__main__":

    yesturday = (dt.date.today()-dt.timedelta(days=1)).strftime("%Y-%m-%d")
    #harvest_and_save_blindern('2000-01-01', yesturday)
    #harvest_and_save_nordnesfjelet('2014-08-01', yesturday)

    data = harvest_for_mylake_hakkloa('2013-04-01', '2015-10-01')
    mp.pickle_anything(data, data.output_file_path +'.pickle')
    data2 = mp.unpickle_anything('{0}HAK_input'.format(env.data_path) +'.pickle')

    mfd.write_mylake_inputfile(data2)
