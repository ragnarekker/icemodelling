__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import requests
from lxml import etree
import datetime
from weather import WeatherElement, unit_from_okta
import xml.etree.ElementTree as ET      # used in the incomplete methods
from setEnvironment import data_path

# Incomplete
def getElementsProperties():
    url = "http://eklima.met.no/metdata/MetDataService?invoke=getElementsProperties&language=&elem_codes="
    ws = requests.get(url)

    # print ws.text
    filename = 'ElementsProperties.xml'

    f = open(filename, 'w')
    f.write((ws.text).encode('utf-8'))
    f.close()

    tree = ET.parse(filename)
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
    ws = requests.get(url)

    # print ws.text
    filename = '{0}TimeseriesTypesProperties.xml'.format(data_path)

    f = open(filename, 'w')
    f.write((ws.text).encode('utf-8'))
    f.close()

    tree = ET.parse(filename)
    root = tree.getroot()

    filename = '{0}TimeseriesTypesProperties.csv'.format(data_path)
    f = open(filename, 'w')
    for element in root.iter('item'):
        Name = (element.find('serieTypeName').text).encode('utf-8')
        ID = (element.find('serieTypeID').text).encode('utf-8')
        Description = (element.find('serieTypeDescription').text).encode('utf-8')
        f.write('{0}\t{1}\t{2}\n'.format(Name, ID, Description))

    f.close()

# Incomplete
def getStationsFromTimeserieTypeElemCodes():
    url = "http://eklima.met.no/metdata/MetDataService?invoke=getStationsFromTimeserieTypeElemCodes&timeserietypeID=0&elem_codes=ss_24%2C+tam&username="
    # Asker har id 19710 og Blindern 18700


def getElementsFromTimeserieTypeStation(stationID, timeseriesType, output='list'):
    """
    Gets availabe weather elements on a given met station.

    Parameters and return:
        :param stationID:       The station number.
        :param timeseriesType:  The timeserie type to be requested. Eg 0 is daily avarage.
        :param output:          3 types of output are available.
        :return:                A list of weatherElements or makes files that are saved to the working directory.

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

    NOTE that if you only which to read data for a given station check out
    http://eklima.met.no/eklimapub/servlet/ReportInfo?action=parameterinfo&tab=T_ELEM_DIURNAL&s=19710&la=no&co=NO
    """

    url = "http://eklima.met.no/metdata/MetDataService?invoke=getElementsFromTimeserieTypeStation&timeserietypeID={1}&stnr={0}"\
        .format(stationID, timeseriesType)
    wsKlimaRequest = requests.get(url)

    # Check which output option is requested
    if output == 'list':
        stationElementList = []
    elif output == 'xml':
        filename = '{0}Elements on {1}_{2}.xml'.format(data_path, stationID, timeseriesType)
        f = open(filename, 'w')
        f.write((wsKlimaRequest.text).encode('utf-8'))
        f.close()
        return
    elif output == 'csv':
        filename = '{0}Elements on {1}_{2}.csv'.format(data_path, stationID, timeseriesType)
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
        fromdate = datetime.datetime.strptime(tempfromdate[0:10],  "%Y-%m-%d")

        temptodate = element.find('todate').text
        if temptodate == None:
            todate = None
        else:
            todate = datetime.datetime.strptime(temptodate[0:10], "%Y-%m-%d")

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

    # Wrap up. Close files (xml file is allready closed) and return data if it exists
    if output == 'csv':
        f.close()
        return
    elif output == 'list':
        return stationElementList


def getMetData(stationID, elementID, fromDate, toDate, timeseriesType, output='list'):
    '''
    The method uses the eklima webservice from met.no documented om eklims.met.no/wsklima

    Parameters and return:
        :param stationID:       The station number
        :param elementID:       The weather element code
        :param fromDate:        The from date as string 'YYYY-MM-DD' or datetime
        :param toDate:          The to date as string 'YYYY-MM-DD' or datetime
        :param timeseriesType:  The timeserie type to be requested. Eg 0 is daily avarage.
        :param output:          3 types of output are available.
        :return:                A list of weatherElements or files are made to working directory.

    Output options:
        'list':         returns a list of WeatherElement objects (default).
        'xml':          returns NULL but saves a .xml file to the working folder.
        'csv':          returns NULL but saves a .csv file to the working folder. The separation value are tab

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

    url = "http://eklima.met.no/metdata/MetDataService?invoke=getMetData&timeserietypeID={4}&format=&from={2}&to={3}&stations={0}&elements={1}&hours=&months=&username="\
        .format(stationID, elementID, fromDate, toDate, timeseriesType)
    wsKlimaRequest = requests.get(url)

    # Check which output option is requested
    if output == 'list':
        weatherElementList = []
    elif output == 'xml':
        filename = '{0}{1}_{2}_{3}_{4}.xml'.format(data_path, stationID, elementID, fromDate, toDate)
        f = open(filename, 'w')
        f.write((wsKlimaRequest.text).encode('utf-8'))
        f.close()
        return
    elif output == 'csv':
        filename = '{0}{1}_{2}_{3}_{4}.csv'.format(data_path, stationID, elementID, fromDate, toDate)
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
            elementDate = datetime.datetime.strptime(elementDate, "%Y-%m-%dT%H:%M:%S.%fZ")

            elementLocatonID = element.find('location').find('item').find('id').text.encode('utf-8')
            elementLocatonID = int(elementLocatonID)

            weatherElements = element.find('location').find('item').find('weatherElement')
            for weatherElementItem in weatherElements.iter('item'):

                elementValue = weatherElementItem.find('value').text.encode('utf-8')
                elementValue = float(elementValue)

                elementID = weatherElementItem.find('id').text.encode('utf-8')

                if output == 'list':
                    weatherElementList.append(WeatherElement(elementLocatonID, elementDate, elementID, elementValue))

                elif output == 'csv':
                    f.write('{0}\t{1}\t{2}\t{3}\n'.format(elementLocatonID, elementDate, elementID, elementValue))

    # Wrap up. Close files (xml file is allready closed) and return data if it exists
    if output == 'csv':
        f.close()
        return
    elif output == 'list':
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
    getElementsFromTimeserieTypeStation(19710, 0, 'csv')


    a = 0
