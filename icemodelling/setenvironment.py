# -*- coding: utf-8 -*-
import sys as sys
import os as os

__author__ = 'ragnarekker'

"""Setup work environment

@var data_folder:           Folder where all data files are stored. These are csv's as output or pickles for local storage.
@var
@var
@var database_location:     Database for the CloudMaker experiment
@var environment_config_complete: If false, no variables are declared. A safeguard so not lots of folders are unintentionally declared.
"""

operational = False
project_folder_linux_or_darwin = '/Users/ragnarekker/Dropbox/Kode/Python/icemodelling/icemodelling/'
project_folder_developer_windows = 'C:\\Users\\raek\\Dropbox\\Kode\\Python\\icemodelling\\icemodelling\\'
project_folder_operational_windows = 'C:\\Kode\\icemodelling\\icemodelling\\'
output_folder_operational = 'Z:\\iceplots\\'
environment_config_complete = True

if environment_config_complete:

    if 'linux' in sys.platform or 'darwin' in sys.platform:
        project_folder = project_folder_linux_or_darwin
        output_folder = project_folder + 'output/'
        plot_folder = project_folder + 'output/plots/'
        sesong_folder = plot_folder + 'sesong/'
        ni_dogn_folder = plot_folder + '9dogn/'
        log_folder = project_folder + 'logs/'
        data_path = project_folder + 'timeseriesdata/'
        input_folder = project_folder + 'input/'
        kdv_elements_folder = project_folder + 'localstorage/'
        local_storage = project_folder + 'localstorage/'
        database_location = project_folder + 'databases/cloudMakingResults.sqlite'

    elif 'win' in sys.platform:

        if operational:
            project_folder = project_folder_operational_windows
            output_folder = output_folder_operational
            plot_folder = output_folder + 'plots\\'
            sesong_folder = plot_folder + 'sesong\\'
            ni_dogn_folder = plot_folder + '9dogn\\'
            log_folder = output_folder + 'logs\\'
            data_path = project_folder + 'timeseriesdata\\'
            input_folder = project_folder + 'input\\'
            kdv_elements_folder = project_folder + 'localstorage\\'
            local_storage = project_folder + 'localstorage\\'
            database_location = project_folder + "databases\\cloudMakingResults.sqlite"

        else:
            project_folder = project_folder_developer_windows
            output_folder = project_folder + 'output\\'
            plot_folder = project_folder + 'output\\plots\\'
            sesong_folder = plot_folder + 'sesong\\'
            ni_dogn_folder = plot_folder + '9dogn\\'
            log_folder = project_folder + 'logs\\'
            data_path = project_folder + 'timeseriesdata\\'
            input_folder = project_folder + 'input\\'
            kdv_elements_folder = project_folder + 'localstorage\\'
            local_storage = project_folder + 'localstorage\\'
            database_location = project_folder + "databases\\cloudMakingResults.sqlite"

    else:
        print("The current operating system is not supported!")
        project_folder = None

    if project_folder:
        try:
            # If log folder doesnt exist, make it.
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            if not os.path.exists(plot_folder):
                os.makedirs(plot_folder)
            if not os.path.exists(sesong_folder):
                os.makedirs(sesong_folder)
            if not os.path.exists(ni_dogn_folder):
                os.makedirs(ni_dogn_folder)
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
            if not os.path.exists(data_path):
                os.makedirs(data_path)
            if not os.path.exists(input_folder):
                os.makedirs(input_folder)
            if not os.path.exists(kdv_elements_folder):
                os.makedirs(kdv_elements_folder)
            if not os.path.exists(local_storage):
                os.makedirs(local_storage)
            if not os.path.exists(database_location):
                os.makedirs(database_location)

        except:
            error_msg = sys.exc_info()[0]
            print("setenvironment.py: Error creating folders: {}.".format(error_msg))

else:
    print("setenvironment.py: Environment not configured.")

# Requests and URL's
odata_api_version = "v3.1.0"
web_api_version = "v3.2.0"
registration_basestring = 'http://www.regobs.no/Registration/'

# URL to the chartserver/ShowData service
chart_server_base_url = "http://h-web01.nve.no/chartserver/ShowData.aspx?req=getchart&ver=1.0&vfmt=json"



