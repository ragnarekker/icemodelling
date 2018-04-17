import datetime as dt
import requests
import os as os
import copy as cp

from icemodelling import ice as ice
from icemodelling import makepickle as mp
from icemodelling import constants as const
from icemodelling import doconversions as dc
from icemodelling import setenvironment as se
from icemodelling import makelogs as ml
import pandas as pd

__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-


def get_obs_location(LocationName):
    """

    :param LocationName:
    :return:
    """

    oDataQuery = "{0}".format(LocationName)

    # get data for current view and dates
    url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/ObsLocation/?$filter=LocationName eq '{1}'&$format=json"\
        .format(se.odata_api_version, oDataQuery)
    data = requests.get(url).json()
    data_dict = data['d']['results'][0]

    return data_dict


def get_ice_cover(LocationName, fromDate, toDate):
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

    if isinstance(LocationName, list):
        for l in LocationName:
            iceCoverList = iceCoverList + get_ice_cover(l, fromDate, toDate)

    else:
        view = 'IceCoverObsV'
        OdataLocationName = LocationName

        oDataQuery = "DtObsTime gt datetime'{0}' and " \
                     "DtObsTime lt datetime'{1}' and " \
                     "LocationName eq '{2}' and " \
                     "LangKey eq 1".format(fromDate, toDate, OdataLocationName)

        # get data for current view and dates
        url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}&$format=json".format(se.odata_api_version, oDataQuery, view)
        data = requests.get(url).json()
        datalist = data['d']['results']

        for ic in datalist:
            iceCoverDate = dc.unix_time_2_normal(ic['DtObsTime'])
            iceCoverName = ic['IceCoverName']
            iceCoverBefore = ic['IceCoverBeforeName']
            cover = ice.IceCover(iceCoverDate, iceCoverName, iceCoverBefore, LocationName)
            cover.set_regid(ic['RegID'])
            cover.set_utm(ic['UTMNorth'], ic['UTMEast'], ic['UTMZone'])

            iceCoverList.append(cover)

    return iceCoverList


def get_first_ice_cover(LocationName, fromDate, toDate):
    '''Returns the first observation where ice can form on a lake. That is if the ice cover is partly or fully
    formed on observation location or the lake.

    If no such observation is found an "empty" ice cover is returned at fromDate.

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    iceCoverSeason = get_ice_cover(LocationName, fromDate, toDate)
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

    # datetime objects in IceCover datatype
    from_date = dt.datetime.strptime(fromDate, "%Y-%m-%d")

    return ice.IceCover(from_date, "Ikke gitt", 'Ikke gitt', LocationName)


def get_last_ice_cover(LocationName, fromDate, toDate):
    '''
    Method gives the observation confirming ice is gone for the season from a lake.
    It finds the first observation without ice after an observation(s) with ice.
    If none is found, an "empty" icecover object is returned on the last date in the period.
    Method works best when dates range over whole seasons.

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    iceCoverSeason = get_ice_cover(LocationName, fromDate, toDate)
    iceCoverSeason.sort(key=lambda IceCover: IceCover.date, reverse=True) # start looking at newest observations

    # datetime objects in ice cover data type
    to_date = dt.datetime.strptime(toDate, "%Y-%m-%d")

    # make "empty" ice cover object on last date. If there is no ice cover observation confirming that ice has gone,
    # this wil be returned.
    noIceCover = ice.IceCover(to_date, "Ikke gitt", 'Ikke gitt', LocationName)

    for ic in iceCoverSeason:
        # if "Isfritt på målestedet" (TID=1) or "Hele sjøen isfri" (TID=20). That is, if we have an older "no icecover" case
        if (ic.iceCoverTID == 1) or (ic.iceCoverTID == 20):
            noIceCover = ic
        # if "Delvis islagt på målestedet" (TID=2) or "Helt islagt på målestedet" (TID=3) or "Hele sjøen islagt" (TID=21)
        if (ic.iceCoverTID == 2) or (ic.iceCoverTID == 3) or (ic.iceCoverTID == 21):
            return noIceCover   # we have confirmed ice on the lake so we return the no ice cover observation

    return noIceCover


def get_ice_thickness_on_regid(regid):

    view = 'IceThicknessV'
    oDataQuery = "RegID eq {0} and " \
                 "LangKey eq 1".format(regid)

    # get data for current view and dates
    url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}&$format=json".format(se.odata_api_version,
                                                                                                 oDataQuery, view)
    data = requests.get(url).json()
    datalist = data['d']['results']

    #Only one ice column pr regid
    ice_column = _parse_ice_column(datalist[0])

    return ice_column


