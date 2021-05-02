import os
import shutil
import time
import fiona
from fiona import _shim, schema
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import Proj, transform
from scipy.interpolate import griddata
from shapely import geometry
from shapely.geometry import LineString, MultiLineString, Point, Polygon
import descartes

from constants import TEMPLATE


def GISextract(path):
    try:
        rd_list = gpd.read_file(path)
    except:
        raise
        # import traceback
        # traceback.print_exc()
    else:
        return rd_list, path


# Convert GIS data for generating data
def dataConversion(data):
    # GIS data
    rd_list = data.rd_list

    # Set ESPG
    from_proj = Proj(init=data.fromproj)
    to_proj = Proj(init=data.toproj)

    # Unit
    if data.isFeet.get():
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
    dir_name = os.path.dirname(os.path.dirname(data.path))
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


    print(f2m)
    print(L_wd)
    print(L_num)
    print(rd_edge)

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

    print("Conversion finished")

    print(rd_list)

    return rd_list, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m, output_path


def generateLINE(data):
    # Process for LINE (including LINE, RLINE and RLINEXT) source
    print('')
    print('Convert road GIS to Line source..')
    st = time.time()
    frame = []

    # Set column names
    rd_list = data.rd_list
    GISRdID = data.roadID
    L_tp = data.roadTp
    output_path = data.output_path

    print("data check")
    print(rd_list)
    print(GISRdID)
    print(L_tp)

    for i, row in rd_list.iterrows():
        if (type(row.geometry) == LineString):
            rd_geo = gpd.GeoDataFrame(columns=[GISRdID, 'linkID', 'linkID_new', 'F_LTYPE', 'wd', 'bw', 'area', \
                                               'geometry', 'coord_aer'])
            link_coo = row.geometry.coords[:]
            x_m = [x[0] for x in link_coo]
            y_m = [x[1] for x in link_coo]
            rd_geo['geometry'] = [LineString(Point(xy) for xy in zip(x_m[j:j + 2], y_m[j:j + 2])) for j in
                                  range(len(x_m) - 1)]
            rd_geo['area'] = rd_geo.geometry.apply(lambda x: x.length * row['wd'])
            rd_geo['wd'] = row['wd']
            rd_geo['bw'] = row['wd'] / 2.0
            rd_geo[GISRdID] = row[GISRdID]
            rd_geo['linkID'] = row['linkID']
            rd_geo['linkID_new'] = [(str(row['linkID']) + '__' + str(x)) for x in range(len(rd_geo))]
            rd_geo['F_LTYPE'] = row[L_tp]

            def coord_aer_func(coords):
                coord_aer = ''
                for p in coords:
                    coord_aer = coord_aer + str(round(p[0], 1)) + ' ' + str(round(p[1], 1)) + ' '
                return coord_aer

            rd_geo['coord_aer'] = rd_geo['geometry'].apply(lambda x: coord_aer_func(x.coords[:]))
            frame.append(rd_geo)
        elif (type(row.geometry) != LineString):
            iii = 1
            print(type(row.geometry), row['linkID'], ' is multistrings, further assigning IDs')
            for subgeo in row.geometry:
                rd_geo = gpd.GeoDataFrame(columns=[GISRdID, 'linkID', 'linkID_new', 'F_LTYPE', 'wd', 'bw', 'area', \
                                                   'geometry', 'coord_aer'])
                link_coo = subgeo.coords[:]
                x_m = [x[0] for x in link_coo]
                y_m = [x[1] for x in link_coo]
                rd_geo['geometry'] = [LineString(Point(xy) for xy in zip(x_m[j:j + 2], y_m[j:j + 2])) for j in
                                      range(len(x_m) - 1)]
                rd_geo['area'] = rd_geo.geometry.apply(lambda x: x.length * row['wd'])
                rd_geo['wd'] = row['wd']
                rd_geo['bw'] = row['wd'] / 2
                rd_geo[GISRdID] = row[GISRdID]
                rd_geo['linkID'] = row['linkID']
                rd_geo['linkID_new'] = [str(row['linkID']) + '_' + str(iii) + '__' + str(x) for x in range(len(rd_geo))]
                rd_geo['F_LTYPE'] = row[L_tp]
                coord_aer = ''

                def coord_aer_func(coords):
                    coord_aer = ''
                    for p in coords:
                        coord_aer = coord_aer + str(round(p[0], 1)) + ' ' + str(round(p[1], 1)) + ' '
                    return coord_aer

                rd_geo['coord_aer'] = rd_geo['geometry'].apply(lambda x: coord_aer_func(x.coords[:]))
                iii += 1
                frame.append(rd_geo)
    rd_geo = pd.DataFrame(pd.concat(frame))
    # just to show the link geometry to AERMOD
    rd_geo.to_csv(output_path + '/Line.csv', index=False)
    print("Line generation done! exported to 'Line.csv'.")
    end = time.time()
    print('Take about', round((end - st) / 60, 2), 'minutes.')


# Visualizing LINE
def visualizeLINE(output_path, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m):
    def add_line_from_line(row):
        xxxx = row['coord_aer'].split(' ')
        x = [float(xxxx[0]), float(xxxx[2])]
        y = [float(xxxx[1]), float(xxxx[3])]
        return geometry.LineString(Point(xy) for xy in zip(x, y))

    rd_geo = pd.read_csv(output_path + '/Line.csv')
    rd_geo['geometry'] = rd_geo.apply(lambda row: add_line_from_line(row), axis=1)
    rd_geo = gpd.GeoDataFrame(rd_geo, geometry=rd_geo.geometry)
    buffer_rd = gpd.GeoDataFrame(geometry=rd_geo.apply(lambda x: x.geometry.buffer(x['bw'], cap_style=2), axis=1))
    fig, ax = plt.subplots()
    buffer_rd.plot(ax=ax, edgecolor='black', linewidth=0.3, facecolor="none", zorder=2)
    buffer_rd.plot(ax=ax, color='blue', alpha=0.3, linewidth=0.3, zorder=2)
    plt.title("AERMOD 'Line' Geometry")
    plt.axis('scaled')
    plt.xlabel('meter')
    plt.ylabel('meter')
    plt.xlim(xref_left_m, xref_right_m)
    plt.ylim(yref_lower_m, yref_higher_m)
    plt.savefig(output_path + "/GIS_line.jpg", bbox_inches='tight', dpi=600)

    return fig


