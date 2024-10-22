# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 12:00:45 2023

@author: gordon.donald
"""

#Get the footfall metrics for the 55 towns.
import pandas as pd
import geopandas as gpd
import pyodbc

from src.utils.msoas_bua_lookup import get_msoas_in_BUA

#Reuse some pieces from the service density.
BUAs = gpd.read_file("Q:\SDU\Towns_indicative_selection_QA\Shapefiles\BUA_2022_GB_2824430073212747649\BUA_2022_GB.shp")

#Do all towns, but keep population
bua_pop = pd.read_excel("Q:/SDU/Towns_indicative_selection_QA/Data/OFF-SEN - BUA Analysis - LUWPs Ranking v01.02.xlsx", sheet_name='BUA_Population', skiprows=2)
bua_pop_wales = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Data/BUA_pop-wales.csv", skiprows=2, encoding = 'unicode_escape') #Wales sheet of this data)
#bua_pop_scotland = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Data/Scotland_settlement_pop.csv")

bua_pop = bua_pop[['BUA name', 'BUA code', 'Counts']]
bua_pop_wales = bua_pop_wales[['BUA name', 'BUA code', ' Counts ']]
#bua_pop_scotland = bua_pop_scotland[['Settlement name', 'Settlement code', 'population']]

bua_pop.columns = ['BUA22NM', 'BUA22CD', 'Population']
bua_pop_wales.columns = ['BUA22NM', 'BUA22CD', 'Population']
#bua_pop_scotland.columns = ['BUA22NM', 'BUA22CD', 'Population']

bua_pop_all = pd.concat([bua_pop, bua_pop_wales])

bua_filter = bua_pop_all[(bua_pop_all.Population > 8e3)]
BUAs_filter = BUAs[BUAs.BUA22NM.isin(bua_filter.BUA22NM)]


#I want the footfall in all towns in the baseline (can then get the 55 towns by pulling out of the baseline dataset)
server = 'DAP-SQL01\CDS' 
database = 'Place'

# ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
cnxn = pyodbc.connect(driver='{SQL Server Native Client 11.0}', 
                      host=server, database=database, trusted_connection='yes')

#This will query the total journeys to each msoa.
query = '''
    SELECT start_date, end_msoa, SUM(avg_daily_trips) daily_trips
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE journey_purpose_direction = 'OB_HBO' OR journey_purpose_direction = 'NHBO'
    GROUP BY start_date, end_msoa;
    '''
msoa_destination_trips = pd.read_sql_query(query, cnxn) 
weeks = msoa_destination_trips['start_date'].nunique()

msoa_destination_trips['start_date'] = pd.to_datetime(msoa_destination_trips['start_date'])
msoa_destination_trips['weekday_weekend'] = msoa_destination_trips['start_date'].dt.dayofweek

msoa_destination_trips.loc[msoa_destination_trips['weekday_weekend'] == 5, 'weekday_weekend'] = 4 #2 weekend days, but multiply by 2 for two grouped weekends.
msoa_destination_trips.loc[msoa_destination_trips['weekday_weekend'] == 0, 'weekday_weekend'] = 5 #And 5 weekdays

msoa_destination_trips['journeys'] = msoa_destination_trips['weekday_weekend']*msoa_destination_trips['daily_trips']

msoa_total_footfall = msoa_destination_trips[['end_msoa', 'journeys']].groupby('end_msoa').sum().reset_index()
msoa_total_footfall.journeys /=365 #Divide by years per day for daily average over whole year

#Now we want total footfall in BUAs we're calling towns.

def get_footfall_for_BUA(BUA_code):
    msoas = get_msoas_in_BUA(BUA_code)
    trips = msoa_total_footfall[msoa_total_footfall.end_msoa.isin(msoas)].journeys.sum()
    return(trips)

BUA_store = []
for BUA_i in range(len(BUAs_filter)):
#for BUA_i in range(5):
    print(BUA_i)
    code = BUAs_filter.iloc[BUA_i]['BUA22CD']
    name = BUAs_filter.iloc[BUA_i]['BUA22NM']
    footfall = get_footfall_for_BUA(code)
    BUA_store.append([code, name, footfall])
    
BUA_footfall = pd.DataFrame(BUA_store, columns = ['BUA22CD', 'BUA22NM', 'footfall'])

average_footfall = BUA_footfall.footfall.mean()
#Round footfall to neareat 500?
BUA_footfall.footfall = BUA_footfall.footfall.round(-2)

BUA_footfall = BUA_footfall.merge(bua_filter)

BUA_footfall.to_csv("Q:/SDU/Mobility/Data/Processed/LDC_Density/Towns/all_towns/all_towns_O2_footfall_EW.csv", index=False)