def get_ice_thickness_on_location(LocationName, fromDate, toDate):
    '''Method returns a list of ice thickness between two dates for a given location in regObs.

    :param LocationName:    [string/list] name as given in regObs in ObsLocation table. Multiploe locations posible
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    ice_columns = []

    if isinstance(LocationName, list):
        for l in LocationName:
            ice_columns = ice_columns + get_ice_thickness_on_location(l, fromDate, toDate)
    else:
        view = 'IceThicknessV'

        OdataLocationName = LocationName
        oDataQuery = "DtObsTime gt datetime'{0}' and " \
                     "DtObsTime lt datetime'{1}' and " \
                     "LocationName eq '{2}' and " \
                     "LangKey eq 1".format(fromDate, toDate, OdataLocationName)

        # get data for current view and dates
        url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}&$format=json".format(se.odata_api_version, oDataQuery, view)
        data = requests.get(url).json()
        datalist = data['d']['results']

        for ic in datalist:
            ice_column = _parse_ice_column(ic)

            if ice_column:
                ice_columns.append(ice_column)

    return ice_columns


def _parse_ice_column(ic):

    RegID = ic['RegID']
    layers = get_ice_thickness_layers(RegID)

    ice_column = None

    if layers is not None:
        date = dc.unix_time_2_normal(ic['DtObsTime'])

        if len(layers) == 0:
            layers = [ice.IceLayer(float(ic['IceThicknessSum']), 'unknown')]

        ice_column = ice.IceColumn(date, layers)
        ice_column.add_metadata('RegID', RegID)
        ice_column.add_metadata('LocationName', ic['LocationName'])
        ice_column.add_metadata('UTMNorth', ic['UTMNorth'])
        ice_column.add_metadata('UTMEast', ic['UTMEast'])
        ice_column.add_metadata('UTMZone', ic['UTMZone'])

        ice_column.add_layer_at_index(0, ice.IceLayer(ic['SlushSnow'], 'slush'))
        ice_column.add_layer_at_index(0, ice.IceLayer(ic['SnowDepth'], 'snow'))

        ice_column.merge_and_remove_excess_layers()
        ice_column.update_draft_thickness()
        ice_column.update_top_layer_is_slush()

        iha = ic['IceHeightAfter']

        # if ice height after is not given I make an estimate so that I know where to put it in the plot
        if iha is None:
            ice_column.update_water_line()
            ice_column.add_metadata('IceHeightAfter', 'Modeled')
            iha = ice_column.draft_thickness - ice_column.water_line
            if ice_column.top_layer_is_slush:
                iha = iha + const.snow_pull_on_water

        ice_column.water_line = ice_column.draft_thickness - float(iha)

        if ice_column.top_layer_is_slush is True:
            ice_column.water_line -= ice_column.column[0].height

    return ice_column


def get_all_season_ice_on_location(LocationNames, fromDate, toDate):
    '''Uses odata-api. This returns a list of all ice columns in a period from fromDate to toDate.
    At index 0 is first ice (date with no ice layers) and on last index (-1)
    is last ice which is the date where there is no more ice on the lake.

    If no first or last ice is found in regObs the first or/and last dates in the request is used for initial and
    end of ice cover season,

    :param LocationNames:    [string/list] name as given in regObs in ObsLocation table
    :param fromDate:        [string] The from date as 'YYYY-MM-DD'
    :param toDate:          [string] The to date as 'YYYY-MM-DD'
    :return:
    '''

    if not isinstance(LocationNames, list):
        LocationNames = [LocationNames]

    all_columns = []

    for LocationName in LocationNames:

        first = get_first_ice_cover(LocationName, fromDate, toDate)
        last = get_last_ice_cover(LocationName, fromDate, toDate)

        start_column = []
        end_column = []

        fc = ice.IceColumn(first.date, 0)
        fc.add_metadata('LocationName', first.locationName)
        fc.add_metadata('RegID', first.RegID)
        fc.add_metadata('UTMNorth', first.UTMNorth)
        fc.add_metadata('UTMEast', first.UTMEast)
        fc.add_metadata('UTMZone', first.UTMZone)
        start_column.append(fc)

        lc = ice.IceColumn(last.date, 0)
        lc.add_metadata('LocationName', last.locationName)
        lc.add_metadata('RegID', last.RegID)
        lc.add_metadata('UTMNorth', last.UTMNorth)
        lc.add_metadata('UTMEast', last.UTMEast)
        lc.add_metadata('UTMZone', last.UTMZone)
        end_column.append(lc)

        columns = get_ice_thickness_on_location(LocationName, fromDate, toDate)

        all_columns += (start_column + columns + end_column)

    return all_columns


def get_ice_thickness_layers(RegID):
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
        .format(se.odata_api_version, view, RegID)
    data = requests.get(url).json()
    datalist = data['d']['results']

    layers = []

    for l in datalist:

        thickness = l['IceLayerThickness']
        if thickness == None or float(thickness) == 0:
            ml.log_and_print('getregobsdata.py -> get_ice_thickness_layers: RegID {0} har icelayers of None thicness.'.format(RegID))
            # return empty list if some layers at zero or none.
            reversed_layers = []
            return reversed_layers

        else:
            regobs_layer_name = l['IceLayerName']
            layer_type = get_tid_from_name('IceLayerKDV', regobs_layer_name)
            layer_name = get_ice_type_from_tid(layer_type)

            layer = ice.IceLayer(float(thickness), layer_name)
            layers.append(layer)

    return layers


def get_ice_type_from_tid(IceLayerTID):
    '''Method returns a ice type available in the IceLayer class given the regObs type IceLayerTID.

    :param IceLayerTID:
    :return Ice type as string:

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
        return 'unknown'.format(IceLayerTID)


def get_tid_from_name(x_kdv, name):
    '''
    Gets a xTID for a given xName from a xKDV element in regObs. In other words, it gets the ID for a given name.

    :param x_kdv:
    :param name:
    :return tid:

    '''
    x_kdv = get_kdv(x_kdv)

    tid = -1

    for xTID, xName in x_kdv.items():
        if xName == name:
            tid = xTID

    return tid


