#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'ragnarekker'

'''Setup work environment

@var data_folder:           Folder where all data files are stored. These are csv's as output or pickles for local storage.
@var
@var
@var database_location:     Database for the CloudMaker experiment

'''

import sys

if sys.platform == 'linux2' or sys.platform == 'darwin':
    project_folder      = '/Users/ragnarekker/Documents/GitHub/Ice-modelling/Ice-modelling/'
    plot_folder         = project_folder + 'Plots/'
    data_path           = project_folder + 'TimeseriesData/'
    kdv_elements_folder = project_folder + 'KDVelements/'
    database_location   = project_folder + 'Databases/cloudMakingResults.sqlite'

elif sys.platform == 'win32':
    project_folder      = 'C:\\Users\\raek\\Documents\\GitHub\\Ice-modelling\\Ice-modelling\\'
    plot_folder         = project_folder + 'Plots\\'
    data_path           = project_folder + 'TimeseriesData\\'
    kdv_elements_folder = project_folder + 'KDVelements\\'
    database_location   = project_folder + "Databases\\cloudMakingResults.sqlite"

else:
    print "The current operating system is not supported!"

api_version = "v0.9.9"
registration_basestring = 'http://www.regobs.no/Registration/'


