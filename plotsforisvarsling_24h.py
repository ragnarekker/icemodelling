# -*- coding: utf-8 -*-
from icemodelling import runicethickness as rit
from icemodelling import makelogs as ml
import sys as sys

__author__ = 'ragnarekker'

try:
    rit.plot_regobs_observations(period='2017-18')
except:
    error_msg = sys.exc_info()[0]
    ml.log_and_print('plotsforisvarsling.py: Full crash on making observation/9døgn plots. {}'.format(error_msg))

try:
    rit.plot_season(year='2017-18', calculate_new=True, get_new_obs=True, make_plots=True)
except:
    error_msg = sys.exc_info()[0]
    ml.log_and_print('plotsforisvarsling.py: Full crash on making season plots. {}'.format(error_msg))

ml.log_and_print('plotsforisvarsling.py: I GOT TO THE END OF 24H!')