def get_kdv(x_kdv, get_new=False):
    '''Imports a x_kdv view from regObs and returns a dictionary with <key, value> = <ID, Name>
    An x_kdv is requested from the regObs api if a pickle file newer than a week exists.

    :param x_kdv:   [string]    x_kdv view
    :return dict:   {}          x_kdv as a dictionary

    Ex of use: aval_cause_kdv = get_kdv('AvalCauseKDV')
    Ex of url for returning values for IceCoverKDV in norwegian:
    http://api.nve.no/hydrology/regobs/v0.9.4/OData.svc/ForecastRegionKDV?$filter=Langkey%20eq%201%20&$format=json
    '''

    kdv_file = '{0}{1}.pickle'.format(se.kdv_elements_folder, x_kdv)
    dict = {}

    if get_new:
        url = 'http://api.nve.no/hydrology/regobs/{0}/OData.svc/{1}?$filter=Langkey%20eq%201%20&$format=json'\
            .format(se.odata_api_version, x_kdv)

        ml.log_and_print("getregobsdata -> get_kdv: Getting KDV from URL:{0}".format(url))

        kdv = requests.get(url).json()

        for a in kdv['d']['results']:
            try:
                if 'AvalCauseKDV' in url and a['ID'] > 9 and a['ID'] < 26:      # this table gets special treatment
                    dict[a["ID"]] = a["Description"]
                else:
                    dict[a["ID"]] = a["Name"]
            except (RuntimeError, TypeError, NameError):
                pass

            mp.pickle_anything(dict, kdv_file)

    else:
        if os.path.exists(kdv_file):

            # Useful to test if the file is old and if so make a new one
            max_file_age = 7
            mtime = os.path.getmtime(kdv_file)
            last_modified_date = dt.datetime.fromtimestamp(mtime).date()
            date_limit = dt.datetime.now() - dt.timedelta(days=max_file_age)

            # If file older than date limit, request a new.
            if last_modified_date < date_limit.date():
                dict = get_kdv(x_kdv, get_new=True)
            else:
                # ml.log_and_print("getregobsdata -> get_kdv: Getting KDV from pickle:{0}".format(kdv_file))
                dict = mp.unpickle_anything(kdv_file, print_message=False)

        else:
            dict = get_kdv(x_kdv, get_new=True)

    return dict


# webapi


# START VARSOMDATA


def _stringtime_2_datetime(stringtime):
    """Takes in a date as string, both given as unix datetime or normal local time, as string.
    Method returns a normal datetime object.

    :param stringtime:
    :return:           The date as datetime object


    """

    if '/Date(' in stringtime:      # oData gives unix time. Unix date time in milliseconds from 1.1.1970
        unix_date_time = int(stringtime[6:-2])
        unix_datetime_in_seconds = unix_date_time/1000 # For some reason they are given in miliseconds
        date = dt.datetime.fromtimestamp(int(unix_datetime_in_seconds))

    else:                           # regobs api gives local time
        if '.' in stringtime:       # though sometimes with seconds given with decimal places
            non_decimal_stringtime = stringtime[0:stringtime.index('.')]
            stringtime = non_decimal_stringtime

        date = dt.datetime.strptime(stringtime, '%Y-%m-%dT%H:%M:%S')
        ### DOES REGOBS API RETURN UT TIME??? ###

    return date


def _make_data_frame(list):
    """Takes a list of objects and makes a Pandas data frame.

    :param list: [list of objects]
    :return:     [data frame]
    """

    if len(list) == 0:
        data_frame = pd.DataFrame()
    else:
        observation_fields = list[0].__dict__.keys()
        data_frame = pd.DataFrame(columns=observation_fields)

        i = 0
        for l in list:
            observation_values = l.__dict__.values()
            data_frame.loc[i] = observation_values
            i += 1

    return data_frame


def _reg_types_dict(registration_tids=None):
    """Method maps single RegistrationTID values to the query dictionary used in regObs webapi

    :param registration_tids:       [int or list of int] Definition given below
    :return:


    Registration IDs and names
    10	Fritekst
    11	Ulykke/hendelse
    12	Bilde
    13	Faretegn
    -14	Skader
    21	Vær
    22	Snødekke
    23	Snøprofil
    -24	Skredfaretegn
    25	Stabilitetstest
    26	Skredhendelse
    27	Observert skredaktivitet(2011)
    28	Skredfarevurdering (2012)
    -29	Svakt lag
    30	Skredfarevurdering (2013)
    31	Skredfarevurdering
    32	Skredproblem
    33	Skredaktivitet
    40	Snøskredvarsel
    50	Istykkelse
    51	Isdekningsgrad
    61	Vannstand (2017)
    62	Vannstand
    71	Skredhendelse
    80	Hendelser   Grupperings type - Hendelser
    81	Skred og faretegn   Grupperings type - Skred og faretegn
    82	Snødekke og vær Grupperings type - Snødekke og vær
    83	Vurderinger og problemer    Grupperings type - Vurderinger og problemer

    """

    # If input isn't a list, make it so
    if not isinstance(registration_tids, list):
        registration_tids = [registration_tids]

    registration_dicts = []
    for registration_tid in registration_tids:
        if registration_tid is None:
            return None
        elif registration_tid == 10:  # Fritekst
            registration_dicts.append({'Id': 10, 'SubTypes': []})
        elif registration_tid == 11:  # Ulykke/hendelse
            registration_dicts.append({'Id': 80, 'SubTypes': [11]})
        elif registration_tid == 13:  # Faretegn
            registration_dicts.append({'Id': 81, 'SubTypes': [13]})
        elif registration_tid == 21:  # Vær
            registration_dicts.append({'Id': 82, 'SubTypes': [21]})
        elif registration_tid == 22:  # Snødekke
            registration_dicts.append({'Id': 82, 'SubTypes': [22]})
        elif registration_tid == 23:  # Snøprofil
            registration_dicts.append({'Id': 82, 'SubTypes': [23]})
        elif registration_tid == 25:  # Stabilitetstest
            registration_dicts.append({'Id': 82, 'SubTypes': [25]})
        elif registration_tid == 26:  # Skredhendelse
            registration_dicts.append({'Id': 81, 'SubTypes': [26]})
        elif registration_tid == 27:  # Skredaktivitet(2011)
            registration_dicts.append({'Id': 81, 'SubTypes': [27]})
        elif registration_tid == 28:  # Skredfarevurdering (2012)
            registration_dicts.append({'Id': 83, 'SubTypes': [28]})
        elif registration_tid == 30:  # Skredfarevurdering (2013)
            registration_dicts.append({'Id': 83, 'SubTypes': [30]})
        elif registration_tid == 31:  # Skredfarevurdering
            registration_dicts.append({'Id': 83, 'SubTypes': [31]})
        elif registration_tid == 32:  # Skredproblem
            registration_dicts.append({'Id': 83, 'SubTypes': [32]})
        elif registration_tid == 33:  # Skredaktivitet
            registration_dicts.append({'Id': 81, 'SubTypes': [33]})
        elif registration_tid == 50:  # Istykkelse
            registration_dicts.append({'Id': 50, 'SubTypes': []})
        elif registration_tid == 51:  # Isdekningsgrad
            registration_dicts.append({'Id': 51, 'SubTypes': []})
        else:
            ml.log_and_print('getobservations.py -> _reg_types_dict: RegistrationTID {0} not supported (yet).'.format(registration_tid))

    return registration_dicts


