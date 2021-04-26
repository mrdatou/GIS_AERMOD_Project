# Constant values for Roat Tab
class RoadTabConstants():
    road_line = "Line includes LINE, RLINE and RLINEXT. The geometries of line sources are defined with coordinates of two end points and line width."
    road_area = "AREA geometry is defined in AERMOD as a polygon with coordinates of up to 20 vertices"
    road_vol = "VOLUME is defined by the coordinates of the source center and cell size (d)"

    # Graphic example image paths
    lineGrapPath = 'img/Line Graphic Example.png'
    areaGrapPath = 'img/AREA Graphic Example.png'
    volGrapPath = 'img/VOLUME Graphic Example.png'

    # Columns lists: [column name, explanation, color]
    # LINE
    lstLineCol = [
        [" • Col A – ", "Link ID from GIS", 'black'],
        [" • Col B – linkID: ", "new assigned link ID", 'black'],
        [" • Col C – linkID_new: ", "new assigned source ID", 'red'],
        [" • Col D – F_LTYPE: ", "road class from GIS", 'black'],
        [" • Col E – wd: ", "road width in meters, defined as (number of lanes × lane width + shoulder)", 'red'],
        [" • Col F – bw: ", "road width in meters divided by 2", 'black'],
        [" • Col G – area: ", "area of source surface in meters^2", 'black'],
        [" • Col H – geometry: ", "geometry of line source", 'black'],
        [" • Col I – coord_aer: ", "geometry of line source in form of AERMOD", 'red']
        ]

    # AREA
    lstAreaCol = [
        [" • Col A: ", " Link ID from GIS", 'black'],
        [" • Col B – linkID: ", "new assigned link ID", 'black'],
        [" • Col C – linkID_new:", "new assigned source ID", 'red'],
        [" • Col D – F_LTYPE: ", "road class from GIS", 'black'],
        [" • Col E – wd: ", "road width in meters, defined as (number of lanes × lane width + shoulder)", 'black'],
        [" • Col F – bw: ", "road width in meters divided by 2", 'black'],
        [" • Col G – area: ", "area of source surface in meters^2", 'black'],
        [" • Col H – x_ini: ", "original x coord", 'black'],
        [" • Col I – y_ini: ", "original y coord", 'black'],
        [" • Col J – n: ", "number of polygon vertices ", 'red'],
        [" • Col K – poly: ", "geometry of polygon AREA", 'black'],
        [" • Col L – geometry: ", "geometry of AREA source", 'black'],
        [" • Col M – coord: ", "coordinates of AREA source", 'black'],
        [" • Col N – vertex_aer: ", "original coord in form of AERMOD", 'red'],
        [" • Col O – coord_aer: ", "geometry of AREA source in form of AERMOD", 'red']
        ]

    # VOLUME
    lstVolCol = [
        [" • Col A: ", "Link ID from GIS", 'black'],
        [" • Col B – linkID: ", "new assigned link ID", 'black'],
        [" • Col C – linkID_new: ", "new assigned source ID", 'red'],
        [" • Col D – geometry: ", "geometry of VOLUME center", 'black'],
        [" • Col E – nn: ", "number of VOLUME cells from the link", 'black'],
        [" • Col F – subwd: ", "size of VOLUME", 'black'],
        [" • Col G – coord_aer: ", "coord of VOLUME center in form of AERMOD", 'red'],
        [" • Col H – yinit: ", "initial lateral dispersion coefficient", 'black']
        ]

    # Codes for selecting a data generation method
    LINE = 0
    AREA = 1
    VOLUME = 2

    # Titlle of popup window for visualizing data
    visualize_title_LINE = "Visualize LINE.csv"
    visualize_title_AREA = "Visualize AREA.csv"
    visualize_title_VOLUME = "Visualize VOLUME.csv"


# Constant values for Receptors Tab
class ReceptorsTabConstants:
    infoList = ["There are two types of receptors that can be automatically generated.",
                "1. Near-road receptors: receptors around roadways. Define number of layers and space intervals by uploading csv or using table:",
                "  • F_LTYPE: road type matched in GIS",
                "  • LAYER: layer ID (1,2,3,..)",
                "  • DISTANCE: distance (m) of layer from road edge (usually the closest layer = 5 m)",
                "  • INTERVAL: space intervals within each layer",
                "2. Gridded receptors with space intervals specified on the right.",
                "3. Elevation of receptors (m) above road ground, 1.5 m recommended."]

    # Columns for spreadsheet
    colList = ("F_LTYPE",
               "LAYER",
               "DISTANCE",
               "INTERVAL")

    # Visualize window title
    visualizeWindowTitle = "Visualize receptors"

    # Graphic example image paths
    recGrapPath = 'img/Receptors Graphic Example.png'


# Constant values for Emissions Tab
class EmissionsTabConstants:
    infoList = [
        "Emission Module” can be skipped if emission information is not available. Users can still generate AERMOD road geometry and receptors with the tool.",
        "To generate link-level emissions:",
        "1. Select GIS column for link emission info, and emission units in rate (g per mile per hour) or inventory (g per link per hour)",
        "2. Select source(s) you want to generate emissions for",
        "  • “em_AREA.csv” from “AREA.csv”",
        "  • “em_LINE.csv” from “Line.csv”",
        "  • “em_RLINEXT.csv” from “Line.csv”",
        "  • “em_VOLUME_XX.csv” Need to upload VOLUME csv for emissions generation"]


