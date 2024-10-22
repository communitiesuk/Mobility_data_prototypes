# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 14:27:13 2023

@author: gordon.donald
"""

#Visualise the processed data using number of msoas needed to account for x% of journeys from a given origin.

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd
msoa_destinations = pd.read_csv("Q:SDU/Mobility/Data/Processed/Nodes/MSOA_destination_count.csv")

from src.visualise.map_at_sub_la import *
from analysis.utils import *
from src.visualise.bucket_chart import *
import plotly.graph_objects as go

import plotly.io as pio
pio.renderers.default = 'svg'
#pio.renderers.default = 'browser'


msoas= get_all_small_areas()
lads = gpd.read_file("Q:/GI_Data/Boundaries/LAD_MAY_2021_UK_BFE_V2.shp")

def get_name_from_code(la_code):
    name = list(lads[lads['LAD21CD']==la_code]['LAD21NM'])[0]
    return(name)

msoa_destinations['ratio_80'] = msoa_destinations['weekday_80']/msoa_destinations['weekend_80']

plot_at_small_area(msoa_destinations, 'weekday_90', lads, msoas, "E06000002", 'msoa11cd', 'msoa11cd',
                   "MSOAs", suptitle=get_name_from_code("E06000002"), source="Source: O2 Motion")

map_data = msoas.merge(msoa_destinations)

plot_map(map_data, 'weekday_90', plot_title="Number of MSOAs", suptitle="Number of destinations per MSOA", source="Source: O2 Motion",
             line_width=0, colour_scheme='quantiles')
#This is the corresponding histogram to the map.
msoa_destinations['weekday_90'].plot(kind='hist', bins=100, grid=False, title='Number of destination MSOAs')

plot_map(map_data, 'ratio_80', plot_title="Ratio of MSOAs", suptitle="Weekday / Weekend destination count", source="Source: O2 Motion",
             line_width=0, colour_scheme='equalinterval')


lookup = build_msoa_lad_itl_lookup()
msoa_w_lookup = msoa_destinations.merge(lookup, left_on='msoa11cd', right_on='MSOA11CD')


bucket_chart(msoa_w_lookup, 'ITL121NM', 'weekday_100', 'Number of destinations', 'msoa11nm', mean_values_list='auto').show()