def _make_one_request(from_date=None, to_date=None, reg_id=None, registration_types=None,
        region_ids=None, location_id=None, observer_id=None, observer_nick=None, observer_competence=None,
        group_id=None, output='List', geohazard_tids=None, lang_key=1, recursive_count=5):
    """Part of get_data method. Parameters the same except observer_id and reg_id can not be lists.
    """

    # Dates in the web-api request are strings
    if isinstance(from_date, dt.date):
        from_date = dt.date.strftime(from_date, '%Y-%m-%d')
    elif isinstance(from_date, dt.datetime):
        from_date = dt.datetime.strftime(from_date, '%Y-%m-%d')

    if isinstance(to_date, dt.date):
        to_date = dt.date.strftime(to_date, '%Y-%m-%d')
    elif isinstance(to_date, dt.datetime):
        to_date = dt.datetime.strftime(to_date, '%Y-%m-%d')

    data = []  # data from one query

    # query object posted in the request
    rssquery = {'LangKey': lang_key,
                'RegId': reg_id,
                'ObserverGuid': None,  # eg. '4d11f3cc-07c5-4f43-837a-6597d318143c',
                'SelectedRegistrationTypes': _reg_types_dict(registration_types),
                'SelectedRegions': region_ids,
                'SelectedGeoHazards': geohazard_tids,
                'ObserverId': observer_id,
                'ObserverNickName': observer_nick,
                'ObserverCompetence': observer_competence,
                'GroupId': group_id,
                'LocationId': location_id,
                'FromDate': from_date,
                'ToDate': to_date,
                'NumberOfRecords': None,  # int
                'Offset': 0}

    url = 'https://api.nve.no/hydrology/regobs/webapi_{0}/Search/Rss?geoHazard=0'.format(se.web_api_version)
    more_available = True

    # get data from regObs api. It returns 100 items at a time. If more, continue requesting with an offset. Paging.
    while more_available:

        # try or if there is an exception, try again.
        try:
            r = requests.post(url, json=rssquery)
            responds = r.json()
            data += responds['Results']

            if output == 'Count nest':
                ml.log_and_print('getobservations.py -> _make_one_request: total matches {0}'.format(responds['TotalMatches']))
                return [responds['TotalMatches']]

        except:
            ml.log_and_print("getobservations.py -> _make_one_request: EXCEPTION. RECURSIVE COUNT {0}".format(recursive_count))
            if recursive_count > 1:
                recursive_count -= 1  # count down
                data += _make_one_request(from_date=from_date,
                                          to_date=to_date,
                                          reg_id=reg_id,
                                          registration_types=registration_types,
                                          region_ids=region_ids,
                                          location_id=location_id,
                                          observer_id=observer_id,
                                          observer_nick=observer_nick,
                                          observer_competence=observer_competence,
                                          group_id=group_id,
                                          output=output,
                                          geohazard_tids=geohazard_tids,
                                          lang_key=lang_key,
                                          recursive_count=recursive_count)

        # log request status
        if responds['TotalMatches'] == 0:
            ml.log_and_print("getobservations.py -> _make_one_request: no data")
        else:
            ml.log_and_print('getobservations.py -> _make_one_request: {0:.2f}%'.format(len(data) / responds['TotalMatches'] * 100))

        # if more get more by adding to the offset
        if len(data) < responds['TotalMatches']:
            rssquery["Offset"] += 100
        else:
            more_available = False

    return data


def _get_general(registration_class_type, registration_types, from_date, to_date, region_ids=None, location_id=None,
        observer_ids=None, observer_nick=None, observer_competence=None, group_id=None,
        output='List', geohazard_tids=None, lang_key=1):
    """Gets observations of a requested type and mapps them to a class.

    :param registration_class_type: [class for the requested observations]
    :param registration_types:  [int] RegistrationTID for the requested observation type
    :param from_date:           [date] A query returns [from_date, to_date]
    :param to_date:             [date] A query returns [from_date, to_date]
    :param region_ids:          [int or list of ints] If region_ids = None, all regions are selected
    :param observer_ids:        [int or list of ints] If observer_ids = None, all observers are selected
    :param observer_nick:       [int or list of ints] Default None gives all.
    :param observer_competence: [string] Part of a observer nick name
    :param group_id:            [int]
    :param output:              [string] Options: 'List', 'DataFrame' and 'Count'. Default 'List'.
    :param geohazard_tids       [int or list of ints] 10 is snow, 20,30,40 are dirt, 60 is water and 70 is ice
    :param lang_key             [int] 1 is norwegian, 2 is english

    :return:
    """

    list = None
    if output not in ['List', 'DataFrame', 'Count']:
        ml.log_and_print('getobservations.py -> _get_general: Illegal output option.')
        return list

    # In these methods "Count" is obviously to count the list ov observations weras in the more general get_data
    # counting a list and counting a nested list of full registratoins are two different tings.
    output_for_get_data = output
    if output == 'Count':
        output_for_get_data = 'Count list'
    # Dataframes are based on the lists
    if output == 'DataFrame':
        output_for_get_data = 'List'

    # AvalancheEvaluation3 = 31 and is the table for observed avalanche evaluations.
    data_with_more = get_data(from_date=from_date, to_date=to_date, region_ids=region_ids, observer_ids=observer_ids,
                              observer_nick=observer_nick, observer_competence=observer_competence,
                              group_id=group_id, location_id=location_id, lang_key=lang_key,
                              output=output_for_get_data, registration_types=registration_types, geohazard_tids=geohazard_tids)

    # wash out all other observation types
    data = []
    if registration_types:
        for d in data_with_more:
            if d['RegistrationTid'] == registration_types:
                data.append(d)
    else:   # regisrtation_types is None is for all registrations and no single type is picked out.
        data = data_with_more

    if output == 'List' or output == 'DataFrame':
        list = [registration_class_type(d) for d in data]
        list = sorted(list, key=lambda registration_class_type: registration_class_type.DtObsTime)

    if output == 'List':
        return list

    if output == 'DataFrame':
        return _make_data_frame(list)

    if output == 'Count':
        return data


