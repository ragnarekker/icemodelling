__author__ = 'raek'
# -*- coding: utf-8 -*-
import pylab as plb
import matplotlib.pyplot as pplt
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
    plb.figure(figsize=fsize)
    plb.clf()

    # depending on how many days are in the plot, the lineweight of the modelled data should be adjusted
    modelledLineWeight = 1100/len(icecover)

    # dont need to keep the colunm coordinates, but then again, why not..? Usefull for debuging
    allColumnCoordinates = []

    # plot total snow depth on land
    plb.plot(date, snotot, "gray")

    plb.title('{0} - {1} days plotted.'.format(filename, len(icecover)))

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
            plb.vlines(ic.date, fro, too, lw=modelledLineWeight, color=layer.colour()) #ic.getColour(layer.type))

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
                plb.vlines(ic.date, fro, too, lw=4, color=layer.colour())

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


def plotIcecoverEB(icecover, energy_balance, observed_ice, date, temp, snotot, filename):

    fsize = (16, 16)
    fig = pplt.figure(figsize=fsize)
    pplt.clf()


    ############## First subplot
    pplt.subplot(2, 1, 1)

    # depending on how many days are in the plot, the line weight of the modelled data should be adjusted
    modelledLineWeight = 1100/len(icecover)

    # dont need to keep the colunm coordinates, but then again, why not..? Usefull for debuging
    allColumnCoordinates = []

    # plot total snow depth on land
    plb.plot(date, snotot, "gray")

    plb.title('{0} - {1} days plotted.'.format(filename, len(icecover)))

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
            plb.vlines(ic.date, fro, too, lw=modelledLineWeight, color=layer.colour()) #ic.getColour(layer.type))

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
                plb.vlines(ic.date, fro, too, lw=4, color=layer.colour())

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



    pplt.subplot(2, 1, 2)

    EB = []
    S = []
    L = []
    H = []
    LE = []
    R = []
    G = []

    if energy_balance[0].date > date[0]:
        i = 0
        while energy_balance[0].date > date[i]:
            EB.append(np.nan)
            S.append(np.nan)
            L.append(np.nan)
            H.append(np.nan)
            LE.append(np.nan)
            R.append(np.nan)
            G.append(np.nan)
            i += 1

    for eb in energy_balance:
        if eb.EB is None:
            EB.append(np.nan)
            S.append(np.nan)
            L.append(np.nan)
            H.append(np.nan)
            LE.append(np.nan)
            R.append(np.nan)
            G.append(np.nan)
        else:
            EB.append(eb.EB)
            S.append(eb.S)
            L.append(eb.L_a-eb.L_t)
            H.append(eb.H)
            LE.append(eb.LE)
            R.append(eb.R)
            G.append(eb.G)


    plb.plot(date, EB, "gray")
    plb.plot(date, S, "yellow")
    plb.plot(date, L, "orange")
    plb.plot(date, H, "blue")
    plb.plot(date, LE, "navy")
    plb.plot(date, R, "turquoise")
    plb.plot(date, G, "crimson")

     #fig.tight_layout()

    plb.show()

    return