__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

from lxml import etree
import requests as re
import datetime as dt
import weather as we
import xml.etree.ElementTree as et      # used in the incomplete methods
import setEnvironment as env
import types as t
import fEncoding as fe
import makeFiledata as mfd

# Incomplete
def getElementsProperties():
    url = "http://eklima.met.no/metdata/MetDataService?invoke=getElementsProperties&language=&elem_codes="
    ws = re.get(url)

    # print ws.text
    filename = 'ElementsProperties.xml'

    f = open(filename, 'w')
    f.write((ws.text).encode('utf-8'))
    f.close()

    tree = et.parse(filename)
    root = tree.getroot()

    filename = 'ElementsProperties.csv'
    f = open(filename, 'w')

    for element in root.iter('item'):
        group = (element.find('elemGroup').text).encode('utf-8')
        code = (element.find('elemCode').text).encode('utf-8')
        description = (element.find('description').text).encode('utf-8')
        if group == 'Temperatur' or group == 'Snø':
            f.write('{0}\t{1}\t{2}\n'.format(group, code, description))
    f.close()

# Incomplete
def getTimeserieTypesProperties():
    url = "http://eklima.met.no/metdata/MetDataService?invoke=getTimeserieTypesProperties&language=&timeserieTypes="
    ws = re.get(url)

    # print ws.text
    filename = '{0}TimeseriesTypesProperties.xml'.format(env.data_path)

    f = open(filename, 'w')
    f.write((ws.text).encode('utf-8'))
    f.close()

    tree = et.parse(filename)
    root = tree.getroot()

    filename = '{0}TimeseriesTypesProperties.csv'.format(env.data_path)
    f = open(filename, 'w')
    for element in root.iter('item'):
        Name = (element.find('serieTypeName').text).encode('utf-8')
        ID = (element.find('serieTypeID').text).encode('utf-8')
        Description = (element.find('serieTypeDescription').text).encode('utf-8')
        f.write('{0}\t{1}\t{2}\n'.format(Name, ID, Description))

    f.close()


