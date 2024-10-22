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
import sys
sys.path.append(repo.working_tree_dir)

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

#Side question having run the query. Inter-regional travel and English IMD.
imd_msoa = pd.read_csv("Q:/SDU/Mobility/Data/Auxiliary_data/imd2019_msoa_level_data.csv")
imd_msoa=imd_msoa[['MSOAC', 'REG', 'MSOARANK', 'MSOADECILE', 'MSOAQUINTILE']]
data_imd = weekday_data.merge(imd_msoa, left_on='start_msoa', right_on='MSOAC').merge(imd_msoa, left_on='end_msoa', right_on='MSOAC')

trips = data_imd[['MSOAQUINTILE_x', 'MSOAQUINTILE_y', 'daily_trips']].groupby(['MSOAQUINTILE_x', 'MSOAQUINTILE_y']).sum('daily_trips').reset_index()

map_lu_partnership_colour_scale_rev = map_lu_partnership_colour_scale.copy()
map_lu_partnership_colour_scale_rev.reverse()

col_alpha = ['rgba(255,255,204,0.8)','rgba(161,218,180,0.8)','rgba(65,182,196,0.8)','rgba(44,127,184,0.8)','rgba(37,52,148,0.8)']
col_alpha.reverse()

import plotly.graph_objects as go

fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label = list(trips.MSOAQUINTILE_x.drop_duplicates())*2,
            x = [0.001]*5+[0.999]*5,
            y = [0.801-x*0.2 for x in range(5)]*2,
            color=map_lu_partnership_colour_scale_rev*2
            ),
        link = dict(
            source = [x-1 for x in list(trips.MSOAQUINTILE_x)],
            target = [x+4 for x in list(trips.MSOAQUINTILE_y)],
            value = list(trips.daily_trips),
            color= [val for val in col_alpha for _ in range(5)]
            ),
        arrangement='snap'
    )])
fig.add_annotation(text='More deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=1.05,
                    borderwidth=0)
fig.add_annotation(text='More deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=1.05,
                    borderwidth=0)
fig.update_layout(title_text = "Travel by IMD quintile", font_size=12, font_color="black", height=800, width=1400)
fig.write_image("Q:/SDU/SDU_real_time_indicators/outputs/mobility/imd_qunitile_flow.png")

#Alternative is to do IMD deciles
trips_dec = data_imd[['MSOADECILE_x', 'MSOADECILE_y', 'daily_trips']].groupby(['MSOADECILE_x', 'MSOADECILE_y']).sum('daily_trips').reset_index()

fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label = list(trips_dec.MSOADECILE_x.drop_duplicates())*2,
            x = [0.001]*10+[0.999]*10,
            y = [0.801-x*0.2 for x in range(10)]*2,
            color=[val for val in map_lu_partnership_colour_scale_rev for _ in range(2)]*2
            ),
        link = dict(
            source = [x-1 for x in list(trips_dec.MSOADECILE_x)],
            target = [x+9 for x in list(trips_dec.MSOADECILE_y)],
            value = list(trips_dec.daily_trips),
            color= [val for val in map_lu_partnership_colour_scale_rev for _ in range(20)]
            ),
        arrangement='snap'
    )])
fig.add_annotation(text='More deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=1.05,
                    borderwidth=0)
fig.add_annotation(text='More deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=1.05,
                    borderwidth=0)
fig.update_layout(title_text = "Travel by IMD decile", font_size=12, font_color="black", height=800, width=1400)
fig.write_image("Q:/SDU/SDU_real_time_indicators/outputs/mobility/imd_decile_flow.png")

#Check travel connecting MSOAs in same IMD quintile/decile.
trips[trips.MSOAQUINTILE_x==trips.MSOAQUINTILE_y].daily_trips.sum() / trips.daily_trips.sum()
trips_dec[trips_dec.MSOADECILE_x==trips_dec.MSOADECILE_y].daily_trips.sum() / trips_dec.daily_trips.sum()

#Check how much travel is to same MSOA
data_imd[data_imd.start_msoa==data_imd.end_msoa].daily_trips.sum() / data_imd.daily_trips.sum()

#We can plot for journeys between MSOAs
data_imd = data_imd[data_imd.MSOAC_x != data_imd.MSOAC_y]
trips = data_imd[['MSOAQUINTILE_x', 'MSOAQUINTILE_y', 'daily_trips']].groupby(['MSOAQUINTILE_x', 'MSOAQUINTILE_y']).sum('daily_trips').reset_index()

fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label = list(trips.MSOAQUINTILE_x.drop_duplicates())*2,
            x = [0.001]*5+[0.999]*5,
            y = [0.801-x*0.2 for x in range(5)]*2,
            color=map_lu_partnership_colour_scale_rev*2
            ),
        link = dict(
            source = [x-1 for x in list(trips.MSOAQUINTILE_x)],
            target = [x+4 for x in list(trips.MSOAQUINTILE_y)],
            value = list(trips.daily_trips),
            color= [val for val in col_alpha for _ in range(5)]
            ),
        arrangement='snap'
    )])
fig.add_annotation(text='More deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=1.05,
                    borderwidth=0)
fig.add_annotation(text='More deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=1.05,
                    borderwidth=0)
fig.update_layout(title_text = "Inter-MSOA travel by IMD quintile", font_size=12, font_color="black", height=800, width=1400)
fig.write_image("Q:/SDU/SDU_real_time_indicators/outputs/mobility/imd_intermsoa_qunitile_flow.png")

#Repeat for travel to different regions -- as same MSOA for origin/destination is obviosuly same region, we can filter again for different regions
data_imd = data_imd[data_imd.REG_x != data_imd.REG_y]
    #data_imd[['MSOAQUINTILE_x', 'MSOAQUINTILE_y']].sort_values(['MSOAQUINTILE_x']).value_counts()

DISTANCE_FILTER=False
if DISTANCE_FILTER:
    #Can we exclude trips which are to different ITL1 but are short (e.g. under 20km)
    msoa_pwc = pd.read_csv("Q:/SDU/Mobility/Data/PWCs/MSOA_Dec_2011_PWC_in_England_and_Wales_2022_-7657754233007660732.csv")
    msoa_pwc = msoa_pwc[['MSOA11CD', 'x', 'y']]

    data_imd = data_imd.merge(msoa_pwc, left_on='start_msoa', right_on='MSOA11CD').merge(msoa_pwc, left_on='end_msoa', right_on='MSOA11CD')

#Get rid off stuff we definitely don't need.
    data_imd = data_imd[['start_msoa',
                         'end_msoa',
                         'daily_trips',
                         'MSOADECILE_x',
                         'MSOAQUINTILE_x',
                         'MSOADECILE_y',
                         'MSOAQUINTILE_y',
                             'x_x',
                             'y_x',
                             'x_y',
                             'y_y']]

    def distance(x1, x2, y1, y2):
        d2 = (x1-x2)**2 + (y1-y2)**2
        return(d2**0.5/1000)

    data_imd['distance'] = data_imd[['x_x', 'x_y', 'y_x', 'y_y']].apply(lambda row: distance(row.x_x, row.x_y, row.y_x, row.y_y), axis=1)

    data_imd = data_imd[data_imd.distance > 20] # 20km approx 12.5 miles


trips = data_imd[['MSOAQUINTILE_x', 'MSOAQUINTILE_y', 'daily_trips']].groupby(['MSOAQUINTILE_x', 'MSOAQUINTILE_y']).sum('daily_trips').reset_index()

fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label = list(trips.MSOAQUINTILE_x.drop_duplicates())*2,
            x = [0.001]*5+[0.999]*5,
            y = [0.801-x*0.2 for x in range(5)]*2,
            color=map_lu_partnership_colour_scale_rev*2
            ),
        link = dict(
            source = [x-1 for x in list(trips.MSOAQUINTILE_x)],
            target = [x+4 for x in list(trips.MSOAQUINTILE_y)],
            value = list(trips.daily_trips),
            color= [val for val in col_alpha for _ in range(5)]
            ),
        arrangement='snap'
    )])
fig.add_annotation(text='More deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived origin', 
                    showarrow=False,
                    x=0.0,
                    y=1.05,
                    borderwidth=0)
fig.add_annotation(text='More deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=-0.05,
                    borderwidth=0)
fig.add_annotation(text='Less deprived destination', 
                    showarrow=False,
                    x=1.0,
                    y=1.05,
                    borderwidth=0)
fig.update_layout(title_text = "Inter-regional travel by IMD quintile", font_size=12, font_color="black", height=800, width=1400)
fig.write_image("Q:/SDU/SDU_real_time_indicators/outputs/mobility/imd_interregion_qunitile_flow.png")
