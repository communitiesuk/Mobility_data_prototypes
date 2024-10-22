# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 11:41:11 2023

@author: evan.baker
"""


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from functools import reduce

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
from analysis.unexpectedness.avg_non_inbound_trips import *
from analysis.isochrone_Exceedance.exceedance_utils import *
from src.visualise.map_at_sub_la import *
from analysis.utils import *



             
#commented out because this is SLOW (~48 mins for whole UK; ~4 mins for only Exeter)
whole_uk = True
LAD_of_interest = "Camden" #this is only relelvant at this stage to choose what region of isochrones to load
#and to only get a subset of trips from the O2 data if whole_uk = False. We can change this later if need be.
    
Region_of_interest_short, Region_of_interest_long = LA_to_Isochrone_region_finder(LAD_of_interest)
    
#download_avg_non_inbound_trips(whole_uk = whole_uk, LAD_of_interest = LAD_of_interest) #takes a while - only do once
trips = load_avg_non_inbound_trips(whole_uk = whole_uk, LAD_of_interest = LAD_of_interest)
trips = process_trips_get_weighted_avg_week_end(trips)


#load in relevant isochrone (should load them all in)
isochrone = gpd.read_file("Q:/GI_Data/ONS/Isochrones/Clean/" + Region_of_interest_short + "/" + Region_of_interest_long + ".shp") 
#if scottish, change name...
isochrone = isochrone.rename(columns={"OA11CD": "OA21CD"})


# #ok, now we need to union all these geometries up into one shape per MSOA, per timeframe
# #lets use the OAs of MSOA pop weighted centroids


#get MSOA centroids

msoa_PWCs = get_all_small_areas_PWCs()
msoa_PWCs.rename_geometry("MSOA_centroids", inplace=True)

#since we only have some isochrone we also only want to match some MSOAs for now
#so get all reasonably related MSOAs only
MSOA_LA_lookup = build_msoa_lad_itl_lookup()
MSOAs_in_LAD = MSOA_LA_lookup.loc[MSOA_LA_lookup["LAD22NM"]==LAD_of_interest]
allowed_MSOAs = MSOAs_in_LAD["MSOA11CD"].unique()
msoa_PWCs = msoa_PWCs[msoa_PWCs["MSOA11CD"].isin(allowed_MSOAs)]


#get OA centroid is closest to each MSOA centroid
isochrone_OA_nodes = gpd.GeoDataFrame(isochrone["OA21CD"], geometry = gpd.points_from_xy(isochrone['node_X'], isochrone['node_Y']), crs = "EPSG:27700")
MSOA_OAs = gpd.sjoin_nearest(isochrone_OA_nodes, msoa_PWCs, how='right')
MSOA_OAs = MSOA_OAs[["MSOA11CD", "OA21CD"]]
MSOA_OAs = MSOA_OAs.drop_duplicates()


#now get the isochrone for each MSOA, using the isochrones for those centroids
MSOA_isochrone = isochrone.merge(MSOA_OAs, left_on = "OA21CD", right_on = "OA21CD", how = "inner")

#and also swap the MSOA centroids for the MSOA centroid nearest OA nodes
MSOA_OAs = MSOA_OAs.merge(isochrone_OA_nodes, how = "left", on = "OA21CD")
MSOA_OAs = MSOA_OAs.drop_duplicates()
MSOA_OAs = gpd.GeoDataFrame(MSOA_OAs, geometry=MSOA_OAs.geometry)

#now convert the isochrone into a list of MSOA (centroids) that you can reach from the source MSOA centroid
MSOA_isochrone_MSOA = gpd.sjoin(MSOA_isochrone, MSOA_OAs, how='inner', predicate='contains')


#now, every MSOA should be able to get to itself within 15 mins, so lets check that
test = MSOA_isochrone_MSOA.copy()
test_900 = test[test["iso_cutoff"] ==900]
bad_ones = set(test_900["MSOA11CD_left"]) - set(test_900["MSOA11CD_right"]) 
print("These MSOAs can't get to themselves within 15 mins! If this list is not empty, something has gone wrong:", bad_ones)


#and then if need be we can plot some of this
# bad_ones_list = [i for i in bad_ones]
# bad_one = bad_ones_list[2]

# bad_OA = test_900[test_900["MSOA11CD_left"] == bad_one]["OA21CD"].iloc[0]
# test2 = isochrone[isochrone["OA21CD"] == bad_OA]
# ax = test2[test2["iso_cutoff"] == 900].plot()
# ax.scatter(test2["node_X"], test2["node_Y"], color = "red")

# test3 = msoa_PWCs[msoa_PWCs["MSOA11CD"] == bad_one]
# ax.scatter(test3.geometry.x, test3.geometry.y, color = "yellow")

# xmin,xmax = ax.get_xlim()

# ymin,ymax = ax.get_ylim()


# ax.scatter(isochrone["node_X"], isochrone["node_Y"], color = "black")
# plt.xlim(xmin, xmax)
# plt.ylim(ymin, ymax)


#now get the trip data for the LA of itnerest
LAD_of_interest = LAD_of_interest
#LAD_of_interest = "Camden" 

#load in MSOA to LAD lookup
MSOAs_in_LAD = MSOA_LA_lookup.loc[MSOA_LA_lookup["LAD22NM"]==LAD_of_interest]
allowed_MSOAs = MSOAs_in_LAD["MSOA11CD"].unique()
#and only consider those within LA_of_interest
trips_LA = trips[pd.DataFrame(trips.start_msoa.tolist()).isin(allowed_MSOAs).any(axis = 1).values]




#get the results for all 4 possible time thresholds
time_thresholds = [15, 30, 45, 60]
isochrone_ratio_results = []
for time_threshold in time_thresholds: 
    isochrone_ratio_result = isochrone_ratio_calculator(MSOA_isochrone_MSOA, trips_LA, time_threshold = time_threshold)
    isochrone_ratio_result = isochrone_ratio_result.add_suffix(time_threshold)
    isochrone_ratio_result = isochrone_ratio_result.rename(columns={"start_msoa"+str(time_threshold): "start_msoa"})
    isochrone_ratio_results.append(isochrone_ratio_result.copy())

isochrone_ratio = reduce(lambda df1,df2: pd.merge(df1,df2,on='start_msoa'), isochrone_ratio_results)


#plot
msoas = get_all_small_areas()


msoas = msoas.merge(isochrone_ratio, left_on = "msoa11cd", right_on = "start_msoa", how = "inner")


time_mins = 15
plot_map_manual_breakpoints(msoas, 'trips_within_geography_perc'+str(time_mins), 
         suptitle="Percentage of trips made that could be reached \n by public transport in " + str(time_mins) + " minutes (" + LAD_of_interest + ")", 
         plot_title="% of trips", 
         source = "Source: O2 motion data; ONS Isochrones",
         colour_scheme = "UserDefined",
         breakpoints = [20,40,60,80],
         colors = map_lu_partnership_colour_scale[::-1])





time_mins = 60
plot_map_manual_breakpoints(msoas, 'trips_within_geography_perc'+str(time_mins), 
         suptitle="Percentage of trips made that could be reached \n by public transport in " + str(time_mins) + " minutes (" + LAD_of_interest + ")", 
         plot_title="% of trips", 
         source = "Source: O2 motion data; ONS Isochrones",
         colour_scheme = "UserDefined",
         breakpoints = [60,70,80,90],
         colors = map_lu_partnership_colour_scale[::-1])
