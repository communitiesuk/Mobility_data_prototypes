# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 15:29:44 2023

@author: evan.baker
"""
import pandas as pd
import pyodbc 
from sklearn import preprocessing
LE = preprocessing.LabelEncoder()
import time

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
from analysis.utils import *
          
server = 'DAP-SQL01\CDS' 
database = 'Place'

# ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
cnxn = pyodbc.connect(driver='{SQL Server Native Client 11.0}', 
                      host=server, database=database, trusted_connection='yes')


#load in MSOA to LAD lookup
MSOA_LA_lookup = build_msoa_lad_itl_lookup()

#what is the LA we want to look into? Note, in practice, we would want to subset the data at the very last step
#only subsetting it now for testing / saving memory etc, but it will change the results



def download_avg_non_inbound_trips(whole_uk = False, LAD_of_interest = "Exeter"):
    MSOAs_in_LAD = MSOA_LA_lookup.loc[MSOA_LA_lookup["LAD22NM"]==LAD_of_interest]
    MSOAs_in_LAD_sql_list = tuple(MSOAs_in_LAD["MSOA11CD"].unique())
    train_on_whole_uk = True #set this to true to not just use one LA data to train the nueral network (proper way of doing it, but super slow)
    
    if train_on_whole_uk == False:
        query = '''
        SELECT start_msoa, end_msoa, SUM(avg_daily_trips) AS avg_daily_trips, LEFT(RIGHT(FileName, CHARINDEX('_',REVERSE(FileName))-1),7) AS day_type
        FROM Process.tb_O2MOTION_ODMODE_Weekly
        WHERE journey_purpose_direction NOT IN ('IB_HBW', 'IB_HBO')
        AND start_msoa IN {}
        GROUP BY start_msoa, end_msoa, LEFT(RIGHT(FileName, CHARINDEX('_',REVERSE(FileName))-1),7)
        '''.format(MSOAs_in_LAD_sql_list)
    else:
        query = '''
        SELECT start_msoa, end_msoa, SUM(avg_daily_trips) AS avg_daily_trips, LEFT(RIGHT(FileName, CHARINDEX('_',REVERSE(FileName))-1),7) AS day_type
        FROM Process.tb_O2MOTION_ODMODE_Weekly
        WHERE journey_purpose_direction NOT IN ('IB_HBW', 'IB_HBO')
        GROUP BY start_msoa, end_msoa, LEFT(RIGHT(FileName, CHARINDEX('_',REVERSE(FileName))-1),7)
        '''
    
    #commented out because this is SLOW (~48 mins for whole UK; ~4 mins for only Exeter)
    st_query=time.time()
    trips = pd.read_sql_query(query,cnxn) 
    #save queried SQL data
    if whole_uk:
        save_suffix = "whole_UK"
    else:
        save_suffix = LAD_of_interest
    trips.to_csv("Q:\SDU\Mobility\Data\Processed\Processed_Mobility/avg_non_inbound_trips_query_results_"+save_suffix+".csv",
                  index = False)
    et_query=time.time()
    print(et_query-st_query)


def load_avg_non_inbound_trips(whole_uk = False, LAD_of_interest = "Exeter"):
# #and here's how to reload
    if whole_uk:
        save_suffix = "whole_UK"
    else:
        save_suffix = LAD_of_interest
    trips = pd.read_csv("Q:\SDU\Mobility\Data\Processed\Processed_Mobility/avg_non_inbound_trips_query_results_"+save_suffix+".csv")
    
    return(trips)




def process_trips_get_weighted_avg_week_end(trips, weekday_col_name = "weekday", weekend_col_name = "weekend"):
    #get total_avg-daily trips, weighted avg between weekend and weekday
    trips = trips.pivot(index=["start_msoa", "end_msoa"],columns="day_type", values="avg_daily_trips").reset_index()
    #replace NAs with 0
    trips.loc[trips[weekday_col_name].isna(), weekday_col_name] = 0
    trips.loc[trips[weekend_col_name].isna(), weekend_col_name] = 0
    trips["avg_daily_trips"] = (5*trips[weekday_col_name] + 4*trips[weekday_col_name])/9 #get weighted avg, weekday trips are from 5 working days, weekend are from 4 weekend days
    trips = trips.drop(columns = [weekend_col_name, weekday_col_name]).reset_index(drop = True)
    
    return(trips)