# Generate AREA
def generateAREA(rd_list, output_path, GISRdID, L_tp):
    # Process for AREA
    # Maximum number of nodes for AREA modeling (Default as 10 to limit max vertices as 20. The value has to be <=10)
    max_pts = 10
    print('')
    print('Convert road GIS to AREA source..')
    st = time.time()
    rd_geo = gpd.GeoDataFrame(columns=[GISRdID, 'linkID', 'linkID_new', 'F_LTYPE', 'wd', 'bw', 'area', \
                                       'x_ini', 'y_ini', 'n', 'poly', 'geometry', 'coord', 'vertex_aer', 'coord_aer'])
    for i, row in rd_list.iterrows():
        if (type(row.geometry) == LineString):
            link_coo = row.geometry.coords[:]
            nn = int(len(link_coo) / max_pts) - 1 + (len(link_coo) % max_pts > 0)
            ii = 0
            while ii <= nn:
                if (ii == 0):
                    sub_geom = link_coo[ii * max_pts:max_pts * (ii + 1)]
                else:
                    sub_geom = link_coo[ii * max_pts - 1:max_pts * (ii + 1)]
                geo_m = LineString(sub_geom)
                poly, geo_m, p_l, area, ini_x, ini_y, coord_aer, n = geo_area(geo_m, row['wd'] / 2.0)
                rd_geo.loc[len(rd_geo)] = [row[GISRdID], row['linkID'], str(row['linkID']) + '__' + str(ii), row[L_tp], \
                                           row['wd'], row['wd'] / 2, area, ini_x, ini_y, n, poly, \
                                           geo_m, p_l, str(ini_x) + ' ' + str(ini_y), coord_aer]
                ii += 1
        elif (type(row.geometry) == MultiLineString):
            iii = 1
            print(type(row.geometry), row['linkID'], ' is multistrings, further assigning IDs')
            for subgeo in row.geometry:
                link_coo = subgeo.coords[:]
                nn = int(len(link_coo) / max_pts) - 1 + (len(link_coo) % max_pts > 0)
                ii = 0
                while ii <= nn:
                    if ii == 0:
                        sub_geom = link_coo[ii * max_pts:max_pts * (ii + 1)]
                    else:
                        sub_geom = link_coo[ii * max_pts - 1:max_pts * (ii + 1)]
                    geo_m = LineString(sub_geom)
                    poly, geo_m, p_l, area, ini_x, ini_y, coord_aer, n = geo_area(geo_m, row['wd'] / 2.0)
                    rd_geo.loc[len(rd_geo)] = [row[GISRdID], row['linkID'],
                                               str(row['linkID']) + '_' + str(iii) + '__' + str(ii), row[L_tp], \
                                               row['wd'], row['wd'] / 2, area, ini_x, ini_y, n, poly, geo_m, p_l,
                                               str(ini_x) + ' ' + str(ini_y), coord_aer]
                    ii += 1
    # just to show the link geometry to AERMOD
    rd_geo.to_csv(output_path + '/AREA.csv', index=False)
    print("AREA generation done! exported to 'AREA.csv'.")
    end = time.time()
    print('Take about', round((end - st) / 60, 2), 'minutes.')
    # run_df = pd.DataFrame(columns = ['method','links','sources','time'])
    # run_df.loc[0] = ['AREA', len(rd_list), len(rd_geo), round((end-st),2)]
    # with open(path + 'gen_time.csv', 'a') as f:
    #    run_df.to_csv(path + 'gen_time.csv', mode = 'a',index = False, header = f.tell()==0)


# Function for generating AREA
def geo_area(geo_m, wd):
    ini_x = 0.0
    ini_y = 0.0
    lp_l = geo_m.parallel_offset(wd, 'left', join_style=2)
    lp_l = lp_l.coords[:]
    if len(lp_l) > 10:
        index_l = [int(i) for i in np.linspace(0, len(lp_l) - 1, 10)]
        lp_l = [lp_l[i] for i in index_l]
    rp_l = geo_m.parallel_offset(wd, 'right', join_style=2)
    rp_l = rp_l.coords[:]
    if len(rp_l) > 10:
        index_l = [int(i) for i in np.linspace(0, len(rp_l) - 1, 10)]
        rp_l = [rp_l[i] for i in index_l]
    # print(lp_l)
    # print(rp_l)
    p_l = lp_l + rp_l
    ini_x = round(p_l[0][0], 1)
    ini_y = round(p_l[0][1], 1)
    poly = geometry.Polygon((round(p[0], 1), round(p[1], 1)) for p in p_l)
    coord_aer = ''
    for p in p_l:
        coord_aer = coord_aer + str(round(p[0], 1)) + ' ' + str(round(p[1], 1)) + ' '
    area = poly.area
    return poly, geo_m, p_l, area, ini_x, ini_y, coord_aer, len(p_l)


# Visualizing AREA
def visualizeAREA(output_path, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m):

    def add_polygon_from_poly(row):
        xxxx = row['poly'].split('((')[1].split('))')[0].split(', ')
        x = [float(xx.split(' ')[0]) for xx in xxxx]
        y = [float(yy.split(' ')[1]) for yy in xxxx]
        return geometry.Polygon((x[j], y[j]) for j in range(len(x)))

    # For Area:
    rd_geo = pd.read_csv(output_path + '/AREA.csv')
    rd_geo['geometry'] = rd_geo.apply(lambda row: add_polygon_from_poly(row), axis=1)
    rd_geo = gpd.GeoDataFrame(rd_geo, geometry=rd_geo.geometry)
    rd_geo.buffer(2)
    fig, ax = plt.subplots()
    rd_geo.plot(ax=ax, edgecolor='black', linewidth=0.3, facecolor="none", zorder=2)
    rd_geo.plot(ax=ax, color='blue', alpha=0.3, linewidth=0.3, zorder=2)
    plt.title("AERMOD 'AREA' Geometry")
    plt.axis('scaled')
    plt.xlabel('meter')
    plt.ylabel('meter')
    plt.xlim(xref_left_m, xref_right_m)
    plt.ylim(yref_lower_m, yref_higher_m)
    plt.savefig(output_path + "/GIS_area.jpg", bbox_inches='tight', dpi=600)
    return fig


# Generate VOLUME
def generateVOLUME(output_path, rd_list, max_vol, GISRdID):

    print("data check")
    print(max_vol)

    # output path = path + fd_name

    # max_vol = 10.0  # [5,7.9,80]
    method = 'VOLUME'
    print('')
    print('Convert road GIS to VOLUME source..')
    st = time.time()
    rd_list['voln'] = 0
    frame = []
    for i, row in rd_list.iterrows():
        rd_list.loc[i, 'voln'] = int(row['wd'] / max_vol) + (row['wd'] % max_vol > 0)
        subwd = row['wd'] / rd_list.loc[i, 'voln']
        sub_locid = [ii - (rd_list.loc[i, 'voln'] - 1) / 2.0 for ii in range(rd_list.loc[i, 'voln'])]
        sub_loc = [ii * subwd for ii in sub_locid]
        frame.append(geo_volume(rd_list.loc[i], sub_loc, subwd, GISRdID))
    df = pd.DataFrame(pd.concat(frame))
    df = df.reset_index(drop=True)
    gdf = gpd.GeoDataFrame(df, geometry=df.geometry)
    gdf['coord_aer'] = [str(round(xy.coords[0][0], 1)) + ' ' + str(round(xy.coords[0][1], 1)) for xy in
                        gdf['geometry'].tolist()]
    gdf['yinit'] = (gdf['subwd'] / 2.15).round(2)
    gdf.to_csv(output_path + '/' + method + '_' + str(max_vol) + '.csv', index=False)
    print("VOLUME generation done! exported to 'VOLUME_" + str(max_vol) + ".csv'.")
    end = time.time()
    print('Take about', round((end - st) / 60, 2), 'minutes.')
    run_df = pd.DataFrame(columns=['method', 'links', 'sources', 'time'])
    run_df.loc[0] = [method + '_' + str(max_vol), len(rd_list), len(gdf), round((end - st), 2)]

    with open(os.path.dirname(output_path) + 'gen_time.csv', 'a') as f:
        run_df.to_csv(os.path.dirname(output_path) + 'gen_time.csv', mode='a', index=False, header=f.tell() == 0)

    # with open(path + 'gen_time.csv', 'a') as f:
    #    run_df.to_csv(path + 'gen_time.csv', mode='a', index=False, header=f.tell() == 0)


