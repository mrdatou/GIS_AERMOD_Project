import concurrent.futures
import multiprocessing
import os
import queue
import threading
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from time import sleep
from tkinter import filedialog
from tkinter import font
import center_tk_window

import numpy as np
import pandas as pd
import tksheet
from GISPlotWindow import GISplotWindow
from PIL import Image, ImageTk
from constants import RoadTabConstants, ReceptorsTabConstants, EmissionsTabConstants, CompilaionTabConstants, \
    ResultsTabConstants
from generate_data import GISextract, dataConversion, generateLINE, generateAREA, visualizeLINE, visualizeAREA, \
    generateVOLUME, visualizeVOLUME, \
    generateReceptors, visualizeReceptors, generateEmissions, generateResults, runAERMOD_AREA, runAERMOD_VOLUME, \
    runAERMOD_LINE, runAERMOD_B_RLINE, runAERMOD_A_RLINEXT, visualizeResults
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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

    # EPSG setting
    fromproj = None  # EPSG from
    toproj = None  # EPSG to
    isFeet = None  # Unit

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


class Progressbar(tk.Toplevel):
    def __init__(self, title, text, master=None):
        super().__init__(master)

        self.label_font = tk.font.Font(size=13)

        self.title(title)
        self.geometry("400x50")
        center_tk_window.center_on_screen(self)

        # Set focus on this toplevel window
        self.focus_force()
        self.grab_set()

        self.attributes('-disabled', True)

        # Progress window message
        tk.Label(self, text=text, font=self.label_font).pack(anchor=tk.W)

        # Progress bar
        self.progressbar = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode='determinate', length=300)
        self.progressbar.pack(expand=True)

        self.progressbar.start()

    def checkThreadStatus(self):
        pass

    def close(self):
        self.progressbar.stop()
        self.destroy()


