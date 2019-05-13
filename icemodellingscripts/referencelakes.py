# -*- coding: utf-8 -*-
"""

"""
import copy
import json
import datetime as dt
from icemodelling import weatherelement as we, icethickness as it
from icemodelling import parameterization as dp
from icemodelling import ice as ice
import setenvironment as se
from utilities import getregobsdata as gro, makeplots as pts
from utilities import getgts as gts

__author__ = 'ragnarekker'


def calculate_reference_lakes(calculation_date=dt.datetime.now(), make_plots=True, get_new_obs=True):
    """Plot ice thickness for this season for all reference lakes. Create a json-file with information about
    changes in the ice thickness last week and expected changes next week.

    # Always plot
    :param make_plots:       [bool] If true plots of reference lakes are made.
    :param calculation_date: [datetime] Defines the day the plots are made for. Datetime since the ice model uses this.
    :param get_new_obs:      [bool] If true, new observations ar requested from Regobs and added to local storage.

    """

    # Filename including path for input json file with reference lake information
    input_json_file = se.reference_lakes_input_json_file
    # Folder for output json file with ice changes
    output_json_folder = se.reference_lakes_output_json_folder
    # Folder to place the plots
    plot_folder = se.reference_lakes_plot_folder
    # Filename for adjusted position for locations outside the GTS-grid
    adjusted_location_json_file = se.reference_lakes_adjusted_location

    # Calculate season text. Set 1. september as start of season
    fyear = calculation_date.year
    month = calculation_date.month
    if month < 9:
        fyear = fyear - 1
    season = str(fyear) + '-' + str(fyear+1)[2:]

    # Calculate start of plot, use 30. september
    start_season_date = dt.datetime(fyear, 9, 30)
    # Use 10 days before present date for the final plot
    start_plot_date = calculation_date - dt.timedelta(days=11)

    # Get new observations from regobs. This updates the pickle in local storage so we may only get data once.
    gro.get_all_season_ice(season, get_new=get_new_obs)

    # Create json filename, Prognoserte_endringer_date. Save one with todays date, and one copy as overwrite 'latest'
    output_folder = output_json_folder
    if output_folder[-1:] != '/':
        output_folder += '/'
    output_filename = output_folder + f'Endringer_istykkelse-{calculation_date.year}-{calculation_date.month:02}-{calculation_date.day:02}.json'
    output_latest_filename_core = 'Endringer_istykkelse-latest.json'
    output_latest_filename = output_folder + output_latest_filename_core

    # Make sure plot_folder ends with '/'
    if plot_folder[-1:] != '/':
        plot_folder += '/'

    with open(adjusted_location_json_file, encoding='utf-8-sig') as adjusted_location_json:
        adjusted_location_data = json.load(adjusted_location_json)

    # Read json-file
    reference_lakes_jsonfile = input_json_file
    with open(reference_lakes_jsonfile, encoding='utf-8-sig') as reference_lakes_json:
        reference_lakes_data = json.load(reference_lakes_json)

    # Store plot file names for later ftp
    lastregion = ''
    ftp_files = []
    for fcr in reference_lakes_data['forecastRegions']:
        # Message
        if fcr['name'] != lastregion:
            lastregion = fcr['name']
            print("--- ", lastregion, " ---")

        for ls in fcr['lakeSize']:
            for lh in ls['lakeHeight']:
                ref_lake = lh['reference_lake']
                if ref_lake['locationId'] != '':
                    # Create filename 'locationid_season_forecastregionindex_lakesizeindex_lakeheightindex.png'
                    plot_filename = fcr['index'] + '_' + ls['index'] + '_' + lh['index'] + '_' + season + '_' \
                                    + ref_lake['locationId'] + '.png'
                    ftp_files.append(plot_filename)

                    # Calculate ice growth for this location
                    # Use grid data
                    location_name = ref_lake['name']
                    regobs_location_id_text = ref_lake['locationId']
                    regobs_location_id = int(ref_lake['locationId'])

                    # Should we adjust the position for this location to match the GTS weather grid?
                    found_in_list = False
                    for station in adjusted_location_data:
                        if station['locationID'] == regobs_location_id_text:
                            found_in_list = True
                            adjusted33x = int(station['valid33x'])
                            adjusted33y = int(station['valid33y'])
                            break

                    if found_in_list:
                        # Use adjusted values
                        x = adjusted33x
                        y = adjusted33y
                        print('x,y', x, y)
                    else:
                        x = int(ref_lake['utm33x'])
                        y = int(ref_lake['utm33y'])

                    altitude = int(ref_lake['height'])

                    # Message
                    print(str(regobs_location_id) + ' - ' + location_name)

                    # Get start and end date for simulation
                    first_possible_date = dt.datetime(fyear,9,1)
                    if ref_lake['FreezeUpThisYear'] != '':
                        freezeup = ref_lake['FreezeUpThisYear']
                        freezup_dt = dt.datetime(int(freezeup[6:]), int(freezeup[3:5]), int(freezeup[0:2]))
                        if freezup_dt < first_possible_date:
                            # Ignore this date, probably a left over from last season
                            freezeup = ref_lake['FreezeUpNormal']
                    else:
                        freezeup = ref_lake['FreezeUpNormal']

                    # Adjust to correct start year and get from_date in datetime
                    if int(freezeup[3:5]) < 9:
                        # Passed new year
                        from_date = dt.datetime(fyear + 1, int(freezeup[3:5]), int(freezeup[0:2]))
                    else:
                        from_date = dt.datetime(fyear, int(freezeup[3:5]), int(freezeup[0:2]))

                    to_date = calculation_date + dt.timedelta(days=9)

                    # Get regobs-observations, if any
                    observed_ice = gro.get_observations_on_location_id(regobs_location_id, season)
                    if len(observed_ice) > 0:
                        first_ice = observed_ice[0]
                        first_ice.ignore_slush_event_variable = False
                        first_ice.slush_event = False
                    else:
                        first_ice = ice.IceColumn(from_date, [])
                        first_ice.add_metadata('LocationName', location_name)  # used when plotting
                        observed_ice.append(first_ice)

                    # Set from_date equal to when the calculations should start
                    from_date = start_season_date

                    gridTemp = gts.getgts(x, y, 'tm', from_date, to_date)
                    gridSno = gts.getgts(x, y, 'sdfsw', from_date, to_date)
                    gridSnoTot = gts.getgts(x, y, 'sd', from_date, to_date)

                    # Grid altitude and lake at same elevations.
                    gridTempNewElevation = we.adjust_temperature_to_new_altitude(gridTemp, altitude)

                    temp, date = we.strip_metadata(gridTempNewElevation, get_date_times=True)
                    sno = we.strip_metadata(gridSno)
                    sno_tot = we.strip_metadata(gridSnoTot)
                    cc = dp.clouds_from_precipitation(sno)

                    calculated_ice = it.calculate_ice_cover_air_temp(copy.deepcopy(first_ice), date, temp, sno, cloud_cover=cc)

                    # Create output json
                    wanted_output_dates = []
                    # 7 days ago at 00:00
                    wdate = calculation_date - dt.timedelta(days=7)
                    wdate = dt.datetime(wdate.year, wdate.month, wdate.day)
                    wanted_output_dates.append(wdate)
                    # Today, at 00:00
                    wdate = dt.datetime(calculation_date.year, calculation_date.month, calculation_date.day)
                    wanted_output_dates.append(wdate)
                    # + 7 days, at 00:00
                    wdate = calculation_date + dt.timedelta(days=7)
                    wdate = dt.datetime(wdate.year, wdate.month, wdate.day)
                    wanted_output_dates.append(wdate)
                    # Get Ice columns at these dates
                    wanted_snow_thickness = []
                    wanted_slush_thickness = []
                    wanted_ice_thickness = []
                    wanted_thickest_icelayer = []
                    for wanted_date in wanted_output_dates:
                        # Find calculated ice at this date, if any
                        # The method allows to merge slush_ice, black_ice and unknown into one layer
                        # Unknown and slush_ice counts as half the ice thickness to simulate black ice strength
                        found = False
                        tot_snow = 0
                        tot_slush = 0
                        tot_ice = 0
                        thickest_ice_layer = 0
                        for ci in calculated_ice:
                            if ci.date == wanted_date:
                                # Find snow and slush
                                for il in ci.column:
                                    if il.type == 'new snow' or il.type == 'snow' or il.type == 'drained_snow':
                                        tot_snow += il.height
                                    elif il.type == 'slush':
                                        tot_slush += il.height
                                # Total thickness of pure ice layers avoid type = 5 (water intermediate)
                                merged_ice_thickness = 0
                                for il in ci.column:
                                    if il.type == 'slush_ice' or il.type == 'black_ice' or il.type == 'unknown':
                                        tot_ice += il.height
                                        if il.type == 'black_ice':
                                            merged_ice_thickness = il.height + merged_ice_thickness
                                        else:
                                            # Weaker ice than black ice. Use half the height
                                            merged_ice_thickness = il.height * 0.5 + merged_ice_thickness
                                        if merged_ice_thickness > thickest_ice_layer:
                                            thickest_ice_layer = merged_ice_thickness
                                    else:
                                        # Not an ice layer
                                        merged_ice_thickness = 0

                                found = True
                                break
                            elif ci.date > wanted_date:
                                # No ice at this date
                                break

                        # Add the ice information to the array
                        wanted_snow_thickness.append(tot_snow)
                        wanted_slush_thickness.append(tot_slush)
                        wanted_ice_thickness.append(tot_ice)
                        wanted_thickest_icelayer.append(thickest_ice_layer)

                    # Add todays date
                    today_date = f'{calculation_date.day:02}.{calculation_date.month:02}.{calculation_date.year}'
                    ref_lake['Updated'] = today_date
                    # Save present status
                    ref_lake['SnowThickness'] = f'{wanted_snow_thickness[1]:.2f}'
                    ref_lake['SlushThickness'] = f'{wanted_slush_thickness[1]:.2f}'
                    ref_lake['TotalPureIceThickness'] = f'{wanted_ice_thickness[1]:.2f}'
                    ref_lake['ThickestIceLayer'] = f'{wanted_thickest_icelayer[1]:.2f}'
                    # Save status 7 days ago
                    ref_lake['SnowThicknessLast7days'] = f'{wanted_snow_thickness[0]:.2f}'
                    ref_lake['SlushThicknessLast7days'] = f'{wanted_slush_thickness[0]:.2f}'
                    ref_lake['TotalPureIceThicknessLast7days'] = f'{wanted_ice_thickness[0]:.2f}'
                    ref_lake['ThickestIceLayerLast7days'] = f'{wanted_thickest_icelayer[0]:.2f}'
                    # Save status 7 days ahead
                    ref_lake['SnowThicknessNext7days'] = f'{wanted_snow_thickness[2]:.2f}'
                    ref_lake['SlushThicknessNext7days'] = f'{wanted_slush_thickness[2]:.2f}'
                    ref_lake['TotalPureIceThicknessNext7days'] = f'{wanted_ice_thickness[2]:.2f}'
                    ref_lake['ThickestIceLayerNext7days'] = f'{wanted_thickest_icelayer[2]:.2f}'
                    # Calculate differences and put in the dictionary
                    tdiff = wanted_snow_thickness[1] - wanted_snow_thickness[0]
                    ref_lake['SnowThicknessChangeLast7days'] = f'{tdiff:.2f}'
                    tdiff = wanted_slush_thickness[1] - wanted_slush_thickness[0]
                    ref_lake['SlushThicknessChangeLast7days'] = f'{tdiff:.2f}'
                    tdiff = wanted_ice_thickness[1] - wanted_ice_thickness[0]
                    ref_lake['TotalPureIceThicknessChangeLast7days'] = f'{tdiff:.2f}'
                    tdiff = wanted_thickest_icelayer[1] - wanted_thickest_icelayer[0]
                    ref_lake['ThickestIceLayerChangeLast7days'] = f'{tdiff:.2f}'
                    tdiff = wanted_snow_thickness[2] - wanted_snow_thickness[1]
                    ref_lake['SnowThicknessChangeNext7days'] = f'{tdiff:.2f}'
                    tdiff = wanted_slush_thickness[2] - wanted_slush_thickness[1]
                    ref_lake['SlushThicknessChangeNext7days'] = f'{tdiff:.2f}'
                    tdiff = wanted_ice_thickness[2] - wanted_ice_thickness[1]
                    ref_lake['TotalPureIceThicknessChangeNext7days'] = f'{tdiff:.2f}'
                    tdiff = wanted_thickest_icelayer[2] - wanted_thickest_icelayer[1]
                    ref_lake['ThickestIceLayerChangeNext7days'] = f'{tdiff:.2f}'

                    if make_plots:
                        # First remove dates before wanted plot date
                        newdate = []
                        newtemp = []
                        newsno = []
                        newsno_tot = []
                        for i in range(len(date)):
                            if date[i] >= start_plot_date:
                                newdate.append(date[i])
                                newtemp.append(temp[i])
                                newsno.append(sno[i])
                                newsno_tot.append(sno_tot[i])
                        plot_path_and_filename = '{0}{1}'.format(plot_folder, plot_filename)
                        # pts.plot_ice_cover(calculated_ice, observed_ice, newdate, temp, sno, sno_tot, plot_path_and_filename)
                        pts.plot_reference_lake(calculated_ice, observed_ice, newdate, newtemp, newsno, newsno_tot, plot_path_and_filename)

                    # Add todays date
                    today_date = f'{calculation_date.day:02}.{calculation_date.month:02}.{calculation_date.year}'
                    reference_lakes_data['icemodelRunDate'] = today_date

                    # Create pretty string json
                    reference_lakes_output_json = json.dumps(reference_lakes_data, ensure_ascii=False, indent=2)

                    with open(output_filename, 'w', encoding='utf-8-sig') as outfile:
                        outfile.write(reference_lakes_output_json)
                        outfile.close()

    # Save revised json-files
    with open(output_latest_filename, 'w', encoding='utf-8-sig') as outfile_latest:
        outfile_latest.write(reference_lakes_output_json)
        outfile_latest.close()

    return


if __name__ == "__main__":

    calculate_reference_lakes(dt.datetime(2019, 1, 1), get_new_obs=False)
