__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-
# In this file methods for calulating/estimating physical parameters WITHIN THE CURRENT TIMESTEP

import doparameterization as pz

########
# Needs comments
def __getGammafilter(a, lamda, negativeDays, hardness):
    """

    :param a:               shapefactor of a gammadistribution
    :param lamda:           scalefactor of a gammadistribution (sometimes scale=1/lamda as in scipy)
    :param negativeDays:    How many days back should the change have affect? Eg 1.5 goes to noon two days back.
    :param hardness:        Should the filter smoothe or spread? Eg: if hardness = 0.5 and applied to only
                            one rain event the cloud cover will be 0.5 that day.

    :return:                A gammafilter
    """

    from scipy.stats import gamma
    from scipy.integrate import quad

    # find the top of the gamadistribution. This will be noon (12:00) on the day with rain
    gdst = gamma(a, scale=1/lamda)
    increase = True                 # initial value
    delta = 0.01
    x = 0.01                        # initial value

    while increase == True:
        h = gdst.pdf(x+delta) - gdst.pdf(x)
        if h < 0:
            increase = False
        else:
            x = x + delta

    # So. x is where the top of the function is.
    # Update the gammadistribution with this shift so it has its maximum on x = 0
    gdst = gamma(a, loc=-x, scale=1/lamda)

    # Fist I make the weights for the days prior the event (x < 0)
    delta = x/(negativeDays+0.5)
    distr = quad(lambda x: gdst.pdf(x), 0, -delta/2)
    intFrom = -delta/2
    gammaFilter = [-distr[0]]

    while -distr[0] > 0.05:
        distr = quad(lambda x: gdst.pdf(x), intFrom, intFrom-delta)
        intFrom = intFrom - delta
        gammaFilter.append(-distr[0])

    gammaFilter.reverse()

    # Then the weights for the positive days ( x > 0 )
    distr = quad(lambda x: gdst.pdf(x), 0, delta/2)
    intFrom = delta/2
    gammaFilter[-1] = gammaFilter[-1] + distr[0]

    while distr[0] > 0.05:
        distr = quad(lambda x: gdst.pdf(x), intFrom, intFrom+delta)
        intFrom = intFrom + delta
        gammaFilter.append(distr[0])

    # And then I devide the list by the wheight for day = 0 thus weighing it to 1
    gammaFilterNorm = [x/max(gammaFilter)*hardness for x in gammaFilter]

    return gammaFilterNorm


# Needs commenst
def just_gamma_smoothing(*args):

    # Get the gamma "smoothing" filter
    if len(args) == 1:
        print('need inputarguments')
        #gammaFilter = __getGammafilter(5., 1., 1.5, 0.5)
    elif len(args) == 2:
        p = args[1]
        gammaFilter = __getGammafilter(p[0], p[1], p[2], p[3])

    listInn = args[0]

    # add padding to the listInn so that it does ont go out of bound while appling the filtre.
    # Padding will be removed before return
    indexOfD0 = [i for i,x in enumerate(gammaFilter) if x == max(gammaFilter)][0]
    daysAfterD0 = len(gammaFilter)-indexOfD0-1

    paddingPrior = [0.] * indexOfD0
    paddingAfter = [0.] * daysAfterD0
    listInn = paddingPrior + listInn + paddingAfter

    # a temporary empty list to apply the filtering
    listOut = [0.]*len(listInn)

    # Loop through the cloudsInn list and if there is precipitation apply the filter on days prior and after
    for i in range(indexOfD0, len(listInn)-daysAfterD0, 1):
        for j in range(0, len(gammaFilter), 1):
            listOut[i+j-indexOfD0] = listOut[i+j-indexOfD0] + gammaFilter[j] * listInn[i]

    # Cut of padding and return.
    listOut = listOut[indexOfD0:len(listOut)-daysAfterD0]

    return listOut


