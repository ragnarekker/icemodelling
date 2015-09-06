__author__ = 'raek'
# -*- coding: utf-8 -*-


import datetime


def strip_metadata(weather_element_list, get_dates=False):
    """
    Method takes inn a list of WeatherElement objects and strips away all metadata. A list of values is returned and if
    getDate = True a corresponding list of dates is also retuned.

    :param weather_element_list [list of weatherElements]:    List of elements of class WeatherElement
    :param get_dates [bool]:         if True dateList is returned also
    :return valueList, dateList:    dateList is otional and is returned if get_dates is True.
    """

    if get_dates == True:

        valueList = []
        dateList = []

        for e in weather_element_list:
            valueList.append(e.Value)
            dateList.append(e.Date)

        return valueList, dateList

    else:

        valueList = []

        for e in weather_element_list:
            valueList.append(e.Value)

        return valueList


def unit_from_okta(cloud_cover_in_okta_list):
    """
    Cloudcover from met.no is given in units of okta. Numbers 1-8. This method converts that list to values of units
    ranging from 0 to 1 where 1 is totaly overcast.

    NOTE: this conversion is also done in the weatherelelmnt class

    :param cloud_cover_in_okta_list:    cloudcover in okta stored in a list of weatherElements
    :return:                        cloudcover in units stored in a list of weatherElements
    """

    cloudCoverInUnitsList = []

    for we in cloud_cover_in_okta_list:
        if we.Value == 9:
            we.Value = None
        else:
            we.Value = we.Value/8

        we.Metadata.append({'Converted':'from okta to unit'})
        cloudCoverInUnitsList.append(we)

    return cloudCoverInUnitsList


def meter_from_centimeter(weather_element_list):
    """

    :param weather_element_list:
    :return:
    """
    weatherElementListSI = []

    for we in weather_element_list:
        we.Value = we.Value/100.
        we.Metadata.append({'Converted':'from cm to m'})
        weatherElementListSI.append(we)

    return weatherElementListSI


def make_daily_average(weather_element_list):
    """
    Takes a list of weatherelements with resolution less that 24hrs and calculates the dayly avarage
    of the timeseries.

    Tested on 30min periods and 1hr periods

    :param weather_element_list:      list of weatherelements with period < 24hrs
    :return newWeatherElementList:  list of weatherEleemnts averaged to 24hrs

    """

    # Sort list by date. Should not be neccesary but cant hurt.
    weather_element_list = sorted(weather_element_list, key=lambda weatherElement: weatherElement.Date)

    # Initialization
    date = weather_element_list[0].Date.date()
    value = weather_element_list[0].Value
    counter = 1
    lastindex = int(len(weather_element_list)-1)
    index = 0
    newWeatherElementList = []

    # go through all the elements and calculate the avarage of values with the same date
    for e in weather_element_list:

        # If on the same date keep on adding else add the avarage value and reinitialize counters on the new date
        if date == e.Date.date():
            value = value + e.Value
            counter = counter + 1

        else:

            # Make a datetime from the date
            datetimeFromDate = datetime.datetime.combine(date, datetime.datetime.min.time())

            # Make a new weatherelement and inherit relvant data from the old one
            newWeatherElement = WeatherElement(e.LocationID, datetimeFromDate, e.ElementID, value/counter)
            newWeatherElement.Metadata = e.Metadata
            newWeatherElement.Metadata.pop(0)  # first element is the original value form the input eatherelementlist
            newWeatherElement.Metadata.append({'DataManipulation':'24H Average from {0} values'.format(counter)})

            # Append it
            newWeatherElementList.append(newWeatherElement)

            date = e.Date.date()
            value = e.Value
            counter = 1

        # If its the last index add whats averaged so far
        if index == lastindex:

                # Make a datetime from the date
                datetimeFromDate = datetime.datetime.combine(date, datetime.datetime.min.time())

                # Make a new weatherelement and inherit relvant data from the old one
                newWeatherElement = WeatherElement(e.LocationID, datetimeFromDate, e.ElementID, value/counter)
                newWeatherElement.Metadata = e.Metadata
                newWeatherElement.Metadata.append({'DataManipulation':'24H Average from {0} values'.format(counter)})

                # Append it
                newWeatherElementList.append(newWeatherElement)

        index = index + 1

    return newWeatherElementList


def average_value(weather_element_list, lower_index, upper_index):
    """
    The method will return the avarage value of a list or part of a list with weatherElements

    :param weather_element_list:  List of weatherElements
    :param lower_index:          Start summing from this index (0 is first listindex)
    :param upper_index:          Stop summing from this index (-1 is last index)

    :return: avgToReturn:       The avarage value [float]

    """

    avgToReturn = 0

    for i in range(lower_index, upper_index, 1):
        avgToReturn = avgToReturn + weather_element_list[i].Value

    avgToReturn = avgToReturn/(upper_index-lower_index)

    return avgToReturn


