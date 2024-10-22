# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 17:17:55 2024

@author: gordon.donald
"""

import pandas as pd
import geopandas as gpd
import contextily as cx

centres = pd.read_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/Community_centre_stats.csv")
from analysis.utils import *
msoas = get_all_small_areas()

regions = gpd.read_file("Q:/GI_Data/Boundaries/Regions/Regions2019.shp")

msoas_plot = msoas.merge(centres, left_on='msoa11cd', right_on='centre')
msoas_plot.plot('count', cmap='Blues')

key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key

def plot_centres_in_region(region, msoas_plot):
    region_bounds = regions[regions.rgn19nm == region]
    msoas_within = list(region_bounds.overlay(msoas).msoa11cd)
    msoas_to_plot = msoas_plot[msoas_plot.msoa11cd.isin(msoas_within)]
    ax = msoas_to_plot.plot('count', cmap='Blues')
    cx.add_basemap(ax, source=basemap_url, crs=msoas.crs)
    return 0

plot_centres_in_region("South East", msoas_plot)
