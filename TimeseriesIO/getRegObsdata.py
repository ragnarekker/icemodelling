__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import requests
import datetime
from Calculations import parameterization

apiVersion = "v0.9.4"


class iceCover:

    date = 0
    iceCoverTID = 0
    iceCoverName = 0

    def __init__(self, date_inn, iceCoverName_inn):
        self.date = date_inn
        self.iceCoverName = iceCoverName_inn
        self.iceCoverTID = getTIDfromName('IceCoverKDV', 1, iceCoverName_inn)

def __removeNorwegianLetters(nameInn):

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

    name = nameInn
    if u'ae' in name:
        name = name.replace(u'ae', 'æ'.decode('utf8', 'ignore'))
    if u'oe' in name:
        name = name.replace(u'oe', 'ø'.decode('utf8', 'ignore'))
    if u'aa' in name:
        name = name.replace(u'aa', 'å'.decode('utf8', 'ignore'))

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

    oDataQuery = "DtObsTime gt datetime'{0}' and " \
                 "DtObsTime lt datetime'{1}' and " \
                 "LocationName eq '{2}' and " \
                 "LangKey eq 1".format(fromDate, toDate, LocationName)

    # get data for current view and dates
    url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}&$format=json".decode('utf8').format(apiVersion, oDataQuery, view)
    data = requests.get(url).json()
    datalist = data['d']['results']

    iceCoverList = []
    for ic in datalist:
        iceCoverDate = parameterization.unixTime2Normal(int(ic['DtObsTime'][6:-2]))
        iceCoverName = ic['IceCoverName']
        iceCoverList.append(iceCover(iceCoverDate, iceCoverName))

    return iceCoverList

def getFirst():
    return


def getTIDfromName(xKDV, LangKeyTID, name):
    url = 'http://api.nve.no/hydrology/regobs/{1}/OData.svc/{0}?$filter=Langkey%20eq%20{2}%20&$format=json'.format(xKDV, apiVersion, LangKeyTID)
    xKDV = getKDV(url)

    TID = 0

    for xTID, xName in xKDV.iteritems():
        if xName == __removeNorwegianLetters(name):
            TID = xTID

    return TID

def getKDV(url):
    '''
    Imports a xKDV view from regObs and returns a dictionary with <key, value> = <ID, Name>
    :param url:
    :return:
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
    fromDate = '2013-11-01'
    toDate = '2014-06-01'

    a = getIceCover(LocationName, fromDate, toDate)

    b = 1