__author__ = 'raek'


import datetime as dt

today = dt.date.today()

daynumber = today.timetuple().tm_yday

now = dt.datetime.now()
the_date = now.date()
test = False

if the_date == dt.date(2015, 8, 29):
    test = True

c = 1