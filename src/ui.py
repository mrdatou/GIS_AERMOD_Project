import os
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from tkinter import filedialog

import numpy as np
import tksheet
import pandas as pd

from PIL import Image, ImageTk
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from GISPlotWindow import GISplotWindow
from constants import RoadTabConstants, ReceptorsTabConstants, EmissionsTabConstants
from dataprep import GISextract, dataConversion
from generate_data import generateLINE, generateAREA, visualizeLINE, visualizeAREA, generateVOLUME, visualizeVOLUME, \
    generateReceptors, visualizeReceptors, generateEmissions


# Class of variables which are shared with multiple frames
class Data:
    rd_list = None  # GeoPandas
    path = None  # Imported shp File's location
    output_path = None  # Output file's location path

    # Column names
    roadID = None  # Road ID
    roadTp = None  # Road Type
    numLane = None  # Num of Lanes
    laneWid = None  # Lane width
    shoulder = None  # Shoulder
    geom = None  # Geometry

    # ESPG setting
    fromproj = None  # ESPG from
    toproj = None  # ESPG to
    isFeet = False  # Unit

    # Boundary and Reference point
    xRef = None  # Reference X
    yRef = None  # Reference Y
    yHigh = None  # Y high
    yLow = None  # Y low
    xLeft = None  # X left
    xRight = None  # X right

    # Converted coords of reference point
    xref_left_m = None
    xref_right_m = None
    yref_lower_m = None
    yref_higher_m = None

    # Maxsize for VOLUME
    maxsize_var = None

    # Receptor tab
    interval = None
    elevation = None