def getStationsFromTimeserieTypeElemCodes(timeserietypeID, elem_codes, output='list', has_all_elems_now=True):
    """Gets all stations with a given timeserie type and element codes.

    :param timeserietypeID      [string]
    :param elem_codes           [string] or [list of string]
    :param output               [string]
    :param has_all_elems_now    [bool] Station must have all elements stil active
    :return stationList         [list of dictionary elements] or None if file is requested output.

    Output options:
        'list':         returns a list of dictionary elements.
        'xml':          returns NULL but saves a .xml file to the working folder.
        'txt':          returns NULL but saves a .txt file to the working folder.

    timeseriesType options:
        0   dayly averages
        1   monthly averages
        2   hour average

    Denne finner alle stasjoner emd langbølget stråling
    http://eklima.met.no/met/MetService?invoke=getStationsFromTimeserieTypeElemCodes&timeserietypeID=2&elem_codes=QLI&username=

    <item xsi:type="ns3:no_met_metdata_StationProperties">
        <amsl xsi:type="xsd:int">10</amsl>
        <department xsi:type="xsd:string">AKERSHUS</department>
        <fromDay xsi:type="xsd:int">31</fromDay>
        <fromMonth xsi:type="xsd:int">12</fromMonth>
        <fromYear xsi:type="xsd:int">1953</fromYear>
        <latDec xsi:type="xsd:double">59.8927</latDec>
        <latLonFmt xsi:type="xsd:string">decimal_degrees</latLonFmt>
        <lonDec xsi:type="xsd:double">10.6158</lonDec>
        <municipalityNo xsi:type="xsd:int">219</municipalityNo>
        <name xsi:type="xsd:string">FORNEBU</name>
        <stnr xsi:type="xsd:int">19400</stnr>
        <toDay xsi:type="xsd:int">30</toDay>
        <toMonth xsi:type="xsd:int">11</toMonth>
        <toYear xsi:type="xsd:int">1998</toYear>
        <utm_e xsi:type="xsd:int">254787</utm_e>
        <utm_n xsi:type="xsd:int">6647583</utm_n>
        <utm_zone xsi:type="xsd:int">33</utm_zone>
        <wmoNo xsi:type="xsd:int">1488</wmoNo>
    </item>

    """

    if isinstance(elem_codes, t.ListType):
        elem_codes_string = ','.join(elem_codes)
    else:
        elem_codes_string = elem_codes

    url = "http://eklima.met.no/metdata/MetDataService?invoke=getStationsFromTimeserieTypeElemCodes&timeserietypeID={0}&elem_codes={1}&username="\
        .format(timeserietypeID, elem_codes_string)
    wsKlimaRequest = re.get(url)

    station_list = []
    final_station_list = []
    filename = '{0}Stations with {1} of {2}'.format(env.data_path, timeserietypeID, elem_codes_string)

     # Check which output option is requested
    if output == 'xml':     # save the xml received on the eklima request
        mfd.write_large_sting(filename, ".xml", wsKlimaRequest.text.encode('utf-8'))
        return None

    # Take the request and make an element tree to be iterated
    # append all stations to a list
    root = etree.fromstring(wsKlimaRequest.content)
    for station in root.iter('item'):
        amsl = station.find('amsl').text
        department = fe.remove_norwegian_letters(station.find('department').text)
        fromDay = station.find('fromDay').text
        fromMonth = station.find('fromMonth').text
        fromYear = station.find('fromYear').text
        latDec = station.find('latDec').text
        lonDec = station.find('lonDec').text
        municipalityNo = fe.remove_norwegian_letters(station.find('municipalityNo').text)
        name = fe.remove_norwegian_letters(station.find('name').text)
        stnr = station.find('stnr').text
        toDay = station.find('toDay').text
        toMonth = station.find('toMonth').text
        toYear = station.find('toYear').text
        utm_e = station.find('utm_e').text
        utm_n = station.find('utm_n').text
        utm_zone = station.find('utm_zone').text

        from_date = dt.date(year=int(fromYear), month=int(fromMonth), day=int(fromDay))
        to_date = None
        if toYear is not '0':
            to_date = dt.date(year=int(toYear), month=int(toMonth), day=int(toDay))

        station_list.append({
                'amsl': int(amsl),
                'department': fe.add_norwegian_letters(department),
                'latDec': float(latDec),
                'lonDec': float(lonDec),
                'municipalityNo': int(municipalityNo),
                'name': fe.add_norwegian_letters(name),
                'stnr': int(stnr),
                'utm_e': int(utm_e),
                'utm_n': int(utm_n),
                'utm_zone': utm_zone,
                'from_date': from_date,
                'to_date': to_date})

    # look up all stations and find if elements are active and if all are present on the station
    if has_all_elems_now is True:
        for station in station_list:
            if station['to_date'] is None:                          # station is operational today
                use_station = True
                station_elems = getElementsFromTimeserieTypeStation(station['stnr'], timeserietypeID, output='list')
                station_elems_list = []
                for elem in station_elems:
                    if elem['toDate'] is None:                      # list elements being observed today
                        station_elems_list.append(elem['elemCode'])
                for elem in elem_codes:
                    if elem not in station_elems_list:              # requested elements are on the station
                        use_station = False
                if use_station is True:
                    final_station_list.append(station)
    else:
        final_station_list = station_list

    if output == 'list':
        return final_station_list
    elif output == 'txt':
        mfd.write_dictionary(filename, '.txt', final_station_list, tabulated=False)
        return None