# This funcion is for VOLUME source
def geo_volume(geo, sub_loc, subwd, GISRdID):
    frame = []
    if (type(geo.geometry) == LineString):
        geo_m = geo.geometry
        for loc in sub_loc:
            geo_tmp = geo_m.parallel_offset(loc, 'left', join_style=2)
            geo_len = geo_tmp.length
            npts = int(geo_len / subwd)
            if npts == 0:
                npts = 1
            avg_l = geo_len / npts
            distances = np.arange(avg_l / 2, geo_len, avg_l)
            points = [geo_tmp.interpolate(d) for d in distances]
            rt_pt = gpd.GeoDataFrame(columns=('linkID', 'geometry'))
            rt_pt['geometry'] = points
            rt_pt['linkID'] = geo.linkID
            frame.append(rt_pt)
    else:
        print(type(geo.geometry), geo['linkID'], ' is multistrings, further assigning IDs')
        for subgeo in geo.geometry:
            geo_m = subgeo
            for loc in sub_loc:
                geo_tmp = geo_m.parallel_offset(loc, 'left', join_style=2)
                geo_len = geo_tmp.length
                npts = int(geo_len / subwd)
                if npts == 0:
                    npts = 1
                avg_l = geo_len / npts
                distances = np.arange(avg_l / 2, geo_len, avg_l)
                points = [geo_tmp.interpolate(d) for d in distances]
                rt_pt = gpd.GeoDataFrame(columns=('linkID', 'geometry'))
                rt_pt['geometry'] = points
                rt_pt['linkID'] = geo.linkID
                frame.append(rt_pt)
    rt_df = pd.DataFrame(pd.concat(frame))
    rt_df['NO'] = range(len(rt_df))
    rt_df['linkID_new'] = rt_df['linkID'].astype(str) + '__' + rt_df["NO"].astype(str)
    rt_gdf = gpd.GeoDataFrame(rt_df, geometry=rt_df.geometry)
    # rt_gdf['EM_AER'] = geo.EM_RATE/1609.344/3600 * geo_l/n
    rt_gdf['nn'] = len(rt_df)
    rt_gdf['subwd'] = subwd
    rt_gdf[GISRdID] = geo[GISRdID]
    return rt_gdf[[GISRdID, 'linkID', 'linkID_new', 'geometry', 'nn', 'subwd']]


# Visualize VOLUME
def visualizeVOLUME(output_path, rd_list, max_vol, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m):
    print("start visualize VOLUME Max size = " + str(max_vol))
    # VOLUME visualization

    st = time.time()
    gdf = pd.read_csv(output_path + '/VOLUME_' + str(max_vol) + '.csv')
    gdf['geometry'] = gdf.apply(lambda row: Point(float(xx) for xx in row['coord_aer'].split(' ')), axis=1)
    gdf = gpd.GeoDataFrame(gdf, geometry=gdf.geometry)
    fig, ax = plt.subplots()
    buffer_1 = gpd.GeoDataFrame(geometry=gdf.apply(lambda x: x.geometry.buffer(x['yinit'] * 2.15 + 0.99),
                                                   axis=1))  # hide if using more accurate graph option
    buffer_1['dissol'] = 1  # hide if using more accurate graph option
    buffer_2 = gpd.GeoDataFrame(
        buffer_1.dissolve(by='dissol').reset_index(drop=True))  # hide if using more accurate graph option
    buffer_2.plot(linewidth=0.5, edgecolor='orange', facecolor="none",
                  ax=ax)  # hide if using more accurate graph option
    buffer_2.plot(color='orange', alpha=0.1, ax=ax)  # hide if using more accurate graph option
    buffer_1 = gpd.GeoDataFrame(geometry=gdf.apply(lambda x: x.geometry.buffer(x['subwd'] / 2), axis=1))
    buffer_1['dissol'] = 1
    buffer_2 = gpd.GeoDataFrame(buffer_1.dissolve(by='dissol').reset_index(drop=True))
    # buffer_2.plot(linewidth = 0.3,edgecolor='blue',facecolor="none",ax=ax) # hide if using more accurate graph option
    buffer_2.plot(alpha=0.3, ax=ax)
    gdf.plot(color='black', markersize=1, ax=ax)
    plt.title("AERMOD Volume Geometry, MAX Cell: " + str(max_vol) + ' m')
    plt.axis('scaled')
    plt.xlabel('meter')
    plt.ylabel('meter')
    # more precise info
    precise_inf = False
    if precise_inf:
        for i, row in gdf.iterrows():
            circle_ed = plt.Circle(row['geometry'].coords[:][0], radius=row['subwd'] / 2, linewidth=0.3,
                                   edgecolor='blue',
                                   facecolor="none")
            # circle_ex = plt.Circle(row['geometry'].coords[:][0],radius = row['yinit']*2.15+0.99,fc = 'none',linewidth = 0.5, linestyle = 'dashed', edgecolor='orange')
            # plt.gca().add_patch(circle_ex)
            plt.gca().add_patch(circle_ed)

    '''
    rd_geo = pd.read_csv(output_path + '/AREA.csv')
    rd_geo['geometry'] = rd_geo.apply(lambda row: add_polygon_from_poly(row), axis=1)
    rd_geo = gpd.GeoDataFrame(rd_geo, geometry=rd_geo.geometry)
    rd_geo.plot(ax=ax, edgecolor='black', linewidth=0.3, alpha=0.5, facecolor="none", zorder=2)
    '''
    print("pass")
    buffer_0 = gpd.GeoDataFrame(geometry=rd_list.apply(lambda x: x.geometry.buffer(x['bw'], cap_style=2), axis=1))
    buffer_0.plot(ax=ax, edgecolor='black', linewidth=0.3, alpha=0.5, facecolor="none", zorder=2)

    plt.xlim(xref_left_m, xref_right_m)
    plt.ylim(yref_lower_m, yref_higher_m)
    plt.savefig(output_path + "/GIS_volume_" + str(max_vol) + ".jpg", bbox_inches='tight', dpi=600)
    end = time.time()
    print('Take about', round((end - st) / 60, 2), 'minutes.')

    return fig


# Function for visualizing VOLUME
def add_polygon_from_poly(row):
    xxxx = row['poly'].split('((')[1].split('))')[0].split(', ')
    x = [float(xx.split(' ')[0]) for xx in xxxx]
    y = [float(yy.split(' ')[1]) for yy in xxxx]
    return geometry.Polygon((x[j], y[j]) for j in range(len(x)))


