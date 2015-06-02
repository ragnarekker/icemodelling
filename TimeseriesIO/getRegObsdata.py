__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import requests
import datetime
from Calculations import parameterization
import IceCover as COV
import IceColumn as COL
import types

apiVersion = "v0.9.9"

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
    Method returns a list of IceCover objects from regObs between fromDate to toDate.

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:

    http://api.nve.no/hydrology/regobs/v0.9.4/Odata.svc/IceCoverObsV?$filter=
    DtObsTime%20gt%20datetime%272013-11-01%27%20and%20
    DtObsTime%20lt%20datetime%272014-06-01%27%20and%20
    LocationName%20eq%20%27Hakkloa%20nord%20372%20moh%27%20and%20
    LangKey%20eq%201

    """

    iceCoverList = []

    if isinstance(LocationName, types.ListType):
        for l in LocationName:
            iceCoverList = iceCoverList + getIceCover(l, fromDate, toDate)

    else:
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


        for ic in datalist:
            iceCoverDate = parameterization.unixTime2Normal(int(ic['DtObsTime'][6:-2]))
            iceCoverName = ic['IceCoverName']
            iceCoverBefore = ic['IceCoverBeforeName']
            cover = COV.IceCover(iceCoverDate, iceCoverName, iceCoverBefore, LocationName)
            cover.set_regid(int(ic['RegID']))
            iceCoverList.append(cover)

    return iceCoverList

def getFirstIceCover(LocationName, fromDate, toDate):
    '''
    Returns the first observation where ice can form on a lake. That is if the ice cover is partly or fully
    formed on observation location or the lake.

    If no such obervation is found an "empty" icecover is returned at fromDate.

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    iceCoverSeason = getIceCover(LocationName, fromDate, toDate)
    iceCoverSeason.sort(key=lambda IceCover: IceCover.date) # start looking at the oldest observations

    for ic in iceCoverSeason:
        # if the ice cover is partly or fully formed on observation location or the lake
        # 2) delvis islagt på målestedet
        # 3) helt islagt på målestedet
        # 21) hele sjøen islagt
        if (ic.iceCoverTID == 2) or (ic.iceCoverTID == 3) or (ic.iceCoverTID == 21):
            # and if icecover before was
            # 1) isfritt på målestedet
            # 2) delvis islagt på målestedet,
            # 11) islegging langs land
            # 20) hele sjøen isfri,  this is fist ice
            if (ic.iceCoverBeforeTID == 1) or (ic.iceCoverBeforeTID == 2) or \
                    (ic.iceCoverBeforeTID == 11) or (ic.iceCoverBeforeTID == 20):
                return ic

    # datetime objects in icecover datatype
    from_date = datetime.datetime.strptime(fromDate, "%Y-%m-%d")

    return COV.IceCover(from_date, "Ikke gitt", 'Ikke gitt', LocationName)

def getLastIceCover(LocationName, fromDate, toDate):
    '''
    Method gives the observation confirming ice is gone for the season from a lake.
    It finds the first observation without ice after an observation(s) with ice.
    If none is found, an "empty" icecover object is retuned on the last date in the period.
    Method works best when dates range over hole seasons.

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    iceCoverSeason = getIceCover(LocationName, fromDate, toDate)
    iceCoverSeason.sort(key=lambda IceCover: IceCover.date, reverse=True) # start looking at newest observations

    # datetime objects in ice cover data type
    to_date = datetime.datetime.strptime(toDate, "%Y-%m-%d")

    # make "empty" ice cover object on last date. If there is no ice cover observation confirming that ice has gone,
    # this wil be returned.
    noIceCover = COV.IceCover(to_date, "Ikke gitt", 'Ikke gitt', LocationName)

    for ic in iceCoverSeason:
        # if "Isfritt på målestedet" (TID=1) or "Hele sjøen isfri" (TID=20). That is, if we have an older "no icecover" case
        if (ic.iceCoverTID == 1) or (ic.iceCoverTID == 20):
            noIceCover = ic
        # if "Delvis islagt på målestedet" (TID=2) or "Helt islagt på målestedet" (TID=3) or "Hele sjøen islagt" (TID=21)
        if (ic.iceCoverTID == 2) or (ic.iceCoverTID == 3) or (ic.iceCoverTID == 21):
            return noIceCover   # we have confirmed ice on the lake so we return the no ice cover observation

    return noIceCover

def getIceThickness(LocationName, fromDate, toDate):
    '''
    Method returns a list of ice thickness between two dates for a given location in regObs.

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    ice_columns = []

    if isinstance(LocationName, types.ListType):
        for l in LocationName:
            ice_columns = ice_columns + getIceThickness(l, fromDate, toDate)
    else:
        view = 'IceThicknessV'
        OdataLocationName = __changeUnicodeToUTF8Hex(LocationName)  # Crazyshitencoding

        oDataQuery = "DtObsTime gt datetime'{0}' and " \
                     "DtObsTime lt datetime'{1}' and " \
                     "LocationName eq '{2}' and " \
                     "LangKey eq 1".format(fromDate, toDate, OdataLocationName)

        # get data for current view and dates
        url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}&$format=json".decode('utf8').format(apiVersion, oDataQuery, view)
        data = requests.get(url).json()
        datalist = data['d']['results']

        for ic in datalist:
            date = parameterization.unixTime2Normal(int(ic['DtObsTime'][6:-2]))
            RegID = ic['RegID']
            layers = __IceThicknessLayers(RegID)
            if len(layers) == 0:
                layers = [[float(ic['IceThicknessSum']), 'unknown']]

            ice_column = COL.IceColumn(date, layers)
            ice_column.add_metadata('RegID', RegID)
            ice_column.add_metadata('LocatonName', LocationName)

            ice_column.addLayerAtIndex(0, ic['SlushSnow'], 'slush')
            ice_column.addLayerAtIndex(0, ic['SnowDepth'], 'snow')
            ice_column.updateDraftHeight()
            iha = ic['IceHeightAfter']
            if iha == None:
                iha = 0
            ice_column.water_line = ice_column.draft_height - float(iha)

            ice_columns.append(ice_column)

    return ice_columns

def getAllSeasonIce(LocationName, fromDate, toDate):
    '''
    This returns a list of all ice columns in a period from fromDate to toDate. At index 0 is first ice (date with no
    ice layers) and on last index (-1) is last ice which is the date where there is no more ice on the lake.

    If no first or last ice is found in regObs the first or/and last dates in the request is used for initial and
    end of ice cover season,

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    first = getFirstIceCover(LocationName, fromDate, toDate)
    last = getLastIceCover(LocationName, fromDate, toDate)

    start_column = []
    end_column = []

    fc = COL.IceColumn(first.date, 0)
    fc.add_metadata('RegID', first.RegID)
    start_column.append(fc)

    lc = COL.IceColumn(last.date, 0)
    lc.add_metadata('RegID', first.RegID)
    end_column.append(lc)

    columns = getIceThickness(LocationName, fromDate, toDate)

    all_columns = start_column + columns + end_column

    return all_columns


def __IceThicknessLayers(RegID):
    '''
    This method returns the ice layes of a given registration (RegID) in regObs. it reads only what is below the first
    solid ice layer. Thus snow and slush on the ice is not covered here and is added separately in the public method
    for retrieving the full ice column.

    This method is an internal method for getRegObdata.py

    :param RegID:
    :return:

    Example og a ice layer object in regObs:
    http://api.nve.no/hydrology/regobs/v0.9.5/Odata.svc/IceThicknessLayerV?$filter=RegID%20eq%2034801%20and%20LangKey%20eq%201&$format=json

    '''

    view = 'IceThicknessLayerV'

    url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{1}?" \
          "$filter=RegID eq {2} and LangKey eq 1&$format=json"\
        .format(apiVersion, view, RegID)
    data = requests.get(url).json()
    datalist = data['d']['results']

    layers = []

    for l in datalist:

        regobs_layer_name = l['IceLayerName']
        layer_type = getTIDfromName('IceLayerKDV', 1, regobs_layer_name)
        layer_name = __get_ice_type(layer_type)

        thickness = l['IceLayerThickness']
        layer = [float(thickness), layer_name]
        layers.append(layer)

    # Black ice at bottom
    reversed_layers = []
    for l in layers:
        reversed_layers.append(l)

    return reversed_layers

def __get_ice_type(IceLayerTID):
    '''
    Method returns a ice type available in the IceColumn class given the regObs type IceLayerTID

    :param IceLayerTID:
    :return:

    List of layertypes availabel in regObs:
    http://api.nve.no/hydrology/regobs/v0.9.4/OData.svc/IceLayerKDV?$filter=Langkey%20eq%201%20&$format=json

    '''
    #
    if IceLayerTID == 1:
        return 'black_ice'
    elif IceLayerTID == 3:
        return 'slush_ice'
    elif IceLayerTID == 5:
        return 'slush'
    elif IceLayerTID == 11:     # 'Stålis i nedbrytning' in regObs
        return 'black_ice'
    elif IceLayerTID == 13:     # 'Sørpeis i nedbrytning' in regObs
        return 'slush_ice'
    elif IceLayerTID == 14:     # 'Stavis (våris)' in regObs
        return 'slush_ice'
    else:
        return 'Unknown type {0}'.format(IceLayerTID)


def getTIDfromName(xKDV, LangKeyTID, name):
    '''

    :param xKDV:
    :param LangKeyTID:
    :param name:
    :return:
    '''
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

    LocationName1 = 'Hakkloa nord 372 moh'
    LocationName2 = 'Otrøvatnet v/Nystuen 971 moh'
    LocationName3 = 'Semsvannet v/Lo 145 moh'

    LocationNames = [LocationName1, LocationName2, LocationName3]
    fromDate = '2012-10-01'
    toDate = '2013-07-01'

    #IceCoverKDV = getKDV('http://api.nve.no/hydrology/regobs/v0.9.4/OData.svc/IceCoverKDV?$filter=Langkey%20eq%201%20&$format=json')
    #IceCoverBeforeKDV = getKDV('http://api.nve.no/hydrology/regobs/v0.9.4/OData.svc/IceCoverKDV?$filter=Langkey%20eq%201%20&$format=json')
    #ic = getIceCover(LocationNames, fromDate, toDate)
    #first = getFirstIceCover(LocationNames, fromDate, toDate)
    #last = getLastIceCover(LocationNames, fromDate, toDate)
    #ith = getIceThickness(LocationNames, fromDate, toDate)
    all = getAllSeasonIce(LocationNames, fromDate, toDate)

    b = 1