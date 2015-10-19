__author__ = 'ragnarekker'


import types as t
import datetime as dt
import weather as we
import setEnvironment as se


def write_vardat2(file_name, data, WSYS, OPER, DCHA):
    """Writes data to file using the vardat2 format from hydra-II at NVE.
    :param file_name:   [string]
    :param data:        [list of weatherelements] or [list of lists of weatherelements]
    :param WSYS:        [string] WorkingSYStem
    :param OPER:        [string] OPERator
    :param DCHA:        [string] DataCHANel
    :return:
    """

    # If data and DCHA not a list, make it so.
    if not isinstance(data, t.ListType):
        data = [data]
    if not isinstance(DCHA, t.ListType):
        DCHA = [DCHA]

    RTIM = dt.datetime.now().strftime('%Y%m%d/%H%M')

    f = open(file_name, 'w')

    # write header
    f.write('################################# 2 ######################################\n')
    f.write('#WSYS {0}\n'.format(WSYS))
    f.write('#OPER {0}\n'.format(OPER))
    f.write('#RTIM {0}\n'.format(RTIM))
    for dcha in DCHA:
        f.write('#DCHA {0}\n'.format(dcha))
    f.write('##########################################################################\n')

    # write values
    for i in range(0, len(data[0]), 1):
        text_line = '{0}'.format(data[0][i].Date.strftime('%Y%m%d/%H%M'))
        for d in data:
            text_line += '\t{0: >10}'.format(d[i].Value)
        text_line += '\n'
        f.write(text_line)

    f.close()

    return


def write_large_string(file_name, extension, data):
    """Writes large data to file. Typpicaly the whole responds of a request.

    :param file_name:
    :param data:
    :return:
    """
    file_name += extension
    f = open(file_name, 'w')
    f.write(data)
    f.close()


def write_dictionary(file_name, extension, data, tabulated=False):
    """Writes a list of directoiries to file.

    :param file_name:
    :param extension:
    :param data:        [list of dictionaries]
    :param tabulated:   [bool] If True values a written in table form.
    :return:
    """

    file_name += extension

    if tabulated == False:
        with open(file_name, "w") as myfile:
            for d in data:
                for key, value in d.iteritems():
                    myfile.write("{0: <18} {1}\n".format(key+":", value))
                myfile.write("\n")
    else:
        with open(file_name, "w") as myfile:
            myfile.write("Tabulated data goes here. Method not implemented.")


def write_weather_element_list(data, file_name='', extension='csv'):
    """A quick way to print a list of weatherements to file.

    :param data:
    :param file_name:
    :param extension:
    :return:
    """

    if not isinstance(data[0], we.WeatherElement):
        print "makeFiledata/write_weather_element: This method only for weather elements."

    else:
        if file_name == '':
            #file_name = '{0}test_write_weather_element.{1}'.format(se.data_path, extension)
            file_name = '{0}{1} {2} {3}-{4}.{5}'.format(
                se.data_path, data[0].LocationID, data[0].ElementID,
                data[0].Date.strftime('%Y%m%d'), data[-1].Date.strftime('%Y%m%d'), extension)

        f = open(file_name, 'w')

        # write header
        f.write('{0} {1} from {2} to {3}\n'.format(
            data[0].LocationID, data[0].ElementID, data[0].Date.strftime('%Y%m%d %H:%M'), data[-1].Date.strftime('%Y%m%d %H:%M')))

        # write values
        for d in data:

            text_line = '{0};{1}'.format(d.Date.strftime('%Y%m%d/%H%M'), d.Value)
            text_line += '\n'
            f.write(text_line)

        f.close()


def write_mylake_inputfile(data):
    """

    :param data.output_file_path:   [string] Name and path of file
    :param data.output_header:      [string] Custom header
    :param data:                    The rest of the object are lists of weather elments needed to run My Lake
    :return:

    E.g.:
    -999;MyLake model input data time series for Vansjoen, from PGS data, 1984-2000, Last modified 28.02.2005;;;;;;;;;;;;;;;;
    Year;Month;Day;Global_rad (MJ/m2);Cloud_cov (-);Air_temp (deg C);Relat_hum (%);Air_press (hPa);Wind_speed (m/s);Precipitation (mm/day);Inflow (m3/day);Inflow_T (deg C);Inflow_C;Inflow_S (kg/m3);Inflow_TP (mg/m3);Inflow_DOP (mg/m3);Inflow_Chla (mg/m3);Inflow_DOC (mg/m3)
    1984;1;1;NaN;0.375;4.95;64.25;971.4;7.6;0.1;325161.29;3.01;0;0.001;1;0;0;0
    1984;1;2;NaN;0.21875;0.95;73.25;977.575;6.95;0;325161.29;2.08;0;0.001;1;0;0;0
    """

    f = open(data.output_file_path + '.csv', 'w')

    # Write header
    first_line = '-999;{0}, Last modified {1};;;;;;;;;;;;;;;;'.format(data.output_header, dt.date.today())
    second_line = 'Year;Month;Day;Global_rad (MJ/m2);Cloud_cov (-);Air_temp (deg C);Relat_hum (%);Air_press (hPa);' \
                  'Wind_speed (m/s);Precipitation (mm/day);Inflow (m3/day);Inflow_T (deg C);Inflow_C;' \
                  'Inflow_S (kg/m3);Inflow_TP (mg/m3);Inflow_DOP (mg/m3);Inflow_Chla (mg/m3);Inflow_DOC (mg/m3)'
    f.write(first_line + '\n' + second_line + '\n')


    for i in range(0, len(data.Air_temp), 1):
        Year = data.Air_temp[i].Date.year
        Month = data.Air_temp[i].Date.month
        Day  = data.Air_temp[i].Date.day
        Global_rad = data.Global_rad[i].Value
        Cloud_cov = data.Cloud_cov[i].Value
        Air_temp = data.Air_temp[i].Value
        Relat_hum = data.Relat_hum[i].Value
        Air_press = data.Air_press[i].Value
        Wind_speed = data.Wind_speed[i].Value
        Precipitation = data.Precipitation[i].Value
        Inflow = data.Inflow[i].Value
        Inflow_T = data.Inflow_T[i].Value
        Inflow_C = data.Inflow_C[i].Value
        Inflow_S = data.Inflow_S[i].Value
        Inflow_TP = data.Inflow_TP[i].Value
        Inflow_DOP = data.Inflow_DOP[i].Value
        Inflow_Chla = data.Inflow_Chla[i].Value
        Inflow_DOC = data.Inflow_DOC[i].Value

        data_line = '{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};{10};{11};{12};{13};{14};{15};{16};{17}\n'.format(
            Year, Month, Day, Global_rad, Cloud_cov, Air_temp, Relat_hum, Air_press, Wind_speed, Precipitation,
            Inflow, Inflow_T, Inflow_C, Inflow_S, Inflow_TP, Inflow_DOP, Inflow_Chla, Inflow_DOC)
        data_line = data_line.replace("None","NaN")

        f.write(data_line)

    f.close()