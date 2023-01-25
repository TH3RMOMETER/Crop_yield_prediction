import customtkinter
from tkintermapview import TkinterMapView
import geopandas as gpd
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
#from meteostat import Daily, Point
from shapely.geometry import Polygon, mapping
import shapely as sh
from model import get_model_predictions
#import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
polygon = gpd.read_file('agri_46.geojson')
polygon["centroid"] = polygon.geometry.centroid
#print(list(polygon['name']))

model_path = r'/home/maxim/Documents/GitHub/Crop_yield_prediction/tcn_tf/content/tcn_nvdi.tf'

with open('agri_46.geojson') as f:
    data = json.load(f)


customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):

    APP_NAME = "Agurotech map"
    WIDTH = 1250    
    HEIGHT = 600

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.marker_list = []

    # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self, width=450, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.frame_pred= customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_pred.grid(row=0, column=2, padx=0, pady=0, sticky="nsew")

        self.frame_right = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

    # ============ frame_left ============

        self.frame_left.grid_rowconfigure(2, weight=1)

    # Buttons
        self.button_1 = customtkinter.CTkButton(master=self.frame_left, text="Set Marker", command=self.set_marker_event)
        self.button_1.grid(pady=(20, 0), padx=(20, 20), row=0, column=0)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left, text="Clear Markers", command=self.clear_marker_event)
        self.button_2.grid(pady=(20, 0), padx=(20, 20), row=1, column=0)

        self.combobox_1 = customtkinter.CTkOptionMenu(master = self.frame_left, values=(list(polygon['name'])), command=self.update_location)
        self.combobox_1.grid(pady = (10,0), padx = (20,20), row=2, column = 0)

        self.date_label = customtkinter.CTkLabel(master=self.frame_left, text="Enter date")
        self.date_label.grid(row=3, column=0, padx=(20,20), pady=(20,0))

        self.entry_date = customtkinter.CTkEntry(master=self.frame_left, placeholder_text="yyyy-mm-dd")
        self.entry_date.grid(pady=(10,0), padx=(20,20), row=4, column = 0, sticky = 'we')

        self.button_3 = customtkinter.CTkButton(master=self.frame_left, text = "Get NDVI predictions")
        self.button_3.grid(pady=(20, 0), padx=(20, 20), row=5, column=0)

        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Tile Server:", anchor="w")
        self.map_label.grid(row=6, column=0, padx=(20, 20), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal", "Google satellite"],
                                                                       command=self.change_map)
        self.map_option_menu.grid(row=7, column=0, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=8, column=0, padx=(20, 20), pady=(20, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=(20, 20), pady=(10, 20))

    # ============ frame_right ============

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)

        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="type address")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_5 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_5.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

    # ============ frame_pred ============

        self.frame_pred.grid_rowconfigure(1, weight=1)
        self.frame_pred.grid_rowconfigure(0, weight=0)
        self.frame_pred.grid_columnconfigure(0, weight=1)
        self.frame_pred.grid_columnconfigure(1, weight=0)
        self.frame_pred.grid_columnconfigure(2, weight=1)

        self.button_6 = customtkinter.CTkButton(master=self.frame_pred, text="get frame", command= None)
        self.button_6.grid(row=0, column=3, sticky="nswe", padx=(12,0), pady=(20,20))


        self.fig, self.ax = plt.subplots()
        self.fig.set_size_inches(11,5.3)
        self.x_test = np.array([1,2,3,4,5,6,7,8,9,10])
        self.y_test = np.array([1,2,3,4,5,6,7,8,9,10])
        #self.ax.bar(self.x, self.y)
        self.canvas = FigureCanvasTkAgg(self.fig,master=self.frame_pred)
        self.canvas.draw()
        self.canvas.get_tk_widget().place(relx=0.01, rely=0.025)

    # ============ default values ============
        self.map_widget.set_address("Amsterdam")
        self.map_option_menu.set("OpenStreetMap")
        self.appearance_mode_optionemenu.set("Dark")

    # ============ functions ============

    def search_event(self, event=None):
        self.map_widget.set_address(self.entry.get())

    def set_marker_event(self):
        current_position = self.map_widget.get_position()
        self.marker_list.append(self.map_widget.set_marker(current_position[0], current_position[1]))
        print(current_position)

    def clear_marker_event(self):
        for marker in self.marker_list:
            marker.delete()

    def rev_coords(self, poly):
        poly_mapped = mapping(poly)
        poly_coordinates = poly_mapped['coordinates'][0]
        poly_ = [(coords[1],coords[0]) for coords in poly_coordinates]
        print(json.dumps(poly_))
        

    def update_location(self, location):
        #self.map_widget.set_address(self.combobox_1.get())
        #print(self.combobox_1.get())
        #self.map_widget.set_position(48.860381, 2.338594)
        name = self.combobox_1.get()

        for _ , poly in polygon.iterrows():
            if poly[0] == name:
                self.map_widget.set_position(poly[1].centroid.y, poly[1].centroid.x)
                self.marker_list.append(self.map_widget.set_marker(poly[1].centroid.y, poly[1].centroid.x))
                coord_list = list(poly[1].exterior.coords)
                coord_list = [sublist[::-1] for sublist in coord_list[::-1]]
                self.map_widget.set_polygon(coord_list, outline_color="red", fill_color="yellow")

                self.start_date = self.entry_date.get()
                self.end_date = datetime.strptime(self.start_date, '%Y-%m-%d') + timedelta(days=13)

                print(self.start_date,self.end_date)

                self.daterange = pd.date_range(self.start_date, self.end_date, freq = 'd')
                self.ndvi_pred = get_model_predictions(model_path,poly[0],self.daterange)[0]


                self.ax.plot(self.daterange, self.ndvi_pred)
                self.canvas = FigureCanvasTkAgg(self.fig,master=self.frame_pred)
                self.canvas.draw()
                self.canvas.get_tk_widget().place(relx=0.01, rely=0.025)



    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_map(self, new_map: str):
        if new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        elif new_map == "Google normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)


    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()