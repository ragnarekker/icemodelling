# -*- coding: utf-8 -*-
from matplotlib import pylab as plb
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import datetime as dt
import collections as collections
import copy as copy
import setenvironment as se

__author__ = 'raek'


class ObsCalScatterData:
    """Class for handling data in the scatter_calculated_vs_observed plot."""


    def __init__(self, caluclated_draft_inn, observed_draft_inn, date_inn, location_inn):

        if caluclated_draft_inn < 0:
            caluclated_draft_inn = 0
        if observed_draft_inn < 0:
            observed_draft_inn = 0
        self.caluclated_draft = caluclated_draft_inn
        self.observed_draft = observed_draft_inn
        self.date = date_inn
        self.location = location_inn


    def marker_color(self):

        if self.date.month == 8:
            return 'gold'
        elif self.date.month == 9:
            return 'goldenrod'
        elif self.date.month == 10:
            return 'darkgoldenrod'
        elif self.date.month == 11:
            return 'lightskyblue'
        elif self.date.month == 12:
            return 'deepskyblue'
        elif self.date.month == 1:
            return 'blue'
        elif self.date.month == 2:
            return 'violet'
        elif self.date.month == 3:
            return 'magenta'
        elif self.date.month == 4:
            return 'tomato'
        elif self.date.month == 5:
            return 'red'
        elif self.date.month == 6:
            return 'lime'
        elif self.date.month == 7:
            return 'green'
        else:
            return 'pink'


    def marker(self):

        if self.date.month == 8:
            return '*'
        elif self.date.month == 9:
            return '*'
        elif self.date.month == 10:
            return '*'
        elif self.date.month == 11:
            return '*'
        elif self.date.month == 12:
            return 'o'
        elif self.date.month == 1:
            return 'o'
        elif self.date.month == 2:
            return 'o'
        elif self.date.month == 3:
            return 'o'
        elif self.date.month == 4:
            return 'x'
        elif self.date.month == 5:
            return 'x'
        elif self.date.month == 6:
            return 'x'
        elif self.date.month == 7:
            return 'x'
        else:
            return '8'


def scatter_calculated_vs_observed(all_calculated, all_observed, year):
    """For yearly data setts og all observed ice from regObs and all calculations on lakes where these observations
    are made, a scatter plot is made, comaring calculations vs. observations.

    :param all_calculated:
    :param all_observed:
    :param year:            [string]    Eg. '2017-18', '2016-17', ..
    """

    # Turn off interactive mode
    plt.ioff()

    scatter_plot_data = []
    for ln in all_observed.keys():
        skipp_first = True

        for oi in all_observed[ln]:

            if skipp_first:
                skipp_first = False
            else:
                observed_draft = oi.draft_thickness
                calculated_draft = None
                for ci in all_calculated[ln]:
                    if ci.date.date() == oi.date.date():
                        calculated_draft = ci.draft_thickness

                data = ObsCalScatterData(calculated_draft, observed_draft, oi.date.date(), ln)
                scatter_plot_data.append(data)

    x = []
    y = []
    color = []
    #marker = []
    for d in scatter_plot_data:
        x.append(d.observed_draft)
        y.append(d.caluclated_draft)
        color.append(d.marker_color())
        #marker.append(d.marker())

    file_name = '{0}calculated_vs_observed {1}'.format(se.plot_folder, year)

    # Figure dimensions
    fsize = (10, 10)
    plb.figure(figsize=fsize)
    plb.clf()

    plt.scatter(x,y,c=color)
    plt.plot([-0.5, 3],[-0.5, 3], 'k--')

    plb.title('Calculated vs. observed {0}'.format(year))
    plt.xlabel("Observed")
    plt.ylabel("Calculated")

    #plb.xlim(min(x+y), max(x+y))
    #plb.ylim(min(x+y), max(x+y))
    plb.xlim(-0.05, 1)
    plb.ylim(-0.05, 1)

    plb.savefig(file_name)


