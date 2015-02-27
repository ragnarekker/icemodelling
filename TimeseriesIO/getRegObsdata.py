__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

import requests
import datetime
import re


def getIceCover(LocationName):

    # http://api.nve.no/hydrology/regobs/v0.9.4/Odata.svc/IceCoverObsV?$filter=
    # DtObsTime%20gt%20datetime%272013-11-01%27%20and%20
    # DtObsTime%20lt%20datetime%272014-06-01%27%20and%20
    # LocationName%20eq%20%27Hakkloa%20nord%20372%20moh%27%20and%20
    # LangKey%20eq%201


    startDate = datetime.datetime(2013, 11, 1)
    endDate = datetime.datetime(2014, 6, 1)
    apiVersion = "v0.9.4"
    view = 'IceCoverObsV'


    oDataStartDate = datetime.datetime.strftime(startDate, "%Y-%m-%d")
    oDataEndDate = datetime.datetime.strftime(endDate, "%Y-%m-%d")
    oDataLocationName = LocationName
    oDataQuery = "DtObsTime gt datetime'{0}' and " \
                 "DtObsTime lt datetime'{1}' and " \
                 "LocationName eq '{2}' and " \
                 "LangKey eq 1".format(oDataStartDate, oDataEndDate, oDataLocationName)

    # get data for current view and dates
    url = "http://api.nve.no/hydrology/regobs/{0}/Odata.svc/{2}?$filter={1}".decode('utf8').format(apiVersion, oDataQuery, view)
    data = requests.get(url)

    # Take the request and split up all entries and look for keywords
    datatext = data.text
    datatext = re.sub('</entry>', '', datatext)     # removes the close tag
    datalist = datatext.split('<entry>')
    datalist.pop(0) #  take the top which is not an obs

    for ic in datalist:
        # select the datetime and the icecovername and add to dictionary

    a= 1



if __name__ == "__main__":

    getIceCover('Hakkloa nord 372 moh')