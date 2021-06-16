import copy
import math
import uuid
from tkinter import font, ttk, messagebox
import tkinter as tk

import center_tk_window
import geopandas
import pandas as pd
import tksheet
from shapely.geometry import Point, LineString

from canvas import CanvasImage


class Polygons(CanvasImage):
    """ Class of Polygons. Inherit CanvasImage class """

    def __init__(self, placeholder, path, roll_size):

        """ Additional attributes for GIS tool"""
        self.label_font = font.Font(size=13)
        self.width_line = 6  # lines width

        self.line_width = {'line': 6,
                           'scale': 3,
                           'ref_line': 1}

        self.color = {'scale': 'yellow',
                      'selected': 'yellow',
                      'draw': 'blue',
                      'back': 'blue',
                      'ref_line': 'white'}

        self.isScale = False
        self.isLocRef = False
        self.isDrawPoly = False

        # Define scale
        self.scale_edge = None
        self.scaleLine = None
        self.scale_var = None

        # Locate reference
        self.reference = None  # Reference point
        self.ref_lines_x = None  # reference points line
        self.ref_lines_y = None  # reference points line
        self.width_ref_line = 1

        # Polyline
        self.count_polyline = 0
        self.poly_dict = {}
        self.poly_sheet_list = []

        # Link ID set
        self.linkID_set = set()

        # Spreadsheet dataframe
        self.road_info = None

        self.placeholder = placeholder
        """ Initialize the Polygons """
        CanvasImage.__init__(self, placeholder, path)  # call __init__ of the CanvasImage class

        # Spread sheet of road polyline info
        # self.sheet = Sheet(None, master=placeholder)
        # Sheet.__init__(self, None, master=placeholder)

        self.canvas.bind('<ButtonPress-1>', self.set_edge)  # set new edge
        self.canvas.bind('<ButtonRelease-3>', lambda event: self.end_draw_polyline())
        self.canvas.bind('<Motion>', self.motion)  # handle mouse motion

        # Polygon parameters
        self.roi = True  # is it a ROI or hole
        self.rect = False  # show / hide rolling window rectangle
        self.roll_size = roll_size  # size of the rolling window

        self.roll_rect = self.canvas.create_rectangle((0, 0, 0, 0), width=self.width_line,
                                                      state=u'hidden')
        self.dash = (1, 1)  # dash pattern
        self.dash_scale = (2, 1)  # dash pattern

        self.tag_curr_edge_start = '1st_edge'  # starting edge of the current polygon
        self.tag_curr_edge = 'edge'  # edges of the polygon
        self.tag_curr_edge_id = 'edge_id'  # part of unique ID of the current edge
        self.tag_roi = 'roi'  # roi tag
        self.tag_hole = 'hole'  # hole tag
        self.tag_const = 'poly'  # constant tag for polygon
        self.tag_poly_line = 'poly_line'  # edge of the polygon
        self.tag_curr_circle = 'circle'  # sticking circle tag for the current polyline
        self.radius_stick = 10  # distance where line sticks to the polygon's staring point
        self.radius_circle = 3  # radius of the sticking circle
        self.edge = None  # current edge of the new polygon
        self.polygon = []  # vertices of the current (drawing, red) polygon
        self.selected_poly = []  # selected polygons
        self.roi_dict = {}  # dictionary of all roi polygons and their coords on the canvas image
        self.hole_dict = {}  # dictionary of all holes and their coordinates on the canvas image

    def set_edge(self, event):

        # Define scale
        if self.isScale:
            if self.set_edge_scaleLine(event):
                self.createScalingWindow(event)

        # Locate reference
        if self.isLocRef:
            self.set_reference(event)

        # Draw polyline
        errMsg = ""
        if self.isDrawPoly:
            if self.scaleLine is None:
                errMsg += "No scale is set.\n"

            if self.reference is None:
                errMsg += "No reference point."

            if errMsg != "":
                messagebox.showwarning('Warning', errMsg)
                return

            self.set_edge_polyline(event)

    # Locate reference point
    def set_reference(self, event):

        # If reference is already selected
        if self.reference is not None:
            self.reference = None
            self.canvas.delete(self.ref_lines_x)
            self.canvas.delete(self.ref_lines_y)

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        self.reference = (x, y)

        # Draw reference
        self.ref_lines_x = self.canvas.create_line(self.reference[0], 0, self.reference[0], self.imwidth * 2,
                                                   width=self.line_width['ref_line'], fill=self.color['ref_line'])
        self.ref_lines_y = self.canvas.create_line(0, self.reference[1], self.imheight * 2, self.reference[1],
                                                   width=self.line_width['ref_line'], fill=self.color['ref_line'])

        self.isLocRef = False

        pass

    def motion(self, event):
        """ Track mouse position over the canvas """
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)

        if self.edge:  # relocate edge of the drawn polygon
            x1, y1, x2, y2 = self.canvas.coords(self.tag_curr_edge_start)  # get coordinates of the 1st edge
            x3, y3, x4, y4 = self.canvas.coords(self.edge)  # get coordinates of the current edge
            dx = x - x1
            dy = y - y1
            # Set new coordinates of the edge
            if self.radius_stick * self.radius_stick > dx * dx + dy * dy:  # sticking radius
                self.canvas.coords(self.edge, x3, y3, x1, y1)  # stick to the beginning
                # self.set_dash(x1, y1)  # set dash for edge segment
            else:  # follow the mouse
                self.canvas.coords(self.edge, x3, y3, x, y)  # follow the mouse movements
                # self.set_dash(x, y)  # set dash for edge segment

        # Handle polygons on the canvas
        self.deselect_poly()  # change color and zeroize selected polygon
        self.select_poly()  # change color and select polygon

        if self.rect:  # show / hide rolling window rectangle
            w = int(self.roll_size[0] * self.imscale) >> 1
            h = int(self.roll_size[1] * self.imscale) >> 1
            self.canvas.coords(self.roll_rect, (x - w, y - h, x + w, y + h))  # relocate rolling window
            color = self.color_back_roi if self.roi else self.color_back_hole
            self.canvas.itemconfigure(self.roll_rect, state='normal', outline=color)  # show it
        else:
            self.canvas.itemconfigure(self.roll_rect, state='hidden')  # hide rolling window

    def set_edge_scaleLine(self, event):
        """ Set edge of the polygon """
        self.motion(event)  # generate motion event. It's needed for menu bar, bug otherwise!
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.edge and ' '.join(map(str, self.dash)) == self.canvas.itemcget(self.edge, 'dash'):
            return False  # the edge is out of scope or self-crossing with other edges
        elif not self.edge and self.outside(x, y):
            return False  # starting point is out of scope

        if not self.edge:  # start drawing polygon
            self.draw_edge(self.color['scale'], x, y, self.tag_curr_edge_start, dash=self.dash_scale)
            # Draw sticking circle
            # self.canvas.create_oval(x - self.radius_circle, y - self.radius_circle,
            #                        x + self.radius_circle, y + self.radius_circle,
            #                        width=0, fill=self.color['scale'],
            #                        tags=(self.tag_curr_edge, self.tag_curr_circle))
        else:  # continue drawing polygon
            self.draw_edge(self.color['scale'], x, y, dash=self.dash_scale)  # continue drawing polygon, set new edge

            if len(self.polygon) == 2:
                # Stop drawing scale line
                self.isScale = False
                self.scaleLine = copy.copy(self.polygon)  # Keep scale line
                return True
        return False

    # Create toplevel Window of define scale
    def createScalingWindow(self, event):
        self.defineScaleWindow = tk.Toplevel(self.placeholder)
        self.defineScaleWindow.title("Scaling")
        tk.Label(self.defineScaleWindow, text="Enter distance between nodes", font=self.label_font) \
            .pack(side=tk.LEFT)

        self.txt_scale_var = tk.StringVar()
        self.txt_scale_var = tk.Entry(self.defineScaleWindow, textvariable=self.txt_scale_var, width=10,
                                      font=self.label_font, justify=tk.RIGHT)
        self.txt_scale_var.pack(side=tk.LEFT)

        tk.Label(self.defineScaleWindow, text="m", font=self.label_font) \
            .pack(side=tk.LEFT)

        self.button_setScale = ttk.Button(self.defineScaleWindow)
        self.button_setScale.configure(text="OK", padding=10, default=tk.ACTIVE, command=lambda: self.setScale(event))
        self.button_setScale.pack(side=tk.LEFT)

        # Bind functions
        self.defineScaleWindow.bind('<Return>', self.setScale)  # set new edge

        def close_scalewindow():  # Close pop-up window control
            self.delete_edges()
            self.defineScaleWindow.destroy()

        self.defineScaleWindow.protocol("WM_DELETE_WINDOW", close_scalewindow)

        center_tk_window.center_on_screen(self.defineScaleWindow)
        self.defineScaleWindow.focus_force()
        self.defineScaleWindow.grab_set()

    # Set scale values
    def setScale(self, event):

        # Check input value
        if self.txt_scale_var.get() == "":
            tk.messagebox.showerror("Error", "The scale is empty.")
            return
        else:
            try:
                self.scale_var = float(self.txt_scale_var.get())

                if self.scale_var <= 0:
                    tk.messagebox.showerror("Error", "The scale should be non-negative number")
                    return

            except ValueError:
                tk.messagebox.showerror("Error", "The scale should be non-negative number")
                return

        self.scaleLine = copy.copy(self.polygon)
        self.defineScaleWindow.destroy()

        # Delete Line
        self.delete_edges()

        pass

    def set_edge_polyline(self, event):
        """ Set edge of the polygon """
        self.motion(event)  # generate motion event. It's needed for menu bar, bug otherwise!
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.edge and ' '.join(map(str, self.dash)) == self.canvas.itemcget(self.edge, 'dash'):
            return  # the edge is out of scope or self-crossing with other edges
        elif not self.edge and self.outside(x, y):
            return  # starting point is out of scope

        if not self.edge:  # start drawing polygon
            self.draw_edge(self.color['draw'], x, y, self.tag_curr_edge_start)
            # Draw sticking circle
            self.canvas.create_oval(x - self.radius_circle, y - self.radius_circle,
                                    x + self.radius_circle, y + self.radius_circle,
                                    width=0, fill=self.color['draw'],
                                    tags=(self.tag_curr_edge, self.tag_curr_circle))
        else:  # continue drawing polygon

            self.draw_edge(self.color['draw'], x, y)  # continue drawing polygon, set new edge

            if len(self.polygon) == 10:  # draw polygon on the zoomed image canvas

                self.createDrawpolywindow()

                self.draw_polygon(self.polygon, self.color, self.tag_roi, self.poly_dict)
                self.delete_edges()  # delete edges of drawn polygon
                self.count_polyline += 1
                self.isDrawPoly = False

    # Finish drawing polyline when right-click
    def end_draw_polyline(self):
        # Draw polyline pop up window
        if self.isDrawPoly is True and len(self.polygon) > 1:
            self.createDrawpolywindow()

            self.draw_polygon(self.polygon, self.color, self.tag_roi, self.poly_dict)
            self.delete_edges()  # delete edges of drawn polygon
            self.count_polyline += 1
            self.isDrawPoly = False

    def draw_polygon(self, polygon, color, tag, dictionary):
        """ Draw polygon on the canvas """
        # Calculate coordinates of vertices on the zoomed image
        bbox = self.canvas.coords(self.container)  # get image area
        vertices = list(map((lambda i: (i[0] * self.imscale + bbox[0],
                                        i[1] * self.imscale + bbox[1])), polygon))

        # Unique ID for each polyline
        self.tag_uid = uuid.uuid4().hex

        list_edges = []

        # Create polyline. 2nd tag is ALWAYS a unique tag ID.
        for j in range(0, len(vertices) - 1):
            item = self.canvas.create_line(vertices[j], vertices[j + 1], width=self.width_line,
                                           fill=color['back'], tags=(self.tag_poly_line, self.tag_uid))

            list_edges.append(item)

        # Set polyline coordinates and edge ids
        dictionary[self.tag_uid] = polygon.copy()

    def draw_edge(self, color, x, y, tags=None, dash=None):
        """ Draw edge of the polygon """
        if len(self.polygon) > 1:
            x1, y1, x2, y2 = self.canvas.coords(self.edge)

            if x1 == x2 and y1 == y2:
                return  # don't draw edge in the same point, otherwise it'll be self-intersection
        curr_edge_id = self.tag_curr_edge_id + str(len(self.polygon))  # ID of the edge in the polygon

        width = self.line_width['scale'] if self.isScale else self.line_width['line']
        self.edge = self.canvas.create_line(x, y, x, y, fill=color, width=width,
                                            tags=(tags, self.tag_curr_edge, curr_edge_id,), dash=dash)

        '''self.edge = self.canvas.create_line(x, y, x, y, fill=color['draw'], width=self.width_line,
                                            tags=(tags, self.tag_curr_edge, curr_edge_id,), dash=dash)'''

        bbox = self.canvas.coords(self.container)  # get image area
        x1 = round((x - bbox[0]) / self.imscale)  # get real (x,y) on the image without zoom
        y1 = round((y - bbox[1]) / self.imscale)
        self.polygon.append((x1, y1))  # add new vertex to the list of polygon vertices

    def deselect_poly(self):
        """ Deselect current roi object """
        if not self.selected_poly: return  # selected polygons list is empty
        for i in self.selected_poly:
            j = i + self.tag_const  # unique tag of the polygon
            color = self.color_roi if self.is_roi(j) else self.color_hole  # get color palette
            self.canvas.itemconfigure(i, fill=color['back'])  # deselect lines
            self.canvas.itemconfigure(j, state='hidden')  # hide figure
        self.selected_poly.clear()  # clear the list

    def select_poly(self):
        """ Select and change color of the current roi object """
        if not self.isScale and not self.isLocRef and not self.isDrawPoly:

            if self.edge: return  # new polygon is being created (drawn) right now
            i = self.canvas.find_withtag('current')  # id of the current object
            tags = self.canvas.gettags(i)  # get tags of the current object

            # When any edge is selected
            if len(tags) > 1:
                # Get data of id column
                id_list = self.sheet.get_column_data(5)

                if tags[1] in id_list:
                    selected_id_row = id_list.index(tags[1])
                    self.sheet.select_row(selected_id_row)

    # Change color of selected polyline
    def selected_polyline(self, tag_id):
        # Change line color to yellow
        self.canvas.itemconfigure(tag_id, fill=self.color['selected'])

    def deselect_polyline(self, tag_id):
        # Change line color back to blue
        self.canvas.itemconfigure(tag_id, fill=self.color['draw'])

    def delete_edges(self):
        """ Delete edges of drawn polygon """
        if self.edge:  # if polygon is being drawing, delete it
            self.edge = None  # delete all edges and set current edge to None
            self.canvas.delete(self.tag_curr_edge)  # delete all edges
            self.polygon.clear()  # remove all items from vertices list

    def delete_selected_polyline(self, tag_id):
        # Delete polyline of selected row
        self.canvas.delete(tag_id)
        del (self.poly_dict[tag_id])

    def delete_poly(self):
        """ Delete selected polygon """
        self.delete_edges()  # delete edges of drawn polygon
        if self.selected_poly:  # delete selected polygon
            for i in self.selected_poly:
                j = i + self.tag_const  # unique tag of the polygon
                if self.is_roi(j):
                    del (self.roi_dict[i])  # delete ROI from the dictionary of all ROIs
                else:
                    del (self.hole_dict[i])  # delete hole from the dictionary of all holes
                self.canvas.delete(i)  # delete lines
                self.canvas.delete(j)  # delete polygon
            self.selected_poly.clear()  # clear selection list

    @staticmethod
    def orientation(p1, p2, p3):
        """ Find orientation of ordered triplet (p1, p2, p3). Returns following values:
             0 --> p1, p2 and p3 are collinear
            -1 --> clockwise
             1 --> counterclockwise """
        val = (p2[0] - p1[0]) * (p3[1] - p2[1]) - (p2[1] - p1[1]) * (p3[0] - p2[0])
        if val < 0:
            return -1  # clockwise
        elif val > 0:
            return 1  # counterclockwise
        else:
            return 0  # collinear

    @staticmethod
    def on_segment(p1, p2, p3):
        """ Given three collinear points p1, p2, p3, the function checks
            if point p2 lies on line segment p1-p3 """
        # noinspection PyChainedComparisons
        if p2[0] <= max(p1[0], p3[0]) and p2[0] >= min(p1[0], p3[0]) and \
                p2[1] <= max(p1[1], p3[1]) and p2[1] >= min(p1[1], p3[1]):
            return True
        return False

    # Convert input data into geopandas dataframe
    def convertData(self):

        unit = self.getUnit(self.scaleLine[0][0], self.scaleLine[0][1], self.scaleLine[1][0], self.scaleLine[1][1],
                            self.scale_var)

        sheet_data = self.sheet.get_sheet_data()

        ref_x = self.reference[0]
        ref_y = self.reference[1]

        output_list = []

        # Get max, min coordinates
        self.x_r = self.x_l = self.y_h = self.y_lo = 0

        for row in sheet_data:

            list_row = []

            list_row.append(row[0])
            list_row.append(row[1])
            list_row.append(float(row[2]))
            list_row.append(float(row[3]))
            list_row.append(int(row[4]))

            list_points = []  # List of points
            image_coords = self.poly_dict.get(row[5])

            for coord in image_coords:
                list_points.append(self.convertCoordinates(coord[0], coord[1], ref_x, ref_y, unit))

            list_row.append(LineString(list_points))
            output_list.append(list_row)

        df = pd.DataFrame(output_list)
        df.columns = ['linkID', 'rdTypeID', 'wd', 'bw', 'n', 'geometry']

        gdf = geopandas.GeoDataFrame(df, geometry='geometry')

        return self.x_r + 100, self.x_l - 100, self.y_h + 100, self.y_lo - 100, gdf

    # Calculate unit defined by Define Scale function
    def getUnit(self, x_1, y_1, x_2, y_2, scale):

        unit = math.sqrt((x_2 - x_1) ** 2 + (y_2 - y_1) ** 2) / scale

        return unit

    # Convert pixel coordinates to GIS coordinates
    def convertCoordinates(self, x, y, x_ref, y_ref, unit):
        x = x - x_ref
        y = y_ref - y

        x = x / unit
        y = y / unit

        self.x_r = max(self.x_r, x)
        self.x_l = min(self.x_l, x)
        self.y_h = max(self.y_h, y)
        self.y_lo = min(self.y_lo, y)

        return Point(x, y)

    # Create draw poly window when finish drawing
    def createDrawpolywindow(self):
        self.drawPolyWindow = tk.Toplevel(self.placeholder)
        self.drawPolyWindow.title("Link information")

        # LinkID
        tk.Label(self.drawPolyWindow, text="LinkID", font=self.label_font).grid(row=0, column=0, padx=5, pady=5,
                                                                                sticky=tk.W + tk.S)

        self.txt_linkID_var = tk.StringVar()
        self.txt_linkID_var.set(repr(self.count_polyline))
        self.txt_linkID = tk.Entry(self.drawPolyWindow, textvariable=self.txt_linkID_var, width=10,
                                   font=self.label_font, justify=tk.RIGHT)
        self.txt_linkID.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.S)

        # Link width
        tk.Label(self.drawPolyWindow, text="Link Width (m)", font=self.label_font).grid(row=1, column=0, padx=5, pady=5,
                                                                                        sticky=tk.W + tk.S)

        self.txt_linkWid_var = tk.StringVar()
        self.txt_linkWid = tk.Entry(self.drawPolyWindow, textvariable=self.txt_linkWid_var, width=10,
                                    font=self.label_font, justify=tk.RIGHT)
        self.txt_linkWid.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.S)

        # Road Type
        tk.Label(self.drawPolyWindow, text="Road Type", font=self.label_font).grid(row=2, column=0, padx=5, pady=5,
                                                                                   sticky=tk.W + tk.N)

        self.txt_roadTp_var = tk.StringVar()
        self.txt_roadTp = tk.Entry(self.drawPolyWindow, textvariable=self.txt_roadTp_var, width=10,
                                   font=self.label_font, justify=tk.RIGHT)
        self.txt_roadTp.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W + tk.N)

        self.button_ok = ttk.Button(self.drawPolyWindow)
        self.button_ok.configure(text="OK", padding=10, default=tk.ACTIVE, width=15,
                                 command=self.btn_OK)
        self.button_ok.grid(row=1, column=3, rowspan=2, sticky=tk.W + tk.S, padx=10, pady=10)

        center_tk_window.center_on_screen(self.drawPolyWindow)
        self.drawPolyWindow.focus_force()
        self.drawPolyWindow.grab_set()

        def close_window_event():
            self.canvas.delete(self.tag_uid)
            del (self.poly_dict[self.tag_uid])
            self.drawPolyWindow.destroy()
            self.count_polyline -= 1

        self.drawPolyWindow.protocol("WM_DELETE_WINDOW", close_window_event)
        pass

    def btn_OK(self):
        if self.error_check() is not True:
            # Set values
            self.linkID_set.add(self.txt_linkID_var.get())

            # LinkID, Road Type, wd, bw, unique-id, coordinates, index of self.edge_dict

            row = [self.txt_linkID_var.get(), self.txt_roadTp_var.get(), float(self.txt_linkWid_var.get()),
                   float(self.txt_linkWid_var.get()) / 2, len(self.poly_dict[self.tag_uid]), self.tag_uid]

            self.poly_sheet_list.append(row)

            self.sheet.set_sheet_data(self.poly_sheet_list)

            # Destroy the window
            self.drawPolyWindow.destroy()

        else:
            return

    def error_check(self):
        isError = False

        # Error message string
        errMsg = ""

        # Link ID
        if self.txt_linkID_var.get() == "":
            errMsg += "\n 1. Link ID should be nonnegative\n"
            isError = True
        elif self.txt_linkID_var.get() in self.linkID_set:
            errMsg += "\n 1. Link ID is duplicated\n"
            isError = True

        # Road Type
        if self.txt_roadTp_var.get() == "":
            errMsg += "\n 1. Road Type is empty\n"
            isError = True

        # Link Width
        try:
            linkWid = float(self.txt_linkWid_var.get())
            if linkWid < 0:
                # Give warning if shoulder is greater than 8
                errMsg += "\n 1. Line width should be nonnegative\n"
                isError = True
        except ValueError:
            errMsg += "\n 1. Line width should be number(float)\n"
            isError = True

        if isError:
            tk.messagebox.showerror('Error', errMsg)

        return isError


