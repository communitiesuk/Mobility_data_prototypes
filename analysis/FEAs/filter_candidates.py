# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 10:39:55 2024

@author: gordon.donald
"""

import geopandas as gpd
import pandas as pd
from analysis.utils import *
import contextily as cx
import matplotlib.pyplot as plt


import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

#Read in shapes.
#Not used.
#communities = gpd.read_file("Q:/SDU/Mobility/Outputs/NetworkAnalysis/CommunitiesStatsAndRanking_simplified_1.gpkg")

#Read in community data, with lists of MSOA code
community_data = pd.read_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/Community_ranking_simplified.csv")


def process_string_list(string):
    our_list = string.replace("(", "").replace(")", "").replace("'", "").replace(" ", "").split(",")
    return our_list

def get_shared_elements(list1, list2):
    list1 = process_string_list(list1)
    list2 = process_string_list(list2)
    
    denom = len(list1)
    shared = {element for element in list1 if element in list2}
    num = len(shared)
    return (num/denom)

#Test these functions
g1 = community_data.iloc[0]['members']
g2 = community_data.iloc[1]['members']

get_shared_elements(g1, g2)
get_shared_elements(g2, g1)

#Compare lists to find the ones with significant overlaps.
#Thresholds - try 90%?
overlap_threshold = 0.9 #Where lists share over 90% of elements, call them the same.

#Remove candidates with populations too high and low
community_data = community_data[community_data.population<3e6]
community_data = community_data[community_data.population>300e3]

#Use the index as an id for now
community_data.rename(columns={"Unnamed: 0": "id"}, inplace=True)

#Start with the best community matching each as itself; we'll update this as we test which are overlapping subtantially.
community_data['best_community'] = community_data['id']

def test_indepedence(community_data, row1, row2, threshold=overlap_threshold):
    msoas1 = community_data.iloc[row1]['members']
    msoas2 = community_data.iloc[row2]['members']
    
    if get_shared_elements(msoas1, msoas2) > overlap_threshold and get_shared_elements(msoas2, msoas1) > overlap_threshold:
        #These two are basically the same
        travel1 = community_data.iloc[row1]['travel_within']
        travel2 = community_data.iloc[row2]['travel_within']
        if travel1 > travel2:
            community_data.iloc[row2, 9] = community_data.iloc[row1]['best_community'] #Column 9 is the one we want to change (best_community)
        elif travel2 > travel1:
            community_data.iloc[row1, 9] = community_data.iloc[row2]['best_community']
    return community_data

#Is this inefficient? Maybe, but completed while I made a cup of tea, so fine.
for row1 in range(len(community_data)):
    for row2 in range(row1, len(community_data)):
        community_data = test_indepedence(community_data, row1, row2)
        
#Filter just the communities which are the best of overlapping ones.
best_fit_communities = community_data[community_data.id == community_data.best_community]

#Plotting communities
msoas=get_all_small_areas()
key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key
lad_bounds = gpd.read_file("Q:/GI_Data/Boundaries/LAD_MAY_2021_UK_BFE_V2.shp")

#Test to plot individual communities.
def plot_community(comm_i):
    f, ax = plt.subplots(figsize=(12, 12))
    our_msoas = process_string_list(best_fit_communities.iloc[comm_i].members)
    msoas_to_plot = msoas[msoas.msoa11cd.isin(our_msoas)]        
    msoas_to_plot.plot(ax=ax, alpha=0.7)  
    lad_bounds.overlay(msoas_to_plot).boundary.plot(ax=ax)
    cx.add_basemap(ax, source=basemap_url, crs=msoas.crs)
      
plot_community(0)

#As a quick check to see where our advice is clear, find the options for each MSOA.
def count_candidates_per_msoa(msoa_code):
    count = sum([msoa_code in best_fit_communities.iloc[i].members for i in range(len(best_fit_communities))])
    return count

msoas['options'] = msoas.apply(lambda row: count_candidates_per_msoa(row.msoa11cd), axis=1)
msoas.plot('options')
msoas.options.hist()

#Combine MSOAs to LADs to see where it's clear what the advice for an LAD would be.
msoa_to_lad_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/MSOA_(2011)_to_MSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_England_and_Wales_(Version_2).csv")
msoa_lad = msoa_to_lad_lookup[['MSOA11CD', 'LAD22CD']]

#First test for LAs, where do all MSOAs within an LTLA agree on which community they're in?
test="E08000023" #North Tyneside
def get_msoas_for_lad(lad_code):
    return list(msoa_lad[msoa_lad.LAD22CD==test].MSOA11CD)

get_msoas_for_lad(test)