def plot_ice_cover_9dogn(ice_cover, observed_ice, date, temp, sno, snotot, filename):
    """Plots ice cover over a given time period. It also plots observed data and snow and temperature data.

    :param ice_cover:
    :param observed_ice:    A list of ice_cover objects. If no observed ice use [] for resources.
    :param date:
    :param temp:
    :param sno:             New snow in m
    :param snotot:          Total snow in m
    :param filename:
    """

    # Get dates for x-axis lables and add a date on each side for padding
    ice_column_dates = [ic.date.date() for ic in ice_cover]
    ice_column_dates.insert(0, ice_column_dates[0] - dt.timedelta(days=1))
    ice_column_dates.append(ice_column_dates[-1] + dt.timedelta(days=1))

    # convert sno and snotot from m to cm
    sno = [s * 100 for s in sno]
    snotot = [st * 100 for st in snotot]

    # convert ice_cover and observed_ice from m to cm
    observed_ice.water_line *= 100
    for l in observed_ice.column:
        l.height *= 100

    for c in ice_cover:
        c.water_line *= 100
        for l in c.column:
            l.height *= 100

    # Turn off interactive mode
    plt.ioff()

    # Figure dimensions
    plt.figure(figsize=(10, 9))
    plt.clf()

    ########## Ice columns sub plot
    plt.subplot2grid((4, 1), (0, 0), rowspan=3)

    # depending on how many days are in the plot, the line weight of the modelled data should be adjusted
    modelledLineWeight = 35

    # dont need to keep the colunm coordinates, but then again, why not..? Usefull for debuging
    all_column_coordinates = []

    location_name = observed_ice.metadata['LocationName']
    if location_name is None:
        location_name = 'Ukjent vann'
    plt.title('{0} observert {1} (RegID={2})'.format(location_name, observed_ice.date.date() , observed_ice.metadata['RegID']))

    # Grid lines an a solid balck dotted line at water level
    plt.grid(color='0.6', linestyle='--', linewidth=0.7, zorder=0)
    plt.plot(ice_column_dates, [0]*len(ice_column_dates), 'k--', linewidth=2, zorder=0)

    # a variable for the lowest point on the ice cover. It is used for setting the lower left y-limit .
    lowest_point = 0.
    highest_point = 0.
    legend = {}

    # Plot ice cover
    for j, ic in enumerate(ice_cover):

        # some idea of progress on the plotting
        if ic.date.day == 1:
            print((ic.date).strftime('%Y%m%d'))

        # make data for plotting. [ice layers.. [fro, too, ice type]].
        column_coordinates = []
        too = -ic.water_line  # water line is on x-axis

        for i in range(len(ic.column)-1, -1, -1):
            layer = ic.column[i]
            fro = too
            too = too + layer.height
            column_coordinates.append([fro, too, layer.type])

            if fro < lowest_point:
                lowest_point = fro

            if too > highest_point:
                highest_point = too

            # Mark observation additionally
            # if j == 0:
            #     padding = 0.
            #     padding_color = 'pink'
            #     line_weight = modelledLineWeight * 1.1
            #     plb.vlines(ic.date.date(), fro - padding, too + padding, lw=line_weight, color=padding_color)

            # add coordinates to a vline plot
            x = ic.date.date()
            plt.vlines(x, fro, too, lw=modelledLineWeight, color=layer.get_colour(), zorder=3) #ic.getColour(layer.type))

            if 'unknown' in layer.type:  # in IceLayer class, the enum for unknown ice is the same as for slush ice.
                legend[-1] = [layer.get_colour(), layer.get_norwegian_name()]
            else:
                legend[layer.get_enum()] = [layer.get_colour(), layer.get_norwegian_name()]

        all_column_coordinates.append(column_coordinates)

    # the limits of the y-axis are defined relative the lowest point in the ice cover
    # and the highest point of the observed snow cover. Minimum set to 0.5meters
    plt.ylim(min(-30, lowest_point*1.1), max(30, highest_point*1.1))
    plt.xlim(ice_column_dates[0], ice_column_dates[-1])
    plt.ylabel('Høyde og dybde i [cm] relativt vannlinjen')

    # Make legend
    legend = collections.OrderedDict(sorted(legend.items()))
    legend_handles = []
    for k, v in legend.items():
        legend_handles.append(mpatches.Patch(color=v[0], label=v[1]))
    legend_handles = list(reversed(legend_handles))
    plt.legend(handles=legend_handles)

    ######## Temp and snow in separate subplot
    plt.subplot2grid((4, 1), (3, 0), rowspan=1)
    plt.grid(color='0.6', linestyle='--', linewidth=0.7, zorder=0)

    # plot total snow depth on land adjusted to new snow axis but with max marked and labeled.
    index_max_snotot = snotot.index(max(snotot))
    max_snotot = snotot[index_max_snotot]
    max_sno = max(sno)

    if max_snotot != 0:
        snotot = [s * 1.5* max(max_sno, 5)/max_snotot for s in snotot]
        dato_max_snotot = date[index_max_snotot]
    else:
        dato_max_snotot = date[-1]

    relative_max_snotot = snotot[index_max_snotot]
    plt.fill_between(date, 0, snotot, facecolor='0.95', edgecolor='k', linewidth=0.1, zorder=3)
    plt.text(dato_max_snotot + dt.timedelta(days=-1),
             relative_max_snotot + max(2.4 * max(sno), 20)*0.15,
             '     {}cm snø i terrenget'.format(int(max_snotot)), color='0.5')
    plt.plot(dato_max_snotot, relative_max_snotot, marker='o', color='0.5', zorder=4)

    # plot new snow
    plt.ylim(0, max(2.4 * max(sno), 20))
    plt.ylabel('Nysnø i [cm]')
    plt.bar(date, sno, width=0.7, facecolor='0.85', edgecolor=['black']*len(date), linewidth=0.5, zorder=3)

    plt.xlim(ice_column_dates[0], ice_column_dates[-1])

    # Plot temperatures on a separate y axis
    plt.twinx()

    temp_pluss = []
    temp_minus = []

    for i in range(0, len(temp), 1):
        if temp[i] >= 0:
            temp_pluss.append(temp[i])
            temp_minus.append(np.nan)
        else:
            temp_minus.append(temp[i])
            temp_pluss.append(np.nan)

    plt.plot(date, temp, 'black')
    plt.plot(date, temp_pluss, 'red')
    plt.plot(date, temp_minus, 'blue')
    plt.plot(date, temp_pluss, 'ro')
    plt.plot(date, temp_minus, 'bo')

    if min(temp) > 0:
        plt.ylim(0, 1.2 * (max(temp)+2))
    else:
        plt.ylim(2.6 * min(temp), 1.2 * (max(temp)+2))
    plt.ylabel('Temp i [C]')

    plt.gca().axes.get_xaxis().set_ticklabels([])
    plt.gcf().text(0.7, 0.05, 'Figur laget {0:%Y-%m-%d %H:%M}'.format(dt.datetime.now()), color='0.5')

    plt.savefig(filename)
    plt.close()


