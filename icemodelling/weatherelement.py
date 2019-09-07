# -*- coding: utf-8 -*-
"""Methods for handling weather data and time series of these."""

import datetime as dt
from utilities import makelogs as ml, getgts as gts, makeplots as mplots
from icemodelling import constants as const

__author__ = 'Ragnar Ekker'


class WeatherElement:
    """All weather data for the model is given as lists of weatherElement object.

    The structure is similar to as they are defined in eKlima. The variables are:

    LocationID:     The location number. Preferably a int, but for NVE stations it may be a sting.
    Date:           Datetime object of the date of the weather element.
    ElementID:      The element ID. TAM og SA for met but may be numbers from NVE data.
    Value:          The value of the weather element. Preferably in SI units.

    Special cases:
    ElementID = SA: Snødybde, totalt fra bakken, måles normalt på morgenen. Kode = -1 betyr snøbart, presenteres
                    som ".", -3 = "umulig å måle". This variable is also calulated from [cm] to [m]
    ElementID = RR: Precipitations has -1 for what seems to be noe precipitation. Are removed.
    ElementID = NNM:Average cloudcover that day (07-07). Comes from met.no in okta.

    Handling data errors:
    The constructor looks for some known cases that gives errors and corrects them so that the data set returned is
    complete."""

    def __init__(self, elementLocationID, elementDate, elementID, elementValue):

        self.LocationID = elementLocationID
        self.Date = elementDate
        self.ElementID = elementID
        self.Metadata = {'OriginalValue': elementValue}  # Metadata given as dictionary {key:value , key:value, ... }
        self.Value = elementValue
        if elementValue is not None:
            self.Value = float(elementValue)

            # Met snow is in [cm] and always positive. Convert to [m]
            if elementID == 'SA':
                if elementValue >= 0.:
                    self.Value = elementValue / 100.
                    self.Metadata['Converted'] = 'from cm to m'

            # Met rain is in [mm] and always positive. We use SI and [m]; not [mm].
            if elementID in ['RR','RR_1']:
                if self.Value > 0.:
                    self.Value = elementValue / 1000.
                    self.Metadata['Converted'] = 'from mm to m'

            # Clouds come in oktas and should be in units (ranging from 0 to 1) for further use
            if elementID == 'NNM':
                if self.Value not in [9., -99999.]:
                    percent = int(self.Value/8*100)
                    self.Value = percent/100.
                    self.Metadata['Converted'] = 'from okta to unit'

    def fix_data_quick(self):

        if self.Value is None:
            self.Value = 0.

        # These values should always be positive. -99999 is often used as unknown number in eklima.
        # RR = 0 or negligible precipitation. RR = -1 is noe precipitation observed.
        if self.ElementID in ['SA', 'RR', 'RR_1', 'QLI', 'QSI']:
            if self.Value < 0.:
                self.Value = 0.
                self.Metadata['Value manipulation'] = 'removed negative value'

        # Clouds come in oktas and should be in units (ranging from 0 to 1) for further use
        if self.ElementID == 'NNM':
            if self.Value in [9., -99999]:
                self.Value = 0.
                self.Metadata['On import'] = 'unknown value replaced with 0.'

        # data corrections. I found errors in data Im using from met
        if (self.Date).date() == dt.date(2012, 2, 2) and self.ElementID == 'SA' and self.LocationID == 19710 and self.Value == 0.:
            self.Value = 0.45
            self.Metadata['ManualValue'] = self.Value

        if (self.Date).date() == dt.date(2012, 3, 18) and self.ElementID == 'SA' and self.LocationID == 54710 and self.Value == 0.:
            self.Value = 0.89
            self.Metadata['ManualValue'] = self.Value

        if (self.Date).date() == dt.date(2012, 12, 31) and self.ElementID == 'SA' and self.LocationID == 54710 and self.Value == 0.:
            self.Value = 0.36
            self.Metadata['ManualValue'] = self.Value

    def add_metadata(self, key, value):
        """Add metadata of any kind to the weather element. Meta data is stored as a dictionary.

        :param key:
        :param value:
        """

        self.Metadata[key] = value

    def add_weather_data_altitude(self, altitude):
        """

        :param altitude:    [float or int] in meters above sea level
        :return:
        """

        self.Metadata['WeatherDataAltitude'] = altitude