# Data Tab class inherit Data class to share data with other tabs
class DataTab(tk.Frame, Data):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)

        self.rd_list = None

        # Create Open, Import button and File Dialog
        self.createTopButtonAndDialog()

        # Create File setting frame
        self.createSettings()

        # Create Verify inputs button
        self.button_open = ttk.Button(self)
        self.button_open.configure(text="Verify inputs in this page", padding=10, default=tk.ACTIVE,
                                   command=self.btnVerify)
        self.button_open.grid(row=3, column=1, sticky=tk.S)

    def createTopButtonAndDialog(self):
        # Open Button
        self.button_open = ttk.Button(self)
        self.button_open.configure(text="Open", padding=10, default=tk.ACTIVE, command=self.btnOpen)
        self.button_open.grid(row=0, column=0, sticky=tk.W)

        # Import Button
        self.button_import = ttk.Button(self)
        self.button_import.configure(text="Import", padding=10, default=tk.ACTIVE, command=self.btnImport)
        self.button_import.grid(row=0, column=1, sticky=tk.W)

        # File dialog
        self.entry_file = tk.Entry(self, width=80)
        self.entry_file.grid(row=1, column=0, columnspan=4, sticky=tk.W)

    # Define Open button function
    def btnOpen(self):
        # Choose shp file
        path = tk.filedialog.askopenfilename(initialdir=os.getcwd(), title="Select file",
                                             filetypes=(("shp files", "*.shp"), ("all files", "*.*"))
                                             )

        # Clear the textbox string
        self.entry_file.delete(0, tk.END)

        # Set the path of shp file in entry_file text box
        self.entry_file.insert(tk.E, path)

    # Define Import button function
    def btnImport(self):
        path = self.entry_file.get()

        if os.path.exists(path):
            # shp file exists
            Data.path = path
            # Extract GIS data
            self.rd_list, Data.path = GISextract(Data.path)

            # Build file setting's drop down menus
            self.buildDropDownMenuSetting()



        else:
            # File does not exist
            tk.messagebox.showerror("Error", "File does not exist")

    # Setting Dropdown menu of File setting frame
    def buildDropDownMenuSetting(self):
        # Get the list of columns of GeoPandas Dataframe of imported GIS data
        columns = self.rd_list.columns.tolist()

        # Set list of choices for each dropdown menu in the File setting frame
        self.combo_roadID["values"] = columns
        self.combo_roadTp["values"] = columns
        self.combo_numLane["values"] = columns
        self.combo_laneWid["values"] = columns

        # Set columns of dropdown menu of Emissions tab
        self.master.master.emissions_tab.combo_emission["values"] = columns

        # For Geometry dropdown menu, set geometry in the top if there exists 'geometry' column
        if 'geometry' in columns:
            columns.remove('geometry')
            columns.insert(0, 'geometry')
            self.combo_geom["values"] = columns
            self.combo_geom.current(0)
        else:
            self.combo_geom["values"] = columns

    # Create setting frames
    def createSettings(self):
        self.createFileSetting()
        self.createProjectionSetting()
        self.createBoundarySetting()

    # Create File setting frame
    def createFileSetting(self):
        # Label Frame
        self.labelFrame_File = tk.LabelFrame(self, text="1. Choose Columns from Shape File", width=400, height=200,
                                             font=(None, 15, "bold"))
        self.labelFrame_File.grid(row=2, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        # Road Unique ID label
        self.label_roadID = tk.Label(self.labelFrame_File, text="Road Unique ID")
        self.label_roadID.grid(row=0, column=0)

        # Road Unique ID Combobox
        self.combo_roadID = ttk.Combobox(self.labelFrame_File, state='readonly')
        self.combo_roadID.grid(row=0, column=1)

        # Road Type label
        self.label_roadTp = tk.Label(self.labelFrame_File, text="Road Type")
        self.label_roadTp.grid(row=1, column=0)

        # Road Type Combobox
        self.combo_roadTp = ttk.Combobox(self.labelFrame_File, state='readonly')
        self.combo_roadTp.grid(row=1, column=1)

        # Number of lanes
        self.label_numLane = tk.Label(self.labelFrame_File, text="Number of Lanes")
        self.label_numLane.grid(row=2, column=0)

        # Number of lanes ID Combobox
        self.combo_numLane = ttk.Combobox(self.labelFrame_File, state='readonly')
        self.combo_numLane.grid(row=2, column=1)

        # Lane width
        self.label_laneWid = tk.Label(self.labelFrame_File, text="Lane Width")
        self.label_laneWid.grid(row=3, column=0)

        # Lane width Combobox
        self.combo_laneWid = ttk.Combobox(self.labelFrame_File, state='readonly')
        self.combo_laneWid.grid(row=3, column=1)

        # Shoulder Label
        self.label_shoulder = tk.Label(self.labelFrame_File, text="Shoulder(m)")
        self.label_shoulder.grid(row=0, column=2)

        # Shoulder textbox
        self.txt_shoulder_var = tk.StringVar()
        self.txt_shoulder = tk.Entry(self.labelFrame_File, textvariable=self.txt_shoulder_var, width=10)
        self.txt_shoulder.grid(row=0, column=3, sticky=tk.W)

        # Geometry Label
        self.label_geom = tk.Label(self.labelFrame_File, text="Geometry")
        self.label_geom.grid(row=1, column=2)

        # Geometry Combobox
        self.combo_geom = ttk.Combobox(self.labelFrame_File, state='readonly')
        self.combo_geom.grid(row=1, column=3)

    # Create Projection setting frame
    def createProjectionSetting(self):
        # Label Frame
        self.labelFrame_Projection = tk.LabelFrame(self, text="2. Origin and Destination", font=(None, 15, "bold"),
                                                   width=400, height=200)
        self.labelFrame_Projection.grid(row=2, column=1, sticky=tk.W + tk.E + tk.N + tk.S)

        # Original ESPG
        label_from_proj = tk.Label(self.labelFrame_Projection, text="Origin ESPG (4-digits)")
        label_from_proj.grid(row=0, column=0)

        self.txt_fromproj_var = tk.StringVar()
        self.txt_fromproj = tk.Entry(self.labelFrame_Projection, textvariable=self.txt_fromproj_var, width=4)
        self.txt_fromproj.grid(row=0, column=1)

        # Dest ESPG
        label_to_proj = tk.Label(self.labelFrame_Projection, text="Destination ESPG (4-digits)")
        label_to_proj.grid(row=1, column=0)

        self.txt_toproj_var = tk.StringVar()
        self.txt_toproj = tk.Entry(self.labelFrame_Projection, textvariable=self.txt_toproj_var, width=4)
        self.txt_toproj.grid(row=1, column=1)

        # Control ESPG text form: limit length = 4
        def limitESPGinput(entry, txtbox):
            if len(entry.get()) > 4:
                entry.set(entry.get()[:3])
                txtbox.insert(tk.E, entry)

        self.txt_toproj_var.trace("w", lambda *args: limitESPGinput(self.txt_toproj_var, self.txt_toproj))

        # CheckBox whether meter or feet
        tk.Label(self.labelFrame_Projection, text="Unit of destination ESPG").grid(row=2, column=0)

        # Meter checkbox
        self.bln_m = tk.BooleanVar()
        self.bln_m.set(False)
        self.chk_m = tk.Checkbutton(self.labelFrame_Projection, variable=self.bln_m, command=self.controlChkM,
                                    text="m")
        self.chk_m.grid(row=2, column=1)

        # Feet checkbox
        self.bln_f = tk.BooleanVar()
        self.bln_f.set(False)
        self.chk_f = tk.Checkbutton(self.labelFrame_Projection, variable=self.bln_f, command=self.controlChkF,
                                    text="ft")
        self.chk_f.grid(row=3, column=1)

        # ESPG resources
        tk.Label(self.labelFrame_Projection, text="Note EPSG code can be found in:", wraplength=200).grid(row=4,
                                                                                                          column=0,
                                                                                                          columnspan=2)

        def callback(event):
            webbrowser.open_new(event.widget.cget("text"))

        link = tk.Label(self.labelFrame_Projection, text=r"https://spatialreference.org/ref/epsg/", wraplength=200,
                        fg="blue", cursor="hand2")
        link.grid(row=5, column=0, columnspan=2)
        link.bind("<Button-1>", callback)

    # Control meter checkbox
    def controlChkM(self):
        self.bln_m.set(True)
        self.bln_f.set(False)

        self.chk_f.config(state=tk.NORMAL)
        self.chk_m.config(state=tk.DISABLED)

    # Control feet checkbox
    def controlChkF(self):
        self.bln_f.set(True)
        self.bln_m.set(False)

        self.chk_m.config(state=tk.NORMAL)
        self.chk_f.config(state=tk.DISABLED)

    # Create Boundary setting frame
    def createBoundarySetting(self):
        # Label Frame
        labelFrame_Boundary = tk.LabelFrame(self, text="3. Locate boundary and reference point", width=500,
                                            height=200, font=(None, 15, "bold"))
        labelFrame_Boundary.grid(row=3, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        # Locate from graph button
        button_locateGraph = ttk.Button(labelFrame_Boundary)
        button_locateGraph.configure(text="Locate from graph", padding=10, default=tk.ACTIVE,
                                     command=self.btnLocateGraph)
        button_locateGraph.grid(row=0, column=7, sticky=tk.E)

        # y high text box
        tk.Label(labelFrame_Boundary, text="Y high").grid(row=0, column=3, sticky=tk.E)

        self.txt_yHigh_var = tk.StringVar()
        txt_yHigh = tk.Entry(labelFrame_Boundary, textvariable=self.txt_yHigh_var, width=10)
        txt_yHigh.grid(row=0, column=4, sticky=tk.W)

        # x left text box
        tk.Label(labelFrame_Boundary, text="X left").grid(row=2, column=0, rowspan=2, sticky=tk.E)

        self.txt_xLeft_var = tk.StringVar()
        txt_xLeft = tk.Entry(labelFrame_Boundary, textvariable=self.txt_xLeft_var, width=10)
        txt_xLeft.grid(row=2, column=1, rowspan=2, sticky=tk.W)

        # X right text box
        tk.Label(labelFrame_Boundary, text="X right").grid(row=2, column=6, rowspan=2, sticky=tk.E)

        self.txt_xRight_var = tk.StringVar()
        txt_xRight = tk.Entry(labelFrame_Boundary, textvariable=self.txt_xRight_var, width=10)
        txt_xRight.grid(row=2, column=7, rowspan=2, sticky=tk.W)

        # Y low text box
        tk.Label(labelFrame_Boundary, text="Y low").grid(row=5, column=3, rowspan=2, sticky=tk.E)

        self.txt_yLow_var = tk.StringVar()
        txt_yLow = tk.Entry(labelFrame_Boundary, textvariable=self.txt_yLow_var, width=10)
        txt_yLow.grid(row=5, column=4, rowspan=2, sticky=tk.W)

        # Reference point x text box
        tk.Label(labelFrame_Boundary, text="Reference x").grid(row=2, column=3, sticky=tk.E)

        self.txt_xRef_var = tk.StringVar()
        txt_xRef = tk.Entry(labelFrame_Boundary, textvariable=self.txt_xRef_var, width=10)
        txt_xRef.grid(row=2, column=4, sticky=tk.W)

        # Reference point y text box
        tk.Label(labelFrame_Boundary, text="Reference y").grid(row=3, column=3, sticky=tk.E)

        self.txt_yRef_var = tk.StringVar()
        txt_yRef = tk.Entry(labelFrame_Boundary, textvariable=self.txt_yRef_var, width=10)
        txt_yRef.grid(row=3, column=4, sticky=tk.W)

        # Empty labels
        tk.Label(labelFrame_Boundary, text="   ").grid(row=1, column=0, sticky=tk.E)

        tk.Label(labelFrame_Boundary, text="   ").grid(row=0, column=2, sticky=tk.E)

        tk.Label(labelFrame_Boundary, text="   ").grid(row=0, column=5, sticky=tk.E)

        tk.Label(labelFrame_Boundary, text="   ").grid(row=4, column=0, sticky=tk.E)

    # Open GIS plot window
    def btnLocateGraph(self):

        # Check if GIS data rd_list is null or not
        if self.rd_list is None:
            tk.messagebox.showerror("Error", "rd_list is null")
            return

        # Open GIS plot window
        locateGraphWindow = tk.Toplevel(self)
        locateGraphWindow.title("Locate boundary and reference point")
        locateGraphWindow.geometry("800x600")

        # Set GIS plot window with pop-up-window
        self.buildMapWindow(locateGraphWindow)

        locateGraphWindow.mainloop()

    # Build GIS plot window
    def buildMapWindow(self, window):
        # Set mapWindow frame with pop up window
        gisWin = GISplotWindow(self.rd_list, window)
        tk.Grid.rowconfigure(gisWin, 0, weight=1)
        tk.Grid.columnconfigure(gisWin, 0, weight=1)

    # Verify inputs button
    def btnVerify(self):
        # Check input values
        if self.checkInputErr():
            self.passInputToMain()

    # Check input values when verify inputs button pressed
    def checkInputErr(self):

        # Error Flag
        errFlag = True

        # Error message string
        errMsg = ""

        # Check if columns are chosen
        if self.combo_roadID.get() == "" or self.combo_roadTp.get() == "" or self.combo_numLane.get() == "" or self.combo_laneWid.get() == "" or self.combo_geom.get() == "":
            errMsg += "Column value is not selected"
            errFlag = False

        if self.txt_shoulder_var.get() == "":
            errMsg += "\n No shoulder value"
            errFlag = False
        else:
            shoulder = float(self.txt_shoulder_var.get())
            if shoulder < 0:
                # Give warning if shoulder is greater than 8
                errMsg += "\n Shoulder value is negative"
                errFlag = False

        if self.txt_fromproj_var.get() == "" or self.txt_toproj_var.get() == "":
            errMsg += "\n ESPG value is missed"
            errFlag = False

        if self.bln_f is False and self.bln_m is False:
            errMsg += "\n No unit selected"
            errFlag = False

        if self.txt_xRef_var.get() == "" or self.txt_yRef_var.get() == "" or self.txt_yHigh_var.get() == "" or self.txt_yLow_var.get() == "" or self.txt_xLeft_var.get() == "" or self.txt_xRight_var.get() == "":
            errMsg += "\n Boundary and Reference point missed"
            errFlag = False

        if errFlag is not True:
            tk.messagebox.showerror('showerror', errMsg)

        return errFlag

    # Pass Data tab input to Main Window variables
    def passInputToMain(self):
        # GeoPandas data
        Data.rd_list = self.rd_list

        # Column names
        Data.roadID = self.combo_roadID.get()  # Road ID
        Data.roadTp = self.combo_roadTp.get()  # Road Type
        Data.numLane = self.combo_numLane.get()  # Num of Lanes
        Data.laneWid = self.combo_laneWid.get()  # Lane width
        Data.shoulder = float(self.txt_shoulder_var.get())  # Shoulder
        Data.geom = self.combo_geom.get()  # Geometry

        # ESPG setting
        Data.fromproj = 'epsg:' + self.txt_fromproj_var.get()  # ESPG from
        Data.toproj = 'epsg:' + self.txt_toproj_var.get()  # ESPG to

        if self.bln_m:
            Data.isFeet = False  # Unit
        elif self.bln_f:
            Data.isFeet = True

        # Boundary and Reference point
        Data.xRef = float(self.txt_xRef_var.get())  # Reference X
        Data.yRef = float(self.txt_yRef_var.get())  # Reference Y
        Data.yHigh = float(self.txt_yHigh_var.get())  # Y high
        Data.yLow = float(self.txt_yLow_var.get())  # Y low
        Data.xLeft = float(self.txt_xLeft_var.get())  # X left
        Data.xRight = float(self.txt_xRight_var.get())  # X right

        # Convert GIS data for future data process
        Data.rd_list, Data.xref_left_m, Data.xref_right_m, Data.yref_lower_m, Data.yref_higher_m, Data.output_path = dataConversion(
            Data)


# Road tab class
class RoadTab(tk.Frame, Data):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)

        # Create Line frame
        self.createLineFrame()

        # Create AREA frame
        self.createAreaFrame()

        # Create VOLUME frame
        self.createVolFrame()

    def createLineFrame(self):
        # Outer Label Frame
        labelFrame_OutLine = tk.LabelFrame(self, text="Line (LINE, RLINE, RLINEXT)", width=10, height=20,
                                           font=(None, 15, "bold"))
        labelFrame_OutLine.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        # Inner Frame
        frame_InLine = tk.Frame(labelFrame_OutLine, highlightbackground="red", highlightcolor="black",
                                highlightthickness=1, width=100, height=100, bd=0)
        frame_InLine.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        str = RoadTabConstants.road_line
        label_emp1 = tk.Label(frame_InLine, text=str, wraplength=200)
        label_emp1.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        # Place LIne's graphic example button
        self.button_lineExample = ttk.Button(frame_InLine)
        self.button_lineExample.configure(text="Graphic example", padding=10, default=tk.ACTIVE,
                                          command=lambda: repr(self.btnGraphicExample(RoadTabConstants.lineGrapPath)))
        self.button_lineExample.grid(row=1, column=0)

        # Place LINE columns button
        self.button_lineCols = ttk.Button(frame_InLine)
        self.button_lineCols.configure(text="LINE columns", padding=10, default=tk.ACTIVE,
                                       command=lambda: repr(self.btnCol(0)))
        self.button_lineCols.grid(row=2, column=0)

        # Place Generate Line button
        self.button_generateLine = ttk.Button(labelFrame_OutLine)
        self.button_generateLine.configure(text="Generate Line", padding=10, default=tk.ACTIVE,
                                           command=lambda: repr(self.btnGenerate(RoadTabConstants.LINE)))
        self.button_generateLine.grid(row=1, column=0)

        # Place Visualize Line button
        self.button_visualizeLine = ttk.Button(labelFrame_OutLine)
        self.button_visualizeLine.configure(text="Visualize Line", padding=10, default=tk.ACTIVE,
                                            command=lambda: repr(self.btnVisualize(RoadTabConstants.LINE)))
        self.button_visualizeLine.grid(row=2, column=0)

    # Create AREA frame
    def createAreaFrame(self):
        # Outer Label Frame
        labelFrame_OutArea = tk.LabelFrame(self, text="AREA", width=400, height=200,
                                           font=(None, 15, "bold"))
        labelFrame_OutArea.grid(row=0, column=1, sticky=tk.W + tk.E + tk.N + tk.S)

        # Inner Frame
        frame_InArea = tk.Frame(labelFrame_OutArea, highlightbackground="red", highlightcolor="black",
                                highlightthickness=1, width=100, height=100, bd=0)
        frame_InArea.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        str = RoadTabConstants.road_area
        label_emp2 = tk.Label(frame_InArea, text=str, wraplength=150)
        label_emp2.grid(row=0, column=0)

        # Place Area's graphic example button
        self.btn_lineExample = ttk.Button(frame_InArea)
        self.btn_lineExample.configure(text="Graphic example", padding=10, default=tk.ACTIVE,
                                       command=lambda: repr(self.btnGraphicExample(RoadTabConstants.areaGrapPath)))
        self.btn_lineExample.grid(row=1, column=0)

        # Place Area columns button
        self.btn_areaCols = ttk.Button(frame_InArea)
        self.btn_areaCols.configure(text="LINE columns", padding=10, default=tk.ACTIVE,
                                    command=lambda: repr(self.btnCol(RoadTabConstants.AREA)))
        self.btn_areaCols.grid(row=2, column=0)

        # Place Generate Area button
        self.btn_generateArea = ttk.Button(labelFrame_OutArea)
        self.btn_generateArea.configure(text="Generate Line", padding=10, default=tk.ACTIVE,
                                        command=lambda: repr(self.btnGenerate(RoadTabConstants.AREA)))
        self.btn_generateArea.grid(row=1, column=0)

        # Place Visualize Area button
        self.btn_visualizeArea = ttk.Button(labelFrame_OutArea)
        self.btn_visualizeArea.configure(text="Visualize Line", padding=10, default=tk.ACTIVE,
                                         command=lambda: repr(self.btnVisualize(RoadTabConstants.AREA)))
        self.btn_visualizeArea.grid(row=2, column=0)

    # Create VOLUME frame
    def createVolFrame(self):
        # Outer Label Frame
        labelFrame_OutVol = tk.LabelFrame(self, text="VOLUME", width=400, height=200,
                                          font=(None, 15, "bold"))
        labelFrame_OutVol.grid(row=0, column=2, sticky=tk.W + tk.E + tk.N + tk.S)

        # Inner Frame
        frame_InVol = tk.Frame(labelFrame_OutVol, highlightbackground="red", highlightcolor="black",
                               highlightthickness=1, width=100, height=100, bd=0)
        frame_InVol.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E)

        str = RoadTabConstants.road_vol
        label_emp3 = tk.Label(frame_InVol, text=str, wraplength=250)
        label_emp3.grid(row=0, column=0, sticky=tk.W + tk.E)

        # Place VOLUME's graphic example button
        btn_volExample = ttk.Button(frame_InVol)
        btn_volExample.configure(text="Graphic example", padding=10, default=tk.ACTIVE,
                                 command=lambda: repr(self.btnGraphicExample(RoadTabConstants.volGrapPath)))
        btn_volExample.grid(row=1, column=0, columnspan=2)

        # Place Area columns button
        btn_volCols = ttk.Button(frame_InVol)
        btn_volCols.configure(text="VOLUME columns", padding=10, default=tk.ACTIVE,
                              command=lambda: repr(self.btnCol(2)))
        btn_volCols.grid(row=2, column=0, columnspan=2)

        # Put textbox for max size
        tk.Label(labelFrame_OutVol, text="Max Size (m) Should <= 8 m").grid(row=1, column=0, sticky=tk.S)

        self.txt_maxsize_var = tk.StringVar()
        self.txt_maxsize = tk.Entry(labelFrame_OutVol, textvariable=self.txt_maxsize_var, width=10)
        self.txt_maxsize.grid(row=1, column=1, sticky=tk.S)

        # Place Generate VOLUME button
        self.btn_generateVol = ttk.Button(labelFrame_OutVol)
        self.btn_generateVol.configure(text="Generate VOLUME", padding=10, default=tk.ACTIVE,
                                       command=lambda: repr(self.btnGenerate(RoadTabConstants.VOLUME)))
        self.btn_generateVol.grid(row=2, column=0, columnspan=2, sticky=tk.S)

        # Place Visualize VOLUME button
        self.btn_visualizeVol = ttk.Button(labelFrame_OutVol)
        self.btn_visualizeVol.configure(text="Visualize VOLUME", padding=10, default=tk.ACTIVE,
                                        command=lambda: repr(self.btnVisualize(RoadTabConstants.VOLUME)))
        self.btn_visualizeVol.grid(row=3, column=0, columnspan=2, sticky=tk.S)

    # Control graphic example button (specifying image path)
    def btnGraphicExample(self, imgPath):

        # Open pop up window
        graphicWin = tk.Toplevel(self)

        print(os.path.isfile(imgPath))
        print(imgPath)

        # my_image = ImageTk.PhotoImage(file=imgPath)

        canvas = tk.Canvas(graphicWin, width=300, height=300, bg='skyblue')
        canvas.pack(expand=True, fill='both')

        jpg = Image.open(imgPath)
        my_image = ImageTk.PhotoImage(jpg, master=graphicWin)
        canvas.create_image(0, 0, anchor=tk.NW, image=my_image)

        # tk.Grid.rowconfigure(graphicWin, 0, weight=1)
        # tk.Grid.columnconfigure(graphicWin, 0, weight=1)

    # Index LINE=0, AREA=1, VOLUME=2
    # Control columns button
    def btnCol(self, index):
        colWin = tk.Toplevel(self)
        # Line
        if index == 0:
            colWin.title("“Line.csv” Features Explained")
            lst = RoadTabConstants.lstLineCol
        # Area
        if index == 1:
            colWin.title("“AREA.csv” Features Explained")
            lst = RoadTabConstants.lstAreaCol
        # Volume
        if index == 2:
            colWin.title("“VOLUME_XX.csv” Features Explained")
            lst = RoadTabConstants.lstVolCol

        # Place labels of the columns in pop up window
        for col in lst:
            label = tk.Label(colWin, text=col, font=(None, 12))
            label.grid(sticky=tk.W)

    # Control Generate button
    def btnGenerate(self, index):
        # Line
        if index == RoadTabConstants.LINE:
            self.generateLINE()
        # Area
        if index == RoadTabConstants.AREA:
            self.generateAREA()
        # Volume
        if index == RoadTabConstants.VOLUME:
            self.generateVOLUME()

    # Generate LINE
    def generateLINE(self):
        # Generate LINE.csv (Argument: converted GIS data, Road ID column, Road Type column)
        generateLINE(Data)

    # Generate AREA
    def generateAREA(self):
        generateAREA(Data.rd_list, Data.output_path, Data.roadID, Data.roadTp)

    # Generate VOLUME
    def generateVOLUME(self):

        # If the maxsize value is null
        if self.txt_maxsize_var.get() == "":
            tk.messagebox.showerror('showerror', "No max size input")
            return
        else:
            # Transform maxsize var to float
            maxsize = float(self.txt_maxsize_var.get())
            if maxsize < 0:
                tk.messagebox.showerror('showerror', "Max size is negative")
                return
            elif maxsize > 8:
                tk.messagebox.showwarning('showwarning', "Max size is greater than 8")

        Data.maxsize_var = maxsize
        generateVOLUME(Data.output_path, Data.rd_list, Data.maxsize_var, Data.roadID)

    # Control Visualize button
    def btnVisualize(self, index):
        # LINE
        if index == RoadTabConstants.LINE:
            fig = visualizeLINE(Data.output_path, Data.xref_left_m, Data.xref_right_m, Data.yref_lower_m,
                                Data.yref_higher_m)
            title = RoadTabConstants.visualize_title_LINE
        # AREA
        if index == RoadTabConstants.AREA:
            fig = visualizeAREA(Data.output_path, Data.xref_left_m, Data.xref_right_m, Data.yref_lower_m,
                                Data.yref_higher_m)
            title = RoadTabConstants.visualize_title_AREA
        # VOLUME
        if index == RoadTabConstants.VOLUME:
            fig = visualizeVOLUME(Data.output_path, Data.maxsize_var, Data.xref_left_m, Data.xref_right_m,
                                  Data.yref_lower_m,
                                  Data.yref_higher_m)
            title = RoadTabConstants.visualize_title_VOLUME

        # Open pop up window to show the output plot
        visualizeWindow = tk.Toplevel(self)
        visualizeWindow.title(title)
        canvas = FigureCanvasTkAgg(fig, master=visualizeWindow)
        canvas.get_tk_widget().pack(expand=True, fill="both")
        toolbar = NavigationToolbar2Tk(canvas, visualizeWindow)
        toolbar.update()
        toolbar.pack(anchor=tk.CENTER)


