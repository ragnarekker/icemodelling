__author__ = 'ragnarekker'

from getRegObsdata import getTIDfromName

class IceCover:

    date = 0
    iceCoverTID = 0
    iceCoverName = ""
    iceCoverBeforeTID = 0
    iceCoverBeforeName = ""
    locationName = ""

    def __init__(self, date_inn, iceCoverName_inn, iceCoverBeforeName_inn, locationName_inn):
        self.date = date_inn
        self.iceCoverName = iceCoverName_inn
        self.iceCoverTID = getTIDfromName('IceCoverKDV', 1, iceCoverName_inn)
        self.iceCoverBeforeName = iceCoverBeforeName_inn
        self.iceCoverBeforeTID = getTIDfromName('IceCoverBeforeKDV', 1, iceCoverBeforeName_inn)
        self.locationName = locationName_inn
