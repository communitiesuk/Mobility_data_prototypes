# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 17:10:13 2024

@author: gordon.donald
"""

#Get MSOA to MSOA links and find MSOA end-point

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd


import matplotlib.pyplot as plt
#use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
#Basemap
import contextily as cx

from analysis.Local_travel_areas.LTA_queries import *
from analysis.Local_travel_areas.LTA_functions import *
from analysis.msoa_jobs_functions import *
from analysis.utils import *

#This takes a while.
weekday_data = get_data_for_all_weekdays()

#For each MSOA, want to find a link mapping it to the MSOA with most journeys (not same MSOA).
links = weekday_data[weekday_data.start_msoa != weekday_data.end_msoa].sort_values('daily_trips', ascending=False).drop_duplicates('start_msoa').reset_index()

#This forms effectively a directed graph. Want to find how many closed loops it has, to see how useful this can be.
def get_link(msoa_code):
    dest = links[links.start_msoa==msoa_code].end_msoa.iloc[0]
    return(dest)

def find_endpoint(msoa_code, chain=[]):
    dest = get_link(msoa_code)
    if dest in chain:
        return(dest)
    else:
        chain.append(dest)
        return(find_endpoint(dest, chain))

links['End_pt'] = links['start_msoa'].apply(lambda x: find_endpoint(x, chain=[]))

#But how many loops are there? Not all of these are in unique loops?
def get_loop(msoa_code, chain=[]):
    dest = get_link(msoa_code)
    if dest in chain:
        chain.sort()
        return(chain[0])
    else:
        chain.append(dest)
        return(get_loop(dest, chain))
    
links['End_loop'] = links['End_pt'].apply(lambda x: get_loop(x, chain=[]))

len(links['End_loop'].drop_duplicates())
ends = links['End_loop'].value_counts().reset_index()
ends.columns=['Centre', 'N_MSOA']

msoas=get_all_small_areas()
msoa_groups = msoas.merge(links, left_on='msoa11cd', right_on='start_msoa')
msoa_main_groups = msoa_groups[msoa_groups.End_loop.isin(ends[ends.N_MSOA>50].Centre)]

msoa_groups = msoa_groups.merge(ends, left_on='End_loop', right_on='Centre')
msoa_groups.plot('N_MSOA')

