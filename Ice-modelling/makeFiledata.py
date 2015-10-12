__author__ = 'ragnarekker'


import types as t
import datetime as dt


def write_vardat2(file_name, data, WSYS, OPER, DCHA):
    """Writes data to file using the vardat2 format from hydra-II at NVE.
    :param file_name:   [string]
    :param data:        [list of weatherelements] or [list of lists of weatherelements]
    :param WSYS:        [string] WorkingSYStem
    :param OPER:        [string] OPERator
    :param DCHA:        [string] DataCHANel
    :return:
    """

    # If data and DCHA not a list, make it so.
    if not isinstance(data, t.ListType):
        data = [data]
    if not isinstance(DCHA, t.ListType):
        DCHA = [DCHA]

    RTIM = dt.datetime.now().strftime('%Y%m%d/%H%M')

    f = open(file_name, 'w')

    # write header
    f.write('################################# 2 ######################################\n')
    f.write('#WSYS {0}\n'.format(WSYS))
    f.write('#OPER {0}\n'.format(OPER))
    f.write('#RTIM {0}\n'.format(RTIM))
    for dcha in DCHA:
        f.write('#DCHA {0}\n'.format(dcha))
    f.write('##########################################################################\n')

    # write values
    for i in range(0, len(data[0]), 1):
        text_line = '{0}'.format(data[0][i].Date.strftime('%Y%m%d/%H%M'))
        for d in data:
            text_line += '\t{0: >10}'.format(d[i].Value)
        text_line += '\n'
        f.write(text_line)

    f.close()

    return


def write_large_sting(file_name, extension, data):
    """Writes large data to file. Typpicaly the whole responds of a request.

    :param file_name:
    :param data:
    :return:
    """
    file_name += extension
    f = open(file_name, 'w')
    f.write(data)
    f.close()


def write_dictionary(file_name, extension, data, tabulated=False):
    """Writes a list of directoiries to file.

    :param file_name:
    :param extension:
    :param data:        [list of dictionaries]
    :param tabulated:   [bool] If True values a written in table form.
    :return:
    """

    file_name += extension

    if tabulated == False:
        with open(file_name, "w") as myfile:
            for d in data:
                for key, value in d.iteritems():
                    myfile.write("{0: <18} {1}\n".format(key+":", value))
                myfile.write("\n")
    else:
        with open(file_name, "w") as myfile:
            myfile.write("Tabulated data goes here. Method not implemented.")
