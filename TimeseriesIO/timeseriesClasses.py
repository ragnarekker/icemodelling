__author__ = 'raek'
# -*- coding: utf-8 -*-

import datetime

def stripMetadata(weatherElementList, getDates):
    """
    Method takes inn a list of weatherElement objects and strips away all metadata. A list of values is returned and if
    getDate = True a corresponding list of dates is also retuned.

    :param weatherElementList [list of weatherElements]:    List of elements of class weatherElement
    :param getDates [bool]:         if True dateList is returned
    :return valueList, dateList:    dateList is otional and is returned if getDates is True.
    """

    if getDates == True:

        valueList = []
        dateList = []

        for e in weatherElementList:
            valueList.append(e.Value)
            dateList.append(e.Date)

        return valueList, dateList

    else:

        valueList = []

        for e in weatherElementList:
            valueList.append(e.Value)

        return valueList

def okta2unit(cloudCoverInOktaList):
    """
    Cloudcover from met.no is given in units of okta. Numbers 1-8. This method converts that list to values of units
    ranging from 0 to 1 where 1 is totaly overcast.

    NOTE: this conversion is also done in the weatherelelmnt class

    :param cloudCoverInOktaList:    cloudcover in okta stored in a list of weatherElements
    :return:                        cloudcover in units stored in a list of weatherElements
    """

    cloudCoverInUnitsList = []

    for we in cloudCoverInOktaList:
        if we.Value == 9:
            we.Value = None
        else:
            we.Value = we.Value/8

        we.Metadata.append({'Converted':'from okta to unit'})
        cloudCoverInUnitsList.append(we)

    return cloudCoverInUnitsList

def makeDailyAvarage(weatherElementList):
    """
    Takes a list of weatherelements with resolution less that 24hrs and calculates the dayly avarage
    of the timeseries.

    Tested on 30min periods and 1hr periods

    :param weatherElementList:      list of weatherelements with period < 24hrs
    :return newWeatherElementList:  list of weatherEleemnts averaged to 24hrs

    """

    # Sort list by date. Should not be neccesary but cant hurt.
    weatherElementList = sorted(weatherElementList, key=lambda weatherElement: weatherElement.Date)

    # Initialization
    date = weatherElementList[0].Date.date()
    value = weatherElementList[0].Value
    counter = 1
    lastindex = int(len(weatherElementList)-1)
    index = 0
    newWeatherElementList = []

    # go through all the elements and calculate the avarage of values with the same date
    for e in weatherElementList:

        # If on the same date keep on adding else add the avarage value and reinitialize counters on the new date
        if date == e.Date.date():
            value = value + e.Value
            counter = counter + 1

        else:

            # Make a datetime from the date
            datetimeFromDate = datetime.datetime.combine(date, datetime.datetime.min.time())

            # Make a new weatherelement and inherit relvant data from the old one
            newWeatherElement = weatherElement(e.LocationID, datetimeFromDate, e.ElementID, value/counter)
            newWeatherElement.Metadata = e.Metadata
            newWeatherElement.Metadata.append({'DataManipulation':'24H Average from {0} values'.format(counter)})

            # Append it
            newWeatherElementList.append(newWeatherElement)

            date = e.Date.date()
            value = e.Value
            counter = 1

        # If its the last index add whats averaged so far
        if index == lastindex:

                # Make a datetime from the date
                datetimeFromDate = datetime.datetime.combine(date, datetime.datetime.min.time())

                # Make a new weatherelement and inherit relvant data from the old one
                newWeatherElement = weatherElement(e.LocationID, datetimeFromDate, e.ElementID, value/counter)
                newWeatherElement.Metadata = e.Metadata
                newWeatherElement.Metadata.append({'DataManipulation':'24H Average from {0} values'.format(counter)})

                # Append it
                newWeatherElementList.append(newWeatherElement)

        index = index + 1

    return newWeatherElementList

def avarageValue(weatherElementList, lowerIndex, upperIndex):
    """
    The method will return the avarage value of a list or part of a list with weatherElements

    :param weatherElementList:  List of weatherElements
    :param lowerIndex:          Start summing from this index (0 is first listindex)
    :param upperIndex:          Stop summing from this index (-1 is last index)

    :return: avgToReturn:       The avarage value [float]

    """

    avgToReturn = 0

    for i in range(lowerIndex, upperIndex, 1):
        avgToReturn = avgToReturn + weatherElementList[i].Value

    avgToReturn = avgToReturn/(upperIndex-lowerIndex)

    return avgToReturn

class weatherElement():

    '''
    A weatherElement object as they are defined in eKlima. The variables are:

    LocationID:     The location number. Preferably a int, but for NVE stations it may be a sting.
    Date:           Datetime object of the date of the weather element.
    ElementID:      The element ID. TAM og SA for met but may be numbers from NVE.
    Value:          The value of the veatherelement. Preferably in SI units.

    Secial cases:
    ElementID = SA: Snødybde, totalt fra bakken, måles normalt på morgenen. Kode = -1 betyr snøbart, presenteres
                    som ".", -3 = "umulig å måle". This variable is also calulated from [cm] to [m]
    ElementID = RR: Precipitations has -1 for what seems to be noe precipitation. Are removed.
    ElementID = NNM:Average cloudcover that day (07-07). Comes from met.no in okta.

    '''

    def __init__(self, elementLocationID, elementDate, elementID, elementValue):

        self.LocationID = elementLocationID
        self.Date = elementDate
        self.ElementID = elementID
        self.Value = float(elementValue)
        self.Metadata = [{'OriginalValue':self.Value}]

        # Snow is different
        if elementID == 'SA':
            if elementValue < 0.:
                self.Value = 0.
            else:
                self.Value = elementValue/100.

        # Rain seems to have a special treatment aswell
        if elementID == 'RR':
            if elementValue < 0.:
                self.Value = 0.
                self.Metadata.append({'On import':'removed negative value'})
            else:
                self.Value = elementValue

        # Clouds come in octas and should be in units (ranging from 0 to 1) for further use
        if elementID == 'NNM':
            if elementValue == 9.:
                self.Value = None
            else:
                self.Value = self.Value/8.

            self.Metadata.append({'Converted':'from okta to unit'})


        # datacorrections. I found errors in data Im using from met
        if (self.Date).date() == datetime.date(2012, 02, 02) and self.ElementID == 'SA' and self.LocationID == 19710 and self.Value == 0.:
            self.Value = 0.45
            self.Metadata.append({"ManualValue":self.Value})

        if (self.Date).date() == datetime.date(2012, 03, 18) and self.ElementID == 'SA' and self.LocationID == 54710 and self.Value == 0.:
            self.Value = 0.89
            self.Metadata.append({"ManualValue":self.Value})

        if (self.Date).date() == datetime.date(2012, 12, 31) and self.ElementID == 'SA' and self.LocationID == 54710 and self.Value == 0.:
            self.Value = 0.36
            self.Metadata.append({"ManualValue":self.Value})