def get_data(from_date=None, to_date=None, registration_types=None, reg_ids=None, region_ids=None, location_id=None,
        observer_ids=None, observer_nick=None, observer_competence=None, group_id=None,
        output='List', geohazard_tids=None, lang_key=1):
    """Gets data from regObs webapi. Each observation returned as a dictionary in a list.

    :param from_date:           [string] 'yyyy-mm-dd'. Result includes from date.
    :param to_date:             [string] 'yyyy-mm-dd'. Result includes to date.
    :param lang_key:            [int] Default 1 gives Norwegian.
    :param reg_id:              [int or list of ints] Default None gives all.
    :param registration_types:  [string or list of strings] Default None gives all.
    :param region_ids:          [int or list of ints]
    :param geo_hazards:         [int or list of ints] Default None gives all.
    :param observer_id:         [int or list of ints] Default None gives all.
    :param observer_nick        [string] Part of a observer nick name
    :param observer_competence  [int or list of int] as given in ComtetanceLevelKDV
    :param group_id:            [int]
    :param location_id:         [int]
    :param output:              [string] 'Nested' collects all observations in one regid in one entry (defult for webapi).
                                         'List' is a flatt structure with one entry pr observation type.
                                         'Count nest' makes one request and picks out info on total matches
                                         'Count list' counts every from in every observation

    :return:                    [list or int] Depending on output requested.


    """

    # If input isn't a list, make it so
    if not isinstance(registration_types, list):
        registration_types = [registration_types]

    if not isinstance(region_ids, list):
        region_ids = [region_ids]

    if not isinstance(geohazard_tids, list):
        geohazard_tids = [geohazard_tids]

    # regObs weabapi does not support multiple ObserverIDs and RegIDs. Making it so.
    if not isinstance(observer_ids, list):
        observer_ids = [observer_ids]

    if not isinstance(reg_ids, list):
            reg_ids = [reg_ids]

    # if output requested is 'Count' a number is expected, else a list og observations
    all_data = []

    for reg_id in reg_ids:
        for observer_id in observer_ids:

            data = _make_one_request(
                from_date=from_date, to_date=to_date, lang_key=lang_key, reg_id=reg_id,
                registration_types=registration_types, region_ids=region_ids, geohazard_tids=geohazard_tids,
                observer_id=observer_id, observer_nick=observer_nick, observer_competence=observer_competence, group_id=group_id, location_id=location_id, output=output)

            all_data += data

    # Output 'Nested' is the structure returned from webapi. All observations on the same reg_id are grouped to one list item.
    # Output 'List' all observation elements are made a separate item on list.
    # Sums of each are available as 'Count list. and 'Count nest'.
    if output == 'Count nest':
        return sum(all_data)

    # data sorted with ascending observation time
    all_data = sorted(all_data, key=lambda d: d['DtObsTime'])
    if output == 'Nested':
        return all_data

    elif output == 'List' or output == 'Count list':
        listed_data = []

        for d in all_data:
            for o in d['Registrations']:
                listed_data.append({**d, **o})
            for p in d['Pictures']:
                p['RegistrationName'] = 'Bilde'
                listed_data.append({**d, **p})

        if output == 'List':
            return listed_data
        if output == 'Count list':
            return len(listed_data)

    else:
        ml.log_and_print('getobservations.py -> get_data: Unsupported output type.')
        return None


# END VARSOMDATA


def _webapi_ice_col_to_ice_class(o):
    """This internal method maps an ice column object as given on webapi to the Ice.IceColumn class

    :param o:
    :return:
    """

    reg_id = o['RegId']
    layers = []
    ordered_layers = sorted(o['FullObject']['IceThicknessLayers'], key=lambda l: l['IceLayerID'])

    for layer in ordered_layers:
        ice_type = get_ice_type_from_tid(layer['IceLayerTID'])
        ice_layer_height = layer['IceLayerThickness']
        if ice_layer_height is not None:
            ice_layer = ice.IceLayer(ice_layer_height, ice_type)
            layers.append(ice_layer)

    date = dt.datetime.strptime(o['DtObsTime'][0:16], "%Y-%m-%dT%H:%M")

    if o['FullObject']['IceThicknessSum'] is not None:
        if len(layers) == 0:
            layers = [ice.IceLayer(float(o['FullObject']['IceThicknessSum']), 'unknown')]

        ice_column = ice.IceColumn(date, layers)
        ice_column.add_metadata('OriginalObject', o)
        ice_column.add_metadata('RegID', reg_id)
        ice_column.add_metadata('LocationName', o['LocationName'])
        ice_column.add_metadata('LocationID', o['LocationId'])
        ice_column.add_metadata('UTMNorth', o['UtmNorth'])
        ice_column.add_metadata('UTMEast', o['UtmEast'])
        ice_column.add_metadata('UTMZone', o['UtmZone'])

        ice_column.add_layer_at_index(0, ice.IceLayer(o['FullObject']['SlushSnow'], 'slush'))
        ice_column.add_layer_at_index(0, ice.IceLayer(o['FullObject']['SnowDepth'], 'snow'))

        ice_column.merge_and_remove_excess_layers()
        ice_column.update_draft_thickness()
        ice_column.update_top_layer_is_slush()

        # I tried to reference ice column to water surface given ice height after or slush snow, but then what if
        # ice height before is given. And what if there are combinations. To many possibilities in regObs..
        # Iv calculate a theoretical ice height and use that.
        # ice_column.update_water_line()

        iha = o['FullObject']['IceHeightAfter']

        # ihb = o['FullObject']['IceHeightBefore']

        # if ice height after is not given I make an estimate so that I know where to put it in the plot
        if iha is None:
            ice_column.update_water_line()
            ice_column.add_metadata('IceHeightAfter', 'Modelled')
            iha = ice_column.draft_thickness - ice_column.water_line
            # Probably dont need the test of topp layer is slush because it is includet in draft thickness
            # if ice_column.top_layer_is_slush:
            #     iha = iha + const.snow_pull_on_water

        ice_column.water_line = ice_column.draft_thickness - float(iha)

        # correct level if top layer was slush
        if ice_column.top_layer_is_slush is True:
           for layer in ice_column.column:
               if layer.get_enum() > 20:  # material types >= 20 are snow
                   continue
               elif layer.get_enum() == 2:  # slush
                   ice_column.water_line -= layer.height
                   break                   # only the top most slush layer counts

        return ice_column

    else:
        return None


