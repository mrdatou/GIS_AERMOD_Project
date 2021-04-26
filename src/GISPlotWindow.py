import tkinter as tk
from tkinter import ttk

import geopandas as gpd
from matplotlib import pyplot
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import RectangleSelector


# Locate boundary and reference point window's class
class GISplotWindow(tk.Frame):
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

        graph_frame = tk.Frame(self.master)
        graph_frame.pack(expand=True, side=tk.LEFT, anchor=tk.NW, fill=tk.BOTH)

        self.canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, anchor=tk.NW, fill=tk.BOTH)

        # Control rectangle info
        def line_select_callback(eclick, erelease):
            # Set Rectangle coordinates
            if self.btnDrawBoundaryFlag:
                # Sort boundary's coords
                self.xLeft, self.xRight = sorted([eclick.xdata, erelease.xdata])
                self.yLow, self.yHigh = sorted([eclick.ydata, erelease.ydata])

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
                self.xRef = event.xdata
                self.yRef = event.ydata
                fig.canvas.draw_idle()

        mouseButtonPressed.RS = RectangleSelector(ax, line_select_callback,
                                                  drawtype='box', button=[1],
                                                  minspanx=5, minspany=5, spancoords='pixels',
                                                  interactive=True)

        toolbar = NavigationToolbar2Tk(self.canvas, graph_frame)
        toolbar.update()
        toolbar.pack(expand=True)

        self.canvas.mpl_connect('button_press_event', mouseButtonPressed)
        self.canvas.mpl_connect("button_release_event", self.release)

    # Create buttons on the right side
    def createButtons(self):
        # Draw Boundary Button
        btn_frame = tk.Frame(self.master)
        btn_frame.pack(expand=True, side=tk.LEFT, fill=tk.BOTH)

        button_drawBoundary = ttk.Button(btn_frame)
        button_drawBoundary.configure(text="Draw boundary", padding=10, default=tk.ACTIVE, command=self.btnDrawBoundary)
        button_drawBoundary.grid(row=0, column=0, pady=50, sticky=tk.W+tk.E)

        # Locate reference point button
        button_refPoint = ttk.Button(btn_frame)
        button_refPoint.configure(text="Draw reference point", padding=10, default=tk.ACTIVE,
                                  command=self.btnLocateRefPoint)
        button_refPoint.grid(row=1, column=0, pady=50, sticky=tk.N+tk.W+tk.E)

        # Confirm & close button
        button_confirmClose = ttk.Button(btn_frame)
        button_confirmClose.configure(text="Confirm & close", padding=10, default=tk.ACTIVE,
                                      command=self.btnConfirmClose)
        button_confirmClose.grid(row=2, column=0, rowspan=3, pady=50, sticky=tk.S+tk.W+tk.E)

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
        # Pass boundary and reference point values to the Data tab
        self.master.master.txt_xRef_var.set(str(self.xRef))
        self.master.master.txt_yRef_var.set(str(self.yRef))

        self.master.master.txt_yHigh_var.set(str(self.yHigh))
        self.master.master.txt_yLow_var.set(str(self.yLow))
        self.master.master.txt_xLeft_var.set(str(self.xLeft))
        self.master.master.txt_xRight_var.set(str(self.xRight))

        # Close this window
        self.master.destroy()

    # If mouse button is released
    def release(self, event):
        # Set Draw boundary button inactive
        self.btnDrawBoundaryFlag = False
        self.btnRefPointFlag = False
