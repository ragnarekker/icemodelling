__author__ = 'raek'

from math import pi, sin, cos, tan
import datetime as dt


def unix_time_2_normal(unix_date_time):
    """
    Takes in a date in unix datetime and returns a "normal date"

    :param unix_date_time:    Unix date time in milliseconds from 1.1.1970
    :return:                The date as datetime object

    Ex: date = unix_time_2_normal(int(p['DtObsTime'][6:-2]))
    """

    # odata returns a string with prefix "Date". Cropp and cast.
    if "Date" in unix_date_time:
        unix_date_time = int(unix_date_time[6:-2])

    unix_datetime_in_seconds = unix_date_time / 1000  # For some reason they are given in miliseconds
    date = dt.datetime.fromtimestamp(int(unix_datetime_in_seconds))
    return date


def lat_long_from_utm33(x, y, output="degrees"):
    '''

    konverterer til lat lon.

    '''

    utmx = x-500000
    utmy = y
    k0 = 0.9996
    long0 = 15.0 * pi / 180         # 15 grader er Central meridian i sone 33  15*pi/180  gir radianer
    M = utmy/k0                     # Meridional arc
    a = 6378137                     # Eq, radius meters
    b = 6356752.3141                # Polar radius meters
    e = (1-(b**2/a**2))**0.5        # e = 0.08
    e2 = (e*a/b)**2                 # e2 = 0.007
    mu = M/(a*(1-(e**2/4)-3*(e**4/64)-5*(e**6/256)))
    e1 = (1-(1-e**2)**0.5)/(1+(1-e**2)**0.5)
    j1 = 3*(e1/2)-27*(e1**3/32)
    j2 = 21*(e1**2/16)-55*(e1**4/32)
    j3 = 151*(e1**3/96)
    j4 = (1097*e1**4)/512
    fp = mu+j1*sin(2*mu)+j2*sin(4*mu)+j3*sin(6*mu)+j4*sin(8*mu)
    C1 = e2*cos(fp)**2
    T1 = tan(fp)**2
    R1 = a*(1-e**2)/(1-e**2*sin(fp)**2)**1.5
    N1 = a/(1-e**2*sin(fp)**2)**0.5
    D = utmx/(N1*k0)
    Q1 = N1*tan(fp)/R1
    Q2 = (D**2/2)
    Q3 = (5+3*T1+10*C1-4*C1**2-9*e2)*D**4/24
    Q4 = (61+90*T1+298*C1+45*T1**2-3*C1**2-252*e2)*D**6/720
    Q5 = D
    Q6 = (1+2*T1+C1)*D**3/6
    Q7 = (5-2*C1+28*T1-3*C1**2+8*e2+24*T1**2)*D**5/120

    phi = fp-Q1*(Q2-Q3+Q4)          # latitude radianer
    thi = long0 +(Q5-Q6+Q7)/cos(fp) # longitude radianer
    phi_lat = phi*180/pi            # latitude grader
    thi_long = thi*180/pi           # longitude grader

    if output == "both":
        return phi, thi, phi_lat, thi_long

    if output == "degrees":
        return phi_lat, thi_long

    if output == "radians":
        return phi, thi


if __name__ == "__main__":

    # Test koordinater i tana
    x_tana = 988130
    y_tana = 7844353
    lat_tana, long_tana = lat_long_from_utm33(x_tana, y_tana)


    # Test Filefjell
    y_file = 6802070
    x_file = 130513
    lat_file, long_file = lat_long_from_utm33(x_file, y_file)

    a = 1