def get_ice_thickness_today():
    """Gets all the observed ice thickness from regObs for today (and 2 days back)

    :return:    ice_thickeness_obs_dict
    """

    to_date = dt.date.today()
    from_date = to_date - dt.timedelta(days=2)

    ice_thickeness_obs = get_data(from_date=from_date, to_date=to_date, registration_types=50, geohazard_tids=70)
    ice_thickeness_obs_dict = {}

    for o in ice_thickeness_obs:
        if o['RegistrationTid'] == 50:
            ice_column = _webapi_ice_col_to_ice_class(o)
            if ice_column is not None:
                ice_thickeness_obs_dict[o['RegId']] = ice_column

    return ice_thickeness_obs_dict


def get_ice_thickness_observations(year, reset_and_get_new=False):
    """Gets all the observed ice thickness (RegistrationTID = 50) from regObs for one year.

    The inner workings of the method:
    1.   We have an option of resetting local storage (delete pickle) and thus forcing the get_new.
    2.1  Try opening a pickle, if it doesnt exist, an exception is thrown and we get new data.
    2.2  If the requested data is from a previous season, load the pickle without adding the last observations
         registered in regObs. Anyway, dont get new data.
    2.3  If the requested data is from this season, set request from_date to the last modified
         date of the pickle and 7 days past that. Add these last obs to the pickle data, and thus it is not
         necessary to get new.
    3.  If get new, it gets all new data for the season.
    4.  Else, load pickle and if some last obs are to be added, do so.

    :param year:                [string] Eg '2017-18'
    :param reset_and_get_new:   [bool]
    :return:                    ice_thickeness_obs_dict
    """

    log_referance = 'getregobsdata.py -> get_ice_thickness_observations'
    pickle_file_name = '{}ice_thickness_obs_{}.pickle'.format(se.local_storage, year)

    # 1. Remove pickle if it exists, forcing the get_new
    if reset_and_get_new:
        try:
            os.remove(pickle_file_name)
        except OSError:
            pass

    from_date, to_date = get_dates_from_year(year)
    add_last_obs = None
    get_new = None

    try:
        mtime = os.path.getmtime(pickle_file_name)
        last_modified_date = dt.datetime.fromtimestamp(mtime).date()

        # if file newer than the season (that is, if this is historical data), load it without requesting new.
        dt_to_date = dt.datetime.strptime(to_date, '%Y-%m-%d').date()
        if last_modified_date > dt_to_date:
            add_last_obs = False
        else:
            add_last_obs = True
            to_date = dt.date.today()
            from_date = last_modified_date - dt.timedelta(days=7)

        get_new = False

    except OSError:
        # file does not exists, so get_new.
        ml.log_and_print('{0}: No matching pickle found, getting new data.'.format(log_referance))
        get_new = True

    if get_new:
        ml.log_and_print('{0}: Getting new for year {1}.'.format(log_referance, year))
        ice_thickeness_obs = get_data(from_date=from_date, to_date=to_date, registration_types=50, geohazard_tids=70)
        ice_thickeness_obs_dict = {}

        for o in ice_thickeness_obs:
            if o['RegistrationTid'] == 50:
                ice_column = _webapi_ice_col_to_ice_class(o)
                if ice_column is not None:
                    ice_thickeness_obs_dict[o['RegId']] = ice_column

        mp.pickle_anything(ice_thickeness_obs_dict, pickle_file_name)

    else:
        ice_thickeness_obs_dict = mp.unpickle_anything(pickle_file_name)

        if add_last_obs:
            ml.log_and_print('{0}: Adding observations from {1} to {2}.'.format(log_referance, from_date, to_date))
            new_ice_thickeness_obs = get_data(from_date=from_date, to_date=to_date, registration_types=50, geohazard_tids=70)
            new_ice_thickeness_obs_dict = {}

            for o in new_ice_thickeness_obs:
                if o['RegistrationTid'] == 50:
                    ice_column = _webapi_ice_col_to_ice_class(o)
                    if ice_column is not None:
                        new_ice_thickeness_obs_dict[o['RegId']] = ice_column

            for k,v in new_ice_thickeness_obs_dict.items():
                ice_thickeness_obs_dict[k] = v

            mp.pickle_anything(ice_thickeness_obs_dict, pickle_file_name)

    return ice_thickeness_obs_dict


