# -*- coding: utf-8 -*-
__author__ = 'ragnarekker'


def remove_norwegian_letters(name_inn):
    """

    :param name_inn:
    :return:

    Samiske tegn
    Áá
    Čč
    Đđ
    Ŋŋ
    Šš
    Ŧŧ
    Žž

    """

    if name_inn is None:
        return None

    name = name_inn

    if u'å' in name:
        name = name.replace(u'å', 'aa')
    if u'ø' in name:
        name = name.replace(u'ø', 'oe')
    if u'æ' in name:
        name = name.replace(u'æ', 'ae')
    if u'Å' in name:
        name = name.replace(u'Å', 'AA')
    if u'Ø' in name:
        name = name.replace(u'Ø', 'OE')
    if u'Æ' in name:
        name = name.replace(u'Æ', 'AE')

    # Samiske tegn
    if u'á' in name:
        name = name.replace(u'á', 'a')
    if u'Á' in name:
        name = name.replace(u'Á', 'A')
    if u'č' in name:
        name = name.replace(u'č', 'c')
    if u'Č' in name:
        name = name.replace(u'Č', 'C')
    if u'đ' in name:
        name = name.replace(u'đ', 'd')
    if u'Đ' in name:
        name = name.replace(u'Đ', 'D')
    if u'ŋ' in name:
        name = name.replace(u'ŋ', 'n')
    if u'Ŋ' in name:
        name = name.replace(u'Ŋ', 'N')
    if u'š' in name:
        name = name.replace(u'š', 's')
    if u'Š' in name:
        name = name.replace(u'Š', 'S')
    if u'ŧ' in name:
        name = name.replace(u'ŧ', 't')
    if u'Ŧ' in name:
        name = name.replace(u'Ŧ', 'T')
    if u'ž' in name:
        name = name.replace(u'ž', 'z')
    if u'Ž' in name:
        name = name.replace(u'Ž', 'Z')

    # name = name.encode('ascii', 'ignore')
    name = name.strip()                 # removes whitespace to left and right
    name = name.replace('\n', '')
    name = name.replace('\t', '')

    return name


def add_norwegian_letters(name_inn):
    """

    :param name_inn:
    :return:
    """

    if name_inn is None:
        return None

    name = name_inn

    if u'ae' in name:
        name = name.replace(u'ae', 'æ')
    if u'oe' in name:
        name = name.replace(u'oe', 'ø')
    if u'aa' in name:
        name = name.replace(u'aa', 'å')
    if u'AE' in name:
        name = name.replace(u'AE', 'Æ')
    if u'OE' in name:
        name = name.replace(u'OE', 'Ø')
    if u'AA' in name:
        name = name.replace(u'AA', 'Å')

    return name


def make_standard_file_name(name_inn):
    """Remove all letters that may cause trouble in a filename

    :param name_inn: [String]
    :return:         [String]
    """

    name = name_inn.replace(",","").replace("/","").replace("\"", "")
    name = remove_norwegian_letters(name)

    return name


def change_unicode_to_utf8hex(name_inn):
    """

    :param name_inn:
    :return:
    """

    if name_inn is None:
        return None

    name = name_inn
    if 'å' in name:
        name = name.replace('å', '%C3%A5').encode('ascii', 'ignore')
    elif 'ø' in name:
        name = name.replace('ø', '%C3%B8').encode('ascii', 'ignore')
    elif 'æ' in name:
        name = name.replace('æ', '%C3%A6').encode('ascii', 'ignore')
    elif 'Å' in name:
        name = name.replace('Å', '%C3%85').encode('ascii', 'ignore')
    elif 'Ø' in name:
        name = name.replace('Ø', '%C3%98').encode('ascii', 'ignore')
    elif 'Æ' in name:
        name = name.replace('Æ', '%C3%86').encode('ascii', 'ignore')
    else:
        name = name.encode('ascii', 'ignore')
    return name


if __name__ == "__main__":

    a = u'æøå'.encode('utf8')
    b = remove_norwegian_letters('ÆæØøÅåÁáČčĐđŊŋŠšŦŧŽž')
    c = add_norwegian_letters('Proeve.')

    b = 1
