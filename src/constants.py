# Constant values for Roat Tab
class RoadTabConstants():
    road_line = "Line includes LINE, RLINE and RLINEXT. The geometries of line sources are defined with coordinates of two end points and line width."
    road_area = "AREA geometry is defined in AERMOD as a polygon with coordinates of up to 20 vertices"
    road_vol = "VOLUME is defined by the coordinates of the source center and cell size (d)"

    # Graphic example image paths
    lineGrapPath = 'img/line_example.png'
    areaGrapPath = 'img/0120.jpg'
    volGrapPath = 'img/0120.jpg'

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

    # Codes for selecting a data generation method
    LINE = 0
    AREA = 1
    VOLUME = 2

    # Titlle of popup window for visualizing data
    visualize_title_LINE = "Visualize LINE.csv"
    visualize_title_AREA = "Visualize AREA.csv"
    visualize_title_VOLUME = "Visualize VOLUME.csv"


# Constant values for Receptors Tab
class ReceptorsTabConstants():

    infoList = ["There are two types of receptors that can be automatically generated.",
                "1. Near-road receptors: receptors around roadways. Define number of layers and space intervals by uploading csv or using table:",
                "• F_LTYPE: road type matched in GIS",
                "• LAYER: layer ID (1,2,3,..)",
                "• DISTANCE: distance (m) of layer from road edge (usually the closest layer = 5 m)",
                "• INTERVAL: space intervals within each layer",
                "2. Gridded receptors with space intervals specified on the right.",
                "3. Elevation of receptors (m) above road ground, 1.5 m recommended."]

    # Columns for spreadsheet
    colList = ("F_LTYPE",
               "LAYER",
               "DISTANCE",
               "INTERVAL")

    # Visualize window title
    visualizeWindowTitle = "Visualize receptors"

# Constant values for Emissions Tab
class EmissionsTabConstants():

    infoList = ["Emission Module” can be skipped if emission information is not available. Users can still generate AERMOD road geometry and receptors with the tool.",
                "To generate link-level emissions:",
                "1. Select GIS column for link emission info, and emission units in rate (g per mile per hour) or inventory (g per link per hour)",
                "2. Select source(s) you want to generate emissions for",
                "• “em_AREA.csv” from “AREA.csv”",
                "• “em_LINE.csv” from “Line.csv”",
                "• “em_RLINEXT.csv” from “Line.csv”",
                "• “em_VOLUME_XX.csv” Need to upload VOLUME csv for emissions generation"]