def plot_ice_cover(ice_cover, observed_ice, date, temp, sno, snotot, filename):
    """Plots ice cover over a given time period. It also plots observed data and snow and temperature data.

    :param ice_cover:
    :param observed_ice:    A list of ice_cover objects. If no observed ice use [] for resources.
    :param date:
    :param temp:
    :param sno:
    :param snotot:
    :param filename:
    """

    axis_date = copy.deepcopy(date)
    for i in range(1,7,1):
        axis_date.append(axis_date[-1] + dt.timedelta(days=1))

    # convert sno and snotot from m to cm
    sno = [s * 100 for s in sno]
    snotot = [st * 100 for st in snotot]

    # convert ice_cover and observed_ice from m to cm
    for oc in observed_ice:
        if oc.water_line != -1:
            oc.water_line *= 100
        for l in oc.column:
            l.height *= 100

    for c in ice_cover:
        c.water_line *= 100
        for l in c.column:
            l.height *= 100

    # Turn off interactive mode
    plt.ioff()

    # Figure dimensions
    plt.figure(figsize=(16, 14))
    plt.clf()

    ########## Ice columns sub plot
    plt.subplot2grid((4, 1), (0, 0), rowspan=3)
    plt.grid(color='0.6', linestyle='--', linewidth=0.7, zorder=0)
    plt.plot(axis_date, [0] * len(axis_date), 'k--', linewidth=2, zorder=0)
    plt.text(axis_date[3], 1, 'Vannlinje', color='0.3', fontsize=12)
    plt.xlim(axis_date[0], axis_date[-1])

    # depending on how many days are in the plot, the lineweight of the modelled data should be adjusted
    if len(axis_date) < 15:
        modelledLineWeight = 400 / len(axis_date)
    elif len(axis_date) >= 15 and len(axis_date) < 50:
        modelledLineWeight = 500 / len(axis_date)
    elif len(axis_date) >= 50 and len(axis_date) < 70:
        modelledLineWeight = 900 / len(axis_date)
    else:
        modelledLineWeight = 1100 / len(axis_date)

    # dont need to keep the colunm coordinates, but then again, why not..? Useful for debuging
    all_column_coordinates = []

    if len(observed_ice) > 0:
        location_name = observed_ice[0].metadata['LocationName']
        if location_name is None:
            location_name = 'Ukjent vann'
    else:
        location_name = 'Ukjent vann'

    # If from and to dates are within the same, year find the next year in line for season label.
    from_year = int('{0:%y}'.format(date[0]))
    to_year = int('{0:%y}'.format(date[-1]))
    if from_year == to_year:
        to_year += 1
    season = '{0:%Y}-{1}'.format(date[0], to_year)
    plt.title('{0} sesongen {1}'.format(location_name, season), fontsize=24)

    # a variable for the lowest point on the ice cover. It is used for setting the lower left y-limit .
    lowest_point = 0.
    highest_point = 0.
    legend = {}

    # Plot ice cover
    for ic in ice_cover:

        # some idea of progress on the plotting
        if ic.date.day == 1:
            print((ic.date).strftime('%Y%m%d'))

        # make data for plotting. [ice layers.. [fro, too, ice type]].
        column_coordinates = []
        too = -ic.water_line  # water line is on xaxis

        for i in range(len(ic.column)-1, -1, -1):
            layer = ic.column[i]
            fro = too
            too = too + layer.height
            column_coordinates.append([fro, too, layer.type])

            if fro < lowest_point:
                lowest_point = fro

            if too > highest_point:
                highest_point = too

            # add coordinates to a vline plot
            plt.vlines(ic.date.date(), fro, too, lw=modelledLineWeight, color=layer.get_colour()) #ic.getColour(layer.type))

            if 'unknown' in layer.type:  # in IceLayer class, the enum for unknown ice is the same as for slush ice.
                legend[-1] = [layer.get_colour(), layer.get_norwegian_name()]
            else:
                legend[layer.get_enum()] = [layer.get_colour(), layer.get_norwegian_name()]

        all_column_coordinates.append(column_coordinates)

    # plot observed ice columns
    for ic in observed_ice:

        if len(ic.column) == 0:
            height = 3.
            plt.vlines(ic.date.date(), -height*0.6, height, lw=6, color='white')
            plt.vlines(ic.date.date(), -height*0.6, height, lw=4, color='red')
        else:
            # some idea of progress on the plotting
            print("Plotting observations.")

            # make data for plotting. [ice layers.. [fro, too, icetype]].
            too = -ic.water_line  # water line is on xaxis

            for i in range(len(ic.column)-1, -1, -1):
                layer = ic.column[i]
                fro = too
                too = too + layer.height

                if fro < lowest_point:
                    lowest_point = fro

                if too > highest_point:
                    highest_point = too

                padding = 0.
                padding_color = 'white'
                # outline the observations in orange if I have modelled the ice height after observation.
                if ic.metadata.get('IceHeightAfter') == 'Modeled':
                    padding_color = 'orange'
                # add coordinates to a vline plot
                plt.vlines(ic.date.date(), fro-padding, too+padding, lw=8, color=padding_color)
                plt.vlines(ic.date.date(), fro, too, lw=6, color=layer.get_colour())

                if 'unknown' in layer.type:  # in IceLayer class, the enum for unknown ice is the same as for slush ice.
                    legend[-1] = [layer.get_colour(), layer.get_norwegian_name()]
                else:
                    legend[layer.get_enum()] = [layer.get_colour(), layer.get_norwegian_name()]

    # the limits of the left side y-axis is defined relative the lowest point in the ice cover
    # and the highest point of the observed snow cover.
    plt.ylim(min(-30, lowest_point*1.1), max(30, highest_point*1.1))
    plt.ylabel('Høyde og dybde i [cm] relativt vannlinjen')

    # Make legend
    legend = collections.OrderedDict(sorted(legend.items()))
    legend_handles = []
    for k, v in legend.items():
        legend_handles.append(mpatches.Patch(color=v[0], label=v[1]))
    legend_handles = list(reversed(legend_handles))
    plt.legend(handles=legend_handles)

    ######## Temp and snow in separate subplot
    plt.subplot2grid((4, 1), (3, 0), rowspan=1)
    plt.grid(color='0.6', linestyle='--', linewidth=0.7, zorder=0)

    # plot total snow depth on land
    index_max_snotot = snotot.index(max(snotot))
    max_snotot = snotot[index_max_snotot]
    max_sno = max(sno)

    if max_snotot != 0:
        snotot = [s * 1.5 * max(max_sno, 5) / max_snotot for s in snotot]
        dato_max_snotot = date[index_max_snotot]
    else:
        dato_max_snotot = date[-1]

    relative_max_snotot = snotot[index_max_snotot]
    plt.fill_between(date, 0, snotot, facecolor='0.95', edgecolor='k', linewidth=0.1, zorder=3)
    plt.text(dato_max_snotot - dt.timedelta(days=len(date)/8),
             relative_max_snotot - max(2.4 * max(sno), 20) * 0.08,
             '{}cm snø i terrenget'.format(int(max_snotot)), color='0.5')
    plt.plot(dato_max_snotot, relative_max_snotot, marker='o', color='0.5', zorder=4)

    # plot new snow
    plt.ylim(0, max(2.4 * max(sno), 20))
    plt.ylabel('Nysnø i [cm]')
    plt.bar(date, sno, width=0.7, facecolor='0.85', edgecolor=['black'] * len(date), linewidth=0.5, zorder=3)

    # Plot temperatures on a separate y axis
    plt.twinx()

    temp_pluss = []
    temp_minus = []

    for i in range(0, len(temp), 1):
        if temp[i] >= 0:
            temp_pluss.append(temp[i])
            temp_minus.append(np.nan)
        else:
            temp_minus.append(temp[i])
            temp_pluss.append(np.nan)

    plt.plot(date, temp, "black")
    plt.plot(date, temp_pluss, "red")
    plt.plot(date, temp_minus, "blue")

    if min(temp) > 0:
        plt.ylim(0, 1.2 * (max(temp)+2))
    else:
        plt.ylim(2. * min(temp), 1.2 * (max(temp)+2))
    plt.ylabel('Temp i [C]')

    plt.xlim(axis_date[0], axis_date[-1])
    plt.gca().axes.get_xaxis().set_ticklabels([])
    plt.gcf().text(0.78, 0.06, 'Figur laget {0:%Y-%m-%d %H:%M}'.format(dt.datetime.now()), color='0.5')

    plt.savefig(filename)
    plt.close()


