# -*- coding: utf-8 -*-
from utilities import getmisc as gm
from utilities import getregobsdata as gro
from icemodellingscripts import calculateandplot as cap
from utilities import makepickle as mp
import setenvironment as se

import pandas as pd

__author__ = 'ragnarekker'


class ObsCalMLData:
    """Class for handling data in the ...

    """

    def __init__(self, calculated_ice_inn, observed_ice_inn):

        self.calculated_ice = calculated_ice_inn
        self.observed_ice = observed_ice_inn

        self.date = None

        self.calculated_draft = None
        self.observed_draft = None
        self.draft_difference = None
        self.calculated_snow = None
        self.observed_snow = None
        self.snow_difference = None

        self.regobs_id = None
        self.regobs_name = None
        self.regobs_elevation = None
        self.utm_n = None
        self.utm_e = None
        self.utm_zone = None

        self.lake_info = None
        self.lake_type = None
        self.lake_name = None
        self.lake_elevation = None
        self.lake_area = None
        self.lake_circumference = None

        self.set_draft_thickness()
        self.set_date()
        self.set_location()
        self.get_lake_info()

    def set_draft_thickness(self):
        self.calculated_draft = float(max(self.calculated_ice.draft_thickness, 0.))
        self.observed_draft = float(max(self.observed_ice.draft_thickness, 0.))
        self.draft_difference = self.calculated_draft-self.observed_draft

        self.calculated_snow = 0
        if self.calculated_ice.column:
            if 'snow' in self.calculated_ice.column[0].type:
                self.calculated_snow = self.calculated_ice.column[0].height/100     # cm to meters

        self.observed_snow = 0
        if self.observed_ice.column:
            if 'snow' in self.observed_ice.column[0].type:
                self.observed_snow = self.observed_ice.column[0].height/100         # cm to meters

        self.snow_difference = self.calculated_snow-self.observed_snow

    def set_date(self):
        self.date = self.observed_ice.date.date()

    def set_location(self):
        self.regobs_id = self.observed_ice.metadata['LocationID']
        self.regobs_name = self.observed_ice.metadata['LocationName']
        self.regobs_elevation = self.observed_ice.metadata['OriginalObject']['LocationHeight']
        self.utm_e = self.observed_ice.metadata['UTMEast']
        self.utm_n = self.observed_ice.metadata['UTMNorth']
        self.utm_zone = self.observed_ice.metadata['UTMZone']

    def get_lake_info(self):
        self.lake_info = gm.get_lake_info(self.utm_e, self.utm_n, reference=32633)

        if self.lake_info:
            self.lake_type = self.lake_info['objektType']
            self.lake_name = self.lake_info['navn']
            self.lake_elevation = self.lake_info['hoyde']
            self.lake_area = self.lake_info['Shape.STArea()']
            self.lake_circumference = self.lake_info['Shape.STLength()']

    def to_dict(self):
        """Convert the object to a dictionary.

        :return: dictionary representation of the WaterLevel class
        """

        _dict = {'date': self.date,
                 'regobs_id': self.regobs_id,
                 'regobs_name': self.regobs_name,
                 'regobs_elevation': self.regobs_elevation,
                 'calculated_draft': self.calculated_draft,
                 'observed_draft': self.observed_draft,
                 'draft_difference': self.draft_difference,
                 'calculated_snow': self.calculated_snow,
                 'observed_snow': self.observed_snow,
                 'snow_difference': self.snow_difference,
                 'utm_n': self.utm_n,
                 'utm_e': self.utm_e,
                 'utm_zone': self.utm_zone,
                 'lake_type': self.lake_type,
                 'lake_name': self.lake_name,
                 'lake_elevation': self.lake_elevation,
                 'lake_areas': self.lake_area,
                 'lake_circumference': self.lake_circumference
                }

        return _dict
        

def make_observation_and_calculation_on_location():

    years = ['2014-15', '2015-16', '2016-17', '2017-18', '2018-19']
    make_plots = False
    get_new_obs = False
    calculate_new = False
    data = []

    for year in years:

        pickle_file_name_and_path = '{0}all_calculated_ice_{1}.pickle'.format(se.local_storage, year)

        all_observations = gro.get_all_season_ice(year, get_new=get_new_obs)
        from_date, to_date = gm.get_dates_from_year(year)
        all_calculated = {}
        all_observed = {}       # will eventually become the same as all_observations

        if calculate_new:
            for location_id, observed_ice in all_observations.items():

                calculated, observed, plot_filename = cap._plot_season(
                    location_id, from_date, to_date, observed_ice, make_plots=make_plots,
                    plot_folder=se.sesong_plots_folder)
                all_calculated[location_id] = calculated
                all_observed[location_id] = observed

                mp.pickle_anything([all_calculated, all_observed], pickle_file_name_and_path)

        else:
            [all_calculated, all_observed] = mp.unpickle_anything(pickle_file_name_and_path)

        for ln in all_observed.keys():
            skipp_first = True

            for oi in all_observed[ln]:

                if skipp_first:
                    skipp_first = False     # first observation is that of the initial ice
                else:
                    for ci in all_calculated[ln]:
                        if ci.date.date() == oi.date.date():
                            data_point = ObsCalMLData(ci, oi)
                            data.append(data_point)

    df = pd.DataFrame([d.to_dict() for d in data])
    csv_file_name = r'{0}all_observed_and_calculated_ice_{1}-{2}.csv'.format(se.data_sets_folder, years[0][:4], years[-1][5:])
    export_csv = df.to_csv(csv_file_name, sep=';', index=None, header=True)

    a = 1


if __name__ == "__main__":

    make_observation_and_calculation_on_location()