def strip_metadata(weather_element_list, get_date_times=False):
    """Method takes inn a list of WeatherElement objects and returns a list of values.
    If getDate = True a corresponding list of dates is also returned.

    :param weather_element_list:    [list] List of elements of class WeatherElement
    :param get_date_times:          [bool] if True, a list of datetimes is returned
    :return value_list, date_list:  [list(s)] date_list is optional and is returned if get_dates is True.
    """

    if len(weather_element_list) == 0:
        ml.log_and_print("[warning] weatherelement.py -> strip_metadata: weather_element_list of len=0")
        return [], []

    if get_date_times:

        value_list = []
        date_list = []

        for e in weather_element_list:
            value_list.append(e.Value)
            date_list.append(e.Date)

        return value_list, date_list

    else:

        value_list = [e.Value for e in weather_element_list]

        return value_list


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
            we.Value = we.Value / 8

        we.Metadata.append({'Converted': 'from okta to unit'})
        cloudCoverInUnitsList.append(we)

    return cloudCoverInUnitsList


def meter_from_centimeter(weather_element_list):
    """Converts cm to meters in a WeatherElement list

    :param weather_element_list:
    :return:
    """
    weatherElementListSI = []

    for we in weather_element_list:
        if we.Value is not None:
            we.Value = we.Value / 100.
            we.Metadata['Converted'] = 'from cm to m'
        weatherElementListSI.append(we)

    return weatherElementListSI


def millimeter_from_meter(weather_element_list):
    """Converts meters to millimeter on precipitation data [RR and RR_1] in a WeatherElement list

    :param weather_element_list:
    :return:
    """
    weatherElementListOut = []

    for we in weather_element_list:
        if we.ElementID in ['RR', 'RR_1']:
            if we.Value >= 0:
                we.Value = we.Value * 1000.
                we.Metadata['Converted'] = 'from m to mm'
        weatherElementListOut.append(we)

    return weatherElementListOut


def adjust_temperature_to_new_altitude(weather_element_list, new_altitude):
    """If the weather parameter represents a different altitude, adjust the time series to a new altitude
    given a laps rate given in constants.

    :param weather_element_list:
    :param new_altitude:
    :return:
    """

    if len(weather_element_list) == 0:
        ml.log_and_print("[warning] weatherelement.py -> adjust_temperature_to_new_altitude: weather_element_list of len=0")
        return weather_element_list

    if new_altitude is None:
        ml.log_and_print("[warning] weatherelement.py -> adjust_temperature_to_new_altitude: new_element=None and no adjustments made.")
        return weather_element_list

    else:
        original_altitude = weather_element_list[0].Metadata['WeatherDataAltitude']
        temp_delta = (new_altitude - original_altitude) * const.laps_rate

        for we in weather_element_list:
            original_value = we.Value
            we.Value -= temp_delta
            we.Metadata['WeatherDataAltitude'] = new_altitude
            we.Metadata['OriginalAltitude'] = original_altitude
            we.Metadata['AltitudeAdjustment'] = 'Adjusting elevation by {0} m, thus also temp from {1}C to {2}C.'.format(new_altitude-original_altitude, original_value, we.Value)

        # ml.log_and_print("[info] weatherelement.py -> adjust_temperature_to_new_altitude: old:{0}masl and new:{1}masl and tempdelta:{2}C".format(original_altitude, new_altitude, temp_delta))
        return weather_element_list


