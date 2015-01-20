__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

from Calculations.parameterization import *
from TimeseriesIO import getMetData, stripMetadata
import pylab as plt
import numpy as np
import copy
import sqlite3 as db
import datetime

plot_folder = "/Users/ragnarekker/Documents/GitHub/Ice-modelling/Plots/"
databaseLocation = '/Users/ragnarekker/Documents/GitHub/Ice-modelling/Databases/cloudMakingResults.sqlite'

def __write2database(database, a, b, c, d, e, f, g, h, i, rms, date, stnr, period):
    """
    Method writes the input prams and  result of the metodcall to database:
    estClouds = ccFromPrecAndTemp(prec, temp, [b, c, d, e], [f, g, h, i])

    Database generated with script:
    ?????

    :param database:    Location of database
    :param a,b,..,i:    as given in the method ccFromPrecAndTemp(prec, temp, [b, c, d, e], [f, g, h, i])
    :param rms:         result benchmarked as root mean square
    :param date:        when was this test preformed
    :param stnr:        on which eKlima station was the test preformed
    :param period:      From which period is the datasett from.
    :return:            NULL
    """

    con = db.connect(database)
    data = (a, b, c, d, e, f, g, h, i, rms, date, stnr, period)

    with con:
        cur = con.cursor()
        cur.execute('INSERT INTO ccREMCresults VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', data)

    return

def __shiftClouds(cloudsInn, shift):
    """
    prec and temp measure form 07 to 07 thus ar values for yesturday. This means that a day shif of +1 og the observed
    clouds (move them one day forward) is a better way to compare with estimated values from temp and prec.

    :param cloudsInn:   {list} list with cloudcover to be shifted.
    :param shift:       {int} no days to be shifted. Positive numbers for shifting forward.
    :return:            {list} shifted cloudcover data

    """

    if shift != 0:
        # dont mess with objects unless they are copies. Normaly they are only referances
        cloudsOut = copy.deepcopy(cloudsInn)

        if shift < 0:
            #take one off at the front and add one at the end
            cloudsOut.pop(0)
            cloudsOut.append(cloudsOut[-1])
        elif shift > 0:
            # take one of at the end and add one at the front
            cloudsOut.pop(-1)
            cloudsOut = [cloudsOut[0]] + cloudsOut

        return cloudsOut

    else:
        return cloudsInn

def doAREMCAnalyssis(stnr, startDate, endDate):
    """
    Preforms a Ragnar Ekker variant of Monte Carlo (or whatever). This metod runs an analysis of several conbinations
    of gammadistributions for precipitation and temperature affect on cloudcover. Results are written to a sqllite
    database for further study.

    :param stnr:        eKlima station where there is cloudcover for testing method.
    :param startDate:   simulations and referance data from this data
    :param endDate:     simulations and referance data to this data
    :return:
    """

    wsTemp = getMetData(stnr, 'TAM', startDate, endDate, 0, 'list')
    wsPrec = getMetData(stnr, 'RR', startDate, endDate, 0, 'list')
    wsCC = getMetData(stnr, 'NNM', startDate, endDate, 0, 'list')

    temp, date = stripMetadata(wsTemp, getDates=True)
    prec = stripMetadata(wsPrec, False)
    clouds = stripMetadata(wsCC, False)

    loggdate = datetime.datetime.now()
    period = '{0} to {1}'.format(startDate,endDate)

    cs = [1]        # cloudshift the observed data one day forward

    psh = [2.8, 3.0, 3.3]          # prec gamma shapefactor
    psc = [2.0]                    # prec gamma scalefactor
    pdb = [0.2, 0.3, 0.5, 0.7]     # prec days back
    pap = [0.3, 0.4, 0.5]          # prec amplitude factor

    tsh = [4.3, 4.5, 4.8, 5.0]     # temp gamma shapefactor
    tsc = [1.0]                    # temp gamma scalefactor
    tdb = [4.8, 5.0, 5.5]          # temp days back
    tap = [0.02, 0.03, 0.05]       # temp amplitude factor

    estimateSimulations = len(cs)*len(psh)*len(psc)*len(pdb)*len(pap)*len(tsh)*len(tsc)*len(tdb)*len(tap)
    doneSimulations = 0

    for a in cs:
        cloudsShifted = __shiftClouds(clouds, a)
        for b in psh:
            for c in psc:
                for d in pdb:
                    for e in pap:
                        for f in tsh:
                            for g in tsc:
                                for h in tdb:
                                    for i in tap:

                                        estClouds = ccFromPrecAndTemp(prec, temp, [b, c, d, e], [f, g, h, i])

                                        # What is the root mean square of estimatet vs observed clouds?
                                        rms = np.sqrt(((np.array(estClouds) - np.array(cloudsShifted)) ** 2).mean())

                                        __write2database(databaseLocation, a, b, c, d, e, f, g, h, i, rms, loggdate, stnr, period)

                                        doneSimulations = doneSimulations + 1
                                        print('beregning {0} av {1}'.format(doneSimulations, estimateSimulations))

    return

