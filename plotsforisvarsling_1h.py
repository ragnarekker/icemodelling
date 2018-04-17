# -*- coding: utf-8 -*-
from icemodelling import runicethickness as rit
from icemodelling import makelogs as ml
import sys as sys

__author__ = 'ragnarekker'

try:
    rit.plot_regobs_observations(period='Today')
except:
    error_msg = sys.exc_info()[0]
    ml.log_and_print('plotsforisvarsling.py: Full crash on making last day with observation/9døgn plots. {}'.format(error_msg))

ml.log_and_print('plotsforisvarsling.py: I GOT TO THE END OF 1H!')