# Data Tab class inherit Data class to share data with other tabs
class DataTab(tk.Frame, Data):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)

        self.label_font = tk.font.Font(size=13)

        # Flag if open shp file first time or not
        self.isOpenSecond = tk.BooleanVar()
        self.isOpenSecond.set(False)

        self.rd_list = None

        # Create Open, Import button and File Dialog
        self.createTopButtonAndDialog()

        # Create File setting frame
        self.createSettings()

        # Create Verify inputs button
        self.button_open = ttk.Button(self)
        self.button_open.configure(text="Verify Inputs and \nConvert GIS Coordinates", padding=10, default=tk.ACTIVE,
                                   command=self.btnVerify)
        self.button_open.grid(row=3, column=1)

    def createTopButtonAndDialog(self):
        # Open Button
        self.button_open = ttk.Button(self)
        self.button_open.configure(text="Open", padding=10, default=tk.ACTIVE, command=self.btnOpen)
        self.button_open.grid(row=0, column=0, sticky=tk.W)

        # GIS file path label
        self.GIS_path = tk.StringVar()
        self.label_GISfile = tk.Label(self, textvariable=self.GIS_path, font=("", 12), width=80, anchor=tk.W,
                                      wraplength=600,
                                      justify='left')
        self.label_GISfile.grid(row=1, column=0, columnspan=3, sticky=tk.W)

    # Define Open button function
    def btnOpen(self):

        # If shp file opened second time
        if self.isOpenSecond.get():
            Msg_shoulder = tk.messagebox.askquestion('',
                                                     "shp file is already open. Want to open new shp file?")

            # Yes is selected to proceed
            if Msg_shoulder == 'no':
                return

        # Choose shp file
        path = tk.filedialog.askopenfilename(initialdir=os.getcwd(), title="Select file",
                                             filetypes=(("shp files", "*.shp"), ("all files", "*.*"))
                                             )

        if os.path.exists(path):
            # print("path exist")
            # Clear all values of old shp file
            if self.isOpenSecond.get():
                self.clearAllVals()

            # shp file exists
            Data.path = path
            self.GIS_path.set(Data.path)
            # Extract GIS data
            self.rd_list, Data.path = GISextract(Data.path)

            # Build file setting's drop down menus
            self.buildDropDownMenuSetting()

            # Flag of open shp file second time is True
            self.isOpenSecond.set(True)

    # Clear all values of shp file
    def clearAllVals(self):

        # Columns setting
        self.combo_roadID.set("")
        self.combo_roadTp.set("")
        self.combo_numLane.set("")
        self.combo_laneWid.set("")
        self.txt_shoulder_var.set("")
        self.combo_geom.set("")

        # Projection setting
        self.txt_fromproj_var.set("")
        self.txt_toproj_var.set("")

        # Boundaries
        self.txt_xRight_var.set("")
        self.txt_xLeft_var.set("")
        self.txt_yLow_var.set("")
        self.txt_yHigh_var.set("")
        self.txt_xRef_var.set("")
        self.txt_yRef_var.set("")

        # Data class values
        Data.rd_list = None  # GeoPandas
        Data.path = None  # Imported shp File's location
        Data.output_path = None  # Output file's location path
        Data.roadID = None  # Road ID
        Data.roadTp = None  # Road Type
        Data.numLane = None  # Num of Lanes
        Data.laneWid = None  # Lane width
        Data.shoulder = None  # Shoulder
        Data.geom = None  # Geometry
        Data.fromproj = None  # EPSG from
        Data.toproj = None  # EPSG to
        Data.isFeet = None  # Unit
        Data.xRef = None  # Reference X
        Data.yRef = None  # Reference Y
        Data.yHigh = None  # Y high
        Data.yLow = None  # Y low
        Data.xLeft = None  # X left
        Data.xRight = None  # X right
        Data.xref_left_m = None
        Data.xref_right_m = None
        Data.yref_lower_m = None
        Data.yref_higher_m = None
        Data.maxsize_var = None
        Data.interval = None
        Data.elevation = None

        # print(Data.rd_list)

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
        self.labelFrame_File = tk.LabelFrame(self, text="1. Choose Columns from Shape File", width=200, height=300,
                                             font=(None, 15, "bold"))
        self.labelFrame_File.grid(row=2, column=0, padx=20, pady=20, sticky=tk.W + tk.N + tk.E + tk.S)

        # Road Unique ID label
        self.label_roadID = tk.Label(self.labelFrame_File, text="Road Unique ID", font=self.label_font)
        self.label_roadID.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.S)

        # Road Unique ID Combobox
        self.combo_roadID = ttk.Combobox(self.labelFrame_File, font=self.label_font, state='readonly')
        self.combo_roadID.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.S)

        # Road Type label
        self.label_roadTp = tk.Label(self.labelFrame_File, text="Road Type", font=self.label_font)
        self.label_roadTp.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        # Road Type Combobox
        self.combo_roadTp = ttk.Combobox(self.labelFrame_File, font=self.label_font, state='readonly')
        self.combo_roadTp.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Number of lanes
        self.label_numLane = tk.Label(self.labelFrame_File, text="Number of Lanes", font=self.label_font)
        self.label_numLane.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        # Number of lanes ID Combobox
        self.combo_numLane = ttk.Combobox(self.labelFrame_File, font=self.label_font, state='readonly')
        self.combo_numLane.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        # Lane width
        self.label_laneWid = tk.Label(self.labelFrame_File, text="Lane Width", font=self.label_font)
        self.label_laneWid.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)

        # Lane width Combobox
        self.combo_laneWid = ttk.Combobox(self.labelFrame_File, font=self.label_font, state='readonly')
        self.combo_laneWid.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        # Shoulder Label
        self.label_shoulder = tk.Label(self.labelFrame_File, text="Shoulder(m)", font=self.label_font)
        self.label_shoulder.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W + tk.S)

        # Shoulder textbox
        self.txt_shoulder_var = tk.StringVar()
        self.txt_shoulder = tk.Entry(self.labelFrame_File, textvariable=self.txt_shoulder_var, width=10,
                                     font=self.label_font, justify=tk.RIGHT)
        self.txt_shoulder.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W + tk.S)

        # Geometry Label
        self.label_geom = tk.Label(self.labelFrame_File, text="Geometry", font=self.label_font)
        self.label_geom.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        # Geometry Combobox
        self.combo_geom = ttk.Combobox(self.labelFrame_File, font=self.label_font, state='readonly')
        self.combo_geom.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

    # Create Projection setting frame
    def createProjectionSetting(self):
        # Label Frame
        self.labelFrame_Projection = tk.LabelFrame(self, text="2. Origin and Destination", font=(None, 15, "bold"),
                                                   width=400, height=200)
        self.labelFrame_Projection.grid(row=2, column=1, padx=20, pady=20, sticky=tk.W + tk.N)

        # Control EPSG text form: limit length = 4
        def limitESPGinput():
            if len(self.txt_fromproj_var.get()) > 4:
                self.txt_fromproj_var.set(self.txt_fromproj_var.get()[:3])

        # Original EPSG
        label_from_proj = tk.Label(self.labelFrame_Projection, text="Origin EPSG (4-digits): ", font=self.label_font)
        label_from_proj.grid(row=0, column=0)

        self.txt_fromproj_var = tk.StringVar()
        self.txt_fromproj = tk.Entry(self.labelFrame_Projection, textvariable=self.txt_fromproj_var, width=4,
                                     font=self.label_font, justify=tk.RIGHT)
        self.txt_fromproj.grid(row=0, column=1, padx=10, pady=10)

        # Dest EPSG
        label_to_proj = tk.Label(self.labelFrame_Projection, text="Destination EPSG (4-digits): ", font=self.label_font)
        label_to_proj.grid(row=1, column=0)

        self.txt_toproj_var = tk.StringVar()
        self.txt_toproj = tk.Entry(self.labelFrame_Projection, textvariable=self.txt_toproj_var,
                                   width=4, font=self.label_font, justify=tk.RIGHT)
        self.txt_toproj.grid(row=1, column=1, padx=10, pady=10)

        # CheckBox whether meter or feet
        tk.Label(self.labelFrame_Projection, text="Unit of destination EPSG", font=self.label_font).grid(row=2,
                                                                                                         column=0)

        # Meter checkbox
        self.bln_m = tk.BooleanVar()
        self.bln_m.set(False)
        self.chk_m = tk.Checkbutton(self.labelFrame_Projection, variable=self.bln_m, command=self.controlChkM,
                                    text="m", font=self.label_font)
        self.chk_m.grid(row=2, column=1)

        # Feet checkbox
        self.bln_f = tk.BooleanVar()
        self.bln_f.set(False)
        self.chk_f = tk.Checkbutton(self.labelFrame_Projection, variable=self.bln_f, command=self.controlChkF,
                                    text="ft", font=self.label_font)
        self.chk_f.grid(row=3, column=1)

        # EPSG resources
        tk.Label(self.labelFrame_Projection, text="Note EPSG code can be found in:", wraplength=200,
                 font=self.label_font).grid(row=4,
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
        labelFrame_Boundary.grid(row=3, column=0, padx=20, pady=20, sticky=tk.W + tk.N + tk.E)
        tk.Grid.rowconfigure(labelFrame_Boundary, 0, weight=1)
        tk.Grid.columnconfigure(labelFrame_Boundary, 0, weight=1)

        # Canvas for Boundary frame
        canvas = tk.Canvas(labelFrame_Boundary, width=300, height=300, bd=0, highlightthickness=0)
        canvas.pack(expand=True, fill=tk.BOTH)

        # Locate from graph button
        button_locateGraph = ttk.Button(canvas)
        button_locateGraph.configure(text="Locate from graph", padding=10, default=tk.ACTIVE,
                                     command=self.btnLocateGraph)
        button_locateGraph.grid(row=0, column=7, columnspan=2, sticky=tk.E, padx=10, pady=10)

        # y high text box
        tk.Label(canvas, text="Y high", font=self.label_font).grid(row=1, column=3, sticky=tk.S + tk.E)

        self.txt_yHigh_var = tk.StringVar()
        txt_yHigh = tk.Entry(canvas, textvariable=self.txt_yHigh_var, width=10, font=self.label_font)
        txt_yHigh.grid(row=1, column=4, sticky=tk.W, padx=5, pady=5)

        # x left text box
        tk.Label(canvas, text="X left", font=self.label_font).grid(row=2, column=1, rowspan=2, sticky=tk.W)

        self.txt_xLeft_var = tk.StringVar()
        txt_xLeft = tk.Entry(canvas, textvariable=self.txt_xLeft_var, width=10, font=self.label_font)
        txt_xLeft.grid(row=3, column=1, rowspan=2, sticky=tk.W, padx=5, pady=5)

        # X right text box
        tk.Label(canvas, text="X right", font=self.label_font).grid(row=2, column=7, rowspan=2, sticky=tk.E, padx=5,
                                                                    pady=5)

        self.txt_xRight_var = tk.StringVar()
        txt_xRight = tk.Entry(canvas, textvariable=self.txt_xRight_var, width=10, font=self.label_font)
        txt_xRight.grid(row=3, column=7, rowspan=2, sticky=tk.W, padx=5, pady=5)

        # Y low text box
        tk.Label(canvas, text="Y low", font=self.label_font).grid(row=5, column=3, rowspan=2, sticky=tk.E + tk.S)

        self.txt_yLow_var = tk.StringVar()
        txt_yLow = tk.Entry(canvas, textvariable=self.txt_yLow_var, width=10, font=self.label_font)
        txt_yLow.grid(row=6, column=4, rowspan=2, sticky=tk.W, padx=5, pady=5)

        # Reference point x text box
        tk.Label(canvas, text="Reference x", font=self.label_font).grid(row=3, column=3, sticky=tk.E, padx=5, pady=5)

        self.txt_xRef_var = tk.StringVar()
        txt_xRef = tk.Entry(canvas, textvariable=self.txt_xRef_var, width=10, font=self.label_font)
        txt_xRef.grid(row=3, column=4, sticky=tk.W, padx=5, pady=5)

        # Reference point y text box
        tk.Label(canvas, text="Reference y", font=self.label_font).grid(row=4, column=3, sticky=tk.E, padx=5, pady=5)

        self.txt_yRef_var = tk.StringVar()
        txt_yRef = tk.Entry(canvas, textvariable=self.txt_yRef_var, width=10, font=self.label_font)
        txt_yRef.grid(row=4, column=4, sticky=tk.W, padx=5, pady=5)

        # Empty labels
        tk.Label(canvas, text="   ").grid(row=2, column=0, sticky=tk.E)

        tk.Label(canvas, text="   ").grid(row=2, column=2, sticky=tk.E)

        tk.Label(canvas, text="   ").grid(row=2, column=5, sticky=tk.E, padx=50)

        tk.Label(canvas, text="   ").grid(row=5, column=0, sticky=tk.E)

        # Line
        canvas.create_rectangle(60, 80, 510, 225, width=1, dash=(4, 2))

    # Open GIS plot window
    def btnLocateGraph(self):

        # Check if GIS data rd_list is null or not
        if self.rd_list is None:
            tk.messagebox.showerror("Error", "rd_list is null")
            return

        # Open GIS plot window
        locateGraphWindow = tk.Toplevel(self)
        locateGraphWindow.title("Locate boundary and reference point")
        locateGraphWindow.geometry("890x530")

        # Place the window in the center
        center_tk_window.center_on_screen(locateGraphWindow)

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
        # Set test input (This is for test!!!)
        # self.setTestInput()

        # Check input values
        if self.checkInputErr():

            # Progressbar window
            progressbar = Progressbar("Processing", "Generating GIS coordinate system...")

            # Data conversion in another thread
            thread_conversion = threading.Thread(name="conversion", target=self.passInputToMain)
            thread_conversion.start()

            def checkConversionThread():
                if thread_conversion.is_alive():
                    self.master.master.after(1000, checkConversionThread)
                else:
                    progressbar.close()

            checkConversionThread()

    # Set test input for test Should be disabled when not testing
    def setTestInput(self):
        self.combo_roadID.set("A_B")
        self.combo_roadTp.set("rdtype_aer")
        self.combo_numLane.set("LANES")
        self.combo_laneWid.set("lane_width")
        self.combo_geom.set("geometry")
        self.txt_shoulder_var.set("1")
        self.txt_fromproj_var.set("2240")
        self.txt_toproj_var.set("2240")
        self.bln_f.set(True)
        self.txt_xRef_var.set("2245379.696")
        self.txt_yRef_var.set("1393239.2335")
        self.txt_xLeft_var.set("2243303.739")
        self.txt_xRight_var.set("2247455.653")
        self.txt_yLow_var.set("1391045.639")
        self.txt_yHigh_var.set("1395432.828")

    # Check input values when verify inputs button pressed
    def checkInputErr(self):

        # Error Flag
        errFlag = True

        # Error message string
        errMsg = ""

        # Check if columns are chosen
        if self.combo_roadID.get() == "" or self.combo_roadTp.get() == "" or self.combo_numLane.get() == "" or self.combo_laneWid.get() == "" or self.combo_geom.get() == "":
            errMsg += "1. Column value is not selected"
            errFlag = False

        if self.txt_shoulder_var.get() == "":
            errMsg += "\n No shoulder value"
            errFlag = False
        else:

            try:
                shoulder = float(self.txt_shoulder_var.get())
                if shoulder < 0:
                    # Give warning if shoulder is greater than 8
                    errMsg += "\n 1. Shoulder should be nonnegative"
                    errFlag = False
            except ValueError:
                errMsg += "\n 1. Shoulder should be number(float)"
                errFlag = False

        if self.txt_fromproj_var.get() == "" or self.txt_toproj_var.get() == "":
            errMsg += "\n 2. ESPG value is missed"
            errFlag = False

        else:

            try:
                a = int(self.txt_fromproj_var.get())
                b = int(self.txt_toproj_var.get())
            except ValueError:
                errMsg += "\n 2. EPSG should be integer"
                errFlag = False

        if self.bln_f is False and self.bln_m is False:
            errMsg += "\n 2. No unit selected"
            errFlag = False

        if self.txt_xRef_var.get() == "" or self.txt_yRef_var.get() == "" or self.txt_yHigh_var.get() == "" or self.txt_yLow_var.get() == "" or self.txt_xLeft_var.get() == "" or self.txt_xRight_var.get() == "":
            errMsg += "\n 3. Boundary and Reference point is missed"
            errFlag = False
        else:
            try:
                a = float(self.txt_xRef_var.get())  # Reference X
                b = float(self.txt_yRef_var.get())  # Reference Y
                c = float(self.txt_yHigh_var.get())  # Y high
                d = float(self.txt_yLow_var.get())  # Y low
                e = float(self.txt_xLeft_var.get())  # X left
                f = float(self.txt_xRight_var.get())  # X right

            except ValueError:
                errMsg += "\n 3. Boundary and Reference point should be number"
                errFlag = False

        if errFlag is not True:
            tk.messagebox.showerror('Error', errMsg)

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

        Data.isFeet = tk.BooleanVar()
        if self.bln_f:
            Data.isFeet.set(True)
        else:
            Data.isFeet.set(False)

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
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)

        self.label_font = tk.font.Font(size=13)

        # Create Line frame
        self.createLineFrame()

        # Create AREA frame
        self.createAreaFrame()

        # Create VOLUME frame
        self.createVolFrame()

    def createLineFrame(self):
        # Outer Label Frame
        labelFrame_OutLine = tk.LabelFrame(self, text="Line (LINE, RLINE, RLINEXT)", width=100, height=300,
                                           font=(None, 15, "bold"))
        labelFrame_OutLine.pack(expand=True, padx=10, pady=10, side=tk.LEFT, anchor=tk.N, fill='both')

        # Inner Frame
        frame_InLine = tk.Frame(labelFrame_OutLine, borderwidth=1, highlightbackground="grey54",
                                highlightcolor="grey54", highlightthickness=1, height=350)
        frame_InLine.pack(expand=True, padx=10, pady=10, anchor=tk.N, fill='x')
        frame_InLine.pack_propagate(0)

        str = RoadTabConstants.road_line
        tk.Label(frame_InLine, text=str, wraplength=190, font=self.label_font, anchor=tk.W, justify='left').pack(
            expand=True,
            padx=20,
            pady=20)

        # Place Line's graphic example button
        self.button_lineExample = ttk.Button(frame_InLine)
        self.button_lineExample.configure(text="Graphic example", padding=10, default=tk.ACTIVE, width=15,
                                          command=lambda: repr(self.btnGraphicExample(RoadTabConstants.LINE)))
        self.button_lineExample.pack(pady=10, anchor=tk.S)

        # Place LINE columns button
        self.button_lineCols = ttk.Button(frame_InLine)
        self.button_lineCols.configure(text="LINE columns", padding=10, default=tk.ACTIVE, width=15,
                                       command=lambda: repr(self.btnCol(0)))
        self.button_lineCols.pack(pady=10, anchor=tk.S)

        # Place Generate Line button
        self.button_generateLine = ttk.Button(labelFrame_OutLine)
        self.button_generateLine.configure(text="Generate Line", padding=10, default=tk.ACTIVE, width=15,
                                           command=lambda: repr(self.btnGenerate(RoadTabConstants.LINE)))
        self.button_generateLine.pack(anchor=tk.S, pady=30)

        # Place Visualize Line button
        self.button_visualizeLine = ttk.Button(labelFrame_OutLine)
        self.button_visualizeLine.configure(text="Visualize Line", padding=10, default=tk.ACTIVE, width=15,
                                            command=lambda: repr(self.btnVisualize(RoadTabConstants.LINE)))
        self.button_visualizeLine.pack(anchor=tk.S, pady=30)

    # Create AREA frame
    def createAreaFrame(self):
        # Outer Label Frame
        labelFrame_OutArea = tk.LabelFrame(self, text="AREA", width=100, height=300,
                                           font=(None, 15, "bold"))
        labelFrame_OutArea.pack(expand=True, padx=10, pady=10, side=tk.LEFT, anchor=tk.N, fill='both')

        # Inner Frame
        frame_InArea = tk.Frame(labelFrame_OutArea, borderwidth=1, highlightbackground="grey54",
                                highlightcolor="grey54", highlightthickness=1, width=100, height=350)
        frame_InArea.pack(expand=True, padx=10, pady=10, anchor=tk.N, fill=tk.X)
        frame_InArea.pack_propagate(0)

        str = RoadTabConstants.road_area
        tk.Label(frame_InArea, text=str, wraplength=180, font=self.label_font, anchor=tk.W, justify='left').pack(
            expand=True,
            padx=20,
            pady=20)

        # Place Area's graphic example button
        self.btn_areaExample = ttk.Button(frame_InArea)
        self.btn_areaExample.configure(text="Graphic example", padding=10, default=tk.ACTIVE, width=15,
                                       command=lambda: repr(self.btnGraphicExample(RoadTabConstants.AREA)))
        self.btn_areaExample.pack(pady=10, anchor=tk.S)

        # Place Area columns button
        self.btn_areaCols = ttk.Button(frame_InArea)
        self.btn_areaCols.configure(text="AREA columns", padding=10, default=tk.ACTIVE, width=15,
                                    command=lambda: repr(self.btnCol(RoadTabConstants.AREA)))
        self.btn_areaCols.pack(pady=10, anchor=tk.S)

        # Place Generate Area button
        self.btn_generateArea = ttk.Button(labelFrame_OutArea)
        self.btn_generateArea.configure(text="Generate AREA", padding=10, default=tk.ACTIVE, width=15,
                                        command=lambda: repr(self.btnGenerate(RoadTabConstants.AREA)))
        self.btn_generateArea.pack(anchor=tk.S, padx=10, pady=30)

        # Place Visualize Area button
        self.btn_visualizeArea = ttk.Button(labelFrame_OutArea)
        self.btn_visualizeArea.configure(text="Visualize AREA", padding=10, default=tk.ACTIVE, width=15,
                                         command=lambda: repr(self.btnVisualize(RoadTabConstants.AREA)))
        self.btn_visualizeArea.pack(anchor=tk.S, padx=10, pady=30)

    # Create VOLUME frame
    def createVolFrame(self):
        # Outer Label Frame
        labelFrame_OutVol = tk.LabelFrame(self, text="VOLUME", width=100, height=300,
                                          font=(None, 15, "bold"))
        labelFrame_OutVol.pack(expand=True, padx=10, pady=10, side=tk.LEFT, anchor=tk.N, fill='both')

        # Inner Frame
        frame_InVol = tk.Frame(labelFrame_OutVol, borderwidth=1, highlightbackground="grey54", highlightcolor="grey54",
                               highlightthickness=1, width=100, height=350, bd=0)
        frame_InVol.pack(expand=True, padx=10, pady=10, anchor=tk.N, fill=tk.X)
        frame_InVol.pack_propagate(0)

        str = RoadTabConstants.road_vol
        label_emp3 = tk.Label(frame_InVol, text=str, wraplength=180, font=self.label_font, anchor=tk.W, justify='left')
        label_emp3.pack(expand=True, padx=10, pady=10)

        # Place VOLUME's graphic example button
        btn_volExample = ttk.Button(frame_InVol)
        btn_volExample.configure(text="Graphic example", padding=10, default=tk.ACTIVE, width=18,
                                 command=lambda: repr(self.btnGraphicExample(RoadTabConstants.VOLUME)))
        btn_volExample.pack(pady=10, anchor=tk.S)

        # Place Area columns button
        btn_volCols = ttk.Button(frame_InVol)
        btn_volCols.configure(text="VOLUME columns", padding=10, default=tk.ACTIVE, width=18,
                              command=lambda: repr(self.btnCol(2)))
        btn_volCols.pack(pady=10, anchor=tk.S)

        # Max size frame
        f_maxsize = tk.Frame(labelFrame_OutVol, height=30)
        f_maxsize.pack(expand=True, anchor=tk.N)
        f_maxsize.pack_propagate(0)

        # Put textbox for max size
        tk.Label(f_maxsize, text="Max Size (m) Should <= 8 m", font=self.label_font).grid(row=0, column=0)

        self.txt_maxsize_var = tk.StringVar()
        self.txt_maxsize = tk.Entry(f_maxsize, textvariable=self.txt_maxsize_var, width=10, font=self.label_font,
                                    justify=tk.RIGHT)
        self.txt_maxsize.grid(row=0, column=1)

        # Place Generate VOLUME button
        self.btn_generateVol = ttk.Button(labelFrame_OutVol)
        self.btn_generateVol.configure(text="Generate VOLUME", padding=10, default=tk.ACTIVE, width=18,
                                       command=lambda: repr(self.btnGenerate(RoadTabConstants.VOLUME)))
        self.btn_generateVol.pack(anchor=tk.S, padx=10, pady=30)

        # Place Visualize VOLUME button
        self.btn_visualizeVol = ttk.Button(labelFrame_OutVol)
        self.btn_visualizeVol.configure(text="Visualize VOLUME", padding=10, default=tk.ACTIVE, width=18,
                                        command=lambda: repr(self.btnVisualize(RoadTabConstants.VOLUME)))
        self.btn_visualizeVol.pack(anchor=tk.S, padx=10, pady=30)

    # Control graphic example button (specifying image path)
    def btnGraphicExample(self, index):

        # Open pop up window
        graphicWin = tk.Toplevel(self)

        # Set window title
        if index == RoadTabConstants.LINE:
            graphicWin.title("Line Source Geometry")
            imgPath = RoadTabConstants.lineGrapPath

        if index == RoadTabConstants.AREA:
            graphicWin.title("AREA Source Geometry")
            imgPath = RoadTabConstants.areaGrapPath

        if index == RoadTabConstants.VOLUME:
            graphicWin.title("VOLUME Source Geometry")
            imgPath = RoadTabConstants.volGrapPath

        img_label = tk.Label(graphicWin, bg='black')
        img_label.image = tk.PhotoImage(file=imgPath)
        img_label['image'] = img_label.image

        img_label.pack()

        center_tk_window.center_on_screen(graphicWin)

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
        i = 0
        for col in lst:
            frame = tk.Frame(colWin)
            frame.pack(anchor=tk.W)

            c_0 = col[0].translate("[]")
            c_1 = col[1].translate("[]")

            tk.Label(frame, text=c_0, font=(None, 13, 'bold'), fg=col[2]).grid(sticky=tk.W, row=i, column=0)
            tk.Label(frame, text=c_1, font=self.label_font, fg=col[2]).grid(sticky=tk.W, row=i, column=1)

            i += 1

        center_tk_window.center_on_screen(colWin)

    # Control Generate button
    def btnGenerate(self, index):

        # Check if GIS data is imported
        if Data.rd_list is None:
            tk.messagebox.showerror('Error', 'Covert GIS first in Data Tab')
            return

        # Line
        if index == RoadTabConstants.LINE:
            progressbar = Progressbar("Processing", "Generating geometry of Line source...")
            thread_generate = threading.Thread(name="genLINE", target=self.generateLINE)
            thread_generate.start()

        # Area
        if index == RoadTabConstants.AREA:
            progressbar = Progressbar("Processing", "Generating geometry of AREA source...")
            thread_generate = threading.Thread(name="genAREA", target=self.generateAREA)
            thread_generate.start()

            # self.generateAREA()

        # Volume
        if index == RoadTabConstants.VOLUME:

            # If the maxsize value is null
            if self.txt_maxsize_var.get() == "":
                tk.messagebox.showerror('Error', "No max size input")
                return
            else:
                # Transform maxsize var to float
                try:
                    maxsize = float(self.txt_maxsize_var.get())
                except ValueError:
                    tk.messagebox.showerror('Error', "Max size should be number")
                    return

                if maxsize < 0:
                    tk.messagebox.showerror('Error', "Max size should be nonnegative number")
                    return
                elif maxsize > 8 or maxsize < 1:
                    Msg_shoulder = tk.messagebox.askquestion('Error',
                                                             "Maz Size should be any flow larger than 1 m," +
                                                             "\n and recommended to be no larger than 8 m. " +
                                                             "\n Do you want to proceed?")

                    # Yes is selected to proceed
                    if Msg_shoulder == 'no':
                        return

            progressbar = Progressbar("Processing", "Generating geometry of VOLUME source...")

            Data.maxsize_var = maxsize

            thread_generate = threading.Thread(name="genVOLUME", target=self.generateVOLUME)
            thread_generate.start()

            # self.generateVOLUME()

        def checkGenerateThread():
            if thread_generate.is_alive():
                self.master.master.after(1000, checkGenerateThread)
            else:
                progressbar.close()

        checkGenerateThread()

    # Generate LINE
    def generateLINE(self):
        # Generate LINE.csv (Argument: converted GIS data, Road ID column, Road Type column)
        generateLINE(Data)

    # Generate AREA
    def generateAREA(self):

        generateAREA(Data.rd_list, Data.output_path, Data.roadID, Data.roadTp)

    # Generate VOLUME
    def generateVOLUME(self):

        generateVOLUME(Data.output_path, Data.rd_list, Data.maxsize_var, Data.roadID)

    # Control Visualize button
    def btnVisualize(self, index):

        # Check if rd_list is imported
        if Data.rd_list is None:
            tk.messagebox.showerror('Error', 'Covert GIS first in Data Tab')
            return

        que = queue.Queue()

        # LINE
        if index == RoadTabConstants.LINE:
            """
            progressbar = Progressbar("Processing", "Generating graph for Line source...")

            que = multiprocessing.Queue()

            thread_visualize = multiprocessing.Process(None, visualizeLINE(Data.output_path, Data.xref_left_m,
                                                                  Data.xref_right_m, Data.yref_lower_m,
                                                                  Data.yref_higher_m), args=(que,))
            thread_visualize.start()
            """

            # Progressbar window
            progressbar = Progressbar("Processing", "Generating graph for Line source...")

            title = RoadTabConstants.visualize_title_LINE

            # Data conversion in another thread
            thread_visualize = threading.Thread(name="conversion",
                                                target=lambda q: q.put(
                                                    visualizeLINE(Data.output_path, Data.xref_left_m,
                                                                  Data.xref_right_m, Data.yref_lower_m,
                                                                  Data.yref_higher_m)), args=(que,))
            thread_visualize.start()

        # AREA
        if index == RoadTabConstants.AREA:
            # Progressbar window
            progressbar = Progressbar("Processing", "Generating graph for AREA source...")

            title = RoadTabConstants.visualize_title_AREA

            # Data conversion in another thread
            thread_visualize = threading.Thread(name="conversion",
                                                target=lambda q: q.put(
                                                    visualizeAREA(Data.output_path, Data.xref_left_m,
                                                                  Data.xref_right_m, Data.yref_lower_m,
                                                                  Data.yref_higher_m)), args=(que,))
            thread_visualize.start()

        # VOLUME
        if index == RoadTabConstants.VOLUME:
            # Progressbar window
            progressbar = Progressbar("Processing", "Generating graph for VOLUME source...")

            title = RoadTabConstants.visualize_title_VOLUME

            # Data conversion in another thread
            thread_visualize = threading.Thread(name="conversion",
                                                target=lambda q: q.put(
                                                    visualizeVOLUME(Data.output_path, Data.rd_list, Data.maxsize_var,
                                                                    Data.xref_left_m, Data.xref_right_m,
                                                                    Data.yref_lower_m,
                                                                    Data.yref_higher_m)), args=(que,))
            thread_visualize.start()

        def checkVisualizeThread():
            if thread_visualize.is_alive():
                self.master.master.after(1000, checkVisualizeThread)
            else:
                self.vizualizeWindow(que.get(), title)
                progressbar.close()

        checkVisualizeThread()

    # Visualize popup window
    def vizualizeWindow(self, fig, title):
        visualizeWindow = tk.Toplevel(self)
        visualizeWindow.title(title)
        canvas = FigureCanvasTkAgg(fig, master=visualizeWindow)
        canvas.get_tk_widget().pack(expand=True, fill="both")
        toolbar = NavigationToolbar2Tk(canvas, visualizeWindow)
        toolbar.update()
        toolbar.pack(anchor=tk.CENTER)
        center_tk_window.center_on_screen(visualizeWindow)


