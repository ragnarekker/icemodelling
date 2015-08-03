__author__ = 'raek'


# READS A FILE AND RETURNS A MATRIX
# Input:
#   innfilepath where the file is located
#   separator is the separator used between data. Eg ';', '\t'
# Output:
#   2 dimensional matrix[i][j]

def myreadfile(innfilepath, separator):
    infile = open(innfilepath)
    indata = infile.readlines()
    infile.close()

    for i in range(len(indata)):
        indata[i] = indata[i].strip()           # get rid of ' ' and '\n' and such
        indata[i] = indata[i].split(separator)  # splits line into list of elements in the line

    return indata
