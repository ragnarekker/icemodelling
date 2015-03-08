__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import requests
import datetime
from Calculations import parameterization
from IceCover import *

apiVersion = "v0.9.4"



def __removeNorwegianLetters(nameInn):
    """

    :param nameInn:
    :return:
    """
    name = nameInn
    if u'å' in name:
        name = name.replace(u'å', 'aa').encode('ascii', 'ignore')
    elif u'ø' in name:
        name = name.replace(u'ø', 'oe').encode('ascii', 'ignore')
    elif u'æ' in name:
        name = name.replace(u'æ', 'ae').encode('ascii', 'ignore')
    else:
        name = name.encode('ascii', 'ignore')
    return name

def __addNorwegianLetters(nameInn):
    """

    :param nameInn:
    :return:
    """

    name = nameInn
    if u'ae' in name:
        name = name.replace(u'ae', 'æ'.decode('utf8', 'ignore'))
    if u'oe' in name:
        name = name.replace(u'oe', 'ø'.decode('utf8', 'ignore'))
    if u'aa' in name:
        name = name.replace(u'aa', 'å'.decode('utf8', 'ignore'))

    return name

def __changeUnicodeToUTF8Hex(nameInn):
    """

    :param nameInn:
    :return:
    """

    name = nameInn
    if 'å' in name:
        name = name.replace('å', '%C3%A5').encode('ascii', 'ignore')
    elif 'ø' in name:
        name = name.replace('ø', '%C3%B8').encode('ascii', 'ignore')
    elif 'æ' in name:
        name = name.replace('æ', '%C3%A6').encode('ascii', 'ignore')
    elif 'Å' in name:
        name = name.replace('Å', '%C3%85').encode('ascii', 'ignore')
    elif 'Ø' in name:
        name = name.replace('Ø', '%C3%98').encode('ascii', 'ignore')
    elif 'Æ' in name:
        name = name.replace('Æ', '%C3%86').encode('ascii', 'ignore')
    else:
        name = name.encode('ascii', 'ignore')
    return name


def getIceCover(LocationName, fromDate, toDate):
    """

    :param LocationName:
    :param fromDate:        The from date as string 'YYYY-MM-DD'
    :param toDate:          The to date as string 'YYYY-MM-DD'
    :return:
    """

    # http://api.nve.no/hydrology/regobs/v0.9.4/Odata.svc/IceCoverObsV?$filter=
    # DtObsTime%20gt%20datetime%272013-11-01%27%20and%20
    # DtObsTime%20lt%20datetime%272014-06-01%27%20and%20
    # LocationName%20eq%20%27Hakkloa%20nord%20372%20moh%27%20and%20
    # LangKey%20eq%201

    view = 'IceCoverObsV'
    OdataLocationName = __changeUnicodeToUTF8Hex(LocationName)


    oDataQuery = "DtObsTime gt datetime'{0}' and " \
                 "DtObsTime lt datetime'{1}' and " \
                 "LocationName eq '{2}' and " \
                 "LangKey eq 1".format(fromDate, toDate, OdataLocationName)

    # get data for current view and dates
    url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}&$format=json".decode('utf8').format(apiVersion, oDataQuery, view)
    data = requests.get(url).json()
    datalist = data['d']['results']

    iceCoverList = []
    for ic in datalist:
        iceCoverDate = parameterization.unixTime2Normal(int(ic['DtObsTime'][6:-2]))
        iceCoverName = ic['IceCoverName']
        iceCoverBefore = ic['IceCoverBeforeName']
        iceCoverList.append(IceCover(iceCoverDate, iceCoverName, iceCoverBefore, LocationName))

    return iceCoverList

def getFirstIceCover(LocationName, fromDate, toDate, *args):
    '''
    :param LocationName:
    :param fromDate:
    :param toDate:
    :param returnType:

    :return:
    '''

    returnType = 'IceCover'

    if len(args) == 1:
        returnType = args[0]

    iceCoverSeason = getIceCover(LocationName, fromDate, toDate)

    for ic in iceCoverSeason:
        if (ic.iceCoverTID == 2) or (ic.iceCoverTID == 3) or (ic.iceCoverTID == 21):
            return ic

    return IceCover(fromDate, "Ikke gitt", 'Ikke gitt', LocationName)

