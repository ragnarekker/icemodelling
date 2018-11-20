# -*- coding: utf-8 -*-
"""Handles pickling and unpickling for storing data."""

import pickle as pickle
from utilities import makelogs as ml

__author__ = 'raek'


def pickle_anything(something_to_pickle, file_name_and_path, print_message=True):
    """Pickles anything.

    :param something_to_pickle:
    :param file_name_and_path:
    :param print_message:
    :return:
    """

    pickle.dump(something_to_pickle, open(file_name_and_path, 'wb'))

    if print_message is True:
        ml.log_and_print("[info] makepickle.py -> pickle_anything: {0} pickled.".format(file_name_and_path))


def unpickle_anything(file_name_and_path, print_message=True):
    """Unpickles anything.

    :param file_name_and_path:
    :param print_message:
    :return something_to_unpickle:
    """

    something_to_unpickle = pickle.load( open(file_name_and_path, 'rb') )

    if print_message is True:
        ml.log_and_print("[info] makepickle.py -> unpickle_anything: {0} unpickled.".format(file_name_and_path))

    return something_to_unpickle