# Generate receptors
def generateReceptors(rd_list, output_path, L_tp, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m, rec_lyr,
                      rec_grid_interval, rec_z):
    rec_lyr = rec_lyr[rec_lyr['F_LTYPE'].isin(rd_list[L_tp].unique())].reset_index(drop=True)
    ###########################################################################################
    ###################################################################
    # 2. Receptor Module: Generate receptor layers
    ###################################################################
    # Intervals of gridded receptors in meters
    print('Generate the near-road receptor...')

    '''
    print("rd_list:")
    print(rd_list)
    print("rec_lyr:")
    print(rec_lyr)
    print("L_tp:")
    print(L_tp)
    print("Interval:")
    print(rec_grid_interval)
    print("Elevation:")
    print(rec_z)
    '''

    ## 2.1. Generate near road receptors
    # Input needed below!!
    # Also, please define receptor layers in 'receptor_layers.csv' for each road type
    # DISTANCE: distance in meters from road edge. INTERVAL: receptor intervals in meters
    # Then load the layer information
    frame_tt = []
    for rt in rec_lyr.F_LTYPE.unique():
        rd_list1 = rd_list[rd_list[L_tp] == rt].reset_index(drop=True)
        rec_lyr1 = rec_lyr[rec_lyr['F_LTYPE'] == rt].reset_index(drop=True)
        for li, lrow in rec_lyr1.iterrows():
            buffer_1 = gpd.GeoDataFrame( \
                geometry=rd_list1.apply(lambda x: \
                                            x.geometry.buffer(lrow['DISTANCE'] + x['bw'], cap_style=1), axis=1))
            buffer_1['dissol'] = 1
            buffer_2 = gpd.GeoDataFrame(buffer_1.dissolve(by='dissol').reset_index(drop=True))
            ii = 0
            print("     Road Type " + str(lrow['F_LTYPE']) + " - Generating layer " + str(
                lrow['LAYER']) + " receptors...")
            frame = []
            rec_n = str(lrow['F_LTYPE']) + '_' + str(lrow['LAYER']) + '_'
            for i, row in buffer_2.iterrows():
                if (type(row.geometry) == Polygon):
                    rec_rd = gpd.GeoDataFrame(columns=['geometry', 'x', 'y', 'coord_aer'])
                    x_m = [x[0] for x in row.geometry.exterior.coords[:]]
                    y_m = [x[1] for x in row.geometry.exterior.coords[:]]
                    geo_bufl = LineString(Point(xy) for xy in zip(x_m, y_m))
                    bl = geo_bufl.length
                    distances = np.arange(2, bl, lrow['INTERVAL'])
                    points = [geo_bufl.interpolate(distance) for distance in distances]
                    rec_rd['geometry'] = points
                    # rec_rd['rec_id'] = [rec_n + str(ii) for ii in range(1, len(rec_rd)+1)]
                    rec_rd['x'] = [x.coords[:][0][0] for x in points]
                    rec_rd['y'] = [y.coords[:][0][1] for y in points]
                    rec_rd['coord_aer'] = rec_rd['x'].round(1).astype(str) + ' ' + rec_rd['y'].round(1).astype(
                        str) + ' ' + str(round(rec_z, 1))
                    frame.append(rec_rd.copy())
                    for interior in row.geometry.interiors:
                        rec_rd = gpd.GeoDataFrame(columns=['rec_id', 'geometry', 'x', 'y', 'coord_aer'])
                        x_m = [x[0] for x in interior.coords[:]]
                        y_m = [x[1] for x in interior.coords[:]]
                        geo_bufl = LineString(Point(xy) for xy in zip(x_m, y_m))
                        bl = geo_bufl.length
                        distances = np.arange(2, bl, lrow['INTERVAL'])
                        points = [geo_bufl.interpolate(distance) for distance in distances]
                        rec_rd['geometry'] = points
                        # rec_rd['rec_id'] = [rec_n + str(ii) for ii in range(1, len(rec_rd)+1)]
                        rec_rd['x'] = [x.coords[:][0][0] for x in points]
                        rec_rd['y'] = [y.coords[:][0][1] for y in points]
                        rec_rd['coord_aer'] = rec_rd['x'].round(1).astype(str) + ' ' + rec_rd['y'].round(1).astype(
                            str) + ' ' + str(round(rec_z, 1))
                        frame.append(rec_rd.copy())
                else:
                    for pg1 in row.geometry:
                        rec_rd = gpd.GeoDataFrame(columns=['geometry', 'x', 'y', 'coord_aer'])
                        x_m = [x[0] for x in pg1.exterior.coords[:]]
                        y_m = [x[1] for x in pg1.exterior.coords[:]]
                        geo_bufl = LineString(Point(xy) for xy in zip(x_m, y_m))
                        bl = geo_bufl.length
                        distances = np.arange(2, bl, lrow['INTERVAL'])
                        points = [geo_bufl.interpolate(distance) for distance in distances]
                        rec_rd['geometry'] = points
                        # rec_rd['rec_id'] = [rec_n + str(ii) for ii in range(1, len(rec_rd)+1)]
                        rec_rd['x'] = [x.coords[:][0][0] for x in points]
                        rec_rd['y'] = [y.coords[:][0][1] for y in points]
                        rec_rd['coord_aer'] = rec_rd['x'].round(1).astype(str) + ' ' + rec_rd['y'].round(1).astype(
                            str) + ' ' + str(round(rec_z, 1))
                        frame.append(rec_rd.copy())
                        for interior in pg1.interiors:
                            rec_rd = gpd.GeoDataFrame(columns=['rec_id', 'geometry', 'x', 'y', 'coord_aer'])
                            x_m = [x[0] for x in interior.coords[:]]
                            y_m = [x[1] for x in interior.coords[:]]
                            geo_bufl = LineString(Point(xy) for xy in zip(x_m, y_m))
                            bl = geo_bufl.length
                            distances = np.arange(2, bl, lrow['INTERVAL'])
                            points = [geo_bufl.interpolate(distance) for distance in distances]
                            rec_rd['geometry'] = points
                            # rec_rd['rec_id'] = [rec_n + str(ii) for ii in range(1, len(rec_rd)+1)]
                            rec_rd['x'] = [x.coords[:][0][0] for x in points]
                            rec_rd['y'] = [y.coords[:][0][1] for y in points]
                            rec_rd['coord_aer'] = rec_rd['x'].round(1).astype(str) + ' ' + rec_rd['y'].round(1).astype(
                                str) + ' ' + str(round(rec_z, 1))
                            frame.append(rec_rd.copy())
            df1 = pd.DataFrame(pd.concat(frame))
            df1['rec_id'] = [rec_n + str(ii) for ii in range(1, len(df1) + 1)]
            frame_tt.append(df1)



    rec_rd = pd.DataFrame(pd.concat(frame_tt))
    rec_rd = rec_rd[['rec_id', 'geometry', 'x', 'y', 'coord_aer']]

    ## 2.2. Generate grided receptor
    print('')
    print("Generating grided receptor...")
    rec_gr = gpd.GeoDataFrame(columns=['rec_id', 'geometry', 'x', 'y', 'coord_aer'])
    ii = 0
    # Original
    # for x in range(int(xref_left_m), int(xref_right_m) + rec_grid_interval, rec_grid_interval):
    # for y in range(int(yref_lower_m), int(yref_higher_m) + rec_grid_interval, rec_grid_interval):

    # Linespace
    count = 0
    # for x in np.linspace(xref_left_m, xref_right_m + rec_grid_interval, (xref_right_m + rec_grid_interval - xref_left_m) / rec_grid_interval + 1):
    #    for y in np.linspace(yref_lower_m, yref_higher_m + rec_grid_interval, (yref_higher_m + rec_grid_interval - yref_lower_m) / rec_grid_interval + 1):
    #        count += 1

    print("#loop of Linespace: " + str(count))

    count = 0
    for x in range(int(xref_left_m), int(xref_right_m) + int(rec_grid_interval), int(rec_grid_interval)):
        for y in range(int(yref_lower_m), int(yref_higher_m) + int(rec_grid_interval), int(rec_grid_interval)):
            count += 1

            pt = Point(x, y)
            rec_gr.loc[len(rec_gr)] = ['gr_' + str(ii), pt, \
                                       round(pt.coords[0][0], 1), round(pt.coords[0][1], 1), \
                                       str(round(pt.coords[0][0], 1)) + ' ' + str(
                                           round(pt.coords[0][1], 1)) + ' ' + str(
                                           round(rec_z, 1))]
            ii += 1
    # combine two types of receptors: grid and near-road

    print("#loop of range: " + str(count))

    rec_df = pd.DataFrame(pd.concat([rec_gr, rec_rd])).reset_index(drop=True)
    rec_gdf = gpd.GeoDataFrame(rec_df, geometry=rec_df.geometry)
    # Delete receptor falls into the link
    print('')
    print("Almost done! Deleting receptors that fall into the link within 5 m...")
    buffer_rd = gpd.GeoDataFrame(
        geometry=rd_list.apply(lambda x: x.geometry.buffer(x['bw'] + 4.9999, cap_style=1), axis=1))
    buffer_rd['dissol'] = 1
    buffer_rd1 = gpd.GeoDataFrame(buffer_rd.dissolve(by='dissol').reset_index(drop=True))

    """
    rec_new = gpd.GeoDataFrame(columns = ['rec_id','geometry','x','y','coord_aer'])
    for ii, rr in buffer_rd1.iterrows():
        for i , row in rec_df.iterrows():
            if not rr.geometry.intersects(row.geometry):
                rec_new.loc[len(rec_new)] = [row['rec_id'],row['geometry'],row['x'],row['y'],row['coord_aer']]
                #print(i)
    rec_gdf.plot()
    buffer_rd1.plot()
    # Show geometry and receptors
    """
    rec_gdf = rec_gdf[~rec_gdf['rec_id'].isin(gpd.clip(rec_gdf, buffer_rd1)['rec_id'].tolist())]
    rec_gdf.to_csv(output_path + '/receptors_list.csv', index=False)
    print("Done! Receptor lists exported to 'receptors_list.csv'.")

    return rec_gdf