def getLastIceCover(LocationName, fromDate, toDate, *args):
    '''

    :param LocationName:
    :param fromDate:
    :param toDate:
    :param args:
    :return:
    '''

    returnType = 'IceCover'

    if len(args) == 1:
        returnType = args[0]

    iceCoverSeason = getIceCover(LocationName, fromDate, toDate)
    iceCoverSeason = reversed(iceCoverSeason)

    noIceCover = IceCover(toDate, "Ikke gitt", 'Ikke gitt', LocationName)

    for ic in iceCoverSeason:
        if (ic.iceCoverTID == 1) or (ic.iceCoverTID == 20):
            noIceCover = ic
        if (ic.iceCoverTID == 2) or (ic.iceCoverTID == 3) or (ic.iceCoverTID == 21):
            return noIceCover

    return noIceCover


def getIceThickness():

    view = 'IceThicknessV'
    OdataLocationName = __changeUnicodeToUTF8Hex(LocationName)

    oDataQuery = "DtObsTime gt datetime'{0}' and " \
                 "DtObsTime lt datetime'{1}' and " \
                 "LocationName eq '{2}' and " \
                 "LangKey eq 1".format(fromDate, toDate, OdataLocationName)

    # get data for current view and dates
    url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}&$format=json".decode('utf8').format(apiVersion, oDataQuery, view)
    data = requests.get(url).json()
    datalist = data['d']['results']
    a = 1





def getTIDfromName(xKDV, LangKeyTID, name):
    url = 'http://api.nve.no/hydrology/regobs/{1}/OData.svc/{0}?$filter=Langkey%20eq%20{2}%20&$format=json'.format(xKDV, apiVersion, LangKeyTID)
    xKDV = getKDV(url)

    TID = -1

    for xTID, xName in xKDV.iteritems():
        if xName == __removeNorwegianLetters(name):
            TID = xTID

    return TID

def getKDV(url):
    '''
    Imports a xKDV view from regObs and returns a dictionary with <key, value> = <ID, Name>
    :param url:
    :return:

    Eg: 'http://api.nve.no/hydrology/regobs/v0.9.4/OData.svc/IceCoverKDV?$filter=Langkey%20eq%201%20&$format=json'
    returns values for IceCoverKDV in norwegian.
    '''


    # print("Getting KDV from URL:{0}".format(url))

    xKDV = requests.get(url).json()
    xDict = {}
    for a in xKDV['d']['results']:
        try:
            if 'AvalCauseKDV' in url and a['ID'] > 9 and a['ID'] < 25:      # this table gets special treatment
                xDict[a["ID"]] = __removeNorwegianLetters(a["Description"])
            else:
                xDict[a["ID"]] = __removeNorwegianLetters(a["Name"])
        except (RuntimeError, TypeError, NameError):
            pass

    return xDict



if __name__ == "__main__":

    LocationName = 'Hakkloa nord 372 moh'
    LocationName = 'Otrøvatnet v/Nystuen 971 moh'
    fromDate = '2013-10-01'
    toDate = '2014-07-01'

    IceCoverKDV = getKDV('http://api.nve.no/hydrology/regobs/v0.9.4/OData.svc/IceCoverKDV?$filter=Langkey%20eq%201%20&$format=json')
    IceCoverBeforeKDV = getKDV('http://api.nve.no/hydrology/regobs/v0.9.4/OData.svc/IceCoverKDV?$filter=Langkey%20eq%201%20&$format=json')
    ic = getIceCover(LocationName, fromDate, toDate)
    first = getFirstIceCover(LocationName, fromDate, toDate, 'IceColumn')
    last = getLastIceCover(LocationName, fromDate, toDate)

    ith = getIceThickness()

    b = 1