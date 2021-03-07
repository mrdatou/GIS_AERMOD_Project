# Mesages for Road tab's explanation for each AERMOD method

class RoadTabMsg():
    road_line = "Line includes LINE, RLINE and RLINEXT. The geometries of line sources are defined with coordinates of two end points and line width."
    road_area = "AREA geometry is defined in AERMOD as a polygon with coordinates of up to 20 vertices"
    road_vol = "VOLUME is defined by the coordinates of the source center and cell size (d)"

    # Graphic example image paths
    lineGrapPath = 'image/0120.jpg'
    areaGrapPath = '../img/0120.jpg'
    volGrapPath = '../img/0120.jpg'

    # Columns lists
    # LINE
    lstLineCol = ["Col A – Link ID from GIS",
                  "Col B – linkID: new assigned link ID",
                  "Col C – linkID_new: new assigned source ID",
                  "Col D – F_LTYPE: road class from GIS",
                  "Col E – wd: road width in meters, defined as (number of lanes × lane width + shoulder)",
                  "Col F – bw: road width in meters divided by 2",
                  "Col G – area: area of source surface in meters^2"]

    # AREA
    lstAreaCol = ["Col A – Link ID from GIS",
                  "Col B – linkID: new assigned link ID",
                  "Col C – linkID_new: new assigned source ID",
                  "Col D – F_LTYPE: road class from GIS",
                  "Col E – wd: road width in meters, defined as (number of lanes × lane width + shoulder)",
                  "Col F – bw: road width in meters divided by 2",
                  "Col G – area: area of source surface in meters^2",
                  "Col H – x_ini: original x coord",
                  "Col I – y_ini: original y coord",
                  "Col J – n: number of polygon vertices ",
                  "Col K – poly: geometry of polygon AREA",
                  "Col L – geometry: geometry of AREA source",
                  "Col M – coord: coordinates of AREA source",
                  "Col N – vertex_aer: original coord in form of AERMOD",
                  "Col O – coord_aer: geometry of AREA source in form of AERMOD"]

    # VOLUME
    lstVolCol = ["Col A – Link ID from GIS",
                 "Col B – linkID: new assigned link ID",
                 "Col C – linkID_new: new assigned source ID",
                 "Col D – geometry: geometry of VOLUME center",
                 "Col E – nn: number of VOLUME cells from the link",
                 "Col F – subwd: size of VOLUME",
                 "Col G – coord_aer: coord of VOLUME center in form of AERMOD",
                 "Col H – yinit: initial lateral dispersion coefficient"]
