# -*- coding: utf-8 -*-
__author__ = 'raek'

import pickle

def pickle_anything(something_to_pickle, file_name_and_path):
    with open(file_name_and_path, 'w') as f:
        pickle.dump(something_to_pickle, f)

def unpickle_anything(file_name_and_path):
    with open(file_name_and_path) as f:
        something_to_unpickle = pickle.load(f)
    #print'{0} unpickled.'.format(file_name_and_path)
    return something_to_unpickle

