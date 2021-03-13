import os
import time

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely import geometry
from shapely.geometry import LineString, MultiLineString, Point
import descartes


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
    show_receptor = False

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
def visualizeVOLUME(output_path, max_vol, xref_left_m, xref_right_m, yref_lower_m, yref_higher_m):
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
    rd_geo = pd.read_csv(output_path + '/AREA.csv')
    rd_geo['geometry'] = rd_geo.apply(lambda row: add_polygon_from_poly(row), axis=1)
    rd_geo = gpd.GeoDataFrame(rd_geo, geometry=rd_geo.geometry)
    rd_geo.plot(ax=ax, edgecolor='black', linewidth=0.3, alpha=0.5, facecolor="none", zorder=2)
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
