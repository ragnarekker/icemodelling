# -*- coding: utf-8 -*-
"""Environment for running plots for iskart.no on hb_datainn"""
import sys as sys
import os as os
import json as json
from pathlib import Path
from shutil import copyfile

__author__ = 'raek'


def _load_config_json(path, name):
    """Reading json's in the config folder is a repetitive task. If config file is missing copy in the
    template file in the same path, but prefixed with underscore (_).

    :param path:                [string]        full path of project
    :param name:                [string]        name of config file
    :return dict_of name:       [dictionary]    content of json returned as dict
    """

    path_name_json = '{0}/config/{1}.json'.format(path, name)
    path_name_template = '{0}/config/_{1}.json'.format(path, name)

    config_json = Path(path_name_json)

    try:
        if not config_json.exists():
            copyfile(path_name_template, path_name_json)
        dict_of_name = json.loads(open(config_json).read())
    except:
        error_msg = sys.exc_info()[0]
        print("setenvironment.py: Error creating folders: {}.".format(error_msg))
        dict_of_name = {}

    return dict_of_name


# project_path = 'C:\\Kode\\icemodelling\\icemodelling\\'
project_path = str(Path(__file__).parent.resolve())
folders = _load_config_json(project_path, 'folders')
api = _load_config_json(project_path, 'api')

# Set project folders
kdv_elements_folder = project_path + folders['kdv_elements']
local_storage = project_path + folders['local_storage']
output_folder = 'Z:\\iceplots\\'
plot_folder = 'Z:\\iceplots\\plots\\'
sesong_plots_folder = 'Z:\\iceplots\\sesong\\'
ni_dogn_plots_folder = 'Z:\\iceplots\\9dogn\\'
log_folder = 'Z:\\iceplots\\logs\\'

# Create project folders if missing
if project_path:
    try:
        # If log folder doesnt exist, make it.
        if not os.path.exists(kdv_elements_folder):
            os.makedirs(kdv_elements_folder)
        if not os.path.exists(local_storage):
            os.makedirs(local_storage)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if not os.path.exists(plot_folder):
            os.makedirs(plot_folder)
        if not os.path.exists(sesong_plots_folder):
            os.makedirs(sesong_plots_folder)
        if not os.path.exists(ni_dogn_plots_folder):
            os.makedirs(ni_dogn_plots_folder)
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

    except:
        error_msg = sys.exc_info()[0]
        print("setenvironment.py: Error creating folders: {}.".format(error_msg))

# Set resource folders
logos = project_path + folders['logos']
time_series_data = project_path + folders['time_series_data']

# Set api variables
odata_version = api['odata_version']
web_api_version = api['web_api_version']
forecast_api_version = api['forecast_api_version']
registration_basestring = api['registration_basestring']
chart_server_basestring = api['chart_server_basestring']
