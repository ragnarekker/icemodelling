# -*- coding: utf-8 -*-
"""

"""

import datetime as dt

__author__ = 'raek'


def get_dates_from_season(year):
    """Get dates for hydrological year [1st sept, 31st aug] given a season as string.

    :param year:        [string] Year interval 'YYYY-YY'
    :return:            [date] from_date, to_date
    """

    if year == '2012-13':
        from_date = dt.date(2012, 9, 1)
        to_date = dt.date(2013, 8, 31)
    elif year == '2013-14':
        from_date = dt.date(2013, 9, 1)
        to_date = dt.date(2014, 8, 31)
    elif year == '2014-15':
        from_date = dt.date(2014, 9, 1)
        to_date = dt.date(2015, 8, 31)
    elif year == '2015-16':
        from_date = dt.date(2015, 9, 1)
        to_date = dt.date(2016, 8, 31)
    elif year == '2016-17':
        from_date = dt.date(2016, 9, 1)
        to_date = dt.date(2017, 8, 31)
    elif year == '2017-18':
        from_date = dt.date(2017, 9, 1)
        to_date = dt.date(2018, 9, 1)
    elif year == '2018-19':
        from_date = dt.date(2018, 9, 1)
        to_date = dt.date.today()
    else:
        from_date = 'Undefined dates'
        to_date = 'Undefined dates'

    return from_date, to_date


def get_season_from_date(date_inn):
    """A date belongs to a season. This method returns it.

    :param date_inn:    datetime.date object
    :return:
    """

    if date_inn >= dt.date(2020, 9, 1) and date_inn < dt.date(2021, 9, 1):
        return '2020-21'
    elif date_inn >= dt.date(2019, 9, 1) and date_inn < dt.date(2020, 9, 1):
        return '2019-20'
    elif date_inn >= dt.date(2018, 9, 1) and date_inn < dt.date(2019, 9, 1):
        return '2018-19'
    elif date_inn >= dt.date(2017, 9, 1) and date_inn < dt.date(2018, 9, 1):
        return '2017-18'
    elif date_inn >= dt.date(2016, 9, 1) and date_inn < dt.date(2017, 9, 1):
        return '2016-17'
    elif date_inn >= dt.date(2015, 9, 1) and date_inn < dt.date(2016, 9, 1):
        return '2015-16'
    elif date_inn >= dt.date(2014, 9, 1) and date_inn < dt.date(2015, 9, 1):
        return '2014-15'
    elif date_inn >= dt.date(2013, 9, 1) and date_inn < dt.date(2014, 9, 1):
        return '2013-14'
    elif date_inn >= dt.date(2012, 9, 1) and date_inn < dt.date(2013, 9, 1):
        return '2014-13'
    elif date_inn >= dt.date(2011, 9, 1) and date_inn < dt.date(2012, 9, 1):
        return '2011-12'
    else:
        return 'Requested date is before the beginning of time.'


if __name__ == "__main__":

    pass