def testCloudMaker(stnr, startDate, endDate, method):
    """
    gets data from a eKlima station and smooths the data depending on wich method we wish to test.
    We find the root mean square to observations of clouds.
    And we plott and save the result to Plots folder.

    :param stnr:        eKlima station where there is cloudcover for testing method.
    :param startDate:   simulations and referance data from this data
    :param endDate:     simulations and referance data to this data
    :param method:      specify wich method to be tested
    :return:

    Availabe methods to test:
        ccFromPrecAndTemp
        ccFromPrec
        ccGammaSmoothing
        ccFromTempchange


    """

    wsTemp = getMetData(stnr, 'TAM', startDate, endDate, 0, 'list')
    wsPrec = getMetData(stnr, 'RR', startDate, endDate, 0, 'list')
    wsCC = getMetData(stnr, 'NNM', startDate, endDate, 0, 'list')

    temp, date = stripMetadata(wsTemp, getDates=True)
    prec = stripMetadata(wsPrec, False)
    clouds = stripMetadata(wsCC, False)

    dayShift = 1
    clouds = __shiftClouds(clouds, dayShift)

    if method == 'ccFromPrec':
        estClouds = ccFromPrec(prec)
        gammaFigtext = 'No gamma smoothing and dayshift = {0}'.format(dayShift)
    elif method == 'ccGammaSmoothing':
        gammaPrec = [2.8, 2., 0.3, 0.4]
        estClouds = ccFromPrec(prec)
        estClouds = ccGammaSmoothing(estClouds, gammaPrec)
        gammaFigtext = "gamma smoothing prec = {0} and dayshift = {1}".format(gammaPrec, dayShift)
    elif method == 'ccFromTempchange':
        gammaTemp = [4.8, 1., 5., 0.03]
        estClouds = ccFromTempchange(temp, gammaTemp)
        gammaFigtext = "gamma smoothing temp = {0} and dayshift = {1}".format(gammaTemp, dayShift)
    elif method == 'ccFromPrecAndTemp':
        gammaPrec = [2.8, 2., 0.3, 0.4]
        gammaTemp = [4.8, 1., 5., 0.03]
        estClouds = ccFromPrecAndTemp(prec, temp, gammaPrec, gammaTemp)
        gammaFigtext = "prec = {0} and temp = {1} and dayshift = {2}".format(gammaPrec, gammaTemp, dayShift)
    elif method == 'ccFromAverage':
        estClouds = ccFromAvaragePrecDays(prec)
        gammaFigtext = 'Cloudcover from avarage and dayshift = {0}'.format(dayShift)

    fileName = "{3} {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7], method)

    # What is the root mean square of estimatet vs observed clouds?
    rms = np.sqrt(((np.array(estClouds) - np.array(clouds)) ** 2).mean())

    # Figure dimensions
    fsize = (16, 10)
    plt.figure(figsize=fsize)
    plt.clf()

    # plot total snowdepth on land
    plt.bar(date, prec, width=1, color="0.4")

    # plot the estimated cloudcover
    for i in range(0, len(estClouds) - 1, 1):
        if estClouds[i] > 0:
            plt.hlines(max(prec) * 1.2, date[i], date[i + 1], lw=45, color=str(-(estClouds[i] - 1.)))
        elif estClouds[i] == None:
            plt.hlines(max(prec) * 1.2, date[i], date[i + 1], lw=45, color="pink")
        else:
            plt.hlines(max(prec) * 1.2, date[i], date[i + 1], lw=45, color=str(-(estClouds[i] - 1.)))

    # plot cloudcover from met
    for i in range(0, len(clouds) - 1, 1):
        if clouds[i] > 0:
            plt.hlines(max(prec) * 1.1, date[i], date[i + 1], lw=45, color=str(-(clouds[i] - 1.)))
        elif clouds[i] == None:
            plt.hlines(max(prec) * 1.1, date[i], date[i + 1], lw=45, color="pink")
        else:
            plt.hlines(max(prec) * 1.1, date[i], date[i + 1], lw=45, color=str(-(clouds[i] - 1.)))

    # this plots temperature on separate rightside axis
    plt.twinx()
    temp_pluss = []
    temp_minus = []
    for i in range(0, len(temp), 1):
        if temp[i] >= 0:
            temp_pluss.append(temp[i])
            temp_minus.append(np.nan)
        else:
            temp_minus.append(temp[i])
            temp_pluss.append(np.nan)
    plt.plot(date, temp, "black")
    plt.plot(date, temp_pluss, "red")
    plt.plot(date, temp_minus, "blue")

    # title and text fields
    plt.title("{3} {0} {1} {2}".format(stnr, startDate[0:7], endDate[0:7], method))
    plt.text(date[len(date)/2], min(temp)*1.2, 'gamma smoothing [shape, scale, days back, amplification]')
    plt.text(date[len(date)/2], min(temp)*1.3, gammaFigtext)

    # this is a scatterplot of modelled and estimated cloudcover
    xfrac = 0.15
    yfrac = (float(fsize[0])/float(fsize[1])) * xfrac
    xpos = 0.95-xfrac
    ypos = 0.42-yfrac
    a = plt.axes([xpos, ypos, xfrac, yfrac])
    a.scatter(clouds, estClouds)
    plt.setp(a, xticks=[0, 0.5, 1], yticks=[0, 0.5, 1])

    plt.text(0.0, -0.1, 'rms = {0}'.format(rms))

    plt.savefig("{0}{1}".format(plot_folder, fileName))
    return

if __name__ == "__main__":

    testCloudMaker(19710, '2011-10-01', '2012-06-01', 'ccFromPrecAndTemp')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', 'ccFromPrec')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', 'ccGammaSmoothing')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', 'ccFromTempchange')

    #doAREMCAnalyssis(19710, '2011-10-01', '2012-06-01')

    a = 1