def plot_ice_cover_copy(ice_cover, observed_ice, date, temp, sno, snotot, filename):
    """Plots ice cover over a given time period. It also plots observed data and snow and temperature data.

    :param ice_cover:
    :param observed_ice:    A list of ice_cover objects. If no observed ice use [] for resources.
    :param date:
    :param temp:
    :param snotot:
    :param filename:
    """

    # Turn off interactive mode
    plb.ioff()

    # Figure dimensions
    fsize = (16, 10)

    plb.figure(figsize=fsize)
    plb.clf()

    # depending on how many days are in the plot, the lineweight of the modelled data should be adjusted
    modelledLineWeight = 1100/len(ice_cover)

    # dont need to keep the colunm coordinates, but then again, why not..? Usefull for debuging
    all_column_coordinates = []

    # plot total snow depth on land
    plb.plot(date, snotot, "gray")

    plb.title('{0} - {1} days plotted.'.format(filename, len(ice_cover)))

    # a variable for the lowest point on the ice cover. It is used for setting the lower left y-limit .
    lowest_point = 0.

    # Plot ice cover
    for ic in ice_cover:

        # some idea of progress on the plotting
        if ic.date.day == 1:
            print((ic.date).strftime('%Y%m%d'))

        # make data for plotting. [ice layers.. [fro, too, ice type]].
        column_coordinates = []
        too = -ic.water_line  # water line is on xaxis

        for i in range(len(ic.column)-1, -1, -1):
            layer = ic.column[i]
            fro = too
            too = too + layer.height
            column_coordinates.append([fro, too, layer.type])

            if fro < lowest_point:
                lowest_point = fro

            # add coordinates to a vline plot
            plb.vlines(ic.date.date(), fro, too, lw=modelledLineWeight, color=layer.get_colour()) #ic.getColour(layer.type))

        all_column_coordinates.append(column_coordinates)

    # plot observed ice columns
    for ic in observed_ice:

        if len(ic.column) == 0:
            height = 0.05
            plb.vlines(ic.date.date(), -height, height, lw=4, color='white')
            plb.vlines(ic.date.date(), -height, height, lw=2, color='red')
        else:
            # some idea of progress on the plotting
            print("Plotting observations.")

            # make data for plotting. [ice layers.. [fro, too, icetype]].
            too = -ic.water_line  # water line is on xaxis

            for i in range(len(ic.column)-1, -1, -1):
                layer = ic.column[i]
                fro = too
                too = too + layer.height

                if fro < lowest_point:
                    lowest_point = fro

                padding = 0.
                padding_color = 'white'
                # outline the observations in orange if I have modelled the ice height after observation.
                if ic.metadata.get('IceHeightAfter') == 'Modeled':
                    padding_color = 'orange'
                # add coordinates to a vline plot
                plb.vlines(ic.date.date(), fro-padding, too+padding, lw=6, color=padding_color)
                plb.vlines(ic.date.date(), fro, too, lw=4, color=layer.get_colour())

    # the limits of the left side y-axis is defined relative the lowest point in the ice cover
    # and the highest point of the observed snow cover.
    plb.ylim(lowest_point*1.1, max(snotot)*1.05)

    # Plot temperatures on a separate y axis
    plb.twinx()
    temp_pluss = []
    temp_minus = []

    for i in range(0, len(temp), 1):
        if temp[i] >= 0:
            temp_pluss.append(temp[i])
            temp_minus.append(np.nan)
        else:
            temp_minus.append(temp[i])
            temp_pluss.append(np.nan)

    plb.plot(date, temp, "black")
    plb.plot(date, temp_pluss, "red")
    plb.plot(date, temp_minus, "blue")
    plb.ylim(-4*(max(temp)-min(temp)), max(temp))

    plb.savefig(filename)
    plb.close()


