import os

import geopandas as gpd
import numpy as np
from pyproj import Proj, transform
from shapely.geometry import LineString, Point
# From the path to shape file, get geoPandas dataframe
from shapely.geometry import MultiLineString


def GISextract(path):
    try:
        rd_list = gpd.read_file(path)
    except:
        raise
        # import traceback
        # traceback.print_exc()
    else:
        return rd_list, path


# Get the list of the column of GeoPandas Dataframe
def getColumnsOfGIS(gis):
    columnsList = []

    for column in gis:
        columnsList.append(column)

    return columnsList


# Convert GIS data for generating data
def dataConversion(data):
    # GIS data
    rd_list = data.rd_list

    # Set ESPG
    from_proj = Proj(init=data.fromproj)
    to_proj = Proj(init=data.toproj)

    # Unit
    if data.isFeet:
        f2m = 0.3048
    else:
        f2m = 1

    # Set boundary
    y_higherb = data.yHigh
    y_lowerb = data.yLow
    x_leftb = data.xLeft
    x_rightb = data.xRight

    # Set reference point
    x_0 = data.xRef
    y_0 = data.yRef

    ## GIS Road Unique ID
    GISRdID = data.roadID
    ## Road Type
    L_tp = data.roadTp
    ## number of Lane
    L_num = data.numLane
    ## lane width
    L_wd = data.laneWid
    ## Shoulder
    rd_edge = data.shoulder

    # Make directory for generated files
    dir_name = os.path.dirname(data.path)
    fd_name = os.path.basename(data.path.split('.shp')[0])
    if not os.path.exists(dir_name + '/' + fd_name):
        os.makedirs(dir_name + '/' + fd_name)
        os.makedirs(dir_name + '/' + fd_name + '/results')

    output_path = dir_name + '/' + fd_name + '/results'

    x_0_f, y_0_f = transform(from_proj, to_proj, x_0, y_0)
    x_leftb_f, y_higherb_f = transform(from_proj, to_proj, x_leftb, y_higherb)
    x_rightb_f, y_lowerb_f = transform(from_proj, to_proj, x_rightb, y_lowerb)

    xref_left_m = (x_leftb_f - x_0_f) * f2m
    xref_right_m = (x_rightb_f - x_0_f) * f2m
    yref_lower_m = (y_lowerb_f - y_0_f) * f2m
    yref_higher_m = (y_higherb_f - y_0_f) * f2m

    rd_list['wd'] = rd_list[L_num] * rd_list[L_wd] * f2m + rd_edge
    rd_list['bw'] = rd_list['wd'] / 2
    # Assign unique ID to each link
    rd_list['linkID'] = range(1, len(rd_list) + 1)
    lineStr_list = []
    ii = 0
    for i, row in rd_list.iterrows():
        if (type(row.geometry) == LineString):
            link_coo = row.geometry.coords[:]
            x_m, y_m = (transform(from_proj, to_proj, [x[0] for x in link_coo], [x[1] for x in link_coo]))
            x_m = list((np.array(x_m) - x_0_f) * f2m)
            y_m = list((np.array(y_m) - y_0_f) * f2m)
            geo_m = LineString(Point(xy) for xy in zip(x_m, y_m))
            # rd_list.loc[i,'geometry'] = geo_m
            lineStr_list.append(geo_m)
        elif (type(row.geometry) == MultiLineString):
            lineStr_list1 = []
            print(type(row.geometry), row['linkID'], ' is multistrings.')
            for subgeo in row.geometry:
                link_coo = subgeo.coords[:]
                x_m, y_m = (transform(from_proj, to_proj, [x[0] for x in link_coo], [x[1] for x in link_coo]))
                x_m = list((np.array(x_m) - x_0_f) * f2m)
                y_m = list((np.array(y_m) - y_0_f) * f2m)
                # print(x_m,y_m)
                geo_m = LineString(Point(xy) for xy in zip(x_m, y_m))
                lineStr_list1.append(geo_m)
                ii = i
            lineStr_list.append(MultiLineString(lineStr_list1))
    rd_list = gpd.GeoDataFrame(rd_list, geometry=lineStr_list)

    return rd_list, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m, output_path
