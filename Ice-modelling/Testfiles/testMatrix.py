__author__ = 'raek'
import numpy

dogn = 60*60*24

a = [1,2,3]
print max(a)
print min(a)


data = numpy.zeros(0)
data = numpy.zeros(shape=(10,10))
print data

for i in range(0, len(data), 1):
    for j in range(0, len(data[0]), 1):
        data[i][j] = i-j

print data