def make_daily_average(weather_element_list, time_resolution=None):
    """Takes a list of WeatherElements with resolution less that 24hrs and calculates the dayly avarage
    of the timeseries.

    :param weather_element_list:        list of WeatherElements with period < 24hrs
    :param time_resolution:             int time resolution of the initial list in seconds
    :return new_weather_element_list:   list of WeatherElements averaged to 24hrs
    """

    # Sort list by date. Should not be necessary but cant hurt.
    weather_element_list = sorted(weather_element_list, key=lambda weatherElement: weatherElement.Date)
    new_weather_element_list = []

    if not time_resolution:
        time_resolution = int((weather_element_list[1].Date - weather_element_list[0].Date).total_seconds())

    # Remove values of None
    weather_element_list = [e for e in weather_element_list if e.Value is not None]

    # Only make data if there is data
    if len(weather_element_list) > 0:

        # go through all the elements and calculate the average of values with the same date
        for i, e in enumerate(weather_element_list):

            if i == 0:
                current_time = e.Date
                midnight = dt.datetime.combine(current_time.date(), dt.datetime.min.time())
                seconds_today = (current_time - midnight).seconds
                if seconds_today < time_resolution: # ie the current value represents also yesterday
                    value = e.Value
                    seconds_today = time_resolution - seconds_today

                    # Make a new weather element for yesterday and inherit relevant data from the old one
                    new_weather_element = WeatherElement(e.LocationID, midnight + dt.timedelta(seconds=-1), e.ElementID, value)
                    new_weather_element.Metadata = e.Metadata
                    new_weather_element.Metadata['DataManipulation'] = 'Made 00-24H average with data for {}% of 24hrs.'.format(seconds_today/(60*60*24)*100)
                    new_weather_element_list.append(new_weather_element)

                    # start fresh counting values and seconds
                    seconds_to_go = (current_time - midnight).total_seconds()
                    value = e.Value * seconds_to_go
                    seconds_today = seconds_to_go

                else:
                    value = e.Value * time_resolution
                    seconds_today = time_resolution

            # note that a value is timestamped at the end of the period it represents
            else:  # ie i > 0
                current_time = e.Date
                previous_time = weather_element_list[i-1].Date

                # if value is on the same date as the previous
                if previous_time.date() == current_time.date():
                    seconds_with_current_value = (current_time - previous_time).total_seconds()
                    value += e.Value * seconds_with_current_value
                    seconds_today += seconds_with_current_value

                # else it is on a new day and we add a fraction to the value and
                # initialize a new value with whats on the current date.
                else:

                    midnight = dt.datetime.combine(current_time.date(), dt.datetime.min.time())
                    seconds_in_previous_day = (midnight - previous_time).total_seconds()
                    value += e.Value * seconds_in_previous_day
                    seconds_today += seconds_in_previous_day

                    # Make a new weatherelement and inherit relevant data from the old one
                    dayly_avarage_value = value/seconds_today
                    new_weather_element = WeatherElement(e.LocationID, midnight + dt.timedelta(seconds=-1), e.ElementID, dayly_avarage_value)
                    new_weather_element.Metadata = e.Metadata
                    new_weather_element.Metadata['DataManipulation'] = 'Made 00-24H average with data for {}% of 24hrs.'.format(seconds_today/(60*60*24)*100)
                    new_weather_element_list.append(new_weather_element)

                    # start fresh counting values and seconds
                    seconds_to_go = (current_time - midnight).total_seconds()
                    value = e.Value * seconds_to_go
                    seconds_today = seconds_to_go

        # take whats left in value and secondstoday and make a new weather element
        dayly_avarage_value = value / seconds_today
        new_weather_element = WeatherElement(e.LocationID, midnight + dt.timedelta(days=1) + dt.timedelta(seconds=-1), e.ElementID, dayly_avarage_value)
        new_weather_element.Metadata = e.Metadata
        new_weather_element.Metadata['DataManipulation'] = 'Made 00-24H average with data for {}% of 24hrs.'.format(seconds_today/(60*60*24)*100)
        new_weather_element_list.append(new_weather_element)

        return new_weather_element_list

    # if no data, return the list unchanged
    else:
        return weather_element_list


def fix_data_quick(weather_element_list):

    for we in weather_element_list:
        we.fix_data_quick()

    return weather_element_list


def multiply_constant(weather_element_list, constant):

    for we in weather_element_list:
        we.Value = we.Value * constant
        we.Metadata.append({'Multiplied by {0}.'.format(constant)})

    return weather_element_list


def average_value(weather_element_list, lower_index, upper_index):
    """The method will return the avarage value of a list or part of a list with weatherElements

    :param weather_element_list:  List of weatherElements
    :param lower_index:          Start summing from this index (0 is first listindex)
    :param upper_index:          Stop summing from this index (-1 is last index)

    :return: avgToReturn:       The avarage value [float]

    """

    avgToReturn = 0

    for i in range(lower_index, upper_index, 1):
        avgToReturn = avgToReturn + weather_element_list[i].Value

    avgToReturn = avgToReturn / (upper_index - lower_index)

    return avgToReturn