# Receptors tab class
class ReceptorsTab(tk.Frame, Data):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)

        # Create Info frame
        # Label-frame for Info frame
        infoFrame = tk.LabelFrame(self, text="Information for receptors", width=300, height=200,
                                  font=(None, 15, "bold"))
        infoFrame.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        self.createInfoFrame(infoFrame)

        # Create Receptor generation frame
        # Label-frame for Receptor generation frame
        self.receptor_gen_frame = tk.LabelFrame(self, text="Input for receptors generation", width=300, height=200,
                                                font=(None, 15, "bold"))
        self.receptor_gen_frame.grid(row=0, column=1, sticky=tk.W + tk.E + tk.N + tk.S)

        self.createReceptorGenFrame()

    def createInfoFrame(self, labelframe):
        # Labels
        for str in ReceptorsTabConstants.infoList:
            tk.Label(labelframe, text=str, wraplength=300).grid(sticky=tk.W)

    def createReceptorGenFrame(self):
        # Label
        tk.Label(self.receptor_gen_frame, text="Near-road receptors:", wraplength=300).grid(row=0, column=0,
                                                                                            columnspan=2, sticky=tk.W)
        tk.Label(self.receptor_gen_frame, text="1.1. Import from csv file", wraplength=300).grid(row=1, column=0,
                                                                                                 sticky=tk.W)

        # Upload csv button
        self.btn_uploadCSV = ttk.Button(self.receptor_gen_frame)
        self.btn_uploadCSV.configure(text="Upload csv", padding=10, default=tk.ACTIVE,
                                     command=self.btnUploadCSV)
        self.btn_uploadCSV.grid(row=1, column=1, sticky=tk.W)

        # Label for upload file path
        self.label_uploadcsv = tk.Label(self.receptor_gen_frame, text="No csv file selected", wraplength=500)
        self.label_uploadcsv.grid(row=2, column=0, columnspan=2, sticky=tk.W)

        tk.Label(self.receptor_gen_frame, text="or", wraplength=300).grid(row=3, column=0, columnspan=2)
        tk.Label(self.receptor_gen_frame, text="1.2. Type layers information:", wraplength=300).grid(row=4, column=0,
                                                                                                     columnspan=2)

        # Receptor csv table
        self.sheet = Sheet(None, self.receptor_gen_frame)
        self.sheet.grid(row=4, column=0, columnspan=2)

        # 2
        tk.Label(self.receptor_gen_frame, text="2. Gridded - interval (SG in m)", wraplength=300).grid(row=6, column=0,
                                                                                                       columnspan=1,
                                                                                                       sticky=tk.W)

        self.entry_interval = tk.StringVar()
        entry_interval = tk.Entry(self.receptor_gen_frame, textvariable=self.entry_interval, width=10)
        entry_interval.grid(row=6, column=1, sticky=tk.W)

        # 3
        tk.Label(self.receptor_gen_frame, text="3. Receptor elevations", wraplength=300).grid(row=7, column=0,
                                                                                              columnspan=1, sticky=tk.W)

        self.entry_elevation = tk.StringVar()
        entry_elevation = tk.Entry(self.receptor_gen_frame, textvariable=self.entry_elevation, width=10)
        entry_elevation.grid(row=7, column=1, sticky=tk.W)

        # Generate and visualize receptors buttons
        self.btn_generateRecp = ttk.Button(self.receptor_gen_frame)
        self.btn_generateRecp.configure(text="Generate receptors", padding=10, default=tk.ACTIVE,
                                        command=self.btnGenerateRec)
        self.btn_generateRecp.grid(row=8, column=0, sticky=tk.W)

        self.btn_visualizeRecp = ttk.Button(self.receptor_gen_frame)
        self.btn_visualizeRecp.configure(text="Visualize receptors", padding=10, default=tk.ACTIVE,
                                         command=self.btnVisualizeRec)
        self.btn_visualizeRecp.grid(row=8, column=1, sticky=tk.W)

    # Upload csv button control
    def btnUploadCSV(self):
        # Choose csv file
        path = tk.filedialog.askopenfilename(initialdir=os.getcwd(), title="Select file",
                                             filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
                                             )

        # Set path in the label
        self.label_uploadcsv.config(text=path)

        # Read csv as dataframe
        csv_df = pd.read_csv(path)

        self.sheet = Sheet(csv_df, self.receptor_gen_frame)
        self.sheet.grid(row=4, column=0, columnspan=2)

    # Generate receptors button control
    def btnGenerateRec(self):
        if self.checkInput():
            # Transform list data of receptor to dataframe
            output_list = self.sheet.get_sheet_data(return_copy=False, get_header=False, get_index=False)
            df = pd.DataFrame(output_list)

            # Add columns
            df.columns = ReceptorsTabConstants.colList

            # Replace empty string with NaN
            df = df.replace('', np.nan, regex=True)

            # Delete rows which have at least one null value
            df = df.dropna(how='any')

            # Transform all data to int
            df = df.astype(int)

            # Leave corresponding road type of receptor to the GIS data
            df = df[df['F_LTYPE'].isin(Data.rd_list[Data.roadTp].unique())].reset_index(drop=True)

            # Check if receptor data has no row
            if df.size == 0:
                tk.messagebox.showerror('showerror', "The receptor dataframe does not have data")
                return

            # Generate receptor
            self.generateRec(df)

    # Check input of Receptor tab
    def checkInput(self):
        errFlag = True
        errMsg = ""

        # Check rd_list is not None
        if Data.rd_list is None:
            errFlag = False
            errMsg += " No road data imported"

        # Check interval
        if self.entry_interval.get() == "":
            errFlag = False
            errMsg += "\n No interval value"
        else:
            # Transform value to float
            Data.interval = float(self.entry_interval.get())

        # Check elevations
        if self.entry_elevation.get() == "":
            errFlag = False
            errMsg += "\n No elevation value"
        else:
            # Transform value to float
            Data.elevation = float(self.entry_elevation.get())

        if errFlag is not True:
            tk.messagebox.showerror('showerror', errMsg)

        return errFlag

    # Generate receptors (Arguments: receptor dataframe, interval, elevation)
    def generateRec(self, rec_df):
        # Generate receptors
        self.rec_gdf = generateReceptors(Data.rd_list, Data.output_path, Data.roadTp, Data.xref_left_m,
                                         Data.xref_right_m,
                                         Data.yref_lower_m, Data.yref_higher_m, rec_df,
                                         Data.interval, Data.elevation)

    # Visualize receptors button control
    def btnVisualizeRec(self):
        fig = visualizeReceptors(Data.rd_list, self.rec_gdf, Data.xref_left_m, Data.xref_right_m,
                                 Data.yref_lower_m,
                                 Data.yref_higher_m)
        title = ReceptorsTabConstants.visualizeWindowTitle

        # Open pop up window to show the output plot
        visualizeWindow = tk.Toplevel(self)
        visualizeWindow.title(title)
        canvas = FigureCanvasTkAgg(fig, master=visualizeWindow)
        canvas.get_tk_widget().pack(expand=True, fill="both")
        toolbar = NavigationToolbar2Tk(canvas, visualizeWindow)
        toolbar.update()
        toolbar.pack(anchor=tk.CENTER)


