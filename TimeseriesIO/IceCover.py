__author__ = 'ragnarekker'

import TimeseriesIO as TIO

class IceCover:

    def __init__(self, date_inn, iceCoverName_inn, iceCoverBeforeName_inn, locationName_inn):
        self.date = date_inn
        self.iceCoverName = iceCoverName_inn
        self.iceCoverTID = TIO.getTIDfromName('IceCoverKDV', 1, iceCoverName_inn)
        self.iceCoverBeforeName = iceCoverBeforeName_inn
        self.iceCoverBeforeTID = TIO.getTIDfromName('IceCoverBeforeKDV', 1, iceCoverBeforeName_inn)
        self.locationName = locationName_inn

        self.RegID = None

    def set_regid(self, regid_inn):
        self.RegID = regid_inn
