__author__ = 'raek'
# -*- coding: utf-8 -*-

import datetime


def readWeather(from_date, to_date, filename):

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
        this_date = datetime.datetime.strptime(indata[i][0], "%Y-%m-%d")
        if this_date >= from_date and this_date <= to_date:
            date.append(this_date)
            if float(indata[i][1]) >= 0:            # only snow accumulation is used. The model melts and compresses snow.
                sno.append(float(indata[i][1]))
            else:
                sno.append(0.)
            temp.append(float(indata[i][4]))
            snotot.append(float(indata[i][5]))

    return date, temp, sno, snotot

# new way to read observed icecolumns for file. Inputfile contains multiple observations. Method returns a list of icecoluns
def importColumns(filepath_inn):
    '''

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
    import copy
    from TimeseriesIO import IceColumn

    # Read file
    innfile = open(filepath_inn)
    inndata = innfile.readlines()
    innfile.close()

    # fileseperator
    separator = ';'

    # This column is only for initiation and is removed from columns before returned
    column = IceColumn.IceColumn(datetime.datetime(1,1,1), 0)
    columns = []

    for row in inndata:
        row = row.strip()                   # get rid of ' ' and '\n' and such on the row
        if len(row) != 0 and row[0] != '#':
            row = row.split(separator)      # splits line into list of elements in the line
            row[0] = row[0].strip()                   # get rid of ' ' and '\n' and such on the separate elements
            row[1] = row[1].strip()
            if row[1] == 'date':
                columns.append(copy.deepcopy(column))
                date = datetime.datetime.strptime(row[0], "%Y-%m-%d")
                column = IceColumn.IceColumn(date, 0)
            elif row[1] == 'water_line':
                column.water_line = float(row[0])
            else:
                column.addLayerAtIndex(-1, float(row[0]), row[1])

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