# Receptor table class
class Sheet(tksheet.Sheet):
    def __init__(self, receptor_df, master=None):
        super().__init__(master, column_width=75, height=200)

        # Receptor csv data frame
        self.receptor_df = receptor_df

        # Create spreadsheet table
        self.createTable(receptor_df)

    # Create Spread sheet table of receptor data frame
    def createTable(self, receptor_df):

        # List of output table
        if receptor_df is None or len(receptor_df) == 0:
            lst_df = [["", "", "", ""]]
        else:
            lst_df = receptor_df.values.tolist()

        # Set header
        headers_list = ReceptorsTabConstants.colList
        headers = [f'{c}' for c in headers_list]
        self.headers(headers)

        # Set data
        self.set_sheet_data(lst_df)

        # Set bindings
        self.enable_bindings(("single_select",

                              "row_select",

                              "column_width_resize",

                              "arrowkeys",

                              "right_click_popup_menu",

                              "rc_select",

                              "rc_insert_row",

                              "rc_delete_row",

                              "copy",

                              "cut",

                              "paste",

                              "delete",

                              "undo",

                              "edit_cell"))


# Emissions tab class
class EmissionsTab(tk.Frame, Data):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)

        self.vol_df = None  # VOLUME csv data frame

        # Create Info frame
        # Label-frame for Info frame
        infoFrame = tk.LabelFrame(self, text="Information for emissions", width=300, height=200,
                                  font=(None, 15, "bold"))
        infoFrame.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        self.createInfoFrame(infoFrame)

        # Create Emissions conversion frame
        self.emission_conversion_frame = tk.Frame(self, borderwidth=5, relief=tk.GROOVE, width=300, height=200)
        self.emission_conversion_frame.grid(row=0, column=1, sticky=tk.W + tk.E + tk.N + tk.S)

        self.createEmissionConvFrame()

    # Create emissions info frame
    def createInfoFrame(self, labelframe):
        # Labels
        for str in EmissionsTabConstants.infoList:
            tk.Label(labelframe, text=str, wraplength=300).grid(sticky=tk.W)

    # Create Emissions conversion frame
    def createEmissionConvFrame(self):
        # Skip checkbox
        self.bln_skip = tk.BooleanVar()
        self.bln_skip.set(False)
        self.chk_skip = tk.Checkbutton(self.emission_conversion_frame, command=self.controlChkSkip,
                                       variable=self.bln_skip, text="Skip the “Emission Module”")
        self.chk_skip.grid(row=0, column=0)

        # 1. Title
        tk.Label(self.emission_conversion_frame, text="Input for Emission Conversion", wraplength=300).grid(row=1,
                                                                                                            column=0,
                                                                                                            columnspan=2,
                                                                                                            sticky=tk.W)
        tk.Label(self.emission_conversion_frame, text="1. Select link emission column and unit in GIS",
                 wraplength=300).grid(row=2,
                                      column=0,
                                      columnspan=2,
                                      sticky=tk.W)

        # Combo box to choose the emission column
        tk.Label(self.emission_conversion_frame, text="Emission", wraplength=300).grid(row=3, column=0, sticky=tk.W)

        self.combo_emission = ttk.Combobox(self.emission_conversion_frame, state='readonly')
        self.combo_emission.grid(row=3, column=1)

        # Emission Unit
        tk.Label(self.emission_conversion_frame, text="Em Unit", wraplength=300).grid(row=4, column=0, rowspan=2,
                                                                                      sticky=tk.W)

        # Emission Unit checkbox
        self.bln_mile = tk.BooleanVar()
        self.bln_mile.set(False)
        self.chk_mile = tk.Checkbutton(self.emission_conversion_frame, command=lambda: self.controlChkEmUnit(1),
                                       variable=self.bln_mile, text="g/mile/hr")
        self.chk_mile.grid(row=4, column=1)

        self.bln_link = tk.BooleanVar()
        self.bln_link.set(False)
        self.chk_link = tk.Checkbutton(self.emission_conversion_frame, command=lambda: self.controlChkEmUnit(2),
                                       variable=self.bln_link, text="g/link/hr")
        self.chk_link.grid(row=5, column=1)

        # 2. Title
        tk.Label(self.emission_conversion_frame, text="2. Which source(s) do you want to generate emissions for?",
                 wraplength=300).grid(row=6, column=0, columnspan=2,
                                      sticky=tk.W)

        # AREA
        self.bln_area = tk.BooleanVar()
        self.bln_area.set(False)
        self.chk_area = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_area, text="AREA")
        self.chk_area.grid(row=7, column=0, sticky=tk.W)

        # LINE
        self.bln_line = tk.BooleanVar()
        self.bln_line.set(False)
        self.chk_line = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_line, text="LINE or RLINE")
        self.chk_line.grid(row=8, column=0, sticky=tk.W)

        # RLINEXT
        self.bln_rlinext = tk.BooleanVar()
        self.bln_rlinext.set(False)
        self.chk_rlinext = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_rlinext, text="RLINEXT")
        self.chk_rlinext.grid(row=9, column=0, sticky=tk.W)

        # VOLUME
        self.bln_vol = tk.BooleanVar()
        self.bln_vol.set(False)
        self.chk_vol = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_vol, text="VOLUME")
        self.chk_vol.grid(row=10, column=0, sticky=tk.W)

        self.button_volume = ttk.Button(self.emission_conversion_frame)
        self.button_volume.configure(text="Upload VOLUME csv", padding=10, default=tk.ACTIVE, command=self.btnVol)
        self.button_volume.grid(row=10, column=1, sticky=tk.W)

        # Verify input and generate emission button
        self.button_generateEm = ttk.Button(self.emission_conversion_frame)
        self.button_generateEm.configure(text="Upload VOLUME csvVerify input and generate emission", padding=10,
                                         default=tk.ACTIVE, command=self.btnEm)
        self.button_generateEm.grid(row=11, column=0, columnspan=2)

    # Control Skip check button
    def controlChkSkip(self):
        # If true, disable all features
        if self.bln_skip.get() == True:
            self.combo_emission.config(state=tk.DISABLED)

            self.chk_mile.config(state=tk.DISABLED)
            self.chk_link.config(state=tk.DISABLED)

            self.chk_area.config(state=tk.DISABLED)
            self.chk_line.config(state=tk.DISABLED)
            self.chk_rlinext.config(state=tk.DISABLED)
            self.chk_vol.config(state=tk.DISABLED)

            self.button_volume.config(state=tk.DISABLED)
            self.button_generateEm.config(state=tk.DISABLED)

        else:
            self.combo_emission.config(state=tk.NORMAL)

            self.chk_mile.config(state=tk.NORMAL)
            self.chk_link.config(state=tk.NORMAL)

            self.chk_area.config(state=tk.NORMAL)
            self.chk_line.config(state=tk.NORMAL)
            self.chk_rlinext.config(state=tk.NORMAL)
            self.chk_vol.config(state=tk.NORMAL)

            self.button_volume.config(state=tk.NORMAL)
            self.button_generateEm.config(state=tk.NORMAL)

    # Emissions Unit checkbox control
    def controlChkEmUnit(self, index):
        if index == 1:
            self.bln_link.set(False)
            self.chk_link.config(state=tk.NORMAL)
            self.chk_mile.config(state=tk.DISABLED)
        if index == 2:
            self.bln_mile.set(False)
            self.chk_mile.config(state=tk.NORMAL)
            self.chk_link.config(state=tk.DISABLED)

    # Upload VOLUME csv button control
    def btnVol(self):
        # Choose VOLUME csv file
        self.pathVolcsv = tk.filedialog.askopenfilename(initialdir=os.getcwd(), title="Select file",
                                                   filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
                                                   )

    # Verify input and generate emission button
    def btnEm(self):
        if self.checkInput():
            self.generateEmissions()

    # Check input for generate emissions
    def checkInput(self):
        errFlag = True
        errMsg = ""

        # Check if Emission column is selected
        if self.combo_emission.get() == "":
            errFlag = False
            errMsg += "No Emission is selected"

        # Em Unit
        if self.bln_mile.get() == False and self.bln_link.get() == False:
            errFlag = False
            errMsg += "\nNo Emission unit is selected"

        # If any source is selected
        if self.bln_area.get() == False and self.bln_line.get() == False and self.bln_rlinext.get() == False and self.bln_vol.get() == False:
            errFlag = False
            errMsg += "\nNo source is selected"

        # If VOLUME is selected, then check if VOLUME csv is selected
        if self.bln_vol.get() == True and (self.pathVolcsv is None or self.pathVolcsv == ""):
            errFlag = False
            errMsg += "\nVOLUME csv file is not selected"

        if errFlag is not True:
            tk.messagebox.showerror('showerror', errMsg)

        return errFlag

    # Generate Emissions
    def generateEmissions(self):

        generateEmissions(self.bln_area, self.bln_line, self.bln_rlinext, self.bln_vol, self.bln_link, Data.rd_list,
                          Data.roadID, self.combo_emission.get(), self.pathVolcsv, Data.output_path)