def constant_weather_element(location, from_date, to_date, parameter, value):
    """Creates a list of weather elements of constant value over a period. Also, if None is passed
    it creates a list of None weatherelements.

    :param location:
    :param from_date:
    :param to_date:
    :param parameter:
    :param value:
    :return:
    """

    delta = to_date - from_date
    dates = []
    for i in range(delta.days + 1):
        dates.append(from_date + dt.timedelta(days=i))

    weather_element_list = []
    for d in dates:
        element = WeatherElement(location, d, parameter, value)
        if value is None:
            element.Metadata['No value'] = 'from {0} to {1}'.format(from_date.date(), to_date.date())
        else:
            element.Metadata['Constant value'] = 'from {0} to {1}'.format(from_date.date(), to_date.date())
        weather_element_list.append(element)

    return weather_element_list


def patch_novalue_in_weather_element_list(weather_element_list):
    """If the data provider sends a gapless data sett where no value is given as None in WeatherElement lists
    with gaps, this will patch it up. Simple patching using nearest neighbour values/avarages.

    :param weather_element_list:
    :return: weather_element_list
    """

    log_reference = 'weatherelement.py -> patch_novalue_in_weather_element_list: '
    location_id = weather_element_list[0].LocationID
    element_id = weather_element_list[0].ElementID

    # make sure we have first value
    if weather_element_list[0].Value is None:
        looker = 1
        replacement = weather_element_list[0 + looker].Value

        while replacement is None:
            looker += 1

            if looker > len(weather_element_list)-1:    # case of all values are None
                ml.log_and_print('{}No values in WeatherElement list. Patching not posiible. {} {}'.format(log_reference, location_id,element_id))
                return weather_element_list

            replacement = weather_element_list[0 + looker].Value

        weather_element_list[0].Value = replacement
        weather_element_list[0].Metadata['Value patched'] = 'First element missing. Use the next element with value {}'.format(replacement)
        ml.log_and_print('{}First date value missing on {} {} {}. Adding value {}.'.format(log_reference, location_id, weather_element_list[0].Date, element_id, replacement))

    # and the last value
    if weather_element_list[-1].Value is None:
        looker = 1
        replacement = weather_element_list[-1 - looker].Value

        while replacement is None:
            looker += 1
            replacement = weather_element_list[-1 - looker].Value

        weather_element_list[-1].Value = replacement
        weather_element_list[-1].Metadata['Value patched'] = 'Last element missing. Use the previous element with value {}'.format(replacement)
        ml.log_and_print('{}Las date value missing on {} {} {}. Adding value {}.'.format(log_reference, location_id, weather_element_list[-1].Date, element_id, replacement))

    # then check the ones in the middle
    for i, we in enumerate(weather_element_list):

        if we.Value is None:
            previous_value = weather_element_list[i-1].Value
            looker = 1
            next_value = weather_element_list[i + looker].Value
            while next_value is None:
                looker += 1
                next_value = weather_element_list[i + looker].Value
            average_value = previous_value + 1/(2*looker)*(next_value-previous_value)   # weight next value less if looker has gone looking.
            weather_element_list[i].Value = average_value
            weather_element_list[i].Metadata['Value patched'] = 'Use average value {}'.format(average_value)
            ml.log_and_print('{}Value missing on {} {} {}. Adding avg value {}.'.format(log_reference, location_id, weather_element_list[i].Date, element_id, average_value))

    return weather_element_list