# Receptors tab class
class ReceptorsTab(tk.Frame, Data):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)

        self.label_font = tk.font.Font(size=14)

        # Create Info frame
        # Label-frame for Info frame
        infoFrame = tk.LabelFrame(self, text="Information for receptors", width=300, height=200,
                                  font=(None, 15, "bold"))
        infoFrame.pack(expand=True, side=tk.LEFT, fill='both', padx=10, pady=10)

        self.createInfoFrame(infoFrame)

        # Create Receptor generation frame
        # Label-frame for Receptor generation frame
        self.receptor_gen_frame = tk.LabelFrame(self, text="Input for receptors generation", width=300, height=200,
                                                font=(None, 15, "bold"))
        self.receptor_gen_frame.pack(expand=True, side=tk.LEFT, anchor=tk.N, padx=10, pady=10)

        self.createReceptorGenFrame()

    def createInfoFrame(self, labelframe):
        # Labels
        for str in ReceptorsTabConstants.infoList:
            tk.Label(labelframe, text=str, wraplength=450, font=self.label_font, anchor=tk.W, justify='left').grid(
                sticky=tk.W)

        # Place Receptor graphic example button
        self.button_recExample = ttk.Button(labelframe)
        self.button_recExample.configure(text="Graphic example", padding=10, default=tk.ACTIVE, width=15,
                                         command=lambda: repr(
                                             self.btnGraphicExample(ReceptorsTabConstants.recGrapPath)))
        self.button_recExample.grid(pady=10, sticky=tk.E)

    # Graphic example button control
    def btnGraphicExample(self, imgPath):
        # Open pop up window
        graphicWin = tk.Toplevel(self)
        # center_tk_window.center_on_screen(graphicWin)
        graphicWin.title("Near-road and Gridded Receptors")

        img_label = tk.Label(graphicWin, bg='black')
        img_label.image = tk.PhotoImage(file=imgPath)
        img_label['image'] = img_label.image

        img_label.pack()

    def createReceptorGenFrame(self):
        # Label
        tk.Label(self.receptor_gen_frame, text="Near-road receptors:", wraplength=300, font=self.label_font).grid(row=0,
                                                                                                                  column=0,
                                                                                                                  columnspan=2,
                                                                                                                  sticky=tk.W)
        tk.Label(self.receptor_gen_frame, text="1.1. Import from csv file", wraplength=300, font=self.label_font).grid(
            row=1, column=0,
            sticky=tk.W)

        # Upload csv button
        self.btn_uploadCSV = ttk.Button(self.receptor_gen_frame)
        self.btn_uploadCSV.configure(text="Upload csv", padding=10, default=tk.ACTIVE,
                                     command=self.btnUploadCSV)
        self.btn_uploadCSV.grid(row=1, column=1, sticky=tk.W)

        # Label for upload file path
        self.label_uploadcsv = tk.Label(self.receptor_gen_frame, text="No csv file selected", wraplength=500,
                                        justify=tk.LEFT, font=self.label_font)
        self.label_uploadcsv.grid(row=2, column=0, columnspan=2, sticky=tk.W)

        tk.Label(self.receptor_gen_frame, text="or", wraplength=300, font=self.label_font).grid(row=3, column=0,
                                                                                                columnspan=2)
        tk.Label(self.receptor_gen_frame, text="1.2. Type layers information:", wraplength=300,
                 font=self.label_font).grid(row=4, column=0, columnspan=2, sticky=tk.W)

        # Receptor csv table
        self.sheet = Sheet(None, self.receptor_gen_frame)
        self.sheet.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

        # 2
        tk.Label(self.receptor_gen_frame, text="2. Gridded - interval (SG in m)", wraplength=300,
                 font=self.label_font).grid(row=6, column=0,
                                            columnspan=1,
                                            sticky=tk.W, padx=10, pady=10)

        self.entry_interval = tk.StringVar()
        entry_interval = tk.Entry(self.receptor_gen_frame, textvariable=self.entry_interval, width=10,
                                  font=self.label_font, justify=tk.RIGHT)
        entry_interval.grid(row=6, column=1, sticky=tk.W, padx=10, pady=10)

        # 3
        tk.Label(self.receptor_gen_frame, text="3. Receptor elevations", wraplength=300, font=self.label_font).grid(
            row=7, column=0,
            columnspan=1, sticky=tk.W, padx=10, pady=10)

        self.entry_elevation = tk.StringVar()
        entry_elevation = tk.Entry(self.receptor_gen_frame, textvariable=self.entry_elevation, width=10,
                                   font=self.label_font, justify=tk.RIGHT)
        entry_elevation.grid(row=7, column=1, sticky=tk.W, padx=10, pady=10)

        # Generate and visualize receptors buttons
        self.btn_generateRecp = ttk.Button(self.receptor_gen_frame)
        self.btn_generateRecp.configure(text="Generate receptors", padding=10, default=tk.ACTIVE,
                                        command=self.btnGenerateRec)
        self.btn_generateRecp.grid(row=8, column=0, sticky=tk.W, padx=10, pady=10)

        self.btn_visualizeRecp = ttk.Button(self.receptor_gen_frame)
        self.btn_visualizeRecp.configure(text="Visualize receptors", padding=10, default=tk.ACTIVE,
                                         command=self.btnVisualizeRec)
        self.btn_visualizeRecp.grid(row=8, column=1, sticky=tk.W, padx=10, pady=10)

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
        self.sheet.grid(row=5, column=0, columnspan=2)

    # Generate receptors button control
    def btnGenerateRec(self):

        # Input test values (Remove when not testing!!!)
        # self.setTestValues()

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
                tk.messagebox.showerror('Error', "The receptor dataframe does not have data")
                return

            # Generate receptor
            # Progressbar window
            progressbar = Progressbar("Processing", "Generating near-road and gridded receptors...")

            # Generate emission in another thread
            thread_gen_rec = threading.Thread(name="generate_rec",
                                              target=lambda: self.generateRec(df))
            thread_gen_rec.start()

            def checkGenRecThread():
                if thread_gen_rec.is_alive():
                    self.master.master.after(1000, checkGenRecThread)
                else:
                    progressbar.close()

            checkGenRecThread()

            # self.generateRec(df)

    # Input test values
    def setTestValues(self):
        self.entry_interval = "200"
        self.entry_elevation = "1.5"

    # Check input of Receptor tab
    def checkInput(self):
        errFlag = True
        errMsg = ""

        # Check rd_list is not None
        if Data.rd_list is None:
            errFlag = False
            errMsg += " 1.1. No road data imported"

        # Check interval
        if self.entry_interval.get() == "":
            errFlag = False
            errMsg += "\n 2. No interval value"
        else:
            # Transform value to float
            try:
                interval = float(self.entry_interval.get())

                if interval < 0:
                    errFlag = False
                    errMsg += "\n 2. SG should be positive number (float)."
                else:
                    Data.interval = interval

            except ValueError:
                errFlag = False
                errMsg += "\n 2. SG should be positive number (float)."

        # Check elevations
        if self.entry_elevation.get() == "":
            errFlag = False
            errMsg += "\n 3. No elevation value"
        else:
            # Transform value to float
            try:
                Data.elevation = float(self.entry_elevation.get())

            except ValueError:
                errFlag = False
                errMsg += "\n 3. Receptor elevation should be number (float)."

        if errFlag is not True:
            tk.messagebox.showerror('Error', errMsg)

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

        # Check if rd_list is imported
        if Data.rd_list is None:
            tk.messagebox.showerror('Error', 'Covert GIS first in Data Tab')
            return

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
        center_tk_window.center_on_screen(visualizeWindow)


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
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)

        self.label_font = tk.font.Font(size=14)

        self.vol_df = None  # VOLUME csv data frame
        self.pathVolcsv = None

        # Create Info frame
        # Label-frame for Info frame
        infoFrame = tk.LabelFrame(self, text="Information for emissions", width=300, height=200,
                                  font=(None, 15, "bold"))
        infoFrame.pack(expand=True, side=tk.LEFT, padx=10, pady=10, fill='both', anchor=tk.N)

        self.createInfoFrame(infoFrame)

        # Create Emissions conversion frame
        self.emission_conversion_frame = tk.Frame(self, borderwidth=5, highlightbackground="grey54",
                                                  highlightcolor="grey54", highlightthickness=1, width=300, height=200)
        self.emission_conversion_frame.pack(expand=True, side=tk.LEFT, padx=10, pady=10, anchor=tk.N, fill='both')

        self.createEmissionConvFrame()

    # Create emissions info frame
    def createInfoFrame(self, labelframe):
        # Labels
        for str in EmissionsTabConstants.infoList:
            tk.Label(labelframe, text=str, wraplength=450, font=self.label_font, justify=tk.LEFT).grid(sticky=tk.W)

    # Create Emissions conversion frame
    def createEmissionConvFrame(self):
        # Skip checkbox
        self.bln_skip = tk.BooleanVar()
        self.bln_skip.set(False)
        self.chk_skip = tk.Checkbutton(self.emission_conversion_frame, command=self.controlChkSkip,
                                       variable=self.bln_skip, text="Skip the “Emission Module”", font=self.label_font)
        self.chk_skip.grid(row=0, column=0)

        # 1. Title
        tk.Label(self.emission_conversion_frame, text="Input for Emission Conversion", wraplength=300,
                 font=('', 12, 'bold')).grid(row=1,
                                             column=0,
                                             columnspan=2)
        tk.Label(self.emission_conversion_frame, text="1. Select link emission column and unit in GIS",
                 font=self.label_font).grid(row=2,
                                            column=0,
                                            columnspan=2,
                                            sticky=tk.W)

        # Combo box to choose the emission column
        tk.Label(self.emission_conversion_frame, text="Emission", wraplength=300, font=self.label_font).grid(row=3,
                                                                                                             column=0,
                                                                                                             sticky=tk.W)

        self.combo_emission = ttk.Combobox(self.emission_conversion_frame, font=self.label_font, state='readonly')
        self.combo_emission.grid(row=3, column=1)

        # Emission Unit
        tk.Label(self.emission_conversion_frame, text="Em Unit", wraplength=300, font=self.label_font).grid(row=4,
                                                                                                            column=0,
                                                                                                            rowspan=2,
                                                                                                            sticky=tk.W)

        # Emission Unit checkbox
        self.bln_mile = tk.BooleanVar()
        self.bln_mile.set(False)
        self.chk_mile = tk.Checkbutton(self.emission_conversion_frame, command=lambda: self.controlChkEmUnit(1),
                                       variable=self.bln_mile, text="g/mile/hr", font=self.label_font)
        self.chk_mile.grid(row=4, column=1)

        self.bln_link = tk.BooleanVar()
        self.bln_link.set(False)
        self.chk_link = tk.Checkbutton(self.emission_conversion_frame, command=lambda: self.controlChkEmUnit(2),
                                       variable=self.bln_link, text="g/link/hr", font=self.label_font)
        self.chk_link.grid(row=5, column=1)

        # 2. Title
        tk.Label(self.emission_conversion_frame, text="2. Which source(s) do you want to generate emissions for?",
                 wraplength=300, font=self.label_font).grid(row=6, column=0, columnspan=2,
                                                            sticky=tk.W)

        # AREA
        self.bln_area = tk.BooleanVar()
        self.bln_area.set(False)
        self.chk_area = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_area, text="AREA",
                                       font=self.label_font)
        self.chk_area.grid(row=7, column=0, sticky=tk.W)

        # LINE
        self.bln_line = tk.BooleanVar()
        self.bln_line.set(False)
        self.chk_line = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_line, text="LINE or RLINE",
                                       font=self.label_font)
        self.chk_line.grid(row=8, column=0, sticky=tk.W)

        # RLINEXT
        self.bln_rlinext = tk.BooleanVar()
        self.bln_rlinext.set(False)
        self.chk_rlinext = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_rlinext, text="RLINEXT",
                                          font=self.label_font)
        self.chk_rlinext.grid(row=9, column=0, sticky=tk.W)

        # VOLUME
        self.bln_vol = tk.BooleanVar()
        self.bln_vol.set(False)
        self.chk_vol = tk.Checkbutton(self.emission_conversion_frame, variable=self.bln_vol, text="VOLUME",
                                      font=self.label_font)
        self.chk_vol.grid(row=10, column=0, sticky=tk.W)

        self.button_volume = ttk.Button(self.emission_conversion_frame)
        self.button_volume.configure(text="Upload VOLUME csv", padding=10, default=tk.ACTIVE, command=self.btnVol)
        self.button_volume.grid(row=10, column=1, sticky=tk.W, padx=10, pady=10)

        # Verify input and generate emission button
        self.button_generateEm = ttk.Button(self.emission_conversion_frame)
        self.button_generateEm.configure(text="Verify input and generate emission", padding=10,
                                         default=tk.ACTIVE, command=self.btnEm)
        self.button_generateEm.grid(row=11, column=0, columnspan=2, padx=10, pady=10)

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
        self.pathVolcsv = tk.filedialog.askopenfilename(initialdir=Data.output_path, title="Select file",
                                                        filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
                                                        )

    # Verify input and generate emission button
    def btnEm(self):
        if self.checkInput():

            # Progressbar window
            progressbar = Progressbar("Processing", "Generating AERMOD emissions...")

            # Generate emission in another thread
            thread_gen_em = threading.Thread(name="generate_emission", target=self.generateEmissions)
            thread_gen_em.start()

            def checkThread():
                if thread_gen_em.is_alive():
                    self.master.master.after(1000, checkThread)
                else:
                    progressbar.close()

            checkThread()

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

        self.label_font = tk.font.Font(size=14)

        self.surffile = None
        self.proffile = None

        # Checkbox for Run AERMOD or not
        self.bln_runAERMOD = tk.BooleanVar()
        self.bln_runAERMOD.set(True)
        self.chk_runAERMOD = tk.Checkbutton(self, variable=self.bln_runAERMOD, text="Run AERMOD", font=self.label_font,
                                            command=lambda: self.controlChkRun(0))
        self.chk_runAERMOD.grid(row=0, column=0, sticky=tk.W)
        self.chk_runAERMOD.config(state=tk.DISABLED)

        self.bln_noEmission = tk.BooleanVar()
        self.bln_noEmission.set(False)
        self.chk_noEmission = tk.Checkbutton(self, variable=self.bln_noEmission, font=self.label_font,
                                             command=lambda: self.controlChkRun(1),
                                             text="Emission unavailable, just compile road and receptors input")
        self.chk_noEmission.grid(row=0, column=1, sticky=tk.W)

        # Create Rnning Info frame
        infoFrame = tk.LabelFrame(self, text="Running Information", width=300, height=200,
                                  font=(None, 15, "bold"))
        infoFrame.grid(row=1, column=0, rowspan=5, sticky=tk.W + tk.N)

        self.createRunInfoFrame(infoFrame)

        # Buttons
        self.area_comp = CompilationButtons("AREA", "Run AERMOD\n or compile\n AREA input", master=self)
        self.area_comp.grid(row=1, column=1, sticky=tk.W + tk.E)

        self.vol_comp = CompilationButtons("VOLUME", "Run AERMOD\n or compile\n VOLUME\n input",
                                           master=self)
        self.vol_comp.grid(row=2, column=1, sticky=tk.W + tk.E)

        self.line_comp = CompilationButtons("LINE", "Run AERMOD\n or compile\n LINE input", master=self)
        self.line_comp.grid(row=3, column=1, sticky=tk.W + tk.E)

        self.brline_comp = CompilationButtons("BETA RLINE", "Run AERMOD\n or compile\n RLINE input",
                                              master=self)
        self.brline_comp.grid(row=4, column=1, sticky=tk.W + tk.E)

        self.arline_comp = CompilationButtons("ALPHA RLINEXT", "Run AERMOD\n or compile\n RLINEXT\n input",
                                              master=self)
        self.arline_comp.grid(row=5, column=1, sticky=tk.W + tk.E)

    def createRunInfoFrame(self, frame):
        # POLLITID
        tk.Label(frame, text="POLLITID", wraplength=300, font=self.label_font).grid(row=0, column=0, sticky=tk.W,
                                                                                    padx=10, pady=10)

        self.combo_pollitid = ttk.Combobox(frame, font=self.label_font, state='readonly')
        self.combo_pollitid["values"] = CompilaionTabConstants.pollutidList
        self.combo_pollitid.bind('<FocusIn>', lambda event: avertime_refresh(event))
        self.combo_pollitid.grid(row=0, column=1, padx=10, pady=10)

        # AVERTIME
        tk.Label(frame, text="AVERTIME", wraplength=300, font=self.label_font).grid(row=1, column=0, sticky=tk.W,
                                                                                    padx=10, pady=10)

        self.combo_avertime = ttk.Combobox(frame, font=self.label_font, state='readonly')
        self.combo_avertime.grid(row=1, column=1, padx=10, pady=10)

        # Refresh AVERTIME Menu
        def avertime_refresh(event):
            self.combo_avertime["values"] = CompilaionTabConstants.avertimeMenu.get(self.combo_pollitid.get())

        # URBANOPT
        tk.Label(frame, text="URBANOPT", wraplength=300, font=self.label_font).grid(row=2, column=0, sticky=tk.W,
                                                                                    padx=10, pady=10)

        self.txt_urbanopt_var = tk.StringVar()
        self.txt_urbanopt_var.set('200000')
        self.txt_urbanopt = tk.Entry(frame, textvariable=self.txt_urbanopt_var, width=10, font=self.label_font,
                                     justify=tk.RIGHT)
        self.txt_urbanopt.grid(row=2, column=1, padx=10, pady=10)

        # FLAGPOLE
        tk.Label(frame, text="FLAGPOLE", wraplength=300, font=self.label_font).grid(row=3, column=0, sticky=tk.W,
                                                                                    padx=10, pady=10)

        self.txt_flagpole_var = tk.StringVar()
        self.txt_flagpole_var.set('1.5')
        self.txt_flagpole = tk.Entry(frame, textvariable=self.txt_flagpole_var, width=10, font=self.label_font,
                                     justify=tk.RIGHT)
        self.txt_flagpole.grid(row=3, column=1, padx=10, pady=10)

        # SURFILE
        tk.Label(frame, text="SURFILE", wraplength=300, font=self.label_font).grid(row=4, column=0, sticky=tk.W,
                                                                                   padx=10, pady=10)

        # SURFILE upload button control
        def btnSurfile():
            self.surffile = tk.filedialog.askopenfilename(initialdir=os.getcwd(), title="Select file",
                                                          filetypes=(("SFC files", "*.SFC"), ("all files", "*.*"))
                                                          )

            self.label_surfile_var.set(self.surffile)

        self.btn_surfile = ttk.Button(frame)
        self.btn_surfile.configure(text="Upload", padding=5, default=tk.ACTIVE,
                                   command=btnSurfile)
        self.btn_surfile.grid(row=4, column=1, sticky=tk.S)

        self.label_surfile_var = tk.StringVar()
        self.label_surfile = tk.Label(frame, textvariable=self.label_surfile_var, wraplength=300, font=self.label_font,
                                      justify=tk.LEFT)
        self.label_surfile.grid(row=5, column=0, columnspan=2, sticky=tk.W)

        # PROFFILE
        tk.Label(frame, text="PROFFILE", wraplength=300, font=self.label_font).grid(row=6, column=0, sticky=tk.W,
                                                                                    padx=10, pady=10)

        # PROFFILE upload button control
        def btnProffile():
            self.proffile = tk.filedialog.askopenfilename(initialdir=os.getcwd(), title="Select file",
                                                          filetypes=(("PFL files", "*.PFL"), ("all files", "*.*"))
                                                          )

            self.label_proffile_var.set(self.proffile)

        self.btn_proffile = ttk.Button(frame)
        self.btn_proffile.configure(text="Upload", padding=5, default=tk.ACTIVE,
                                    command=btnProffile)
        self.btn_proffile.grid(row=6, column=1, sticky=tk.S)

        self.label_proffile_var = tk.StringVar()
        self.label_proffile = tk.Label(frame, textvariable=self.label_proffile_var, wraplength=300,
                                       font=self.label_font, justify=tk.LEFT)
        self.label_proffile.grid(row=7, column=0, columnspan=2, sticky=tk.W)

    # Control Emission unavailable check button
    def controlChkRun(self, index):
        # If true, disable all features
        if index == 0:
            self.chk_runAERMOD.config(state=tk.DISABLED)
            self.chk_noEmission.config(state=tk.NORMAL)
            self.bln_runAERMOD.set(True)
            self.bln_noEmission.set(False)

            self.area_comp.btn_UploadEm["state"] = tk.NORMAL
            self.vol_comp.btn_UploadEm["state"] = tk.NORMAL
            self.line_comp.btn_UploadEm["state"] = tk.NORMAL
            self.brline_comp.btn_UploadEm["state"] = tk.NORMAL
            self.arline_comp.btn_UploadEm["state"] = tk.NORMAL

        if index == 1:
            self.chk_runAERMOD.config(state=tk.NORMAL)
            self.chk_noEmission.config(state=tk.DISABLED)
            self.bln_runAERMOD.set(False)
            self.bln_noEmission.set(True)

            self.area_comp.btn_UploadEm["state"] = tk.DISABLED
            self.vol_comp.btn_UploadEm["state"] = tk.DISABLED
            self.line_comp.btn_UploadEm["state"] = tk.DISABLED
            self.brline_comp.btn_UploadEm["state"] = tk.DISABLED
            self.arline_comp.btn_UploadEm["state"] = tk.DISABLED


