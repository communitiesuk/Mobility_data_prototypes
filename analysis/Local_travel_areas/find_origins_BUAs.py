import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd
import time

import matplotlib.pyplot as plt
# Use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
# Basemap
import contextily as cx

from analysis.Local_travel_areas.LTA_queries import *
from analysis.Local_travel_areas.LTA_functions import *
from analysis.msoa_jobs_functions import *
from analysis.utils import *


# MSOA-BUA lookup
msoa_bua_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA_lookup.csv")

# Get the LTA for a BUA.
our_bua='Hastings'

weekday_data = get_data_for_all_weekdays()

def get_BUA_origins(our_bua, data, threshold=0.9):
    #Get MSOAs.
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
    bua_journeys = data[data.end_msoa.isin(our_msoas)]
    bua_origins = bua_journeys[['start_msoa', 'daily_trips']].groupby('start_msoa').sum().reset_index()


    # Find the start MSOAs accounting for up to X% of total trips.
    bounds = get_bounds(bua_origins, 'daily_trips', threshold,  msoa_pos="start_msoa")
    
    return(bounds)


# Function to plot origins of journeys to a BUA.
# Args:
# our_bua ~ name of chosen bua (str)
# data ~ data to be plotted (df)
# BUA_boudary ~ default True. This will use the BUA boundary. If false, will use the set of MSOAs which intersect the BUA as the boundary (bool)
# read in SDU OS API key

key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key


def plot_LTA_origins_around_BUA(our_bua, data, BUA_boundary=True):

    # Finding start MSOAs with 50, 80, 90% of trips
    bounds90 = get_BUA_origins(our_bua, data, 0.9)    
    bounds80 = get_BUA_origins(our_bua, data, 0.8) 
    if BUA_boundary:   
        bounds50 = get_BUA_origins(our_bua, data, 0.5)    

    # Get BUA/MSOA intersection with BUA boundary.
    # Reading in BUA shp file if not already in global scope
    if BUA_boundary:   
        if "BUAs" not in globals():
            global BUAs
            BUAs=get_BUAs()
        chosen_BUA = BUAs[BUAs['BUA22NM']==our_bua]
    else:
        our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
        bua_journeys = data[data.end_msoa.isin(our_msoas)]
        bua_origins = bua_journeys[['start_msoa', 'daily_trips']].groupby('start_msoa').sum().reset_index()
        bounds_cen = get_bounds_central(bua_origins, our_msoas, msoa_pos="start_msoa")

    # Plot map
    f, ax = plt.subplots(figsize=(12, 12))
    bounds90.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.6, label='90% LTA')
    bounds80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
    if BUA_boundary:
        bounds50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
        chosen_BUA.plot(ax=ax, color=map_lu_partnership_colour_scale[4], alpha=0.9, label=our_bua)
    else:
        bounds_cen.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label=our_bua)

    lines = [
        Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
        for t in ax.collections[0:]
        ]
    labels = [t.get_label() for t in ax.collections[0:]]
    ax.legend(lines, labels)
    plt.suptitle("Area containing 90% of trips to "+ our_bua)
    cx.add_basemap(ax, source=basemap_url, crs=bounds90.crs)
    plt.show()
    plt.close()
    return(0)

# Plot using BUA boundaries
plot_LTA_origins_around_BUA(our_bua, weekday_data, BUA_boundary=True)

# Plot BUA boundary as the set of MSOAs which intersect the BUA.
plot_LTA_origins_around_BUA(our_bua, weekday_data, BUA_boundary=False)