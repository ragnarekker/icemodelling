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


def plotIcecoverEB(icecover, energy_balance, observed_ice, date, temp, snotot, filename,
                   prec=None, wind=None, clouds=None):
    """
    http://matplotlib.org/mpl_examples/color/named_colors.png


    :param icecover:
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
    """

    fsize = (16, 16)
    pplt.figure(figsize=fsize)
    #fig = pplt.figure(figsize=fsize)
    pplt.clf()


    ############## First subplot
    pplt.subplot2grid((11, 1), (0, 0), rowspan=3)

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

        else:
            temp_atm.append(eb.temp_atm)
            temp_surf.append(eb.temp_surface)
            atm_minus_surf.append(eb.temp_atm-eb.temp_surface)
            itterations.append(eb.iterations)
            EB.append(eb.EB)
            S.append(eb.S)
            L.append(eb.L_a-eb.L_t)
            H.append(eb.H)
            LE.append(eb.LE)
            R.append(eb.R)
            G.append(eb.G)
            s_inn.append(eb.s_inn)
            albedo.append(eb.albedo)
            SC.append(eb.SC)


    #########################################
    pplt.subplot2grid((11, 1), (3, 0), rowspan=1)
    plb.bar(date, itterations, label="Iterations for T_sfc", color="gray")
    plb.xlim(date[0], date[-1])
    plb.xticks([])
    plb.ylabel("#")
    # l = plb.legend()
    # l.set_zorder(20)


    ########################################
    pplt.subplot2grid((11, 1), (4, 0), rowspan=1)

    # plot precipitation
    prec_mm = [p*1000. for p in prec]
    plb.bar(date, prec_mm, width=1, lw=0.5, label="Precipitation", color="deepskyblue", zorder=10)
    plb.ylabel("RR [mm]")
    plb.xlim(date[0], date[-1])
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



    #########################################
    pplt.subplot2grid((11, 1), (5, 0), rowspan=2)

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
    plb.ylim(-3, 10)
    plb.ylabel("delta [C]")




    #############################
    pplt.subplot2grid((11, 1), (7, 0), rowspan=4)


    # plot surface albedo
    for i in range(0, len(albedo) - 1, 1):
        if albedo[i] > 0.:
            plb.hlines(-8000, date[i], date[i + 1], lw=25, color=str(albedo[i]))
        elif clouds[i] == np.nan:
            plb.hlines(-8000, date[i], date[i + 1], lw=25, color="1.0")


    plb.plot(date, EB, "gray")
    plb.plot(date, H, "blue")
    plb.plot(date, LE, "navy")
    plb.plot(date, R, "turquoise")
    plb.plot(date, G, "crimson")
    plb.plot(date, L, "green", lw=1)
    plb.plot(date, S, "gold", lw=1)
    #plb.plot(date, s_inn, "gold", lw=1)
    plb.plot(date, SC, "red", lw=1)


    plb.ylim(-12000, 13000)
    plb.xlim(date[0], date[-1])
     #fig.tight_layout()
    plb.ylabel("Q [kJ/m2/24hrs]")


    plb.savefig(filename)

    #plb.show()

    return

