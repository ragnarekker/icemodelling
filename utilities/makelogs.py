import datetime as dt
import os as os
import setenvironment as se

# -*- coding: utf-8 -*-
__author__ = 'raek'


def log_and_print(message, print_it=False, log_it=True):
    """For logging and printing this method does both.

    :param message:     [string] what to print and/or log
    :param print_it:    [bool] default True
    :param log_it:      [bool] default True

    :return:
    """

    time_and_message = '{:%H:%M}: '.format(dt.datetime.now().time()) + message
    time_and_message.encode('utf-8')

    if print_it:
        print(time_and_message)

    if log_it:

        # If log folder doesnt exist, make it.
        if not os.path.exists(se.log_folder):
            os.makedirs(se.log_folder)

        file_name = '{0}icemodelling_{1}.log'.format(se.log_folder, dt.date.today())
        with open(file_name, 'a', encoding='utf-8') as f:
            f.write(time_and_message + '\n')
