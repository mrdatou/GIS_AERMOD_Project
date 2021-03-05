import tkinter as tk
from tkinter import ttk

import geopandas as gpd
from matplotlib import pyplot
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import RectangleSelector


class MapWindow(tk.Frame):
    def __init__(self, rd_list, master=None):
        super().__init__(master)
        self.master = master

        # GIS data
        self.rd_list = rd_list

        # Buttons' flags are False initially
        self.btnDrawBoundaryFlag = False
        self.btnRefPointFlag = False

        # Initialize reference point
        self.xb1 = None
        self.yb1 = None

        # Create canvas
        self.createMapPlot()

        # Place buttons on the right side
        self.createButtons()

    # Create Figure of GIS data plot
    def createMapPlot(self):
        fig = pyplot.figure()
        ax = fig.add_subplot()
        point, = ax.plot([], [], marker="o", color="crimson")
        self.rd_list.plot(ax=ax)

        self.canvas = FigureCanvasTkAgg(fig, master=self.master)
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=4, sticky=tk.N + tk.S + tk.W + tk.E)

        # Control rectangle info
        def line_select_callback(eclick, erelease):
            # Set Rectangle coordinates
            if self.btnDrawBoundaryFlag:
                self.xb1, self.yb1 = eclick.xdata, eclick.ydata
                self.xb2, self.yb2 = erelease.xdata, erelease.ydata

            # If Locate reference button pressed
            if self.btnRefPointFlag:
                pass

        # Control toggle
        def mouseButtonPressed(event):

            # If Draw boundary button pressed
            if self.btnDrawBoundaryFlag:
                mouseButtonPressed.RS.set_active(True)
            else:
                mouseButtonPressed.RS.set_active(False)

            if self.btnRefPointFlag:
                point.set_data([event.xdata], [event.ydata])
                fig.canvas.draw_idle()

        mouseButtonPressed.RS = RectangleSelector(ax, line_select_callback,
                                                  drawtype='box', button=[1],
                                                  minspanx=5, minspany=5, spancoords='pixels',
                                                  interactive=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self.master, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=4, column=0)

        self.canvas.mpl_connect('button_press_event', mouseButtonPressed)
        # self.canvas.mpl_connect("button_press_event", self.press)
        # self.canvas.mpl_connect("motion_notify_event", self.drag)
        self.canvas.mpl_connect("button_release_event", self.release)

    # Create buttons on the right side
    def createButtons(self):
        # Draw Boundary Button
        button_drawBoundary = ttk.Button(self.master)
        button_drawBoundary.configure(text="Draw boundary", padding=10, default=tk.ACTIVE, command=self.btnDrawBoundary)
        button_drawBoundary.grid(row=0, column=1, sticky=tk.W + tk.E)

        # Locate reference point button
        button_refPoint = ttk.Button(self.master)
        button_refPoint.configure(text="Draw reference point", padding=10, default=tk.ACTIVE,
                                  command=self.btnLocateRefPoint)
        button_refPoint.grid(row=1, column=1)

        # Confirm & close button
        button_confirmClose = ttk.Button(self.master)
        button_confirmClose.configure(text="Confirm & close", padding=10, default=tk.ACTIVE,
                                      command=self.btnConfirmClose)
        button_confirmClose.grid(row=4, column=1, sticky=tk.W + tk.E)

    # Define Draw boundary button function
    def btnDrawBoundary(self):
        # Only Draw boundary button is activated
        self.btnDrawBoundaryFlag = True
        self.btnRefPointFlag = False

    # Define Locate reference point button
    def btnLocateRefPoint(self):
        # Only Locate reference point button is activated
        self.btnRefPointFlag = True
        self.btnDrawBoundaryFlag = False

    # Define Confirm and Close function
    def btnConfirmClose(self):
        pass

    # 　If mouse button pressed
    def press(self, event):

        # Dose not allow cursor outside the plot
        if (event.xdata is None) or (event.ydata is None):
            return

        # If draw boundary button clicked, allow user to draw boundary
        if self.btnDrawBoundaryFlag:
            self.setPressCoordBoundary(event)

        # If Locate reference point button is activated
        if self.btnRefPointFlag:
            self.setReferencePoint(event)

    # Set the first coordinate of drawing boundary
    def setPressCoordBoundary(self, event):
        # Get the coordinate
        self.xb1 = event.xdata
        self.yb1 = event.ydata

        print("First Coord: " + str(self.xb1))

    # Set reference Point when mouse button is pressed
    def setReferencePoint(self, event):

        # Get the coordinates
        self.xRef = event.xdata
        self.yRef = event.ydata

        # Set reference point flag False
        self.btnRefPointFlag = False

    # If mouse drag on the plot
    def drag(self, event):

        # Dose not allow cursor outside the plot
        if (event.xdata is None) or (event.ydata is None):
            return

        # Does not allow if xb1 and yb1 is None
        if (self.xb1 is None) or (self.yb1 is None):
            return

        # Check if Draw boundary button is True. If True, allow rectangle
        if self.btnDrawBoundaryFlag:
            '''Function of drawing rectangle on the plot'''
            # Get the coordinate of the mouse when it is moving
            xb2 = event.xdata
            yb2 = event.ydata

            # Sort the coordinate data to visualize them as boundaries
            self.ix1, self.ix2 = sorted([self.xb1, xb2])
            self.iy1, self.iy2 = sorted([self.yb1, yb2])

    # If mouse button is released
    def release(self, event):
        # Set Draw boundary button inactive
        self.btnDrawBoundaryFlag = False
        self.btnRefPointFlag = False
