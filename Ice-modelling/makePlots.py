__author__ = 'raek'
# -*- coding: utf-8 -*-
import pylab as plt
import numpy as np

# needs comments
def plotIcecover(icecover, observed_ice, date, temp, snotot, filename):
    '''
    :param icecover:
    :param observed_ice:    A list of icecover objects. If no observed ice use [] for input.
    :param date:
    :param temp:
    :param snotot:
    :param filename:
    :return:
    '''

    # Figure dimensions
    fsize = (16, 10)
    plt.figure(figsize=fsize)
    plt.clf()

    # depending on how many days are in the plot, the lineweight of the modelled data should be adjusted
    modelledLineWeight = 1100/len(icecover)

    # dont need to keep the colunm coordinates, but then again, why not..? Usefull for debuging
    allColumnCoordinates = []

    # plot total snowdepth on land
    plt.plot(date, snotot, "gray")

    plt.title('{0} - {1} days plotted.'.format(filename, len(icecover)))

    # a variable for the lowest point on the icecover. It is used for setting the lower left y-limit .
    lowest_point = 0.

    # Plot icecover
    for ic in icecover:

        # some idea of progres on the plotting
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
            plt.vlines(ic.date, fro, too, lw=modelledLineWeight, color=layer.colour()) #ic.getColour(layer.type))

        allColumnCoordinates.append(columncoordinates)


    # plot observed ice columns
    for ic in observed_ice:

        if len(ic.column) == 0:
            height = 0.05
            plt.vlines(ic.date, -height, height, lw=4, color='white')
            plt.vlines(ic.date, -height, height, lw=2, color='red')
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
                plt.vlines(ic.date, fro-padding, too+padding, lw=6, color=padding_color)
                plt.vlines(ic.date, fro, too, lw=4, color=layer.colour())

    # the limits of the left side y-axis is defined relative the lowest point in the ice cover
    # and the highest point of the observed snow cover.
    plt.ylim(lowest_point*1.1, max(snotot)*1.05)

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
    plt.ylim(-4*(max(temp)-min(temp)), max(temp))

    plt.savefig(filename)


def plotIcecoverEB(icecover, enegy_balance, observed_ice, date, temp, snotot, filename):
    return