# compilation Button frame class
class CompilationButtons(tk.Frame, Data):
    def __init__(self, title, btn_label, master=None):
        super().__init__(master)
        self.label_font = tk.font.Font(size=12)

        self.title = title

        self.rec_path = None
        self.road_path = None
        self.em_path = None

        self.config(highlightbackground="black", highlightthickness=1)

        # Title label
        tk.Label(self, text=title, width=15, wraplength=300, font=self.label_font).grid(
            row=0,
            column=0,
            rowspan=3,
            sticky=tk.W)

        road = getattr(self, 'btn_UploadRoad')
        rec = getattr(self, 'btn_UploadRec')
        em = getattr(self, 'btn_UploadEm')
        run = getattr(self, 'btn_runAERMOD')

        # Buttons
        self.btn_UploadRoad = ttk.Button(self)
        self.btn_UploadRoad.configure(text="Upload road", default=tk.ACTIVE, width=20,
                                      command=road)
        # command=self.btn_UploadRoad)
        self.btn_UploadRoad.grid(row=0, column=1)

        self.btn_UploadRec = ttk.Button(self)
        self.btn_UploadRec.configure(text="Upload receptors", default=tk.ACTIVE, width=20,
                                     command=rec)
        # command=self.btn_UploadRec)
        self.btn_UploadRec.grid(row=1, column=1)

        self.btn_UploadEm = ttk.Button(self)
        self.btn_UploadEm.configure(text="Upload emissions", default=tk.ACTIVE, width=20,
                                    command=em)
        # command=self.btn_UploadEm)
        self.btn_UploadEm.grid(row=2, column=1)

        # csv labels
        self.label_road_var = tk.StringVar()
        self.label_road = tk.Label(self, textvariable=self.label_road_var, width=20, wraplength=90,
                                   font=self.label_font)
        self.label_road.grid(row=0, column=2, sticky=tk.W)

        self.label_rec_var = tk.StringVar()
        self.label_rec = tk.Label(self, textvariable=self.label_rec_var, width=20, wraplength=90, font=self.label_font)
        self.label_rec.grid(row=1, column=2, sticky=tk.W)

        self.label_em_var = tk.StringVar()
        self.label_em = tk.Label(self, textvariable=self.label_em_var, width=20, wraplength=90, font=self.label_font)
        self.label_em.grid(row=2, column=2, sticky=tk.W)

        # Button
        self.btn_runAERMOD = ttk.Button(self)
        self.btn_runAERMOD.configure(text=btn_label, padding=10,
                                     default=tk.ACTIVE, command=run)
        self.btn_runAERMOD.grid(row=0, column=3, rowspan=3)

    # Upload road button control
    def btn_UploadRoad(self):

        self.road_path = tk.filedialog.askopenfilename(initialdir=Data.output_path, title="Select file",
                                                       filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
                                                       )

        self.label_road_var.set(os.path.basename(self.road_path))

    # Upload receptors control
    def btn_UploadRec(self):
        self.rec_path = tk.filedialog.askopenfilename(initialdir=Data.output_path, title="Select file",
                                                      filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
                                                      )

        self.label_rec_var.set(os.path.basename(self.rec_path))

    # Upload emissions control
    def btn_UploadEm(self):
        self.em_path = tk.filedialog.askopenfilename(initialdir=Data.output_path, title="Select file",
                                                     filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
                                                     )

        self.label_em_var.set(os.path.basename(self.em_path))

    # Run AERMOD or compile
    def btn_runAERMOD(self):

        # Get values from running information frame
        run_AERMOD = self.master.bln_runAERMOD
        POLLUTID = self.master.combo_pollitid.get()
        AVERTIME = self.master.combo_avertime.get()
        URBANOPT = self.master.txt_urbanopt_var.get()
        FLAGPOLE = self.master.txt_flagpole_var.get()

        SURFFILE = self.master.surffile
        PROFFILE = self.master.proffile

        # Input value check
        if self.checkInput(run_AERMOD, POLLUTID, AVERTIME, URBANOPT, FLAGPOLE, SURFFILE, PROFFILE) is not True:
            return

        # Run AERMOD: AREA input
        if self.title == "AREA":
            print(self.title)

            progressbar = Progressbar("Processing", "Running AERMOD or compiling AERMOD AREA")

            # Run AERMOD: AREA thread
            thread_aermod = threading.Thread(name="aermod_area",
                                             target=lambda: runAERMOD_AREA(self.rec_path, self.road_path, run_AERMOD,
                                                                           self.em_path,
                                                                           AVERTIME, URBANOPT, FLAGPOLE, POLLUTID,
                                                                           SURFFILE, PROFFILE, Data.output_path))
            thread_aermod.start()

            # runAERMOD_AREA(self.rec_path, self.road_path, run_AERMOD, self.em_path, AVERTIME, URBANOPT, FLAGPOLE,
            #               POLLUTID, SURFFILE, PROFFILE, Data.output_path)

        # Run AERMOD: VOLUME
        if self.title == "VOLUME":
            print(self.title)

            progressbar = Progressbar("Processing", "Running AERMOD or compiling AERMOD VOLUME")

            # Run AERMOD: VOLUME thread
            thread_aermod = threading.Thread(name="aermod_vol",
                                             target=lambda: runAERMOD_VOLUME(Data.output_path, self.rec_path,
                                                                             self.road_path, run_AERMOD,
                                                                             self.em_path, AVERTIME, URBANOPT, FLAGPOLE,
                                                                             POLLUTID, SURFFILE, PROFFILE))
            thread_aermod.start()

            # runAERMOD_VOLUME(Data.output_path, self.rec_path, self.road_path, run_AERMOD, self.em_path, AVERTIME,
            #                 URBANOPT, FLAGPOLE,
            #                 POLLUTID, SURFFILE, PROFFILE)

        # Run AERMOD: LINE
        if self.title == "LINE":
            print(self.title)

            progressbar = Progressbar("Processing", "Running AERMOD or compiling AERMOD LINE")

            # Run AERMOD: VOLUME thread
            thread_aermod = threading.Thread(name="aermod_line",
                                             target=lambda: runAERMOD_LINE(Data.output_path, self.rec_path,
                                                                           self.road_path,
                                                                           run_AERMOD, self.em_path, AVERTIME, URBANOPT,
                                                                           FLAGPOLE, POLLUTID, SURFFILE, PROFFILE))
            thread_aermod.start()

            # runAERMOD_LINE(Data.output_path, self.rec_path, self.road_path, run_AERMOD, self.em_path, AVERTIME,
            #               URBANOPT, FLAGPOLE,
            #               POLLUTID, SURFFILE, PROFFILE)

        # Run AERMOD: BETA RLINE
        if self.title == "BETA RLINE":
            print(self.title)

            progressbar = Progressbar("Processing", "Running AERMOD or compiling AERMOD RLINE")

            # Run AERMOD: VOLUME thread
            thread_aermod = threading.Thread(name="aermod_rline",
                                             target=lambda: runAERMOD_B_RLINE(Data.output_path, self.rec_path,
                                                                              self.road_path, run_AERMOD, self.em_path,
                                                                              AVERTIME, URBANOPT, FLAGPOLE, POLLUTID,
                                                                              SURFFILE, PROFFILE))
            thread_aermod.start()

            # runAERMOD_B_RLINE(Data.output_path, self.rec_path, self.road_path, run_AERMOD, self.em_path, AVERTIME,
            #                  URBANOPT, FLAGPOLE,
            #                  POLLUTID, SURFFILE, PROFFILE)

        # Run AERMOD: ALPHA RLINEXT
        if self.title == "ALPHA RLINEXT":
            print(self.title)

            progressbar = Progressbar("Processing", "Running AERMOD or compiling AERMOD RLINEXT")

            # Run AERMOD: VOLUME thread
            thread_aermod = threading.Thread(name="aermod_rlinext",
                                             target=lambda: runAERMOD_A_RLINEXT(Data.output_path, self.rec_path,
                                                                                self.road_path,
                                                                                run_AERMOD, self.em_path, AVERTIME,
                                                                                URBANOPT,
                                                                                FLAGPOLE, POLLUTID, SURFFILE, PROFFILE))
            thread_aermod.start()

            # runAERMOD_A_RLINEXT(Data.output_path, self.rec_path, self.road_path, run_AERMOD, self.em_path, AVERTIME,
            #                    URBANOPT, FLAGPOLE,
            #                    POLLUTID, SURFFILE, PROFFILE)

        def checkAERMODThread():
            if thread_aermod.is_alive():
                self.master.master.after(1000, checkAERMODThread)
            else:
                progressbar.close()

        checkAERMODThread()

    # Check input value
    def checkInput(self, run_AERMOD, POLLUTID, AVERTIME, URBANOPT, FLAGPOLE, SURFFILE, PROFFILE):

        # Error Flag
        errFlag = True

        # Error message string
        errMsg = ""

        # Running information input check
        if POLLUTID == "" or AVERTIME == "":
            errMsg += "\n No POLLUTID or AVERTIME is selected"
            errFlag = False

        if URBANOPT == "":
            errMsg += "\n No URBANOPT value"
            errFlag = False
        else:
            # URBANOPT is not integer
            try:
                int(URBANOPT)
            except ValueError:
                errMsg += "\n URBANOPT should be a positive integer. "
                errFlag = False

        if FLAGPOLE == "":
            errMsg += "\n No FLAGPOLE value"
            errFlag = False
        else:
            # FLAGPOLE is not positive float
            try:
                flag = float(FLAGPOLE)
                if flag < 0:
                    errMsg += "\n FLAGPOLE should be a positive number (float). "
                    errFlag = False
            except ValueError:
                errMsg += "\n FLAGPOLE should be a positive number (float). "
                errFlag = False

        if SURFFILE is None or SURFFILE == "":
            errMsg += "\n No SURFFILE file is selected"
            errFlag = False

        if PROFFILE is None or PROFFILE == "":
            errMsg += "\n No PROFFILE file is selected"
            errFlag = False

        # Uploaded file check
        if self.road_path is None or self.road_path == "":
            errMsg += "\n No road file is selected"
            errFlag = False

        if self.rec_path is None or self.rec_path == "":
            errMsg += "\n No receptors file is selected"
            errFlag = False

        if run_AERMOD.get():
            if self.em_path is None or self.em_path == "":
                errMsg += "\n No emissions file is selected"
                errFlag = False

        if errFlag is not True:
            tk.messagebox.showerror('Error', errMsg)

        return errFlag


