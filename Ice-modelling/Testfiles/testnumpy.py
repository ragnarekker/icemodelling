__author__ = 'raek'

import numpy as np

a = np.array([np.nan, 1, 2])
b = np.copy(a)
b[:] = np.nan
b[2] = 1

c = np.minimum(a, b)

d =1