# Visualize receptors
def visualizeReceptors(rd_list, rec_gdf, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m):
    fig, ax = plt.subplots()
    buffer_0 = gpd.GeoDataFrame( \
        geometry=rd_list.apply(lambda x: \
                                   x.geometry.buffer(x['bw'], cap_style=1), axis=1))
    buffer_0['dissol'] = 1
    buffer_0 = gpd.GeoDataFrame(buffer_0.dissolve(by='dissol').reset_index(drop=True))
    buffer_0.plot(ax=ax, color='blue', alpha=0.5)
    rd_list.plot(ax=ax, color='blue')
    plt.scatter(rec_gdf['x'], rec_gdf['y'], color='red', alpha=1, s=0.3)
    plt.title("Receptors Layout")
    plt.axis('scaled')
    plt.xlabel('meter')
    plt.ylabel('meter')
    plt.xlim(xref_left_m, xref_right_m)
    plt.ylim(yref_lower_m, yref_higher_m)

    return fig


# Generate Emissions
def generateEmissions(AREA_em, LINE_em, RLINEXT_em, VOLUME_em, isLink, rd_list, GISRdID, Em, VOLUME_file_path,
                      outputpath):
    # Emission File:
    # Identify if you need to run "Emission Module". Choose False if emission rates is not available.
    # However, generated road geometry files has to be generated before running Emission Module
    em_unit = 'g/mile/hr'  # g/mile/hr or g/link/hr

    print("data check")
    print(VOLUME_em.get())
    print(isLink.get())
    print(rd_list)
    print(Em)

    rd_list['length_m'] = rd_list['geometry'].length
    if isLink.get():
        rd_list['emrate'] = rd_list[Em]
    else:
        rd_list['emrate'] = rd_list[Em] * (rd_list['length_m'] * 0.000621371)

    if not os.path.exists(outputpath + '/emission'):
        os.makedirs(outputpath + '/emission')

    if AREA_em.get():
        print("start area")
        df = pd.read_csv(outputpath + '/AREA.csv')
        df1 = df[[GISRdID, 'area']]
        df1 = df1.groupby([GISRdID]).area.sum().reset_index()
        df1 = df1.rename(columns={'area': 'tt_area'})
        df = pd.merge(df, df1, how='left', on=[GISRdID])
        df = pd.merge(df, rd_list[[GISRdID, 'emrate']], how='left', on=[GISRdID])
        df = df.dropna(how='all')
        df = df[(df['emrate'] > 0)]
        # df['prop'] = df['area'] / df['tt_area']
        df['em_aer'] = df['emrate'] / df['tt_area'] / 3600  # from meter to mile
        df.to_csv(outputpath + '/emission' + '/em_AREA.csv', index=False)

    if LINE_em.get() or RLINEXT_em.get():
        print("start line/ rlinext")
        df = pd.read_csv(outputpath + '/Line.csv')
        df1 = df[[GISRdID, 'area']]
        df1 = df1.groupby([GISRdID]).area.sum().reset_index()
        df1 = df1.rename(columns={'area': 'tt_area'})
        df = pd.merge(df, df1, how='left', on=[GISRdID])
        df = pd.merge(df, rd_list[[GISRdID, 'emrate']], how='left', on=[GISRdID])
        df = df.dropna(how='all')
        df = df[(df['emrate'] > 0)]
        # df['prop'] = df['area'] / df['tt_area']
        df['em_aer'] = df['emrate'] / df['tt_area'] / 3600  # from meter to mile
        if LINE_em.get():
            # df = df.drop(['wd'], axis=1)
            df.to_csv(outputpath + '/emission' + '/em_LINE.csv', index=False)
        if RLINEXT_em.get():
            df['em_aer'] = df['em_aer'] * df['wd']
            df = df.drop(['wd'], axis=1)
            df.to_csv(outputpath + '/emission' + '/em_RLINEXT.csv', index=False)

    if VOLUME_em.get():
        print("start volume")
        df = pd.read_csv(VOLUME_file_path)
        df = pd.merge(df, rd_list[[GISRdID, 'emrate']], how='left', on=[GISRdID])
        df = df.dropna(how='all')
        df = df[(df['emrate'] > 0)]
        df['em_aer'] = df['emrate'] / df['nn'] / 3600  # from meter to mile
        df.to_csv(outputpath + '/emission' + '/em_' + os.path.basename(VOLUME_file_path), index=False)


