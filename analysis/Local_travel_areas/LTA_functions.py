# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 10:57:32 2023

@author: gordon.donald
"""

#Functions for LTA
from analysis.utils import *
import pandas as pd
msoas=get_all_small_areas()
msoa_bua_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA_lookup.csv")
#MAp imports
import contextily as cx
import matplotlib.pyplot as plt
#use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D

def data_to_meet_threshold(data, column, threshold):
    #Sort the column here
    data = data.sort_values(column, ascending=False)
    total = sum(data[column])
    target = total*threshold
    row=0
    while(sum(data.iloc[0:row][column]) < target):
        row +=1
    row-=1 #We've incremented one time too many here in the loop, so revert
    min_value_needed = data.iloc[row][column]
    subset = data[data[column]>=min_value_needed].copy()
    subset['Percent'] = subset[column] / subset[column].sum() * 100
    return(subset)


def get_bounds(data, column, threshold=0.9, msoa_pos="end_msoa"):
    subset = data_to_meet_threshold(data, column, threshold)
    map_data = msoas.merge(subset, right_on=msoa_pos, left_on='msoa11cd')
    return(map_data)

def get_bounds_central(data, bua_msoas, msoa_pos="end_msoa"):
    if type(bua_msoas) == str:
        bua_msoas = [bua_msoas]
    subset = data.reset_index()[data.reset_index()[msoa_pos].isin(bua_msoas)]
    map_data = msoas.merge(subset, right_on=msoa_pos, left_on='msoa11cd')
    return(map_data)

def get_name_from_code(msoa_code):
    name = list(msoas[msoas['msoa11cd']==msoa_code]['msoa11nm'])[0]
    return(name)


def get_BUA_LTA(our_bua, data, threshold=0.9):
    #Get MSOAs.
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
    bua_journeys = data[data.start_msoa.isin(our_msoas)]
    bua_destination = bua_journeys[['end_msoa', 'daily_trips']].groupby('end_msoa').sum().reset_index()


    #Alright -- let's find the destinations accounting for up to X% of total trips.
    bounds = get_bounds(bua_destination, 'daily_trips', threshold)
    
    return(bounds)

key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key


def plot_LTAs_around_BUA(our_bua, data, BUA_boundary=True, title='default', PLOT_LEVELS=False, BUAs=None):
    """
    Plot the areas containing different percentages of trips which begin from a specified Built-Up Area (BUA).
    This shows the area around the BUA where people spend their time.

    Parameters:
    - our_bua (str): The name of the Built-Up Area (BUA) of interest.
    - data (DataFrame): DataFrame containing trip data.
    - BUA_boundary (bool, optional): Whether to include the BUA boundary in the plot. Defaults to True.
    - title (str, optional): Title for the plot. Defaults to 'default'.
    - PLOT_LEVELS (bool, optional): Whether to plot additional levels (e.g., 80%, 50%). Defaults to False.
    - BUAs (GeoDataFrame): The BUA shapefile if we're plotting BUAs

    Returns:
    - fig (matplotlib.figure.Figure): The generated plot figure.
    """
    # Finding start MSOAs with 50, 80, 90% of trips
    bounds90 = get_BUA_LTA(our_bua, data, 0.9)    
    if PLOT_LEVELS:   
        bounds80 = get_BUA_LTA(our_bua, data, 0.8) 
        bounds50 = get_BUA_LTA(our_bua, data, 0.5)    

    # Get BUA/MSOA intersection with BUA boundary.
    # We are reading in the BUA shp file if it's not already in global scope -- this speeds up the code if we apply this function multiple times, but doesn't require have the BUAs.
    if BUA_boundary:   
        chosen_BUA = BUAs[BUAs['BUA22NM']==our_bua]
    else:
        our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
        bua_journeys = data[data.end_msoa.isin(our_msoas)]
        bua_origins = bua_journeys[['start_msoa', 'daily_trips']].groupby('start_msoa').sum().reset_index()
        bounds_cen = get_bounds_central(bua_origins, our_msoas, msoa_pos="start_msoa")

    # Plot map
    f, ax = plt.subplots(figsize=(12, 12))
    bounds90.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.6, label='90% LTA')
    if PLOT_LEVELS:
        bounds80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
        bounds50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
    if BUA_boundary:
        chosen_BUA.plot(ax=ax, color=map_lu_partnership_colour_scale[4], alpha=0.9, label=our_bua)
    else:
        bounds_cen.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label=our_bua)

    lines = [
        Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
        for t in ax.collections[0:]
        ]
    labels = [t.get_label() for t in ax.collections[0:]]
    ax.legend(lines, labels)
    if title == 'default':
        plt.title("Area containing 90% of trips to "+ our_bua+"\n")
    else:
        plt.title(title+"\n")
    plt.axis('off')
    cx.add_basemap(ax, source=basemap_url, crs=bounds90.crs)
    plt.show()
    #plt.close()
    return(f)


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

def plot_LTA_origins_around_BUA(our_bua, data, BUA_boundary=True, BUAs=None):
    """
    Plot the areas containing different percentages of trips which go to a specified Built-Up Area (BUA).
    This shows the areas nearby from which people come from to visit the BUA.

    Parameters:
    - our_bua (str): The name of the Built-Up Area (BUA) of interest.
    - data (DataFrame): DataFrame containing trip data.
    - BUA_boundary (bool, optional): Whether to include the BUA boundary in the plot. Defaults to True.
    - BUAs (GeoDataFrame): The BUA shapefile if we're plotting BUAs

    Returns:
    - fig (matplotlib.figure.Figure): The generated plot figure.
    """
    # Finding start MSOAs with 50, 80, 90% of trips
    bounds90 = get_BUA_origins(our_bua, data, 0.9)    
    bounds80 = get_BUA_origins(our_bua, data, 0.8) 
    
    # Get BUA/MSOA intersection with BUA boundary.
    # We are reading in the BUA shp file if it's not already in global scope -- this speeds up the code if we apply this function multiple times, but doesn't require have the BUAs.
    if BUA_boundary:   
        #Only plot the 50% LTA if we are showing the BUA.
        bounds50 = get_BUA_origins(our_bua, data, 0.5)    
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