# Needs coments
def old_ccFromTempAndPrec(temp, prec):
    """

    :param temp:
    :param prec:
    :return:
    """

    # Calibratable sizes
    delta = 5                       # half the no of days in range. range = [-delta, delta]
    theshForMaxCcRange = 5          # threshhold for the use of a croppped max out range
    croppedCCRange = 0.5            # if not max cc range than this range.

    # Variables in the calculations
    ccList = []
    ccOutput = []

    # First we need to make som cloudcover estimates on partranges
    for i in range(5, len(temp)-delta, 1):

        cc = [ None ] * len(temp)   # reinitialize cc as close to an empty array I get with length of temp list
        ccRange = 1.                # reinitialize with the cloudcoverrange maxed out to 100%
        tmax = temp[i-delta]
        tmin = temp[i-delta]

        lowerLim = int(i - delta)
        upperLim = int(i + delta)
        totalSnow = float(sum(prec[lowerLim: upperLim]))

        # first looping to determine cc potential
        for j in range(lowerLim, upperLim, 1):

            ns = float(prec[j])
            t = float(temp[j])

            # if i have a snow event in the range
            if float(totalSnow) != 0.0:
                # if we have a snowevent tempraturerange ends (tmax) where temp is coldest (lowest) on a snow event
                if ns > 0.:
                    if t > tmax:
                        tmax = t
                # there is no snowevent an i look for the coldest day an assume it has lowes ccme this is a clear day
                else:
                    if t < tmin:
                        tmin = t
            # no snowevent in range
            else:
                # i assume the coldest day has least cc and the warmest highesy
                if t > tmax:
                    tmax = t
                if t < tmin:
                    tmin = t

        # If I have no snow event to link to 100% CC the ccRange will be smaller/cropped
        if (tmax - tmin) < theshForMaxCcRange:
            ccRange = croppedCCRange

        # second looping to set the cc to days in range
        for j in range(lowerLim, upperLim, 1):

            # If snowevent we have 100% cc
            if prec[j] > 0:
                cc[j] = 1.
            # or if the temperature is warmer on no snow events set None since I dont have a good solution foir this case..
            elif (tmax - tmin) <= 0:
                cc[j] = None
            # or if the outside temp is warmer than during snowevents we have 100% cc
            elif temp[j] > tmax:
                cc[j] = 1.
            else:
                deltaCCprUnitTemp = ccRange/(tmax - tmin)
                # first part of the equation is different from zero if a cropped CC range is used
                # Eg: With the cropped range of 50% the cc goes to 75% on wearmest days and 25% on coldest
                cc[j] = (1-ccRange)/2 + (temp[j]-tmin) * deltaCCprUnitTemp

        ccList.append(cc)

    # Average all values in the ccList to one list of length same as temp
    for i in range(0, len(temp), 1):

        # initialize/reinitialize
        avgCC = 0
        totCC = 0

        # look on one column (values with same date)
        for j in range(0, len(ccList), 1):

            if ccList[j][i] != None:
                avgCC = avgCC + ccList[j][i]
                totCC = totCC + 1

        # append the average
        if totCC != 0:
            ccOutput.append(avgCC/totCC)
        else:
            ccOutput.append(None)           # should never happen

    # Cant have values of None..
    for i in range(0, len(temp), 1):
        if ccOutput[i] == None:
            ccOutput[i] = 0.

    return ccOutput


# Needs comments
def cc_gamma_temp_change(*args):
    '''Makes a cloud cover from a list of temperature change where a gamma filter has been applied.


    Args[0] is the temperature change
    Args[1] is the configurations og the gamma smoothing. Eg. gammaTemp = [4.8, 1., 5., 0.03]

    :param args:
    :return:

    '''


    dtemp = args[0]
    gammaTemp = args[1]
    dTemp_abs = map(abs, dtemp)

    cloudsOut = just_gamma_smoothing(dTemp_abs, gammaTemp)

    cloudsOut_cropped = []
    for clo in cloudsOut:
        if clo > 1.:
            cloudsOut_cropped.append(1.)
        elif clo < 0.:
            cloudsOut_cropped.append(0.)
        else:
            cloudsOut_cropped.append(clo)

    return cloudsOut_cropped


# needs comments
def cc_gamma_temp(*args):

    temp = args[0]

    # make array of tempchnge from yesterday to today
    dtemp = pz.delta_temperature_from_temperature(temp)

    return cc_gamma_temp_change(dtemp, args[1])


# Needs comments
def cc_gamma_smoothing(*args):
    """Same as just_gamma_smoothing but since were talking about clouds values below 0% is set to 0% and
    values over 100% are set to 100%"""

    cloudsOut = just_gamma_smoothing(args[0], args[1])

    cloudsOut_cropped = []
    for clo in cloudsOut:
        if clo > 1.:
            cloudsOut_cropped.append(1.)
        elif clo < 0.:
            cloudsOut_cropped.append(0.)
        else:
            cloudsOut_cropped.append(clo)

    return cloudsOut_cropped


# Needs comments
def cc_gamma_prec_and_temp_change(*args):

    if len(args) == 2:
        ccPrec = pz.clouds_from_precipitation(args[0], method='Binary')
        ccPrec = cc_gamma_smoothing(ccPrec)
        ccTemp = cc_gamma_temp(args[1])
    elif len(args) == 4:
        ccPrec = pz.clouds_from_precipitation(args[0], method='Binary')
        ccPrec = cc_gamma_smoothing(ccPrec, args[2])
        ccTemp = cc_gamma_temp(args[1], args[3])
    else:
        print("Wrong input. Method takes 2 or 4 arguments.")

    cc = []
    for i in range(0, len(ccPrec), 1):
        cc.append(ccPrec[i] + ccTemp[i])
        if cc[i] > 1.:
            cc[i] = 1.

    return cc


if __name__ == "__main__":

    # ccFromPrec2(0)

    a = 1