# Run AERMOD: AREA input
def runAERMOD_AREA(rec_path, road_path, run_AERMOD, em_path, AVERTIME, URBANOPT, FLAGPOLE, POLLUTID, SURFFILE, PROFFILE,
                   output_path):
    AREA_rec_path = rec_path
    if run_AERMOD.get():
        AREA_em_path = em_path
    AREA_rd_path = road_path

    AREA_recdf = pd.read_csv(AREA_rec_path)
    AREA_RECEPTORCOORD = "\n".join(('RE DISCCART ' + AREA_recdf['coord_aer']).tolist())
    if run_AERMOD.get():
        AREA_emdf = pd.read_csv(AREA_em_path)
        AREA_LINKLOC = "\n".join(
            ('SO LOCATION ' + AREA_emdf['linkID_new'] + ' AREAPOLY ' + AREA_emdf['vertex_aer'] + ' 0'))
        AREA_LINKCOORD = "\n".join(('SO AREAVERT ' + AREA_emdf['linkID_new'] + ' ' + AREA_emdf['coord_aer']))
        AREA_SRCPARAMEM = "\n".join(('SO SRCPARAM ' + AREA_emdf['linkID_new'] + ' ' + AREA_emdf['em_aer'].map(
            str) + ' 1.3 ' + AREA_emdf['n'].map(str) + ' 2'))
    else:
        AREA_rddf = pd.read_csv(AREA_rd_path)
        AREA_LINKLOC = "\n".join(
            ('SO LOCATION ' + AREA_rddf['linkID_new'] + ' AREAPOLY ' + AREA_rddf['vertex_aer'] + ' 0'))
        AREA_LINKCOORD = "\n".join(('SO AREAVERT ' + AREA_rddf['linkID_new'] + ' ' + AREA_rddf['coord_aer']))
        AREA_SRCPARAMEM = "\n".join(
            ('SO SRCPARAM ' + AREA_rddf['linkID_new'] + ' [emissionRate] 1.3 ' + AREA_rddf['n'].map(str) + ' 2'))
    AREA_RBARRIER = ''
    content = TEMPLATE.format( \
        AVERTIME=AVERTIME, \
        URBANOPT=URBANOPT, \
        FLAGPOLE=FLAGPOLE, \
        POLLUTID=POLLUTID, \
        LINK_LOCATION=AREA_LINKLOC, \
        SRCPARAM=AREA_SRCPARAMEM, \
        RBARRIER=AREA_RBARRIER, \
        LINKCOORD=AREA_LINKCOORD, \
        RECEPTORCOORD=AREA_RECEPTORCOORD, \
        file_sfc=os.path.basename(SURFFILE), \
        file_pfl=os.path.basename(PROFFILE)
    )
    with open(output_path + "/aermod.inp", "w") as fp:
        fp.write(content)
    out_AREA = os.path.basename(AREA_rd_path).split('.')[0] + '_' + POLLUTID + '_' + AVERTIME
    shutil.copy(output_path + '/aermod.inp', output_path + '/' + out_AREA + '.inp')
    if run_AERMOD.get():
        if not os.path.exists(output_path + '/aermod.exe'):
            path = os.path.dirname(os.path.dirname(output_path))
            print(path)
            shutil.copy(path + "/aermod.exe", output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(SURFFILE)):
            shutil.copy(SURFFILE, output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(PROFFILE)):
            shutil.copy(PROFFILE, output_path);
        os.chdir(output_path)
        os.system('aermod.exe')
        shutil.copy('aermod.out', out_AREA + '.out')


# Run AERMOD: VOLUME input
def runAERMOD_VOLUME(output_path, rec_path, road_path, run_AERMOD, em_path, AVERTIME, URBANOPT, FLAGPOLE, POLLUTID,
                     SURFFILE, PROFFILE):

    print("Run AERMOD")
    print(run_AERMOD.get())
    ##################Compile / Run AERMOD for VOLUME ##############################################
    VOLUME_rec_path = rec_path
    if run_AERMOD.get():
        VOLUME_em_path = em_path
    VOLUME_rd_path = road_path

    VOLUME_recdf = pd.read_csv(VOLUME_rec_path)
    VOLUME_RECEPTORCOORD = "\n".join(('RE DISCCART ' + VOLUME_recdf['coord_aer']).tolist())
    if run_AERMOD.get():
        VOLUME_emdf = pd.read_csv(VOLUME_em_path)
        VOLUME_LINKLOC = "\n".join(
            ('SO LOCATION ' + VOLUME_emdf['linkID_new'] + ' VOLUME ' + VOLUME_emdf['coord_aer'] + ' 0'))
        VOLUME_LINKCOORD = "** no nodes coord needed\n"
        VOLUME_SRCPARAMEM = "\n".join(('SO SRCPARAM ' + VOLUME_emdf['linkID_new'] + ' ' + \
                                       VOLUME_emdf['em_aer'].map(str) + ' 1.3 ' + VOLUME_emdf['yinit'].map(str) + ' 2'))
    else:
        VOLUME_rddf = pd.read_csv(VOLUME_rd_path)
        VOLUME_LINKLOC = "\n".join(
            ('SO LOCATION ' + VOLUME_rddf['linkID_new'] + ' VOLUME ' + VOLUME_rddf['coord_aer'] + ' 0'))
        VOLUME_LINKCOORD = "** no nodes coord needed\n"
        VOLUME_SRCPARAMEM = "\n".join(
            ('SO SRCPARAM ' + VOLUME_rddf['linkID_new'] + ' [emissionRate] 1.3 ' + VOLUME_rddf['yinit'].map(
                str) + ' 2'))
    VOLUME_RBARRIER = ''
    content = TEMPLATE.format(\
        AVERTIME=AVERTIME,\
        URBANOPT=URBANOPT,\
        FLAGPOLE=FLAGPOLE,\
        POLLUTID=POLLUTID,\
        LINK_LOCATION=VOLUME_LINKLOC,\
        SRCPARAM=VOLUME_SRCPARAMEM,\
        RBARRIER=VOLUME_RBARRIER,\
        LINKCOORD=VOLUME_LINKCOORD,\
        RECEPTORCOORD=VOLUME_RECEPTORCOORD,\
        file_sfc=os.path.basename(SURFFILE),\
        file_pfl=os.path.basename(PROFFILE)
    )

    print("content")
    print(content)

    with open(output_path + "/aermod.inp", "w") as fp:
        fp.write(content)
    out_VOLUME = os.path.basename(VOLUME_rd_path).split('.')[0] + '_' + POLLUTID + '_' + AVERTIME
    shutil.copy(output_path + '/aermod.inp', output_path + '/' + out_VOLUME + '.inp')
    if run_AERMOD.get():
        if not os.path.exists(output_path + '/aermod.exe'):
            path = os.path.dirname(os.path.dirname(output_path))
            shutil.copy(path + "/aermod.exe", output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(SURFFILE)):
            shutil.copy(SURFFILE, output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(PROFFILE)):
            shutil.copy(PROFFILE, output_path)
        os.chdir(output_path)
        os.system('aermod.exe')
        shutil.copy('aermod.out', out_VOLUME + '.out')