def getElementsFromTimeserieTypeStation(stationID, timeserietypeID, output='list'):
    """Gets availabe weather elements on a given met station.

    :param stationID:       The station number.
    :param timeserietypeID: The timeserietypeID to be requested. Eg 0 is daily avarage.
    :param output:          3 types of output are available.
    :return:                A list of dictionary elements or makes files that are saved to the data directory.

    Output options:
        'list':         returns a list of dictionary elements.
        'xml':          returns NULL but saves a .xml file to the working folder.
        'csv':          returns NULL but saves a .csv file to the working folder. The separation value is tab.

    Example of xml that is iterated:

        <item xsi:type="ns3:no_met_metdata_ElementProperties">
            <description xsi:type="xsd:string">Nedbør for en løpende måned (30 døgn)</description>
            <elemCode xsi:type="xsd:string">RR_720</elemCode>
            <elemGroup xsi:type="xsd:string">Nedbør</elemGroup>
            <elemNo xsi:type="xsd:int">-1</elemNo>
            <fromdate xsi:type="xsd:dateTime">1957-01-30T00:00:00.000Z</fromdate>
            <language xsi:type="xsd:string">no</language>
            <name xsi:type="xsd:string">Nedbør 720 timer (siste 30 døgn)</name>
            <todate xsi:type="xsd:dateTime" xsi:nil="true"/>
            <unit xsi:type="xsd:string">mm</unit>
        </item>

    NOTE: if you only wish to read data for a given station check out
    http://eklima.met.no/eklimapub/servlet/ReportInfo?action=parameterinfo&tab=T_ELEM_DIURNAL&s=19710&la=no&co=NO

    NOTE2: Asker has id 19710 and Blindern 18700
    """
    print 'getWSklima: Requesting getElementsFromTimeserieTypeStation on {0} for {1}'\
        .format(stationID, timeserietypeID)

    url = "http://eklima.met.no/metdata/MetDataService?invoke=getElementsFromTimeserieTypeStation&timeserietypeID={1}&stnr={0}"\
        .format(stationID, timeserietypeID)
    wsKlimaRequest = re.get(url)

    # Check which output option is requested
    if output == 'list':
        stationElementList = []
    elif output == 'xml':
        filename = '{0}Elements on {1}_{2}.xml'.format(env.data_path, stationID, timeserietypeID)
        f = open(filename, 'w')
        f.write((wsKlimaRequest.text).encode('utf-8'))
        f.close()
        return
    elif output == 'csv':
        filename = '{0}Elements on {1}_{2}.csv'.format(env.data_path, stationID, timeserietypeID)
        f = open(filename, 'w')

    # Take the request and make an element tree to be iterated
    root = etree.fromstring(wsKlimaRequest.content)
    for element in root.iter('item'):
        elemGroup = element.find('elemGroup').text.encode('utf-8')
        elemCode = element.find('elemCode').text.encode('utf-8')
        name = element.find('name').text.encode('utf-8')
        description = element.find('description').text.encode('utf-8')
        unit = element.find('unit').text.encode('utf-8')

        tempfromdate = element.find('fromdate').text
        fromdate = dt.datetime.strptime(tempfromdate[0:10], "%Y-%m-%d").date()

        temptodate = element.find('todate').text
        if temptodate == None:
            todate = None
        else:
            todate = dt.datetime.strptime(temptodate[0:10], "%Y-%m-%d").date()

        if output == 'list':
            stationElementList.append({'elemGroup': elemGroup,
                                       'elemCode': elemCode,
                                       'name': name,
                                       'description': description,
                                       'unit': unit,
                                       'fromdate': fromdate,
                                       'toDate': todate})
        elif output == 'csv':
            f.write( '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'
                     .format(elemGroup, elemCode, name, unit, fromdate, todate, description) )

    # Wrap up. Close files (xml file is already closed) and return data if it exists
    if output == 'csv':
        f.close()
        return
    elif output == 'list':
        return stationElementList