# Results tab class
class ResultsTab(tk.Frame, Data):

    def __init__(self, master=None):
        super().__init__(master)
        self.grid(row=0, column=0)

        self.maxVal = None
        self.con_df = None

        self.label_font = tk.font.Font(size=12)

        tk.Label(self, text="Upload an AERMOD ‘.out’ file to organize and visualize", font=self.label_font).grid(row=0,
                                                                                                                 column=0,
                                                                                                                 sticky=tk.W,
                                                                                                                 padx=10,
                                                                                                                 pady=10)

        # Upload AERMOD .out file button
        self.btnAERMODout = ttk.Button(self)
        self.btnAERMODout.configure(text="Upload AERMOD ‘.out’ file\n and Organize into CSV", default=tk.ACTIVE,
                                    padding=10, width=35,
                                    command=self.btn_uploadAERMODout)
        self.btnAERMODout.grid(row=1, column=0, padx=10, pady=10)

        self.label_AERMODout_var = tk.StringVar()
        self.label_AERMODout = tk.Label(self, textvariable=self.label_AERMODout_var, width=80, font=self.label_font,
                                        anchor=tk.W, justify='left', wraplength=500)
        self.label_AERMODout.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)

        # maxVal and minVal input
        frame = tk.LabelFrame(self, text="Concentration value", width=100, font=(None, 15, "bold"))
        frame.grid(row=2, column=0, padx=10, pady=10)

        tk.Label(frame, text="Visualize concentration value in range of", font=self.label_font).grid(row=0, column=0,
                                                                                                     columnspan=3,
                                                                                                     padx=10, pady=5)

        # minVal textbox
        self.txt_minVal_var = tk.StringVar()
        self.txt_minVal_var.set(0)
        self.txt_minVal = tk.Entry(frame, textvariable=self.txt_minVal_var, width=10,
                                   font=self.label_font, justify=tk.RIGHT)
        self.txt_minVal.grid(row=1, column=0, padx=10, pady=10)

        tk.Label(frame, text="to", font=self.label_font, width=5).grid(row=1, column=1, padx=10, pady=5)

        # maxVal textbox
        self.txt_maxVal_var = tk.StringVar()
        self.txt_maxVal = tk.Entry(frame, textvariable=self.txt_maxVal_var, width=10,
                                   font=self.label_font, justify=tk.RIGHT)
        self.txt_maxVal.grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)

        # Organize button
        self.btnOrganize = ttk.Button(self)
        self.btnOrganize.configure(text="Visualize concentration profile", default=tk.ACTIVE, padding=10,
                                   width=35,
                                   command=self.btn_organize)
        self.btnOrganize.grid(row=3, column=0, padx=10, pady=10)

        # Question button
        self.btnQuestions = ttk.Button(self)
        self.btnQuestions.configure(text="Questions?", default=tk.ACTIVE, padding=10,
                                    width=35,
                                    command=self.btn_questions)
        self.btnQuestions.grid(row=4, column=0, sticky=tk.S, padx=10, pady=10)

    # Upload AERMOD .out control
    def btn_uploadAERMODout(self):

        self.out_path = tk.filedialog.askopenfilename(initialdir=Data.output_path, title="Select file",
                                                      filetypes=(("out files", "*.out"), ("all files", "*.*"))
                                                      )

        if os.path.exists(self.out_path):

            # Progressbar window
            progressbar = Progressbar("Processing", "Organizing AERMOD output into CSV file...")

            # Clear minVal and maxVal
            self.txt_minVal_var.set(0)
            self.txt_maxVal_var.set("")

            # Set the out file path to the label
            self.label_AERMODout_var.set(self.out_path)

            # Upload AERMOD .out and Organize into CSV in another thread
            que = queue.Queue()

            thread_aermod_out = threading.Thread(name="aermod_out",
                                                 target=lambda q: q.put(
                                                     generateResults(self.out_path, Data.output_path)), args=(que,))
            thread_aermod_out.start()

            def checkThreadOut():
                if thread_aermod_out.is_alive():
                    self.master.master.after(1000, checkThreadOut)
                else:
                    # Thread finished
                    result = que.get()
                    maxVal = result[0]
                    self.con_df = result[1]
                    self.txt_maxVal_var.set(maxVal)
                    progressbar.close()

            checkThreadOut()

            # maxVal, self.con_df = generateResults(self.out_path, Data.output_path)

            # Set max val in the text box

    # Organize button control
    def btn_organize(self):
        if self.out_path is None or self.out_path == "":
            tk.messagebox.showerror('Error', "out file is not selected")
            return

        if self.txt_minVal_var == "" or self.txt_maxVal_var == "":
            tk.messagebox.showerror('Error', "Max or Min Value is missed")
            return

        try:
            minVal = float(self.txt_minVal_var.get())
            maxVal = float(self.txt_maxVal_var.get())
        except ValueError:
            tk.messagebox.showerror('Error', "Concentration values should be numbers.")
            return

        if minVal > maxVal:
            tk.messagebox.showerror('Error', "The range values are invalid")
            return

        # Progressbar window
        progressbar = Progressbar("Processing", "Visualizing concentration profile...")

        # Visualize concentration profile in another thread
        que = queue.Queue()

        thread_visualizeConc = threading.Thread(name="visualize_concentration",
                                                target=lambda q: q.put(
                                                    visualizeResults(minVal, maxVal, self.con_df, self.out_path,
                                                                     Data.rd_list, Data.xref_left_m, Data.xref_right_m,
                                                                     Data.yref_lower_m, Data.yref_higher_m)),
                                                args=(que,))
        thread_visualizeConc.start()

        # fig = visualizeResults(minVal, maxVal, self.con_df, self.out_path, Data.rd_list, Data.xref_left_m,
        #                       Data.xref_right_m, Data.yref_lower_m, Data.yref_higher_m)

        def checkConcThread():
            if thread_visualizeConc.is_alive():
                self.master.master.after(1000, checkConcThread)
            else:
                # Thread finished. Open visualizing window

                fig = que.get()
                popupWindow = tk.Toplevel(self)
                center_tk_window.center_on_screen(popupWindow)
                popupWindow.title("Concentration Profile Visualization")
                canvas = FigureCanvasTkAgg(fig, master=popupWindow)
                canvas.get_tk_widget().pack(expand=True, fill="both")
                toolbar = NavigationToolbar2Tk(canvas, popupWindow)
                toolbar.update()
                toolbar.pack(anchor=tk.CENTER)

                progressbar.close()

        checkConcThread()

    # Questions button control
    def btn_questions(self):
        popupWindow = tk.Toplevel(self)
        popupWindow.title("Concentration Profile Visualization")
        lst = ResultsTabConstants.questions

        # Place labels of the columns in pop up window
        for col in lst:
            label = tk.Label(popupWindow, text=col, font=self.label_font, wraplength=300, anchor=tk.W, justify=tk.LEFT)
            label.grid(sticky=tk.W)

        center_tk_window.center_on_screen(popupWindow)