# Run AERMOD: LINE input
def runAERMOD_LINE(output_path, rec_path, road_path, run_AERMOD, em_path, AVERTIME, URBANOPT, FLAGPOLE, POLLUTID,
                   SURFFILE, PROFFILE):
    ########### Compile / Run AERMOD for LINE ############################################
    LINE_rec_path = rec_path
    if run_AERMOD.get():
        LINE_em_path = em_path
    LINE_rd_path = road_path

    LINE_recdf = pd.read_csv(LINE_rec_path)
    LINE_RECEPTORCOORD = "\n".join(('RE DISCCART ' + LINE_recdf['coord_aer']).tolist())
    if run_AERMOD.get():
        LINE_emdf = pd.read_csv(LINE_em_path)
        LINE_LINKLOC = "\n".join(('SO LOCATION ' + LINE_emdf['linkID_new'] + ' LINE ' + LINE_emdf['coord_aer'] + ' 0'))
        LINE_LINKCOORD = "** no nodes coord needed\n"
        LINE_SRCPARAMEM = "\n".join(('SO SRCPARAM ' + LINE_emdf['linkID_new'] + ' ' + LINE_emdf['em_aer'].map(
            str) + ' 1.3 ' + LINE_emdf['wd'].map(str) + ' 2'))
    else:
        LINE_rddf = pd.read_csv(LINE_rd_path)
        LINE_LINKLOC = "\n".join(('SO LOCATION ' + LINE_rddf['linkID_new'] + ' LINE ' + LINE_rddf['coord_aer'] + ' 0'))
        LINE_LINKCOORD = "** no nodes coord needed\n"
        LINE_SRCPARAMEM = "\n".join(
            ('SO SRCPARAM ' + LINE_rddf['linkID_new'] + ' [emissionRate] 1.3 ' + LINE_rddf['wd'].map(str) + ' 2'))
    LINE_RBARRIER = ''
    content = TEMPLATE.format( \
        AVERTIME=AVERTIME, \
        URBANOPT=URBANOPT, \
        FLAGPOLE=FLAGPOLE, \
        POLLUTID=POLLUTID, \
        LINK_LOCATION=LINE_LINKLOC, \
        SRCPARAM=LINE_SRCPARAMEM, \
        RBARRIER=LINE_RBARRIER, \
        LINKCOORD=LINE_LINKCOORD, \
        RECEPTORCOORD=LINE_RECEPTORCOORD, \
        file_sfc=os.path.basename(SURFFILE), \
        file_pfl=os.path.basename(PROFFILE)
    )
    print("output_path: " + str(output_path))
    with open(output_path + "/aermod.inp", "w") as fp:
        fp.write(content)
    out_LINE = os.path.basename(LINE_rd_path).split('.')[0] + '_' + POLLUTID + '_' + AVERTIME
    shutil.copy(output_path + '/aermod.inp', output_path + '/' + out_LINE + '.inp')
    if run_AERMOD.get():
        if not os.path.exists(output_path + '/aermod.exe'):
            path = os.path.dirname(os.path.dirname(output_path))
            shutil.copy(path + "/aermod.exe", output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(SURFFILE)):
            shutil.copy(SURFFILE, output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(PROFFILE)):
            shutil.copy(PROFFILE, output_path)
        os.chdir(output_path)
        os.system('aermod.exe')
        shutil.copy('aermod.out', out_LINE + '.out')
    ##################End for Compile / Run AERMOD for LINE ######################################


# Run AERMOD: BETA RLINE input
def runAERMOD_B_RLINE(output_path, rec_path, road_path, run_AERMOD, em_path, AVERTIME, URBANOPT, FLAGPOLE, POLLUTID,
                      SURFFILE, PROFFILE):
    ########### Compile / Run AERMOD for RLINE ############################################
    RLINE_rec_path = rec_path
    if run_AERMOD.get():
        RLINE_em_path = em_path
    RLINE_rd_path = road_path

    RLINE_recdf = pd.read_csv(RLINE_rec_path)
    RLINE_RECEPTORCOORD = "\n".join(('RE DISCCART ' + RLINE_recdf['coord_aer']).tolist())
    if run_AERMOD.get():
        RLINE_emdf = pd.read_csv(RLINE_em_path)
        RLINE_LINKLOC = "\n".join(
            ('SO LOCATION ' + RLINE_emdf['linkID_new'] + ' RLINE ' + RLINE_emdf['coord_aer'] + ' 0'))
        RLINE_LINKCOORD = "** no nodes coord needed\n"
        RLINE_SRCPARAMEM = "\n".join(('SO SRCPARAM ' + RLINE_emdf['linkID_new'] + ' ' + RLINE_emdf['em_aer'].map(
            str) + ' 1.3 ' + RLINE_emdf['wd'].map(str) + ' 2'))
    else:
        RLINE_rddf = pd.read_csv(RLINE_rd_path)
        RLINE_LINKLOC = "\n".join(
            ('SO LOCATION ' + RLINE_rddf['linkID_new'] + ' RLINE ' + RLINE_rddf['coord_aer'] + ' 0'))
        RLINE_LINKCOORD = "** no nodes coord needed\n"
        RLINE_SRCPARAMEM = "\n".join(
            ('SO SRCPARAM ' + RLINE_rddf['linkID_new'] + ' [emissionRate] 1.3 ' + RLINE_rddf['wd'].map(str) + ' 2'))
    RLINE_RBARRIER = ''
    content = TEMPLATE.format( \
        AVERTIME=AVERTIME, \
        URBANOPT=URBANOPT, \
        FLAGPOLE=FLAGPOLE, \
        POLLUTID=POLLUTID, \
        LINK_LOCATION=RLINE_LINKLOC, \
        SRCPARAM=RLINE_SRCPARAMEM, \
        RBARRIER=RLINE_RBARRIER, \
        LINKCOORD=RLINE_LINKCOORD, \
        RECEPTORCOORD=RLINE_RECEPTORCOORD, \
        file_sfc=os.path.basename(SURFFILE), \
        file_pfl=os.path.basename(PROFFILE)
    )
    with open(output_path + "/aermod.inp", "w") as fp:
        fp.write(content)
    out_RLINE = 'RLINE_' + os.path.basename(RLINE_rd_path).split('.')[0] + '_' + POLLUTID + '_' + AVERTIME
    shutil.copy(output_path + '/aermod.inp', output_path + '/' + out_RLINE + '.inp')
    if run_AERMOD.get():
        if not os.path.exists(output_path + '/aermod.exe'):
            path = os.path.dirname(os.path.dirname(output_path))
            shutil.copy(path + "/aermod.exe", output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(SURFFILE)):
            shutil.copy(SURFFILE, output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(PROFFILE)):
            shutil.copy(PROFFILE, output_path)
        os.chdir(output_path)
        os.system('aermod.exe')
        shutil.copy('aermod.out', out_RLINE + '.out')