# Road table sheet
class Sheet(tksheet.Sheet):
    def __init__(self, df, master=None):
        super().__init__(master, column_width=100, height=200)
        self.grid(sticky=tk.W + tk.E)

        # Receptor csv data frame
        self.df = df

        # current selected row
        self.current_selected_id = None

        # Current edit cell
        self.current_edit_cell = None

        # Create spreadsheet table
        self.createTable()

    # Create Spread sheet table of receptor data frame
    def createTable(self):

        # Set header
        headers_list = ("linkID", "rdTypeID", "wd", "bw", "n")
        headers = [f'{c}' for c in headers_list]
        self.headers(headers)

        # Set read-only columns (bw, n)
        self.readonly_columns(columns=[3, 4], readonly=True, redraw=True)

        # Set data
        if self.df is not None:
            lst_df = self.df.values.tolist()
            self.set_sheet_data(lst_df[0:4])

        # Set bindings
        self.extra_bindings("begin_delete_rows", self.delete_row)  # When deleting row starts
        self.extra_bindings("row_select", self.selected_row)  # When a row is selected
        self.extra_bindings("deselect", self.deselect_row)  # When a row get deselected
        self.extra_bindings("begin_edit_cell", self.edit_cell_start)
        self.extra_bindings("end_edit_cell", self.edit_cell_end)

        self.enable_bindings(("single_select",

                              "row_select",

                              "column_width_resize",

                              # "arrowkeys",

                              "rc_select",

                              "rc_delete_row",

                              "copy",

                              "undo",

                              "edit_cell"))

    # When editing cell starts
    def edit_cell_start(self, event):
        # If edited cell is in wd column
        self.current_edit_cell = self.get_selected_cells()
        self.wd_before_edit = self.get_cell_data(list(self.current_edit_cell)[0][0], list(self.current_edit_cell)[0][1])

    # When editting cell ends
    def edit_cell_end(self, event):
        # Get column index
        selected_r = list(self.current_edit_cell)[0][0]
        selected_c = list(self.current_edit_cell)[0][1]

        # If the edited cell is in the column "wd"
        if selected_c == 2:
            # If the edited value is not float
            try:
                val = float(self.get_cell_data(selected_r, selected_c))
                self.set_cell_data(selected_r, selected_c + 1, val / 2)

            except ValueError:
                tk.messagebox.showerror('Error', 'Edited value is not float')
                self.set_cell_data(selected_r, selected_c, self.wd_before_edit)

    def selected_row(self, event):
        # If a row is already selected
        if not self.current_selected_id is None:
            self.master.canvas.deselect_polyline(self.current_selected_id)

        self.current_selected_id = self.get_row_data(self.get_selected_rows().pop())[5]

        # Change color of selected line
        self.master.canvas.selected_polyline(self.current_selected_id)

    def deselect_row(self, event):
        if not self.current_selected_id is None:
            self.master.canvas.deselect_polyline(self.current_selected_id)
            self.current_selected_id = None

    def delete_row(self, event):
        ''' Delete selected polyline'''
        self.master.canvas.delete_selected_polyline(self.current_selected_id)
        self.current_selected_id = None