def get_all_season_ice(year, get_new=True):
    """Returns observed ice columns from regObs over a requested season. Ice covers representing first ice
    or ice cover lois are represented by an ice column of zero height.

    The workings of this routine:
    1.  Get one season of data from regobs-api, spreads them out to a long list.
    2.  Pick out only cover and column and group them on location_ids. We keep only locations with
        date for fist ice that season. All observations are mapped to the cover and column class in Ice.py.
    3.  Map all covers where first_ice or ice_cover_lost is True to zero-height columns. Remove the rest.

    If get_new=True new data is retrieved. If get_new=false data is picked from pickle.

    :param year:
    :param get_new:
    :return:
    """

    file_name_and_path = '{0}all_season_ice_{1}.pickle'.format(se.local_storage, year)
    from_date, to_date = get_dates_from_year(year)

    if get_new:

        all_observations = get_data(from_date=from_date, to_date=to_date, geohazard_tids=70)

        all_locations = {}

        for o in all_observations:
            if o['RegistrationTid'] == 51 or o['RegistrationTid'] == 50:
                if o['LocationId'] in all_locations.keys():
                    all_locations[o['LocationId']].append(o)
                else:
                    all_locations[o['LocationId']] = [o]

        # sort oldest first on each location
        for l, os in all_locations.items():
            sorted_list = sorted(os, key=lambda d : d['DtObsTime'])
            all_locations[l] = sorted_list

        # Use only locations with verified "first ice cover" date.
        all_locations_with_first_ice = {}

        for l, os in all_locations.items():
            for o in os:
                if o['RegistrationTid'] == 51:
                    # if the ice cover is partly or fully formed on observation location or the lake
                    # 2) delvis islagt på målestedet
                    # 3) helt islagt på målestedet
                    # 21) hele sjøen islagt
                    if (o['FullObject']['IceCoverTID'] == 2) or (o['FullObject']['IceCoverTID'] == 3) or \
                            (o['FullObject']['IceCoverTID'] == 21):
                        # and if ice cover before was
                        # 1) isfritt på målestedet
                        # 2) delvis islagt på målestedet,
                        # 11) islegging langs land
                        # 20) hele sjøen isfri,  this is fist ice
                        if (o['FullObject']['IceCoverBeforeTID'] == 1) or (o['FullObject']['IceCoverBeforeTID'] == 2) or \
                                (o['FullObject']['IceCoverBeforeTID'] == 11) or (o['FullObject']['IceCoverBeforeTID'] == 20):
                            all_locations_with_first_ice[l] = os

        # Map all observations from regObs-webapi result structure to the classes in ice.py
        all_locations_with_classes = {}

        for l, os in all_locations_with_first_ice.items():
            all_locations_with_classes[l] = []
            location_name = os[0]['LocationName']

            previous_cover = ice.IceCover(dt.datetime.strptime(from_date, "%Y-%m-%d").date(), "Ikke gitt", 'Ikke gitt', location_name)

            for o in os:
                if o['RegistrationTid'] == 51:

                    cover_date = dt.datetime.strptime(o['DtObsTime'][0:16], "%Y-%m-%dT%H:%M")
                    cover = o['FullObject']['IceCoverTName']
                    cover_before = o['FullObject']['IceCoverBeforeTName']
                    cover_after = o['FullObject']['IceCoverAfterTName']
                    cover_tid = o['FullObject']['IceCoverTID']
                    cover_before_tid = o['FullObject']['IceCoverBeforeTID']
                    cover_after_tid = o['FullObject']['IceCoverAfterTID']

                    this_cover = ice.IceCover(cover_date, cover, cover_before, location_name)
                    this_cover.set_regid(o['RegId'])
                    this_cover.set_locationid(o['LocationId'])
                    this_cover.set_utm(o['UtmNorth'], o['UtmEast'], o['UtmZone'])
                    this_cover.set_cover_after(cover_after, cover_after_tid)
                    this_cover.add_original_object(o)

                    # if the ice cover is partly or fully formed on observation location or the lake
                    # 2) delvis islagt på målestedet
                    # 3) helt islagt på målestedet
                    # 21) hele sjøen islagt
                    if cover_tid == 2 or cover_tid == 3 or cover_tid == 21:
                        # and if icecover before was
                        # 1) isfritt, nå første is på målestedet på målestedet
                        # 2) delvis islagt på målestedet,
                        # 11) islegging langs land
                        # 20) hele sjøen isfri,  this is fist ice
                        if cover_before_tid == 1 or cover_before_tid == 2 or cover_before_tid == 11 or cover_before_tid == 20:
                            this_cover.mark_as_first_ice()

                    # if the ice cover is partly or fully gone on location and there was ice yesterday
                    # 1) Isfritt på målestedet
                    # 2) delvis islagt på målestedet
                    # 20) Hele sjøen isfri
                    if cover_tid == 1 or cover_tid == 2 or cover_tid == 20:
                        # 10) isfritt restren av vinteren
                        if cover_after_tid == 10:
                            this_cover.mark_as_ice_cover_lost()

                        # before 10) forrige obs gjelder til i går
                        if cover_before_tid == 10:
                            # if the frevious ice cover wich was valid yesturday had ice
                            if previous_cover.iceCoverTID == 2 or previous_cover.iceCoverTID == 3 or \
                               previous_cover.iceCoverTID == 10 or previous_cover.iceCoverTID == 11 or \
                               previous_cover.iceCoverTID == 21:
                                this_cover.mark_as_ice_cover_lost()

                    # copy of this cover so that in next iteration I may look up previous cover..
                    previous_cover = cp.deepcopy(this_cover)

                    all_locations_with_classes[l].append(this_cover)

                if o['RegistrationTid'] == 50:
                    ice_column = _webapi_ice_col_to_ice_class(o)

                    if ice_column is not None:
                        all_locations_with_classes[l].append(ice_column)

        # Map all covers where first_ice or ice_cover_lost is True to zero-height columns. Remove all the rest.
        all_locations_with_columns = {}
        for k, v in all_locations_with_classes.items():
            new_v = []
            for o in v:
                if isinstance(o, ice.IceCover):
                    if o.first_ice or o.ice_cover_lost:
                        new_o = ice.IceColumn(o.date, [])
                        new_o.add_metadata('OriginalObject', o.metadata['OriginalObject'])
                        new_o.add_metadata('UTMEast', o.metadata['UTMEast'])
                        new_o.add_metadata('UTMNorth', o.metadata['UTMNorth'])
                        new_o.add_metadata('UTMZone', o.metadata['UTMZone'])
                        new_o.add_metadata('LocationName', o.locationName)
                        new_o.add_metadata('LocationID', o.LocationID)
                        new_v.append(new_o)
                else:
                    new_v.append(o)
            all_locations_with_columns[k] = new_v

        mp.pickle_anything(all_locations_with_columns, file_name_and_path)

    else:
        all_locations_with_columns = mp.unpickle_anything(file_name_and_path, print_message=False)

    return all_locations_with_columns


