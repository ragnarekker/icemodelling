__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import copy
import sqlite3 as db
import datetime

import pylab as plt
import numpy as np
import dogamaclouds as dgc
import doparameterization as dpz

from getWSklima import getMetData
from weather import strip_metadata

from setEnvironment import plot_folder, database_location


def __writeRMC2database(database, a, b, c, d, e, f, g, h, i, rms, date, stnr, period):
    """
    Method writes the input prams and  result of the method call to database:
    estClouds = cc_gamma_prec_and_temp_change(prec, temp, [b, c, d, e], [f, g, h, i])

    Database generated with script:
    CREATE TABLE "ccREMCresults" ("cs" INTEGER, "psh" FLOAT, "psc" FLOAT, "pdb" FLOAT, "pap" FLOAT, "tsh" FLOAT,
    "tsc" FLOAT, "tdb" FLOAT, "tap" FLOAT, "rms" FLOAT, "date" DATETIME, "stnr" INTEGER, "period" TEXT)

    :param database:    Location of database
    :param a,b,..,i:    as given in the method cc_gamma_prec_and_temp_change(prec, temp, [b, c, d, e], [f, g, h, i])
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


def __writeCorrelation2database(database, cs, to, dto, depdT, depT, omc, crossCorr, loggtime, period, stnr):
    """

    Database generated with script:
    CREATE TABLE "corrCCandTemp" ("cs" INTEGER, "to" FLOAT, "dto" FLOAT, "depdT" BOOL, "depT" BOOL, "omc" BOOL,
    "crossCorr" FLOAT, "loggdate" DATETIME, "period" TEXT, "stnr" INTEGER)
    :return:
    """

    con = db.connect(database)
    data = (cs, to, dto, depdT, depT, omc, crossCorr, loggtime, period, stnr)

    with con:
        cur = con.cursor()
        cur.execute('INSERT INTO corrCCandTemp VALUES (?,?,?,?,?,?,?,?,?,?)', data)

    return


def __shiftClouds(cloudsInn, shift):
    """prec and temp measure form 07 to 07 thus are values for yesterday. This means that a day shift of +1 and
    the observed clouds (move them one day forward) is a better way to compare with estimated values
    from temp and prec.

    Clouds are observed at 7, 13 og 19 hrs and NNM is the average of these
    (http://met.no/Variasjoner+og+feilkilder.b7C_w7HQWD.ips).

    :param cloudsInn:   {list} list with cloud cover to be shifted.
    :param shift:       {int} number of days to be shifted. Positive numbers for shifting forward.
    :return:            {list} shifted cloud cover data

    """

    if shift != 0:
        # don't mess with objects unless they are copies. Normally they are only references to memory
        cloudsOut = copy.deepcopy(cloudsInn)

        if shift == -1:
            #take one off at the front and add one at the end
            cloudsOut.pop(0)
            cloudsOut.append(cloudsOut[-1])
        elif shift == 1:
            # take one of at the end and add one at the front
            cloudsOut.pop(-1)
            cloudsOut = [cloudsOut[0]] + cloudsOut
        elif shift < -1:
            # if more days try a recursive approach
            cloudsOut = __shiftClouds(cloudsInn, -1)
            cloudsOut = __shiftClouds(cloudsOut, shift+1)
        elif shift > 1:
            # the recursive approach works! Doing it for shifting more days forward also
            cloudsOut = __shiftClouds(cloudsInn, 1)
            cloudsOut = __shiftClouds(cloudsOut, shift-1)

        return cloudsOut

    else:
        return cloudsInn


def __getSign(values, offset):
    """
    # tempOffset < 0 means that positive temps are set to have negative sign Eg. tempOffset = -5 sets 4deg to -1deg
    # thus giving a negative sign.
    :param values:
    :param offset:
    :return:
    """

    signs = []

    for v in values:
        if v + offset != 0.:
            sign = (v + offset) / abs(v + offset)
        else:
            sign = 1

        signs.append(sign)

    return signs


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

    temp, date = strip_metadata(wsTemp, get_dates=True)
    prec = strip_metadata(wsPrec, False)
    clouds = strip_metadata(wsCC, False)

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

                                        estClouds = dgc.cc_gamma_prec_and_temp_change(prec, temp, [b, c, d, e], [f, g, h, i])

                                        # What is the root mean square of estimatet vs observed clouds?
                                        rms = np.sqrt(((np.array(estClouds) - np.array(cloudsShifted)) ** 2).mean())

                                        __writeRMC2database(database_location, a, b, c, d, e, f, g, h, i, rms, loggdate, stnr, period)

                                        doneSimulations = doneSimulations + 1
                                        print('beregning {0} av {1}'.format(doneSimulations, estimateSimulations))

    return


def correlateCloudsAndTemp(stnr, startDate, endDate):
    """
    DEAD END

    This was an attempt to check different functions of temperature and how well they correlate with an observed
    cloudcover. It turned out all different functions represent different signals so a cross correlation test and
    finding wich has the highest number whont work because the correlation number wil be different from function to
    function.

    :param stnr:
    :param startDate:
    :param endDate:
    :return:

    SELECT * FROM corrCCandTemp
    where loggdate = '2015-02-09 15:57:44.287000'
    order by crossCorr desc

    """


    wsTemp = getMetData(stnr, 'TAM', startDate, endDate, 0, 'list')
    wsCC = getMetData(stnr, 'NNM', startDate, endDate, 0, 'list')

    temp = strip_metadata(wsTemp, False)
    clouds = strip_metadata(wsCC, False)

    oneMinusClouds = [1-cc for cc in clouds]
    dTemp = dpz.delta_temperature_from_temperature(temp)
    abs_dTemp = map(abs, dTemp)
    #sum = [cc + mcc for cc, mcc in zip(clouds,oneMinusClouds)]

    loggdate = datetime.datetime.now()
    period = '{0} to {1}'.format(startDate,endDate)

    tempOffset = [0] #range(-5,6,1)
    dTempOffset = [0] #range(-3,4,1)
    ccShift = range(-4,5,1)
    sign_temp_dependant = [False]
    sign_dTemp_dependant = [False]
    useOneMinusClouds = [False]  # one minus cloudcover

    estimateSimulations = len(tempOffset)*len(dTempOffset) * len(ccShift) * len(sign_temp_dependant) * len(sign_dTemp_dependant) * len(useOneMinusClouds)
    doneSimulations = 0

    for cs in ccShift:
        for to in tempOffset:
            for dto in dTempOffset:
                for depdT in sign_dTemp_dependant:
                    for depT in sign_temp_dependant:
                        for omc in useOneMinusClouds:

                            sign_dTemp = 0
                            sign_temp = 0
                            ccwithoffset = 0

                            # if dTempExpression is not dependant of the signs of temp and dTemp the expression is reduced
                            # to only the abolute value of dTemp
                            if depdT == True:
                                sign_dTemp = __getSign(dTemp, dto)
                            else:
                                sign_dTemp = [1.]*len(temp)

                            if depT == True:
                                sign_temp = __getSign(temp, to)
                            else:
                                sign_temp = [1.]*len(temp)

                            # are we looking at cloud cover or clear skies? Does it matter?
                            if omc == True: # this option would be fraction og clear skies
                                ccwithoffset = __shiftClouds(oneMinusClouds, cs)
                            else:
                                ccwithoffset = __shiftClouds(clouds, cs)

                            dTempExpression = [sdt*adt*st for sdt,adt,st in zip(sign_dTemp,abs_dTemp,sign_temp)]
                            crossCorr = np.correlate(dTempExpression, ccwithoffset)

                            a = 1
                            __writeCorrelation2database(database_location,  cs, to, dto, depdT, depT, omc, crossCorr[0], loggdate, period, stnr)

                            doneSimulations = doneSimulations + 1
                            print('beregning {0} av {1}'.format(doneSimulations, estimateSimulations))

    return


def makeSomeScatterPlots(stnr, startDate, endDate):

    import numpy as numpy
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde


    wsTemp = getMetData(stnr, 'TAM', startDate, endDate, 0, 'list')
    wsPrec = getMetData(stnr, 'RR', startDate, endDate, 0, 'list')
    wsCC = getMetData(stnr, 'NNM', startDate, endDate, 0, 'list')

    temp, date = strip_metadata(wsTemp, get_dates=True)
    prec = strip_metadata(wsPrec, False)
    clouds = strip_metadata(wsCC, False)

    dTemp = dpz.delta_temperature_from_temperature(temp)
    abs_dTemp = map(abs, dTemp)

    method = 'dTemp_with_limit_vs_clouds'

    if method == 'dTemp_with_limit_vs_clouds':

        # Calibration params
        limit_temperature = [7]

        for limit_temp in limit_temperature:

            # Mask out positions in list where temps are above and below the threshhold temp
            temp_filter_high = []
            temp_filter_low = []
            for t in temp:
                if t >= limit_temp:
                    temp_filter_high.append(1.)
                    temp_filter_low.append(0.)
                else:
                    temp_filter_high.append(0.)
                    temp_filter_low.append(1.)

            # And make lists of dTemp_abs beloning to either high or low bands relative the threshhold temp
            dTemp_low_abs = [dt*tfl for dt,tfl in zip(abs_dTemp, temp_filter_low)]
            dTemp_high_abs = [dt*tfh for dt,tfh in zip(abs_dTemp, temp_filter_high)]

            fsize = (20, 20)
            plt.figure(figsize=fsize)
            plt.clf()

            #### Generate data
            x = [round(dtla,1) for dtla in dTemp_low_abs]
            y = [round(cc,2) for cc in clouds]

            # Calculate the point density
            xy = np.vstack([x,y])
            z = gaussian_kde(xy)(xy)

            plt.subplot(2,2,1).scatter(x, y, c=z, s=100, edgecolor='')
            plt.title("dtemp vs clouds (temp < {3}C) {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7], limit_temp))

            ##### Generate data
            x = [round(dtha, 1) for dtha in dTemp_high_abs]
            y = clouds

            # Calculate the point density
            xy = np.vstack([x,y])
            z = gaussian_kde(xy)(xy)

            plt.subplot(2,2,2).scatter(x, y, c=z, s=100, edgecolor='')
            plt.title("dtemp vs clouds (temp >= {3}C) {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7], limit_temp))


            plt.subplot(2,2,3).hist(z)


            fileName = "scatter dtemp vs clouds temp_limit{3} {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7], limit_temp)
            plt.savefig("{0}{1}".format(plot_folder, fileName))

    if method == 'dTemp_density':

        # Generate  data
        x = abs_dTemp
        y = clouds

        # Calculate the point density
        xy = np.vstack([x,y])
        z = gaussian_kde(xy)(xy)

        fig, ax = plt.subplots()
        ax.scatter(x, y, c=z, s=100, edgecolor='')

        plt.title("scatter dtemp_density clouds {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7]))
        fileName = "scatter dtemp_density {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7])

        plt.savefig("{0}{1}".format(plot_folder, fileName))

    if method == 'prec':

        fsize = (10, 10)
        plt.figure(figsize=fsize)
        plt.clf()

        plt.title("scatter prec clouds {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7]))
        fileName = "scatter prec clouds {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7])

       # Generate data
        x = prec
        y = clouds

        # Calculate the point density
        xy = np.vstack([x,y])
        z = gaussian_kde(xy)(xy)

        plt.scatter(x, y, c=z, s=100, edgecolor='')

        # calc the trendline
        z = numpy.polyfit(prec, clouds, 1)
        p = numpy.poly1d(z)
        plt.plot(prec, p(prec) )

        # the line equation:
        line_equation = "clouds = %.6f*prec + %.6f"%(z[0],z[1])
        plt.text(0.0, -0.1, 'Line equation: {0}'.format(line_equation))

        plt.savefig("{0}{1}".format(plot_folder, fileName))





    return


def testCloudMaker(stnr, startDate, endDate, method):
    """Gets data from a eKlima station and smooths the data depending on which method we wish to test.
    We find the nash-sutcliffe to observations of clouds. And we plot and save the result to Plots folder.

    :param stnr:        eKlima station where there is cloud cover for testing method.
    :param startDate:   simulations and reference data from this data
    :param endDate:     simulations and reference data to this data
    :param method:      specify which method to be tested
    :return:

    Available methods to test:
    cc_from_prec
    ccFromAveragePrec
    ccFromAverageObsCc
    ccGammaPrec
    ccGammaTemp
    ccGammaPrecAndTemp"""

    wsTemp = getMetData(stnr, 'TAM', startDate, endDate, 0, 'list')
    wsPrec = getMetData(stnr, 'RR', startDate, endDate, 0, 'list')
    wsCC = getMetData(stnr, 'NNM', startDate, endDate, 0, 'list')

    temp, date = strip_metadata(wsTemp, get_dates=True)
    prec = strip_metadata(wsPrec)
    clouds = strip_metadata(wsCC)

    dayShift = 1
    clouds = __shiftClouds(clouds, dayShift)

    if method == 'ccFromPrec':
        estClouds = dpz.clouds_from_precipitation(prec, method='Binary')
        gammaFigtext = 'No gamma smoothing and dayshift = {0}'.format(dayShift)
    elif method == 'ccFromAveragePrec':
        estClouds = dpz.clouds_from_precipitation(prec, method='Average')
        gammaFigtext = 'No gamma smoothing and dayshift = {0}'.format(dayShift)
    elif method == 'ccFromAverageObsCc':
        estClouds = [sum(clouds)/float(len(clouds))] * len(clouds)
        gammaFigtext = ''.format()
    elif method == 'ccGammaPrec':
        gammaPrec = [2.8, 2., 0.3, 0.4]
        estClouds = dpz.clouds_from_precipitation(prec, method='Binary')
        estClouds = dgc.cc_gamma_smoothing(estClouds, gammaPrec)
        gammaFigtext = "gamma smoothing prec = {0} and dayshift = {1}".format(gammaPrec, dayShift)
    elif method == 'ccGammaTempChange':
        gammaTemp = [4.8, 1., 5., 0.03]
        estClouds = dgc.cc_gamma_temp(temp, gammaTemp)
        gammaFigtext = "gamma smoothing temp = {0} and dayshift = {1}".format(gammaTemp, dayShift)
    elif method == 'ccGammaPrecAndTempChange':
        gammaPrec = [2.8, 2., 0.3, 0.4]
        gammaTemp = [4.8, 1., 5., 0.03]
        estClouds = dgc.cc_gamma_prec_and_temp_change(prec, temp, gammaPrec, gammaTemp)
        gammaFigtext = "prec = {0} and temp = {1} and dayshift = {2}".format(gammaPrec, gammaTemp, dayShift)


    fileName = "{3} {0} {1} {2}.png".format(stnr, startDate[0:7], endDate[0:7], method)

    # What is the root mean square of estimatet vs observed clouds?
    # rms = np.sqrt(((np.array(estClouds) - np.array(clouds)) ** 2).mean())

    # Nash–Sutcliffe model efficiency coefficient from
    # https://en.wikipedia.org/wiki/Nash%E2%80%93Sutcliffe_model_efficiency_coefficient
    numerator = 0
    denominator = 0
    mean_clouds = sum(clouds)/float(len(clouds))
    for i in range(0, len(clouds), 1):
        numerator += (clouds[i] - estClouds[i])**2
        denominator += (clouds[i] - mean_clouds)**2
    nash_sutcliffe = 1 - numerator/denominator

    # Figure dimensions
    fsize = (16, 10)
    plt.figure(figsize=fsize)
    plt.clf()

    # plot total snowdepth on land
    plt.bar(date, prec, width=1, color="0.4")

    # plot the estimated cloud cover
    for i in range(0, len(estClouds) - 1, 1):
        if estClouds[i] > 0:
            plt.hlines(max(prec) * 1.2, date[i], date[i + 1], lw=45, color=str(-(estClouds[i] - 1.)))
        elif estClouds[i] == None:
            plt.hlines(max(prec) * 1.2, date[i], date[i + 1], lw=45, color="pink")
        else:
            plt.hlines(max(prec) * 1.2, date[i], date[i + 1], lw=45, color=str(-(estClouds[i] - 1.)))

    # plot cloud cover from met
    for i in range(0, len(clouds) - 1, 1):
        if clouds[i] > 0:
            plt.hlines(max(prec) * 1.1, date[i], date[i + 1], lw=45, color=str(-(clouds[i] - 1.)))
        elif clouds[i] == None:
            plt.hlines(max(prec) * 1.1, date[i], date[i + 1], lw=45, color="pink")
        else:
            plt.hlines(max(prec) * 1.1, date[i], date[i + 1], lw=45, color=str(-(clouds[i] - 1.)))

    # this plots temperature on separate right side axis
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

    # this is a scatterplot of modelled and estimated cloud cover
    xfrac = 0.15
    yfrac = (float(fsize[0])/float(fsize[1])) * xfrac
    xpos = 0.95-xfrac
    ypos = 0.42-yfrac
    a = plt.axes([xpos, ypos, xfrac, yfrac])
    a.scatter(clouds, estClouds)
    plt.setp(a, xticks=[0, 0.5, 1], yticks=[0, 0.5, 1])

    plt.text(0.0, 0.1, 'na_su = {0}'.format(round(nash_sutcliffe, 2)), color='yellow', bbox={'facecolor':'black'})

    plt.savefig("{0}{1}".format(plot_folder, fileName))
    return


if __name__ == "__main__":

    testCloudMaker(19710, '2011-10-01', '2012-06-01', method='ccFromPrec')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', method='ccFromAveragePrec')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', method='ccFromAverageObsCc')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', method='ccGammaPrec')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', method='ccGammaTempChange')
    testCloudMaker(19710, '2011-10-01', '2012-06-01', method='ccGammaPrecAndTempChange')

    #doAREMCAnalyssis(19710, '2011-10-01', '2012-06-01')

    #correlateCloudsAndTemp(19710, '2011-10-01', '2012-06-01')

    #ccFromPrecAndTemp2(19710, '2011-10-01', '2012-06-01')

    makeSomeScatterPlots(19710, '2005-06-01', '2012-06-01')

    a = 1