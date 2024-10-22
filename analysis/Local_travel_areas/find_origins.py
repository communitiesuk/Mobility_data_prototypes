import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd

from analysis.utils import *
msoas=get_all_small_areas()

import matplotlib.pyplot as plt
#use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.lines import Line2D
#Basemap
import contextily as cx


from analysis.Local_travel_areas.LTA_queries import *
from analysis.Local_travel_areas.LTA_functions import get_bounds, get_bounds_central, get_name_from_code

mb_high_deprivation = "E02002499"
mb_low_deprivation = "E02006811"

our_msoa= mb_low_deprivation

#Finding where 90, 80 and 50 % of trips come from to chosen msoa on weekdays
data_weekday = get_data_for_all_weekdays()

# Choose one of the below. Second is faster if query has already run
origins = get_origins(data_weekday, our_msoa)
origins = get_origins_from_big_df(our_msoa, data_weekday)
   
bounds90 = get_bounds(origins, 'daily_trips', 0.9, 'start_msoa')
bounds80 = get_bounds(origins, 'daily_trips', 0.8, 'start_msoa')
bounds50 = get_bounds(origins, 'daily_trips', 0.5, 'start_msoa')
bounds1 = get_bounds_central(origins, our_msoa, 'start_msoa') #This will pick out the within same MSOA trips

#Plot these as the area containing X% of trips.
# read in SDU OS API key
key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key


f, ax = plt.subplots(figsize=(12, 12))
bounds90.plot(ax=ax, color=map_lu_partnership_colour_scale[1], alpha=0.9, label='90%')
bounds80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
bounds50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
bounds1.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label='End MSOA')
lines = [
    Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
    for t in ax.collections[0:]
]
labels = [t.get_label() for t in ax.collections[0:]]
ax.legend(lines, labels)
plt.suptitle("Area containing 50, 80, and 90% of trips to "+ get_name_from_code(our_msoa))
cx.add_basemap(ax, source=basemap_url, crs=bounds1.crs)
plt.show()

#Get a zoom in to the centre of this area.
lads = gpd.read_file("Q:/GI_Data/Boundaries/LAD_MAY_2021_UK_BFE_V2.shp")

lad_name = 'Middlesbrough'

lad_nn = lads[lads['LAD21NM'].isin([lad_name])]
buffered_lad = gpd.GeoDataFrame(lad_nn.buffer(10000), geometry=0, crs=msoas.crs)
msoas_near_lad = buffered_lad.overlay(msoas)


bounds_cut90 = gpd.overlay(bounds90, msoas_near_lad)
bounds_cut80 = gpd.overlay(bounds80, msoas_near_lad)
bounds_cut50 = gpd.overlay(bounds50, msoas_near_lad)


f, ax = plt.subplots(figsize=(12, 12))
bounds_cut90.plot(ax=ax, color=map_lu_partnership_colour_scale[1], alpha=0.9, label='90%')
bounds_cut80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
bounds_cut50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
bounds1.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label='End MSOA')
lad_nn.boundary.plot(ax=ax, alpha=1, color='red')
lines = [
    Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
    for t in ax.collections[0:]
]
labels = [t.get_label() for t in ax.collections[0:]]
ax.legend(lines, labels)
plt.suptitle("Area containing 50, 80, and 90% of trips to "+ get_name_from_code(our_msoa))
cx.add_basemap(ax, source=basemap_url, crs=bounds1.crs)
plt.show()


#Finding where 90, 80 and 50 % of trips come from to chosen msoa on weekends
data_weekend = get_data_for_all_weekends()

# Choose one of the below. Second is faster if query has already run
origins = get_origins_weekend(data_weekend, our_msoa)
origins = get_origins_from_big_df(our_msoa, data_weekend)

bounds90 = get_bounds(origins, 'daily_trips', 0.9, 'start_msoa')
bounds80 = get_bounds(origins, 'daily_trips', 0.8, 'start_msoa')
bounds50 = get_bounds(origins, 'daily_trips', 0.5, 'start_msoa')
bounds1 = get_bounds_central(origins, our_msoa, 'start_msoa') #This will pick out the within same MSOA trips

f, ax = plt.subplots(figsize=(12, 12))
bounds90.plot(ax=ax, color=map_lu_partnership_colour_scale[1], alpha=0.9, label='90%')
bounds80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
bounds50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
bounds1.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label='End MSOA')
lines = [
    Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
    for t in ax.collections[0:]
]
labels = [t.get_label() for t in ax.collections[0:]]
ax.legend(lines, labels)
plt.suptitle("Area containing 50, 80, and 90% of trips to "+ get_name_from_code(our_msoa))
cx.add_basemap(ax, source=basemap_url, crs=bounds1.crs)
plt.show()