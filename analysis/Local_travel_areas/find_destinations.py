# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 11:04:32 2023

@author: gordon.donald
"""


import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)

import pandas as pd
import geopandas
import time

from analysis.utils import *
msoas=get_all_small_areas()

import matplotlib.pyplot as plt
#use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
#Basemap
import contextily as cx


from analysis.Local_travel_areas.LTA_queries import *
from analysis.Local_travel_areas.LTA_functions import *

test_weekdays = get_data_for_weekdays()
test_weekdays.columns = ['start_msoa', 'end_msoa', 'avg_daily_trips']

test_weekends = get_data_for_weekends()
test_weekends.columns = ['start_msoa', 'end_msoa', 'avg_daily_trips']


#Test this and plot it.
#The follow will both work in the below, but the second one is a lot faster if we already have run the query.
destinations = get_destinations('E02002539')
destinations2 = get_destinations_from_big_df('E02002539', test_weekdays)

#Some tests of 2011 vs 2021 Census MSOAs, to see which are in the O2 dataset.
#destinations = get_destinations('E02002652') #Hull 001 -- expired in 2021, was in 2011 LSOAs -- Returns 303 rows
#destinations = get_destinations('E02007080') #Hull 034 -- one of the successors -- Returns 0 rows

map_data = msoas.merge(destinations2, right_on='end_msoa', left_on='msoa11cd')

#Copy map code from RTIs
#from mapclassify import Quantiles, UserDefined
#import shapely
fig, ax = plt.subplots(figsize=(10, 10))
map_data.plot(
     column='avg_daily_trips',
     edgecolor = 'k', 
     linewidth = 0.4,
     cmap = ListedColormap(map_lu_partnership_colour_scale),
     legend =True,
     scheme='equalinterval',
     k=5,
     legend_kwds={'bbox_to_anchor':(0.38, 0.5), 'markerscale':2, 'title':'Total journeys', 'title_fontsize':16, 'labelspacing': 0.8, 'edgecolor': 'white'},
     ax=ax
     )
plt.axis('off')
 # Get the legend object
legend = ax.get_legend()
legend._legend_box.align = "bottom"
fig.suptitle('Journeys from Stockton 005', fontsize=24)
fig.text(0.2,0.14, 'Source: O2 Motion', fontsize=13);

plt.savefig("./testO2_journeys.png", dpi = 300)

#Alright -- let's find the destinations accounting for up to X% of total trips.
mb_high_deprivation = "E02002499"
mb_low_deprivation = "E02006811"

our_msoa= mb_low_deprivation

destinations = get_destinations_from_big_df(our_msoa, test_weekdays)

#So these will give the number of destination MSOA accounting for 50, 80, 90% of trips.
#len(data_to_meet_threshold(destinations, 'avg_daily_trips', 0.5))
#len(data_to_meet_threshold(destinations, 'avg_daily_trips', 0.8))
#len(data_to_meet_threshold(destinations, 'avg_daily_trips', 0.9))
    
bounds90 = get_bounds(destinations, 'avg_daily_trips', 0.9)
bounds80 = get_bounds(destinations, 'avg_daily_trips', 0.8)
bounds50 = get_bounds(destinations, 'avg_daily_trips', 0.5)
bounds1 = get_bounds_central(destinations, our_msoa) #This will pick out the within same MSOA trips

#Plot these as the area containing X% of trips.
# read in SDU OS API key
key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key

f, ax = plt.subplots(figsize=(12, 12))
bounds90.plot(ax=ax, color=map_lu_partnership_colour_scale[1], alpha=0.9, label='90%')
bounds80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
bounds50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
bounds1.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label='Start MSOA')
lines = [
    Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
    for t in ax.collections[0:]
]
labels = [t.get_label() for t in ax.collections[0:]]
ax.legend(lines, labels)
plt.suptitle("Area containing 50, 80, and 90% of trips from "+ get_name_from_code(our_msoa))
cx.add_basemap(ax, source=basemap_url, crs=bounds1.crs)
plt.show()


#Get a zoom in to the centre of this area. This'll work.
lads = gpd.read_file("Q:/GI_Data/Boundaries/LAD_MAY_2021_UK_BFE_V2.shp")

middlesborugh_nn = lads[lads['LAD21NM'].isin(['Middlesbrough'])]
buffered_mb = gpd.GeoDataFrame(middlesborugh_nn.buffer(10000), geometry=0, crs=msoas.crs)
msoas_near_mb = buffered_mb.overlay(msoas)


bounds_cut90 = gpd.overlay(bounds90, msoas_near_mb)
bounds_cut80 = gpd.overlay(bounds80, msoas_near_mb)
bounds_cut50 = gpd.overlay(bounds50, msoas_near_mb)


f, ax = plt.subplots(figsize=(12, 12))
bounds_cut90.plot(ax=ax, color=map_lu_partnership_colour_scale[1], alpha=0.9, label='90%')
bounds_cut80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
bounds_cut50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
bounds1.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label='Start MSOA')
middlesborugh_nn.boundary.plot(ax=ax, alpha=1, color='red')
lines = [
    Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
    for t in ax.collections[0:]
]
labels = [t.get_label() for t in ax.collections[0:]]
ax.legend(lines, labels)
plt.suptitle("Area containing 50, 80, and 90% of trips from "+ get_name_from_code(our_msoa))
cx.add_basemap(ax, source=basemap_url, crs=bounds1.crs)
plt.show()

#Repeat for the weekend data.

destinations = get_destinations_weekend(our_msoa)
   
bounds90 = get_bounds(destinations, 'avg_daily_trips', 0.9)
bounds80 = get_bounds(destinations, 'avg_daily_trips', 0.8)
bounds50 = get_bounds(destinations, 'avg_daily_trips', 0.5)
bounds1 = get_bounds_central(destinations, our_msoa) #This will pick out the within same MSOA trips


f, ax = plt.subplots(figsize=(12, 12))
bounds90.plot(ax=ax, color=map_lu_partnership_colour_scale[1], alpha=0.9, label='90%')
bounds80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
bounds50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
bounds1.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label='Start MSOA')
lines = [
    Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
    for t in ax.collections[0:]
]
labels = [t.get_label() for t in ax.collections[0:]]
ax.legend(lines, labels)
plt.suptitle("Area containing 50, 80, and 90% of trips from "+ get_name_from_code(our_msoa))
cx.add_basemap(ax, source=basemap_url, crs=bounds1.crs)
plt.show()

#A question to ask: how many MSOAs account for 80 and 90% of journeys?
def msoas_covering_most_journeys(msoa):
    dest = get_destinations_from_big_df(msoa, test_weekdays)
    n100 = len(dest)
    if n100==0: #Quick safety check here -- skip to return 0 for all values if the query retruns nothing.
        return([msoa, get_name_from_code(msoa), 0, 0, 0, 0, 0, 0, 0, 0])
    n90 = len(data_to_meet_threshold(dest, 'avg_daily_trips', 0.9))
    n80 = len(data_to_meet_threshold(dest, 'avg_daily_trips', 0.8))
    n50 = len(data_to_meet_threshold(dest, 'avg_daily_trips', 0.5))
    
    we_dest = get_destinations_from_big_df(msoa, test_weekends)
    we_n100 = len(we_dest)
    we_n90 = len(data_to_meet_threshold(we_dest, 'avg_daily_trips', 0.9))
    we_n80 = len(data_to_meet_threshold(we_dest, 'avg_daily_trips', 0.8))
    we_n50 = len(data_to_meet_threshold(we_dest, 'avg_daily_trips', 0.5))

    return([msoa, get_name_from_code(msoa), n100, n90, n80, n50, we_n100, we_n90, we_n80, we_n50])

st=time.time()
msoa_codes = list(msoas['msoa11cd'])
storage_array=[]
fails=[]

#This will do a brute force for loop and store those that failed separately, right?
x=0
for code in msoa_codes:
    x+=1
    if x%100==0:
        print(x)
    try:
        storage_array.append(msoas_covering_most_journeys(code))
    except: #TBH, we don't need this try/except logic if we aren't querying.
        fails.append(code)
msoa_data = pd.DataFrame(storage_array)

msoa_data.columns = ['msoa11cd', 'msoa11nm', 'weekday_100', 'weekday_90', 'weekday_80', 'weekday_50',
                     'weekend_100', 'weekend_90', 'weekend_80', 'weekend_50']


msoa_data.to_csv("Q:SDU/Mobility/Data/Processed/Nodes/MSOA_destination_count.csv", index=False)
et=time.time()

#Alright, plots? Copy what we have in RTIs?