def plot_ice_cover_eb(
        ice_cover, energy_balance, observed_ice, date, temp, snotot, filename, prec=None, wind=None, clouds=None):
    """

    :param ice_cover:
    :param energy_balance:
    :param observed_ice:
    :param date:
    :param temp:
    :param snotot:
    :param filename:
    :param prec:
    :param wind:
    :param clouds:
    :return:

    Note: http://matplotlib.org/mpl_examples/color/named_colors.png
    """

    fsize = (16, 16)
    plt.figure(figsize=fsize)
    #fig = pplt.figure(figsize=fsize)
    plt.clf()


    ############## First subplot
    plt.subplot2grid((11, 1), (0, 0), rowspan=2)

    # depending on how many days are in the plot, the line weight of the modelled data should be adjusted
    modelledLineWeight = 1100/len(ice_cover)

    # dont need to keep the colunm coordinates, but then again, why not..? Usefull for debuging
    allColumnCoordinates = []

    # plot total snow depth on land
    plb.plot(date, snotot, "gray")

    plb.title('{0} - {1} days plotted.'.format(filename, len(ice_cover)))

    # a variable for the lowest point on the ice_cover. It is used for setting the lower left y-limit .
    lowest_point = 0.

    # Plot ice_cover
    for ic in ice_cover:

        # some idea of progress on the plotting
        if ic.date.day == 1:
            print((ic.date).strftime('%Y%m%d'))

        # make data for plotting. [icelayers.. [fro, too, icetype]].
        columncoordinates = []
        too = -ic.water_line  # water line is on xaxis

        for i in range(len(ic.column)-1, -1, -1):
            layer = ic.column[i]
            fro = too
            too = too + layer.height
            columncoordinates.append([fro, too, layer.type])

            if fro < lowest_point:
                lowest_point = fro

            # add coordinates to a vline plot
            plb.vlines(ic.date, fro, too, lw=modelledLineWeight, color=layer.get_colour()) #ic.getColour(layer.type))

        allColumnCoordinates.append(columncoordinates)


    # plot observed ice columns
    for ic in observed_ice:

        if len(ic.column) == 0:
            height = 0.05
            plb.vlines(ic.date, -height, height, lw=4, color='white')
            plb.vlines(ic.date, -height, height, lw=2, color='red')
        else:
            # some idea of progress on the plotting
            print("Plotting observations.")

            # make data for plotting. [ice layers.. [fro, too, icetype]].
            too = -ic.water_line  # water line is on xaxis

            for i in range(len(ic.column)-1, -1, -1):
                layer = ic.column[i]
                fro = too
                too = too + layer.height

                if fro < lowest_point:
                    lowest_point = fro

                padding = 0.
                padding_color = 'white'
                # outline the observations in orange if I have modelled the ice height after observation.
                if ic.metadata.get('IceHeightAfter') == 'Modeled':
                    padding_color = 'orange'
                # add coordinates to a vline plot
                plb.vlines(ic.date, fro-padding, too+padding, lw=6, color=padding_color)
                plb.vlines(ic.date, fro, too, lw=4, color=layer.get_colour())

    # the limits of the left side y-axis is defined relative the lowest point in the ice cover
    # and the highest point of the observed snow cover.
    plb.ylim(lowest_point*1.1, max(snotot)*1.05)

    # Plot temperatures on a separate y axis
    plb.twinx()
    temp_pluss = []
    temp_minus = []

    for i in range(0, len(temp), 1):
        if temp[i] >= 0:
            temp_pluss.append(temp[i])
            temp_minus.append(np.nan)
        else:
            temp_minus.append(temp[i])
            temp_pluss.append(np.nan)

    plb.plot(date, temp, "black")
    plb.plot(date, temp_pluss, "red")
    plb.plot(date, temp_minus, "blue")
    plb.ylim(-4*(max(temp)-min(temp)), max(temp))


    ########################################

    temp_atm = []
    temp_surf = []
    atm_minus_surf = []
    itterations = []
    EB = []
    S = []
    L = []
    H = []
    LE = []
    R = []
    G = []
    s_inn = []
    albedo = []
    SC = []
    R_i = []
    stability_correction = []
    CC = []
    SM = []


    if energy_balance[0].date > date[0]:
        i = 0
        while energy_balance[0].date > date[i]:
            temp_atm.append(np.nan)
            temp_surf.append(np.nan)
            atm_minus_surf.append(np.nan)
            itterations.append(np.nan)
            EB.append(np.nan)
            S.append(np.nan)
            L.append(np.nan)
            H.append(np.nan)
            LE.append(np.nan)
            R.append(np.nan)
            G.append(np.nan)
            s_inn.append(np.nan)
            albedo.append(np.nan)
            SC.append(np.nan)
            R_i.append(np.nan)
            stability_correction.append(np.nan)
            CC.append(np.nan)
            SM.append(np.nan)
            i += 1

    for eb in energy_balance:
        if eb.EB is None:
            temp_atm.append(np.nan)
            temp_surf.append(np.nan)
            atm_minus_surf.append(np.nan)
            itterations.append(np.nan)
            EB.append(np.nan)
            S.append(np.nan)
            L.append(np.nan)
            H.append(np.nan)
            LE.append(np.nan)
            R.append(np.nan)
            G.append(np.nan)
            s_inn.append(np.nan)
            albedo.append(np.nan)
            SC.append(np.nan)
            R_i.append(np.nan)
            stability_correction.append(np.nan)
            CC.append(np.nan)
            SM.append(np.nan)

        else:
            temp_atm.append(eb.temp_atm)
            temp_surf.append(eb.temp_surface)
            atm_minus_surf.append(eb.temp_atm-eb.temp_surface)
            itterations.append(eb.iterations)
            EB.append(eb.EB)
            S.append(eb.S)
            L.append(eb.L_a+eb.L_t)
            H.append(eb.H)
            LE.append(eb.LE)
            R.append(eb.R)
            G.append(eb.G)
            s_inn.append(eb.s_inn)
            albedo.append(eb.albedo)
            SC.append(eb.SC)
            R_i.append(eb.R_i)
            stability_correction.append(eb.stability_correction)
            CC.append(eb.CC)
            SM.append(eb.SM)


    ############### Second sub plot ##########################
    plt.subplot2grid((11, 1), (2, 0), rowspan=1)
    plb.bar(date, itterations, label="Iterations for T_sfc", color="gray")
    plb.xlim(date[0], date[-1])
    plb.xticks([])
    plb.ylabel("#")
    # l = plb.legend()
    # l.set_zorder(20)


    ############## CC, wind and prec ##########################
    plt.subplot2grid((11, 1), (3, 0), rowspan=1)

    # plot precipitation
    prec_mm = [p*1000. for p in prec]
    plb.bar(date, prec_mm, width=1, lw=0.5, label="Precipitation", color="deepskyblue", zorder=10)
    plb.ylabel("RR [mm]")
    plb.xlim(date[0], date[-1])
    plb.ylim(0, max(prec_mm)*1.1)
    plb.xticks([])

    # plot cloud cover
    for i in range(0, len(clouds) - 1, 1):
        if clouds[i] > 0:
            plb.hlines(0, date[i], date[i + 1], lw=190, color=str(-(clouds[i] - 1.)))
        elif clouds[i] == np.nan:
            plb.hlines(0, date[i], date[i + 1], lw=190, color="pink")
        else:
            plb.hlines(0, date[i], date[i + 1], lw=190, color=str(-(clouds[i] - 1.)))

    plb.twinx()
    plb.plot(date, wind, color="greenyellow", label="Wind 2m", lw=2, zorder=15)
    plb.ylabel("FFM [m/s]")



    ############ Temp diff sfc and atm #############################
    plt.subplot2grid((11, 1), (4, 0), rowspan=2)

    plb.plot(date, temp_atm, "black", zorder=5)
    plb.plot(date, temp, "blue", zorder=10)
    plb.plot(date, temp_surf, "green")
    area = np.minimum(temp_atm, temp_surf)

    plb.fill_between(date, temp_atm, area, color='red') #, alpha='0.5')
    plb.fill_between(date, temp_surf, area, color='blue') #, alpha='0.5')
    plb.ylim(-50, 20)
    plb.ylabel("[C]")


    # this plots temperature on separate right side axis
    plb.twinx()

    temp_pluss = []
    temp_minus = []
    for i in range(0, len(atm_minus_surf), 1):
        if atm_minus_surf[i] >= 0:
            temp_pluss.append(atm_minus_surf[i])
            temp_minus.append(np.nan)
        else:
            temp_minus.append(atm_minus_surf[i])
            temp_pluss.append(np.nan)
    plb.plot(date, atm_minus_surf, "black",  lw=2)
    plb.plot(date, temp_pluss, "red",  lw=2)
    plb.plot(date, temp_minus, "blue",  lw=2)
    plb.xlim(date[0], date[-1])
    plb.xticks([])
    plb.ylim(-1, 15)
    plb.ylabel("atm minus surf [C]")


    ################# Richardson no and stability correction of turbulent fluxes #######################
    plt.subplot2grid((11, 1), (6, 0), rowspan=1)

    plb.plot(date, R_i, color="blue", label="Richardson no.", lw=1, zorder=15)
    plb.ylabel("R_i (b) []")

    plb.twinx()

    stable = []
    unstable = []
    for i in range(0, len(R_i), 1):
        if R_i[i] > 0:
            stable.append(stability_correction[i])
            unstable.append(np.nan)
        elif R_i[i] < 0:
            unstable.append(stability_correction[i])
            stable.append(np.nan)
        else:
            unstable.append(np.nan)
            stable.append(np.nan)

    plb.plot(date, stability_correction, "black",  lw=2)
    plb.plot(date, stable, "green",  lw=2)
    plb.plot(date, unstable, "red",  lw=2)
    plb.xlim(date[0], date[-1])
    plb.xticks([])
    plb.ylabel("stable(g) unstable(r) []")



    ############# Energy terms and albedo ################
    plt.subplot2grid((11, 1), (7, 0), rowspan=4)


    # plot surface albedo
    for i in range(0, len(albedo) - 1, 1):
        if albedo[i] > 0.:
            plb.hlines(-11000, date[i], date[i + 1], lw=25, color=str(albedo[i]))
        elif clouds[i] == np.nan:
            plb.hlines(-11000, date[i], date[i + 1], lw=25, color="1.0")


    plb.plot(date, SM, "red", lw=3)
    plb.plot(date, SC, "blue", lw=3)
    plb.plot(date, [0.]*len(date), "white", lw=2)
    plb.plot(date, H, "blue")
    plb.plot(date, LE, "navy")
    plb.plot(date, R, "turquoise")
    plb.plot(date, G, "crimson")
    plb.plot(date, L, "green", lw=1)
    plb.plot(date, S, "gold", lw=1)
    #plb.plot(date, s_inn, "gold", lw=1)
    plb.plot(date, CC, "pink", lw=1)
    plb.plot(date, EB, "black")

    plb.ylim(-12000, 13000)
    plb.xlim(date[0], date[-1])
     #fig.tight_layout()
    plb.ylabel("Q [kJ/m2/24hrs]")


    plb.savefig(filename)
    #plb.show()


