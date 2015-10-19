# -*- coding: utf-8 -*-
__author__ = 'raek'

import pickle


def pickle_anything(something_to_pickle, file_name_and_path):
    '''Pickles anything.

    :param something_to_pickle:
    :param file_name_and_path:
    :return:
    '''

    with open(file_name_and_path, 'w') as f:
        pickle.dump(something_to_pickle, f)

    print 'makePickle.py -> pickle_anything: {0} pickled.'.format(file_name_and_path)


def unpickle_anything(file_name_and_path):
    '''Unpickles anything.

    :param file_name_and_path:
    :return:
    '''

    with open(file_name_and_path) as f:
        something_to_unpickle = pickle.load(f)

    print 'makePickle.py -> unpickle_anything: {0} unpickled.'.format(file_name_and_path)

    return something_to_unpickle

