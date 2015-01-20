__author__ = 'ragnarekker'
# -*- coding: utf-8 -*-

from scipy.stats import gamma
from scipy.integrate import quad
import scipy

import scipy.optimize
import numpy as np
import matplotlib.pyplot as plt



# testing for distribution on prior and after days
def getProbabilities(a):

    gdst = gamma(a, scale = 1.)

    dm2 = quad(lambda x: gdst.pdf(x), 0, 1)
    dm1 = quad(lambda x: gdst.pdf(x), 1, 3)
    d0 = quad(lambda x: gdst.pdf(x), 3, 5)
    d1 = quad(lambda x: gdst.pdf(x), 5, 7)
    d2 = quad(lambda x: gdst.pdf(x), 7, 9)
    d3 = quad(lambda x: gdst.pdf(x), 9, 20)

    dm2 = dm2[0]/d0[0]
    dm1 = dm1[0]/d0[0]
    d1 = d1[0]/d0[0]
    d2 = d2[0]/d0[0]
    d3 = d3[0]/d0[0]
    d0 = d0[0]/d0[0]

    return dm2, dm1, d0, d1, d2, d3

#dm2, dm1, d0, d1, d2, d3 = getProbabilities(5)


# Example from:
# http://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.stats.gamma.html
# http://docs.scipy.org/doc/scipy-0.14.0/reference/tutorial/integrate.html

# gamma function
a = 5
rv = gamma(a, loc=0., scale = 1.)       # scale = 1.0 / lambda.
median = gamma.median(a)
mean = gamma.mean(a)

x0 = scipy.optimize.fsolve(lambda x: rv.pdf(x), 0.1)       # 0.3 is the starting point

# find the top
increase = True
df0 = 0
delta = 0.01
x = 0.01

while increase == True:
    h = rv.pdf(x+delta) - rv.pdf(x)
    if h < 0:
        increase = False
    else:
        x = x + delta

# integral of the function
result = quad(lambda x: rv.pdf(x), 3, 5)

# plot
fig, ax = plt.subplots(1, 1)
x = np.arange(-4, 12, 0.01)  #np.linspace(gamma.ppf(0.0001, a), gamma.ppf(0.999, a), 100)
ax.plot(x, rv.pdf(x), 'k-', lw=2)
plt.show()