def plot_ice_cover_eb_simple(
        ice_cover, energy_balance, observed_ice, date, temp, snotot, filename):
    """

    :param ice_cover:
    :param energy_balance:
    :param observed_ice:
    :param date:
    :param temp:
    :param snotot:
    :param filename:
    :return:

    Note: http://matplotlib.org/mpl_examples/color/named_colors.png
    """

    fsize = (16, 16)
    plt.figure(figsize=fsize)
    #fig = pplt.figure(figsize=fsize)
    plt.clf()


    ############## First subplot
    plt.subplot2grid((5, 1), (0, 0), rowspan=2)

    # depending on how many days are in the plot, the line weight of the modelled data should be adjusted
    modelledLineWeight = 1100/len(ice_cover)

    # dont need to keep the colunm coordinates, but then again, why not..? Usefull for debuging
    allColumnCoordinates = []

    # plot total snow depth on land
    plb.plot(date, snotot, "gray")

    plb.title('{0} - {1} days plotted.'.format(filename, len(ice_cover)))

    # a variable for the lowest point on the ice_cover. It is used for setting the lower left y-limit .
    lowest_point = 0.

    # Plot ice_cover
    for ic in ice_cover:

        # some idea of progress on the plotting
        if ic.date.day == 1:
            print((ic.date).strftime('%Y%m%d'))

        # make data for plotting. [icelayers.. [fro, too, icetype]].
        columncoordinates = []
        too = -ic.water_line  # water line is on xaxis

        for i in range(len(ic.column)-1, -1, -1):
            layer = ic.column[i]
            fro = too
            too = too + layer.height
            columncoordinates.append([fro, too, layer.type])

            if fro < lowest_point:
                lowest_point = fro

            # add coordinates to a vline plot
            plb.vlines(ic.date, fro, too, lw=modelledLineWeight, color=layer.get_colour()) #ic.getColour(layer.type))

        allColumnCoordinates.append(columncoordinates)


    # plot observed ice columns
    for ic in observed_ice:

        if len(ic.column) == 0:
            height = 0.05
            plb.vlines(ic.date, -height, height, lw=4, color='white')
            plb.vlines(ic.date, -height, height, lw=2, color='red')
        else:
            # some idea of progress on the plotting
            print("Plotting observations.")

            # make data for plotting. [ice layers.. [fro, too, icetype]].
            too = -ic.water_line  # water line is on xaxis

            for i in range(len(ic.column)-1, -1, -1):
                layer = ic.column[i]
                fro = too
                too = too + layer.height

                if fro < lowest_point:
                    lowest_point = fro

                padding = 0.
                padding_color = 'white'
                # outline the observations in orange if I have modelled the ice height after observation.
                if ic.metadata.get('IceHeightAfter') == 'Modeled':
                    padding_color = 'orange'
                # add coordinates to a vline plot
                plb.vlines(ic.date, fro-padding, too+padding, lw=6, color=padding_color)
                plb.vlines(ic.date, fro, too, lw=4, color=layer.get_colour())

    # the limits of the left side y-axis is defined relative the lowest point in the ice cover
    # and the highest point of the observed snow cover.
    plb.ylim(lowest_point*1.1, max(snotot)*1.05)

    # Plot temperatures on a separate y axis
    plb.twinx()
    temp_pluss = []
    temp_minus = []

    for i in range(0, len(temp), 1):
        if temp[i] >= 0:
            temp_pluss.append(temp[i])
            temp_minus.append(np.nan)
        else:
            temp_minus.append(temp[i])
            temp_pluss.append(np.nan)

    plb.plot(date, temp, "black")
    plb.plot(date, temp_pluss, "red")
    plb.plot(date, temp_minus, "blue")
    plb.ylim(-4*(max(temp)-min(temp)), max(temp))


    ########################################

    temp_atm = []
    temp_surf = []
    atm_minus_surf = []
    itterations = []
    EB = []
    S = []
    L = []
    H = []
    LE = []
    T = []
    R = []
    G = []
    s_inn = []
    albedo = []
    SC = []
    R_i = []
    stability_correction = []
    CC = []
    SM = []


    if energy_balance[0].date > date[0]:
        i = 0
        while energy_balance[0].date > date[i]:
            temp_atm.append(np.nan)
            temp_surf.append(np.nan)
            atm_minus_surf.append(np.nan)
            itterations.append(np.nan)
            EB.append(np.nan)
            S.append(np.nan)
            L.append(np.nan)
            H.append(np.nan)
            LE.append(np.nan)
            T.append(np.nan)
            R.append(np.nan)
            G.append(np.nan)
            s_inn.append(np.nan)
            albedo.append(np.nan)
            SC.append(np.nan)
            R_i.append(np.nan)
            stability_correction.append(np.nan)
            CC.append(np.nan)
            SM.append(np.nan)
            i += 1

    for eb in energy_balance:
        if eb.EB is None:
            temp_atm.append(np.nan)
            temp_surf.append(np.nan)
            atm_minus_surf.append(np.nan)
            itterations.append(np.nan)
            EB.append(np.nan)
            S.append(np.nan)
            L.append(np.nan)
            H.append(np.nan)
            LE.append(np.nan)
            T.append(np.nan)
            R.append(np.nan)
            G.append(np.nan)
            s_inn.append(np.nan)
            albedo.append(np.nan)
            SC.append(np.nan)
            R_i.append(np.nan)
            stability_correction.append(np.nan)
            CC.append(np.nan)
            SM.append(np.nan)

        else:
            temp_atm.append(eb.temp_atm)
            temp_surf.append(eb.temp_surface)
            atm_minus_surf.append(eb.temp_atm-eb.temp_surface)
            itterations.append(eb.iterations)
            EB.append(eb.EB)
            S.append(eb.S)
            L.append(eb.L_a+eb.L_t)
            H.append(eb.H)
            LE.append(eb.LE)
            T.append(eb.H+eb.LE)
            R.append(eb.R)
            G.append(eb.G)
            s_inn.append(eb.s_inn)
            albedo.append(eb.albedo)
            SC.append(eb.SC)
            R_i.append(eb.R_i)
            stability_correction.append(eb.stability_correction)
            CC.append(eb.CC)
            SM.append(eb.SM)


    #############################
    plt.subplot2grid((5, 1), (2, 0), rowspan=3)


    plb.plot(date, SM, "red", lw=2)
    plb.plot(date, SC, "blue", lw=2)
    plb.plot(date, [0.]*len(date), "white", lw=2)
    #plb.plot(date, H, "blue")
    #plb.plot(date, LE, "navy")
    #plb.plot(date, T, "blue")
    plb.plot(date, R, "black")
    #plb.plot(date, G, "crimson")
    #plb.plot(date, L, "green", lw=1)
    #plb.plot(date, S, "gold", lw=1)
    #plb.plot(date, s_inn, "gold", lw=1)

    #plb.plot(date, CC, "pink", lw=1)
    #plb.plot(date, EB, "black")

    plb.ylim(-5000, 5000)
    plb.xlim(date[0], date[-1])
     #fig.tight_layout()
    plb.ylabel("Q [kJ/m2/24hrs]")


    plb.savefig(filename)
    #plb.show()


