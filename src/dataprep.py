import sys

import geopandas as gpd
from matplotlib import pyplot

# From the path to shape file, get geoPandas dataframe
def GISextract(path):
    try:
        rd_list = gpd.read_file(path)
    except:
        raise
        #import traceback
        #traceback.print_exc()
    else:
        return rd_list

# Get the list of the column of GeoPandas Dataframe
def getColumnsOfGIS(gis):
    columnsList = []

    for column in gis:
        columnsList.append(column)

    return columnsList