# constant values for Compilation tab
class CompilaionTabConstants():
    pollutidList = ["CO",
                    "NO2",
                    "PM2.5",
                    "PM10",
                    "Others"]

    avertimeMenu = {'CO': ["1", "8"], 'NO2': ["1", "ANNUAL"], 'PM2.5': ["24", "ANNUAL"], 'PM10': ["24"],
                    'Others': ["1", "8", "24", "ANNUAL"]}

    TEMPLATE = """
    CO STARTING
       TITLEONE  An Example Transportation Project
       MODELOPT  BETA ALPHA FLAT CONC
       RUNORNOT  RUN
       AVERTIME  {AVERTIME}
       URBANOPT  {URBANOPT}
       FLAGPOLE  {FLAGPOLE}
       POLLUTID  {POLLUTID}
    CO FINISHED                                                                                                                       

    ** AREAPOLY Source        xini yini (z)
    ** RLINE Source         x1 y1 x2 y2 z
    ** RLINEXT Source      x1 y1 z1 x2 y2 z2
    ** VOLUME Source      x y (z)
    SO STARTING
    {LINK_LOCATION}

    ** AREAPOLY Source        g/s/m2  height  VertixNO  Szinit
    ** RLINE Source         g/s/m2  height  width  Szinit
    ** RLINEXT Source      g/s/m  height  width  Szinit
    ** VOLUME Source      g/s  height  radii  Szinit
    ** Parameters:        ------  ------  -------   -------   -----  ------
    {SRCPARAM}

    ** For RLINEXT RBARRIER (optional)
    {RBARRIER}

    ** For AREAPOLY Source Only      x1 y1 x2 y2 x3 y3 ...
    {LINKCOORD}

    SO URBANSRC ALL
    SO SRCGROUP ALL

    SO FINISHED                                                                                                      

    **-------------------------------------                                                                                                                                
    RE STARTING
    {RECEPTORCOORD}

    RE FINISHED                                                                                                                         

    ME STARTING                                                                                                                         
       SURFFILE  {file_sfc}
       PROFFILE  {file_pfl}
       SURFDATA  13874  2017  ATLANTA,GA
       UAIRDATA  53819  2017  ATLANTA,GA                                                                                                 
       SITEDATA  99999  2017  HUDSON
       PROFBASE  0.0  METERS
    ME FINISHED                                                                                                                     

    OU STARTING                                                                                                                         
       RECTABLE  ALLAVE  FIRST
       MAXTABLE  ALLAVE  50
       SUMMFILE  AERTEST.SUM                                                                                         
    OU FINISHED
    """


class ResultsTabConstants():
    questions = [
        "The tool is developed by Dr. Haobing Liu (PI and algorithm design) and his graduate student Shiro Ishizu (UI design) at University of New Mexico. For technical questions, please contact:",
        "",
        "Haobing Liu, Ph.D.",
        "Assistant Professor",
        "University of New Mexico",
        "Email (1): hliu332@unm.edu ",
        "Email (2): Haobing.liu2012@gmail.com",
        "",
        "The research is supported by Federal Highway Administration (FHWA). The project is managed by Donna Gililland at New Mexico Department of Transportation (NMDOT).",
        "Version: 2021-03-31"]



# aermod input template
TEMPLATE = """CO STARTING
   TITLEONE  An Example Transportation Project
   MODELOPT  BETA ALPHA FLAT CONC
   RUNORNOT  RUN
   AVERTIME  {AVERTIME}
   URBANOPT  {URBANOPT}
   FLAGPOLE  {FLAGPOLE}
   POLLUTID  {POLLUTID}
CO FINISHED                                                                                                                       

** AREAPOLY Source        xini yini (z)
** RLINE Source         x1 y1 x2 y2 z
** RLINEXT Source      x1 y1 z1 x2 y2 z2
** VOLUME Source      x y (z)
SO STARTING
{LINK_LOCATION}

** AREAPOLY Source        g/s/m2  height  VertixNO  Szinit
** RLINE Source         g/s/m2  height  width  Szinit
** RLINEXT Source      g/s/m  height  width  Szinit
** VOLUME Source      g/s  height  radii  Szinit
** Parameters:        ------  ------  -------   -------   -----  ------
{SRCPARAM}

** For RLINEXT RBARRIER (optional)
{RBARRIER}

** For AREAPOLY Source Only      x1 y1 x2 y2 x3 y3 ...
{LINKCOORD}

SO URBANSRC ALL
SO SRCGROUP ALL

SO FINISHED                                                                                                      

**-------------------------------------                                                                                                                                
RE STARTING
{RECEPTORCOORD}

RE FINISHED                                                                                                                         

ME STARTING                                                                                                                         
   SURFFILE  {file_sfc}
   PROFFILE  {file_pfl}
   SURFDATA  13874  2017  ATLANTA,GA
   UAIRDATA  53819  2017  ATLANTA,GA                                                                                                 
   SITEDATA  99999  2017  HUDSON
   PROFBASE  0.0  METERS
ME FINISHED                                                                                                                     

OU STARTING                                                                                                                         
   RECTABLE  ALLAVE  FIRST
   MAXTABLE  ALLAVE  50
   SUMMFILE  AERTEST.SUM                                                                                         
OU FINISHED
"""
