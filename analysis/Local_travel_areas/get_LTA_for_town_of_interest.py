# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 12:18:13 2024

@author: gordon.donald
"""

#Script which will get the LTAs for a town, for all times, for commutes, and for the morning commute period.


import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd
import time

from analysis.utils import get_BUAs, get_BUA_pop
from analysis.Local_travel_areas.LTA_functions import get_BUA_LTA, plot_LTAs_around_BUA
from analysis.Local_travel_areas.LTA_queries import *

BUAs=get_BUAs()

msoa_bua_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA_lookup.csv")

SINGLE_BUA=False
MORNING_ONLY=False # DAP doesn't have enough memory to do both the full day and morning commute period LTAs at once. Need to use a switch flag to do this.

if SINGLE_BUA:
    #BUA of interest
    bua_commission = "Scunthorpe"
   
    our_msoas = list(msoa_bua_lookup[msoa_bua_lookup.BUA22NM==bua_commission].msoa11cd)

    #Querying the whole dataset might use too much memory and cause issues for a single use, but way less efficient if we're doing multiple BUAs
    #For the query want to have these in a string
    string =  "('"+  "', '".join(our_msoas) +"')"

    def get_data_for_all_weekdays_modified():
        query = f'''
        SELECT start_msoa, end_msoa, SUM(avg_daily_trips) daily_trips, journey_purpose, hour_part
        FROM Process.tb_O2MOTION_ODMODE_Weekly
        WHERE (DATEPART(dw, start_date) = 1)
        AND (journey_purpose_direction NOT IN ('IB_HBW', 'IB_HBO'))
        AND (start_msoa IN {string})
        GROUP BY start_msoa, end_msoa, hour_part, journey_purpose;
        '''
        return(submit_sql_query(query))

    #Query all data - run once and here if we need the purpose and time of day, get that too and process later.
    start=time.time()
    data = get_data_for_all_weekdays_modified()
    end=time.time()

    #Print out time taken for this query (seconds)
    print (end-start)

else:
    #Query all data - run once and here if we need the purpose and time of day, get that too and process later.
    start=time.time()
    if MORNING_ONLY:
        data = get_data_for_all_weekdays_morning_commute_time(window_start=7, window_end=10)
    else:
        data = get_data_for_all_weekdays()
    end=time.time()

all_time_data = data[['start_msoa', 'end_msoa', 'daily_trips']].groupby(['start_msoa', 'end_msoa']).sum().reset_index()

#commute_tagged_data = data[data.journey_purpose=='Commute']
#commute_tagged_data = commute_tagged_data[['start_msoa', 'end_msoa', 'daily_trips']].groupby(['start_msoa', 'end_msoa']).sum().reset_index()

#commute_time_end=10
#commute_time_start=7
#morning_data = data[(data.hour_part>commute_time_start) & (data.hour_part<commute_time_end)]
#morning_data = morning_data[['start_msoa', 'end_msoa', 'daily_trips']].groupby(['start_msoa', 'end_msoa']).sum().reset_index()

if SINGLE_BUA:
    #plot_LTAs_around_BUA(bua_commission, commute_tagged_data, title="The Local Travel Area containing 90% of journeys from Scunthorpe tagged as commuting by O2", BUAs=BUAs)
    figure = plot_LTAs_around_BUA(bua_commission, all_time_data, title=f'The Local Travel Area containing 90% of journeys from {bua_commission}', BUAs=BUAs)
    figure.savefig(f"Q:/SDU/Mobility/Outputs/LTAs/{bua_commission}.png",  bbox_inches="tight", dpi=400)

    figure=plot_LTAs_around_BUA(bua_commission, morning_data, title="The Local Travel Area containing 90% of journeys from Scunthorpe between 7am and 10am", BUAs=BUAs)
    figure.savefig(f"Q:/SDU/Mobility/Outputs/LTAs_morning/{bua_commission}.png", bbox_inches="tight",  dpi=400)

else:
    bua_pop = get_BUA_pop()
    buas_used = pd.read_csv("Q:/SDU/Mobility/Data/Processed/towns_ltas.csv")
    bua_list = list(buas_used.Town.drop_duplicates())
    for bua_commission in bua_list:
        if MORNING_ONLY:
            figure=plot_LTAs_around_BUA(bua_commission, all_time_data, title=f"The Local Travel Area containing 90% of journeys from {bua_commission} between 7am and 10am", BUAs=BUAs)
            figure.savefig(f"Q:/SDU/Mobility/Outputs/LTAs_morning/{bua_commission}.png", bbox_inches="tight",  dpi=400)
        else: 
            figure = plot_LTAs_around_BUA(bua_commission, all_time_data, title=f'The Local Travel Area containing 90% of journeys from {bua_commission}', BUAs=BUAs)
            figure.savefig(f"Q:/SDU/Mobility/Outputs/LTAs/{bua_commission}.png",  bbox_inches="tight", dpi=400)
  


