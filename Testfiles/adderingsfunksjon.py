__author__ = 'raek'

import datetime

from Testfiles.functionsIO import *
import matplotlib.pyplot as plt3

#import matplotlib.pyplot as plt2

data = myreadfile("/Users/ragnarekker/Documents/GitHub/Ice-modelling/TimeseriesData/kyrkjestolane_verdata.csv",';')

a = [1,2,3]
print max(a)
print min(a)

dato = []
sno = []
temp = []
for i in range(len(data)-1-366):
    j = i+1+366
    dato.append(datetime.datetime.strptime(data[j][0], "%Y-%m-%d"))
    if data[j][1] >=  0:
        sno.append(float(data[j][1]))
    else:
        sno.append(0)
    temp.append(float(data[j][4]))

# print dato
# print sno
# print temp

# plt2.plot(dato,sno)
# plt2.plot(dato,temp)
# plt2.show()

fig, ax1 = plt3.subplots()
ax1.plot(dato,sno,'b-')
ax2 = ax1.twinx()
ax2.plot(dato,temp,'r-')
plt3.show()



