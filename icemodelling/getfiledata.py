__author__ = 'raek'
# -*- coding: utf-8 -*-

import datetime as dt
from icemodelling import weather as we
from icemodelling import setenvironment as se
import copy
from icemodelling import ice as ice


def read_weather(from_date, to_date, filename):
    """Reads date, temperature, snow and snowchange from a file formated with coluns for
    date, snow change, pressure?, wind, temperature and total snow. See example under.

    :param from_date:
    :param to_date:
    :param filename:
    :return:

    Eg. of file (tabs and spaces are optional):
          Dato;    s [m];       mm;      m/s;      C;  tot_s [m]
    2011-10-01;     0.01;   407.75;     1.14;  10.51;       0.01
    2011-10-02;     0.01;    408.5;     1.61;   8.87;       0.02
    2011-10-03;     0.01;   409.03;     2.36;   5.59;       0.03
    2011-10-04;     0.01;   415.74;     5.69;   2.79;       0.04
    2011-10-05;     0.01;   420.35;     3.71;   3.63;       0.05
    2011-10-06;     0.01;   424.21;     3.09;   2.42;       0.06
    2011-10-07;     0.01;   431.93;     4.19;   0.98;       0.07
    """

    # if not datetime objects, make them so
    if isinstance(from_date, str):
        from_date = dt.datetime.strptime(from_date, "%Y-%m-%d")
    if isinstance(to_date, str):
        to_date = dt.datetime.strptime(to_date, "%Y-%m-%d")

    date = []
    temp = []
    sno = []
    snotot = []

    separator = ';'

    infile = open(filename)
    indata = infile.readlines()
    infile.close()

    for i in range(len(indata)):
        indata[i] = indata[i].strip()               # get rid of ' ' and '\n' and such
        indata[i] = indata[i].split(separator)      # splits line into list of elements in the line

    for i in range(1, len(indata), 1):              # from 1 since index 0 are headers
        this_date = dt.datetime.strptime(indata[i][0], "%Y-%m-%d")
        if this_date >= from_date and this_date <= to_date:
            date.append(this_date)
            if float(indata[i][1]) >= 0:            # only snow accumulation is used. The model melts and compresses snow.
                sno.append(float(indata[i][1]))
            else:
                sno.append(0.)
            temp.append(float(indata[i][4]))
            snotot.append(float(indata[i][5]))

    return date, temp, sno, snotot


def importColumns(filepath_inn):
    '''Reads observed ice columns from file. Input file contains multiple observations.
    Method returns a list of ice coluns.

    :param filepath_inn:    path to the .csv file with observations
    :return:                a list of iceColumn objects [iceColum, iceColum, iceColum, ...]

    Example of inputfile:

    ##################
    #
    #  Observed icecolumns on Otrøvannet winter 2011-2012
    #  Values given as [value; type].
    #  Valid values are: 'date', 'water_line' and all the ice types: 'black_ice', 'slush_ice', 'slush', 'snow'.
    #  Hashtags are omitted and ' ', \n and such are removed when reading the file.
    #  An observation with only date is of "no ice".
    #
    ##################

    2011-12-08; date

    ##################

    2012-01-16; date
    0.32; snow
    0.01; slush
    0.08; slush_ice
    0.22; black_ice
    0.29; water_line

    ##################

    '''


    # Read file
    innfile = open(filepath_inn)
    inndata = innfile.readlines()
    innfile.close()

    # fileseperator
    separator = ';'

    # This column is only for initiation and is removed from columns before returned
    column = ice.IceColumn(dt.datetime(1,1,1), 0)
    columns = []

    for row in inndata:
        row = row.strip()                   # get rid of ' ' and '\n' and such on the row
        if len(row) != 0 and row[0] != '#':
            row = row.split(separator)      # splits line into list of elements in the line
            row[0] = row[0].strip()                   # get rid of ' ' and '\n' and such on the separate elements
            row[1] = row[1].strip()
            if row[1] == 'date':
                columns.append(copy.deepcopy(column))
                date = dt.datetime.strptime(row[0], "%Y-%m-%d")
                column = ice.IceColumn(date, 0)
            elif row[1] == 'water_line':
                column.water_line = float(row[0])
            else:
                column.add_layer_at_index(-1, ice.IceLayer(float(row[0]), row[1]))

    # the last object is not added in the loop
    columns.append(column)

    # this was the inital object. If data is the first element of the inputfile this object is empty.
    # If date was not sett before rows with icelayers the icelayer data is lost.
    columns.remove(columns[0])

    # This must be set on each object because Ive not been able to find a way to initialize it properly yet
    for column in columns:
        if column.water_line == -1:
            column.update_water_line()

    return columns


def read_hydra_time_value(station, element, file_name, from_date=None, to_date=None, timeseries_type=0):
    """Reads a time/value file made in NVEs Start for accessing data in HydraII.

    :param station:
    :param element:
    :param file_name:
    :param from_date:           {datetime} method returns [fromDate , toDate>
    :param to_date:             {datetime} method returns [fromDate , toDate>
    :param timeseries_type:
    :return:
    """

    print("getFildata.py -> read_hydra_time_value: Reading {0}".format(file_name))

    if from_date is None:
        from_date = dt.date(0,0,0)
    if to_date is None:
        to_date = dt.datetime.now().date()

    inn_file = open(file_name)
    inn_data = inn_file.readlines()
    inn_file.close()
    separator = ' '
    for i in range(len(inn_data)):
        inn_data[i] = inn_data[i].strip()               # get rid of ' ' and '\n' and such
        inn_data[i] = inn_data[i].split(separator)      # splits line into list of elements in the line

    weather_element_list = []
    for d in inn_data:
        if d[0] == '':                  # blank line at end of file
            break
        value = float(d[1])
        date = dt.datetime.strptime(d[0], '%Y%m%d/%H%M')
        if from_date.date() <= date.date() < to_date.date():
            weather_element_list.append(we.WeatherElement(station, date, element, value))

    if timeseries_type == -1:                           # do nothing
        weather_element_list = weather_element_list
    elif timeseries_type == 0:                          # make daily averages of hourly values
        weather_element_list = we.make_daily_average(weather_element_list)
    else:
        print('no valid time series type selected')
        weather_element_list = 'no valid time series type selected'

    return weather_element_list


if __name__ == "__main__":

    from icemodelling import makefiledata as mf

    file_name = '{0}6.24.4.17.1 Hakkloa temperatur 20110101-20151009.txt'.format(se.data_path)
    temperature = read_hydra_time_value(
        '6.24.4', '17.1', file_name, from_date=dt.datetime(2015, 7, 1), to_date=dt.datetime(2015, 8, 1))
    #mf.write_weather_element_list(temperature)

    a = 1