def debug_plot_eb(temps_sfc, ebs, date):
    """Plots energy balances for different surface temperatures. Theses are used to debug iteration methods
    for finding where energy balance is 0. Plots are also useful to understand behavior of energy balance
    at surface and air temperature.

    :param temps_sfc:
    :param ebs:
    :param date:
    :return:
    """

    fsize = (16, 10)
    plb.figure(figsize=fsize)
    plb.clf()
    plt.plot(temps_sfc, ebs)
    plt.axhline(y=0, color='k')
    # pplt.axvline(x=0, color='k')
    plt.axvline(x=np.median(temps_sfc), color='gray')
    plt.grid(True, which='both')

    date_string = dt.datetime.strftime(date, "%Y-%m-%d")
    file_name = "{0}energy balance plot {1}.png".format(se.plot_folder, date_string)

    plt.title(file_name)
    plt.xlabel('temp [C]')
    plt.ylabel('eb [kJ/m2/24hrs]')

    plb.savefig(file_name)


def plot_weather_elements(weather_element_lists):

    plt.figure(figsize=(15,10))
    plt.clf()

    for list in weather_element_lists:
        date_times = [e.Date for e in list]
        values = [e.Value for e in list]
        plt.plot(date_times, values, marker='o')


    plt.grid(color='0.6', linestyle='--', linewidth=0.7, zorder=0)

    plt.savefig('{}weatherlementplot'.format(se.plot_folder))
    plt.close()