def getMetData(stationID, elementID, fromDate, toDate, timeseriesType, output='list'):
    '''The method uses the eklima webservice from met.no documented om eklims.met.no/wsklima

    Parameters and return:
        :param stationID:       The station number
        :param elementID:       The weather element code
        :param fromDate:        The from date as string 'YYYY-MM-DD' or datetime
        :param toDate:          The to date as string 'YYYY-MM-DD' or datetime
        :param timeseriesType:  The timeserie type to be requested. Eg 0 is daily avarage.
        :param output:          4 types of output are available.
        :return:                A list of weatherElements or files are made to working directory.

    Output options:
        'list':         returns a list of fixed WeatherElement objects suitable for modelling directly (default).
        'raw list'      returns a list of weatherElements uncorrected and unsuitable for modelling directly.
        'xml':          returns NULL but saves a .xml file to the working folder.
        'csv':          returns NULL but saves a .csv file to the working folder. The separation value are tab

    timeseriesType options:
        0   dayly averages
        1   monthly averages
        2   hour average

    Example of the xml returned from wsKlima:
        <item xsi:type="ns2:no_met_metdata_TimeStamp">
            <from xsi:type="xsd:dateTime">2011-10-02T00:00:00.000Z</from>
            <location xsi:type="ns3:Array" ns3:arrayType="ns2:no_met_metdata_Location[1]">
                <item xsi:type="ns2:no_met_metdata_Location">
                    <id xsi:type="xsd:int">19710</id>
                    <type xsi:type="xsd:string" xsi:nil="true"/>
                    <weatherElement xsi:type="ns3:Array" ns3:arrayType="ns2:no_met_metdata_WeatherElement[1]">
                        <item xsi:type="ns2:no_met_metdata_WeatherElement">
                            <id xsi:type="xsd:string">TAM</id>
                            <quality xsi:type="xsd:int">0</quality>
                            <value xsi:type="xsd:string">12.6</value>
                        </item>
                    </weatherElement>
                </item>
            </location>
            <to xsi:type="xsd:dateTime" xsi:nil="true"/>
        </item>
    '''

    #if isinstance(fromDate, datetime.datetime):
    #    fromDate = fromDate.strftime("%Y-%m-%d")
    #    toDate = toDate.strftime("%Y-%m-%d")

    hours = ""
    if timeseriesType in [2,8,9,13,14,15,16]:
        # hours in the request is given in a comma separated list: '0,..,23'. hours in UTC-time. hours
        # must have a value if timeserietypeID = 2,8,9,13,14,15,16 (hour data). Request all hours.
        hours = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23'

    url = "http://eklima.met.no/metdata/MetDataService?invoke=getMetData&timeserietypeID={4}&format=&from={2}&to={3}&stations={0}&elements={1}&hours={5}&months=&username="\
        .format(stationID, elementID, fromDate, toDate, timeseriesType, hours)
    wsKlimaRequest = re.get(url)

    # Check which output option is requested
    if output in ['list', 'raw list']:
        weatherElementList = []
    elif output == 'xml':
        filename = '{0}{1}_{2}_{3}_{4}.xml'.format(env.data_path, stationID, elementID, fromDate, toDate)
        f = open(filename, 'w')
        f.write((wsKlimaRequest.text).encode('utf-8'))
        f.close()
        return
    elif output == 'csv':
        filename = '{0}{1}_{2}_{3}_{4}.csv'.format(env.data_path, stationID, elementID, fromDate, toDate)
        f = open(filename, 'w')
    else:
        print('No valid output requested.')
        return 'No valid output requested'

    # Take the request and make an element tree to be iterated
    root = etree.fromstring(wsKlimaRequest.content)
    for element in root.iter('item'):

        # I only want item elements with attributes containing "TimeStamp"
        elementAttribute = ''.join(element.attrib.values())
        if 'TimeStamp' in elementAttribute:

            elementDate = element.find('from').text.encode('utf-8')
            elementDate = dt.datetime.strptime(elementDate, "%Y-%m-%dT%H:%M:%S.%fZ")

            elementLocatonID = element.find('location').find('item').find('id').text.encode('utf-8')
            elementLocatonID = int(elementLocatonID)

            weatherElements = element.find('location').find('item').find('weatherElement')
            for weatherElementItem in weatherElements.iter('item'):

                elementValue = weatherElementItem.find('value').text.encode('utf-8')
                elementValue = float(elementValue)

                elementID = weatherElementItem.find('id').text.encode('utf-8')

                if output in ['list', 'raw list']:
                    new_weatherElement = we.WeatherElement(elementLocatonID, elementDate, elementID, elementValue)
                    if output == 'list':
                        new_weatherElement.fix_data_quick()
                    weatherElementList.append(new_weatherElement)
                elif output == 'csv':
                    f.write('{0}\t{1}\t{2}\t{3}\n'.format(elementLocatonID, elementDate, elementID, elementValue))

    # Wrap up. Close files (xml file is allready closed) and return data if it exists
    if output == 'csv':
        f.close()
        return
    elif output in ['list', 'raw list']:
        return weatherElementList


if __name__ == "__main__":

    ### Examles ###
    #getMetData(19710, 'TAM', '2011-10-01', '2012-06-01', 0, 'xml')
    #getMetData(19710, 'SA',  '2011-10-01', '2012-06-01', 0, 'csv')
    #list = getMetData(19710, 'SA',  '2011-10-01', '2012-06-01', 0, 'list')
    # temp = getMetData(19710, 'TAM', '2011-10-01', '2012-06-01', 0, 'list')
    # sno = getMetData(19710, 'SA',  '2011-10-01', '2012-06-01', 0, 'list')
    # CC = getMetData(19710, 'NNM',  '2011-10-01', '2012-07-01', 0, 'list')
    # rr = getMetData(19710, 'RR',  '2011-10-01', '2012-06-01', 0, 'list')
    # elementsOn19710 = getElementsFromTimeserieTypeStation(19710, 0, 'list')
    # elementsOn18700 = getElementsFromTimeserieTypeStation(18700, 0, 'list')
    #elementsOnEvenes = getElementsFromTimeserieTypeStation(84970, 0, 'list')
    #getElementsFromTimeserieTypeStation(84970, 0, 'xml')
    #getElementsFromTimeserieTypeStation(19710, 0, 'csv')

    #list = getStationsFromTimeserieTypeElemCodes(2, ['QLI'], output='xml')
    list = getStationsFromTimeserieTypeElemCodes(2, ['QLI'], output='txt')
    list = getStationsFromTimeserieTypeElemCodes(2, ['QLI', 'RR_1', 'TA'], output='txt')



    a = 0