# Compilation tab class
class CompilationTab(tk.Frame, Data):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)

        # Checkbox for Run AERMOD or not
        self.bln_runAERMOD = tk.BooleanVar()
        self.bln_runAERMOD.set(False)
        self.chk_runAERMOD = tk.Checkbutton(self, variable=self.bln_runAERMOD, text="Run AERMOD")
        self.chk_runAERMOD.grid(row=0, column=0, sticky=tk.W)

        self.bln_noEmission = tk.BooleanVar()
        self.bln_noEmission.set(False)
        self.chk_noEmission = tk.Checkbutton(self, variable=self.bln_noEmission, text="Emission unavailable, just compile road and receptors input")
        self.chk_noEmission.grid(row=0, column=1, sticky=tk.W)

        # Create Rnning Info frame
        infoFrame = tk.LabelFrame(self, text="Running Information", width=300, height=200,
                                  font=(None, 15, "bold"))
        infoFrame.grid(row=1, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        #self.createInfoFrame(infoFrame)


# Main window class
class MainWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Main window
        self.title("GIS TO AERMOD Tool")
        self.geometry("700x500")

        self.nb = ttk.Notebook(self, width=800, height=600)

        # Add Data tab
        self.data_tab = DataTab(master=self.nb)
        self.nb.add(self.data_tab, text='Data', padding=5)

        # Add Road tab
        self.road_tab = RoadTab(master=self.nb)
        self.nb.add(self.road_tab, text='Road', padding=5)

        # Add Receptors tab
        self.receptors_tab = ReceptorsTab(master=self.nb)
        self.nb.add(self.receptors_tab, text='Receptors', padding=5)

        # Add Emissions tab
        self.emissions_tab = EmissionsTab(master=self.nb)
        self.nb.add(self.emissions_tab, text='Emissions', padding=5)

        # Add Compilation tab
        self.compilation_tab = CompilationTab(master=self.nb)
        self.nb.add(self.compilation_tab, text='Compilation', padding=5)

        self.nb.pack(expand=True, fill="both")


def main():
    root = MainWindow()

    root.mainloop()


if __name__ == "__main__":
    main()