def get_observations_on_location(location_name, year, get_new=False):
    '''Uses new or stored data from get_all_season_ice and picks out one requested location.
    First ice cover is mapped to Ice.IceColumn of zero height. Ice cover lost (mid season or last) the same.

    :param location_name:
    :param year:
    :param get_new:
    :return:
    '''

    all_locations = get_all_season_ice(year, get_new=get_new)
    ###
    ### get_all_season_ice returns a dictionary with bservations grouped by location_id.
    ###
    observations_on_location_for_modeling = []

    try:
        for o in all_locations[location_name]:
            if isinstance(o, ice.IceCover):

                if o.first_ice:
                    fc = ice.IceColumn(o.date, 0)
                    fc.add_metadata('LocationName', o.locationName)
                    fc.add_metadata('RegID', o.RegID)
                    fc.add_metadata('UTMNorth', o.metadata['UTMNorth'])
                    fc.add_metadata('UTMEast', o.metadata['UTMEast'])
                    fc.add_metadata('UTMZone', o.metadata['UTMZone'])
                    observations_on_location_for_modeling.append(fc)

                if o.ice_cover_lost:
                    lc = ice.IceColumn(o.date, 0)
                    lc.add_metadata('LocationName', o.locationName)
                    lc.add_metadata('RegID', o.RegID)
                    lc.add_metadata('UTMNorth', o.metadata['UTMZone'])
                    lc.add_metadata('UTMEast', o.metadata['UTMZone'])
                    lc.add_metadata('UTMZone', o.metadata['UTMZone'])
                    observations_on_location_for_modeling.append(lc)

            elif isinstance(o, ice.IceColumn):
                observations_on_location_for_modeling.append(o)

    except Exception as e:
        ml.log_and_print('getregobsdata.py -> get_observations_on_location: {0} not found probably..'.format(location_name), print_it=True)

    return observations_on_location_for_modeling


def get_dates_from_year(year, date_format='yyyy-mm-dd'):
    """Returns start and end dates for given season. Format may be specified for datetime or date or string (default).

    :param year:
    :param date_format:     [String]    'yyyy-mm-dd', 'date' or 'datetime'
    :return:
    """

    log_ref = 'getregobsdata.py -> get_dates_from_year:'

    if year == '2017-18':
        from_date = '2017-08-01'
        to_date = '2018-08-01'
    elif year == '2016-17':
        from_date = '2016-08-01'
        to_date = '2017-08-01'
    elif year == '2015-16':
        from_date = '2015-08-01'
        to_date = '2016-08-01'
    elif year == '2014-15':
        from_date = '2014-08-01'
        to_date = '2015-08-01'
    elif year == '2013-14':
        from_date = '2013-08-01'
        to_date = '2014-08-01'
    elif year == '2012-13':
        from_date = '2012-08-01'
        to_date = '2013-08-01'
    elif year == '2011-12':
        from_date = '2011-08-01'
        to_date = '2012-08-01'
    else:
        ml.log_and_print('{0} Not supported year.'.format(log_ref))
        return 'Not supported year.'

    if 'yyyy-mm-dd' in date_format:
        return from_date, to_date
    elif 'date' in date_format:
        from_date = dt.datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = dt.datetime.strptime(to_date, '%Y-%m-%d').date()
        return from_date, to_date
    elif 'datetime' in date_format:
        from_date = dt.datetime.strptime(from_date, '%Y-%m-%d')
        to_date = dt.datetime.strptime(to_date, '%Y-%m-%d')
        return from_date, to_date
    else:
        ml.log_and_print('{0} Date format not supported.'.format(log_ref))
        return 'Date format not supported.'


def get_new_regobs_data():

    get_all_season_ice('2017-18')
    get_all_season_ice('2016-17')
    get_all_season_ice('2015-16')
    get_all_season_ice('2014-15')
    get_all_season_ice('2013-14')
    get_all_season_ice('2012-13')
    get_all_season_ice('2011-12')


if __name__ == "__main__":

    # get_new_regobs_data()
    # ice_column = get_ice_thickness_on_regid(130979)

    LocationName1 = 'Hakkloa nord 372 moh'
    LocationName2 = 'Otrøvatnet v/Nystuen 971 moh'
    LocationName3 = 'Semsvannet v/Lo 145 moh'

    LocationNames = [LocationName1, LocationName2, LocationName3]
    from_date = '2016-01-01'
    to_date = '2016-02-01'

    ice_thicks = get_ice_thickness_observations('2017-18')

    #ic = get_ice_cover(LocationNames, from_date, to_date)
    #first = get_first_ice_cover(LocationNames, from_date, to_date)
    #last = get_last_ice_cover(LocationNames, from_date, to_date)
    #ith = get_ice_thickness(LocationNames, from_date, to_date)
    #all_on_locations = get_all_season_ice_on_location(LocationNames, from_date, to_date)

    all_in_all = get_all_season_ice('2016-17', get_new=True)

    #hakkloa = get_observations_on_location(LocationName1, '2015-16', get_new=False)
    #otrø = get_observations_on_location(LocationName2, '2014-15', get_new=False)
    Semms = get_observations_on_location(LocationName3, '2014-15', get_new=False)

    b = 1