class WeatherElement():

    '''
    A weatherElement object as they are defined in eKlima. The variables are:

    LocationID:     The location number. Preferably a int, but for NVE stations it may be a sting.
    Date:           Datetime object of the date of the weather element.
    ElementID:      The element ID. TAM og SA for met but may be numbers from NVE.
    Value:          The value of the weather element. Preferably in SI units.

    Special cases:
    ElementID = SA: Snødybde, totalt fra bakken, måles normalt på morgenen. Kode = -1 betyr snøbart, presenteres
                    som ".", -3 = "umulig å måle". This variable is also calulated from [cm] to [m]
    ElementID = RR: Precipitations has -1 for what seems to be noe precipitation. Are removed.
    ElementID = NNM:Average cloudcover that day (07-07). Comes from met.no in okta.

    '''

    def __init__(self, elementLocationID, elementDate, elementID, elementValue):

        self.LocationID = elementLocationID
        self.Date = elementDate
        self.ElementID = elementID
        self.Metadata = [{'OriginalValue':elementValue}]
        if elementValue == None:
            elementValue = 0
        self.Value = float(elementValue)

        # Snow is different
        if elementID == 'SA':
            if elementValue < 0.:
                self.Value = 0.
            else:
                self.Value = elementValue/100.

        # Rain seems to have a special treatment as well. Also, we use meter and not mm..
        if elementID == 'RR':
            if elementValue < 0.:
                self.Value = 0.
                self.Metadata.append({'On import':'removed negative value'})
            else:
                self.Value = elementValue/1000.

        # Clouds come in octas and should be in units (ranging from 0 to 1) for further use
        if elementID == 'NNM':
            if (elementValue == 9. or elementValue == -99999):
                self.Value = 0.
                self.Metadata.append({'On import':'unknown value replaced with 0.'})
            else:
                self.Value = self.Value/8.
                self.Metadata.append({'Converted':'from okta to unit'})




        # datacorrections. I found errors in data Im using from met
        if (self.Date).date() == datetime.date(2012, 02, 02) and self.ElementID == 'SA' and self.LocationID == 19710 and self.Value == 0.:
            self.Value = 0.45
            self.Metadata.append({"ManualValue":self.Value})

        if (self.Date).date() == datetime.date(2012, 03, 18) and self.ElementID == 'SA' and self.LocationID == 54710 and self.Value == 0.:
            self.Value = 0.89
            self.Metadata.append({"ManualValue":self.Value})

        if (self.Date).date() == datetime.date(2012, 12, 31) and self.ElementID == 'SA' and self.LocationID == 54710 and self.Value == 0.:
            self.Value = 0.36
            self.Metadata.append({"ManualValue":self.Value})


class EnergyBalanceElement():
    """
    Class for containing all variables and terms in the energy balance calculations.
    TODO: Energybalance object needs comments

    """
    def __init__(self, date_inn):
        self.date = date_inn

        self.iterations = None




    def add_model_input(self, utm33_x_inn, utm33_y_inn, snow_depth_inn, snow_density_inn,
                        temp_surface_inn, is_ice_inn,
                        temp_atm_inn, prec_inn, prec_snow_inn, cloud_cover_inn,
                        age_factor_tau_inn, albedo_prim_inn,
                        day_no_inn, time_hour_inn, time_span_in_sec_inn):
        self.utm33_x = utm33_x_inn
        self.utm33_y = utm33_y_inn
        self.snow_depth = snow_depth_inn            # Snowdepth on top of colunm. Not total snowdepth on land.
        self.snow_density = snow_density_inn
        self.temp_surface = temp_surface_inn
        self.is_ice = is_ice_inn
        self.cloud_cover = cloud_cover_inn
        self.temp_atm = temp_atm_inn
        self.prec = prec_inn
        self.prec_snow = prec_snow_inn
        self.age_factor_tau_before = age_factor_tau_inn
        self.albedo_prim_before = albedo_prim_inn
        self.day_no = day_no_inn
        self.time_hour = time_hour_inn
        self.time_span_in_sec = time_span_in_sec_inn

        return

    def add_iterations(self, iterations_inn):
        self.iterations = iterations_inn


    def add_no_energy_balance(self, is_ice_inn):
        self.is_ice = is_ice_inn
        self.EB = None



    def add_short_wave(self, S_inn, s_inn_inn, albedo_inn, albedo_prim_inn, age_factor_tau_inn):
        self.S = S_inn
        self.s_inn = s_inn_inn
        self.albedo = albedo_inn
        self.albedo_prim = albedo_prim_inn
        self.age_factor_tau = age_factor_tau_inn

        return


    def add_long_wave(self, L_a_inn, L_t_inn):
        self.L_a = L_a_inn
        self.L_t = L_t_inn

        return


    def add_sensible_and_latent_heat(self, H_inn, LE_inn):
        self.H = H_inn
        self.LE = LE_inn

        return

    def add_ground_heat(self, G_inn):
        self.G = G_inn

        return

    def add_prec_heat(self, R_inn):
        self.R = R_inn

        return

    def add_cold_content(self, SS_inn):
        self.SS = SS_inn

        return


    def add_surface_heat_conduction(self, SC_inn, conductance_inn):
        self.SC = SC_inn
        self.conductance = conductance_inn

        return


    def add_energy_budget(self, EB_inn):
        self.EB = EB_inn