# Main window class
class MainWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Main window
        self.title("GTA (GIS-To-AERMOD) Tool")
        self.geometry("1100x750")

        # Show window in the center of the screen
        center_tk_window.center_on_screen(self)

        style = ttk.Style()
        style.configure('.', font=('', 14, 'bold'))
        style.map(".")

        self.nb = ttk.Notebook(self, width=800, height=600)

        # Add Data tab
        self.data_tab = DataTab(master=self.nb)
        self.nb.add(self.data_tab, text=' Data ', padding=5)

        # Add Road tab
        self.road_tab = RoadTab(master=self.nb)
        self.nb.add(self.road_tab, text=' Road ', padding=5)

        # Add Receptors tab
        self.receptors_tab = ReceptorsTab(master=self.nb)
        self.nb.add(self.receptors_tab, text=' Receptors ', padding=5)

        # Add Emissions tab
        self.emissions_tab = EmissionsTab(master=self.nb)
        self.nb.add(self.emissions_tab, text=' Emissions ', padding=5)

        # Add Compilation tab
        self.compilation_tab = CompilationTab(master=self.nb)
        self.nb.add(self.compilation_tab, text=' Compilation ', padding=5)

        # Add Results tab
        self.results_tab = ResultsTab(master=self.nb)
        self.nb.add(self.results_tab, text='Results', padding=5)

        self.nb.pack(expand=True, fill="both")

        # Closing control
        def on_closing():
            if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
                self.destroy()

        self.protocol("WM_DELETE_WINDOW", on_closing)

# def main():
#    root = MainWindow()

#    root.mainloop()


# if __name__ == "__main__":
#    main()
