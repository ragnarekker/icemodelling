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
    lowestPoint = 0.

    # Plot icecover
    for column in icecover:

        # some idea of progres on the plotting
        if column.date.day == 1:
            print((column.date).strftime('%Y%m%d'))

        # make data for plotting. [icelayers.. [fro, too, icetype]].
        columncoordinates = []
        too = -column.water_line  # water line is on xaxis

        for i in range(len(column.column)-1, -1, -1):
            layer = column.column[i]
            fro = too
            too = too + layer[0]
            columncoordinates.append([fro, too, layer[1]])

            if fro < lowestPoint:
                lowestPoint = fro

            # add coordinates to a vline plot
            plt.vlines(column.date, fro, too, lw=modelledLineWeight, color=column.getColour(layer[1]))

        allColumnCoordinates.append(columncoordinates)


    # plot observed icecolumns
    for column in observed_ice:

        if len(column.column) == 0:
            height = 0.05
            plt.vlines(column.date, -height, height, lw=4, color='white')
            plt.vlines(column.date, -height, height, lw=2, color='red')
        else:
            # some idea of progres on the plotting
            print("Plotting observations.")

            # make data for plotting. [icelayers.. [fro, too, icetype]].
            too = -column.water_line  # water line is on xaxis

            for i in range(len(column.column)-1, -1, -1):
                layer = column.column[i]
                fro = too
                too = too + layer[0]

                if fro < lowestPoint:
                    lowestPoint = fro

                padding = 0.
                # add coordinates to a vline plot
                plt.vlines(column.date, fro-padding, too+padding, lw=6, color= "white")
                plt.vlines(column.date, fro, too, lw=4, color=column.getColour(layer[1]))

    # the limits of the leftside y-axis is defined relative the lowest point in the icecover
    # and the highest point of the observed snowcover.
    plt.ylim(lowestPoint*1.1, max(snotot)*1.05)

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