# Run AERMOD: BETA RLINE input
def runAERMOD_A_RLINEXT(output_path, rec_path, road_path, run_AERMOD, em_path, AVERTIME, URBANOPT, FLAGPOLE, POLLUTID,
                        SURFFILE, PROFFILE):
    ########### Compile / Run AERMOD for RLINEXT ############################################
    RLINEXT_rec_path = rec_path
    if run_AERMOD.get():
        RLINEXT_em_path = em_path
    RLINEXT_rd_path = road_path
    RLINEXT_RBARRIER = ''
    RLINEXT_recdf = pd.read_csv(RLINEXT_rec_path)
    RLINEXT_RECEPTORCOORD = "\n".join(('RE DISCCART ' + RLINEXT_recdf['coord_aer']).tolist())
    if run_AERMOD.get():
        RLINEXT_emdf = pd.read_csv(RLINEXT_em_path)
        RLINEXT_emdf['wd'] = RLINEXT_emdf['bw'] * 2
        RLINEXT_LINKLOC = "\n".join(('SO LOCATION ' + RLINEXT_emdf['linkID_new'] + ' RLINEXT ' + \
                                     RLINEXT_emdf['coord_aer'].apply(lambda x: ' '.join(x.split(' ')[0:2] + \
                                                                                        ['0'] + x.split(' ')[
                                                                                                2:4])) + ' 0'))
        RLINEXT_LINKCOORD = "** no nodes coord needed\n"
        RLINEXT_SRCPARAMEM = "\n".join(('SO SRCPARAM ' + RLINEXT_emdf['linkID_new'] + ' ' + RLINEXT_emdf['em_aer'].map(
            str) + ' 1.3 ' + RLINEXT_emdf['wd'].map(str) + ' 2'))
        # RLINEXT_RBARRIER = "\n".join(('SO RBARRIER ' + RLINEXT_emdf['linkID_new'] + ' 3.5 ' + RLINEXT_emdf['bw'].apply(lambda x: -x-3).map(str)))
    else:
        RLINEXT_rddf = pd.read_csv(RLINEXT_rd_path)
        RLINEXT_rddf['wd'] = RLINEXT_rddf['bw'] * 2
        RLINEXT_LINKLOC = "\n".join(
            ('SO LOCATION ' + RLINEXT_rddf['linkID_new'] + ' RLINEXT ' + RLINEXT_rddf['coord_aer'] + ' 0'))
        RLINEXT_LINKCOORD = "** no nodes coord needed\n"
        RLINEXT_SRCPARAMEM = "\n".join(
            ('SO SRCPARAM ' + RLINEXT_rddf['linkID_new'] + ' [emissionRate] 1.3 ' + RLINEXT_rddf['wd'].map(str) + ' 2'))
        # RLINEXT_RBARRIER = "\n".join(('SO RBARRIER ' + RLINEXT_rddf['linkID_new'] + ' 3.5 ' + RLINEXT_rddf['bw'].apply(lambda x: -x-3).map(str)))
    content = TEMPLATE.format( \
        AVERTIME=AVERTIME, \
        URBANOPT=URBANOPT, \
        FLAGPOLE=FLAGPOLE, \
        POLLUTID=POLLUTID, \
        LINK_LOCATION=RLINEXT_LINKLOC, \
        SRCPARAM=RLINEXT_SRCPARAMEM, \
        RBARRIER=RLINEXT_RBARRIER, \
        LINKCOORD=RLINEXT_LINKCOORD, \
        RECEPTORCOORD=RLINEXT_RECEPTORCOORD, \
        file_sfc=os.path.basename(SURFFILE), \
        file_pfl=os.path.basename(PROFFILE)
    )
    with open(output_path + "/aermod.inp", "w") as fp:
        fp.write(content)
    out_RLINEXT = 'RLINEXT_' + os.path.basename(RLINEXT_rd_path).split('.')[0] + '_' + POLLUTID + '_' + AVERTIME
    shutil.copy(output_path + '/aermod.inp', output_path + '/' + out_RLINEXT + '.inp')
    if run_AERMOD.get():
        if not os.path.exists(output_path + '/aermod.exe'):
            path = os.path.dirname(os.path.dirname(output_path))
            shutil.copy(path + "/aermod.exe", output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(SURFFILE)):
            shutil.copy(SURFFILE, output_path)
        if not os.path.exists(output_path + '/' + os.path.basename(PROFFILE)):
            shutil.copy(PROFFILE, output_path)
        os.chdir(output_path)
        os.system('aermod.exe')
        shutil.copy('aermod.out', out_RLINEXT + '.out')


# Generate and visualize results
def generateResults(aermod_out, output_path):
    ################## Result visualization #############################################################
    aermod_out_fname = os.path.basename(aermod_out).split('.out')[0]
    temp_conc1 = []
    start = 0
    realstart = 0
    for line in (open(aermod_out).readlines()):
        # print(line)
        if ('HIGHEST' in line) and ('AVERAGE' in line) and ('CONCENTRATION' in line) and ('VALUES' in line):
            start = 1
            # print(line)
            continue
        if (start == 1) and ('- - - - -' in line):
            realstart = 1
            # print(line)
            start = 2
            continue
        if (realstart == 1) and ('(' in line):
            temp_conc1.append(line)
            # print(line)
        elif realstart == 1:
            start = 0
            realstart = 0
        if 'THE MAXIMUM' in line:
            break
    con_df = pd.DataFrame(columns=['x', 'y', 'concentration'])
    for conc_l in temp_conc1:
        conc_l = conc_l.split()
        # print(conc_l)
        # conc_l = filter(None, conc_l)
        if len(conc_l) > 7:
            con_df.loc[len(con_df)] = [conc_l[0], conc_l[1], float(conc_l[2].replace("c", ""))]
            con_df.loc[len(con_df)] = [conc_l[4], conc_l[5], float(conc_l[6].replace("c", ""))]
        else:
            con_df.loc[len(con_df)] = [conc_l[0], conc_l[1], float(conc_l[2].replace("c", ""))]
    # print('storing and plotting concentration data...')
    con_df.to_csv(output_path + '/' + aermod_out_fname + '.csv', index=False)
    c_max = (con_df.concentration.max())

    print(con_df)

    print(c_max)

    return c_max, con_df


# Visualize the results
def visualizeResults(c_min, c_max, con_df, aermod_out, rd_list, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m):
    aermod_out_fname = os.path.basename(aermod_out).split('.out')[0]

    # Visualize
    fig = plt.figure()
    ax = fig.add_subplot(111)
    xy = con_df[['x', 'y']].values
    z = (con_df['concentration']).tolist()
    # z = [zz for zz in (df_final[sce]).tolist()]
    # xi = np.linspace(-600, 600, 1201)
    grid_x, grid_y = np.mgrid[xref_left_m:xref_right_m:1001j, yref_lower_m:yref_higher_m:1001j]

    zi = griddata(xy, z, (grid_x, grid_y), method='linear')

    # vv = np.linspace(0, c_max, 31, endpoint=True)
    vv = np.linspace(c_min, c_max, 31, endpoint=True)

    hehe = plt.contourf(grid_x, grid_y, zi, vv, cmap=plt.get_cmap("rainbow"), extend="both",
                        alpha=1)  # cmap=plt.get_cmap("rainbow"),

    # vvv = np.linspace(0, c_max, 31, endpoint=True)
    vvv = np.linspace(c_min, c_max, 31, endpoint=True)

    plt.contour(grid_x, grid_y, zi, vvv, linewidths=0.01, colors='k')
    plt.xlim(xref_left_m, xref_right_m)
    plt.ylim(yref_lower_m, yref_higher_m)
    plt.xticks(rotation=0)
    plt.rc('xtick', labelsize=8)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=8)  # fontsize of the tick labels
    rd_list.plot(ax=ax, color='black', alpha=0.5, linewidth=1)
    plt.xlabel('meter')
    plt.ylabel('meter')
    ax.set_aspect('equal')
    plt.colorbar(hehe)
    plt.title(aermod_out_fname)
    # plt.axis('off')
    # plt.savefig(path + filename + '.png', dpi = 100)

    return fig