def patch_weather_element_list(weather_element_list, from_date=None, to_date=None, time_step=24*60*60):
    """If the dataprovider sends data with gaps, this may patch it up. Simple patching using nearest
    neighbour values/avarages. WORKS ONLY ON 24hrs VALUES

    :param weather_element_list:
    :param from_date:
    :param to_date:
    :param time_step:
    :return: weather_element_list
    """

    log_reference = 'weatherelement.py -> patch_weather_element_list: '

    if from_date is None:
        from_date = weather_element_list[0].Date
    if to_date is None:
        to_date = weather_element_list[-1].Date

    # if dates are strings change to date times
    if isinstance(from_date, str):
        from_date = dt.datetime.strptime(from_date, '%Y-%m-%d').date()
    if isinstance(to_date, str):
        to_date = dt.datetime.strptime(to_date, '%Y-%m-%d').date()

    if isinstance(from_date, dt.datetime):
        from_date = from_date.date()
    if isinstance(to_date, dt.datetime):
        to_date = to_date.date()

    dates_range = to_date - from_date
    dates = []
    for i in range(dates_range.days + 1):
        dates.append(from_date + dt.timedelta(seconds=time_step * i))

    location_id = weather_element_list[0].LocationID
    element_id = weather_element_list[0].ElementID

    if len(weather_element_list) == len(dates):          # No patching needed
        return weather_element_list

    if len(weather_element_list)/len(dates) < 0.95:
        # on short time series the 5% missing rule is to hard.
        if len(dates) - len(weather_element_list) > 3:
            ml.log_and_print('{}More than 5% and more than 3 days missing on {} for {} during {}-{}'.format(log_reference, location_id, element_id, from_date, to_date))
            return weather_element_list

    i = 0
    j = 0

    # make sure we have a last value
    if dates[-1] > weather_element_list[-1].Date.date():
        element_value = weather_element_list[-1].Value
        dates_date_time = dt.datetime.combine(dates[-1], dt.datetime.min.time())
        weather_element_list.append(WeatherElement(location_id, dates_date_time, element_id, element_value))
        ml.log_and_print('{}Last date data missing on {} {} {}. Adding value {}.'.format(log_reference, location_id, dates_date_time, element_id, element_value))

    while i < len(dates):
        dates_date = dates[i]
        weather_date = weather_element_list[j].Date.date()

        if weather_date == dates_date:
            i += 1
            j += 1
        else:
            if j == 0:      # if the first element is missing
                element_value = weather_element_list[j].Value
                meta_data = 'First elelment missing. Copying value of second first element to first index.'
                ml.log_and_print('{}First date data missing on {} {} {}. Adding value {}.'.format(log_reference, location_id, dates_date, element_id, element_value))
                i += 1
            else:           # else add a avarage value
                element_value = (weather_element_list[j].Value + weather_element_list[j-1].Value)/2
                meta_data = 'Elelment missing. Ading avarage og values before and after.'
                ml.log_and_print('{}Date data missing on {} {} {}. Adding value {}.'.format(log_reference, location_id, dates_date, element_id, element_value))
                i += 1

            dates_date_time = dt.datetime.combine(dates_date, dt.datetime.min.time())
            we = WeatherElement(location_id, dates_date_time, element_id, element_value)
            we.Metadata['Value patched'] = meta_data
            weather_element_list.append(we)

    weather_element_list = sorted(weather_element_list, key=lambda weatherElement: weatherElement.Date)

    return weather_element_list


def test_for_missing_elements(weather_element_list, from_date=None, to_date=None, time_step=24*60*60):
    """Tests a list of weather elements if some elements are missing. Should work on all time steps, but 24hrs
    (in seconds) is default. If a missing element is found, message is returned.

    :param weather_element_list:
    :param from_date:               [datetime]
    :param to_date:                 [datetime]
    :param time_step:
    :return:
    """

    if from_date is None:
        from_date = weather_element_list[0].Date
    if to_date is None:
        to_date = weather_element_list[-1].Date

    dates_range = to_date - from_date
    dates = []
    for i in range(dates_range.days):
        dates.append(from_date + dt.timedelta(seconds=time_step * i))

    i = 0
    j = 0

    messages = []

    while i < len(dates):
        dates_date = dates[i]
        weather_date = weather_element_list[j].Date

        if weather_date == dates_date:
            i += 1
            j += 1
        else:
            message = '{0}/{1} missing on {2}'.format(
                weather_element_list[j].LocationID, weather_element_list[j].ElementID, dates[i])
            #print(message)
            messages.append({'Missing data': message})
            i += 1

    if i == j:
        messages.append({'No missing data': 'on {0}/{1}'.format(
            weather_element_list[0].LocationID, weather_element_list[0].ElementID)})

    return messages


def _test_patch_nodata_weather_element_list():

    import copy as copy
    weather_data = gts.getgts(109190, 6817490, 'tm', '2017-12-20', '2018-01-06')
    weather_data_for_fix = copy.deepcopy(weather_data)
    weather_data_for_fix[0].Value = None
    weather_data_for_fix[4].Value = None
    weather_data_for_fix[5].Value = None
    weather_data_for_fix[6].Value = None
    weather_data_for_fix[7].Value = None
    weather_data_for_fix[-1].Value = None
    weather_data_for_fix = patch_novalue_in_weather_element_list(weather_data_for_fix)
    mplots.plot_weather_elements([weather_data, weather_data_for_fix])
