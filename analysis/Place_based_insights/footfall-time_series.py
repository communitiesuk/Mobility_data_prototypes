# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 15:35:55 2024

@author: gordon.donald
"""

#Borrwed for Sean's notebook on seasonality study to begin with. Looking to adapt to answer questions of footfall change detection.

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

#local imports
from src.visualise.map_at_sub_la import *
from src.visualise.line_chart import line_chart, apply_standard_graph_styling 
from src.utils.constants import diverging_colour_scale
from src.visualise.map_at_sub_la import plot_map, plot_region_map, get_location_name_data
from analysis.utils import *

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pyodbc
import plotly.express as px 
from osdatahub import NGD, Extent

server = 'DAP-SQL01\CDS' 
database = 'Place'

# ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
cnxn = pyodbc.connect(driver='{SQL Server Native Client 11.0}', 
                      host=server, database=database, trusted_connection='yes')
#1. get timeseries of destination trips for all msoas, weekday trips only
# Note: Weekend dates have DATEPART = 6, Weekdays have DATEPART = 1.
query = '''
    SELECT start_date, end_msoa, SUM(avg_daily_trips) daily_trips
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE DATEPART(dw, start_date) = 1
    GROUP BY start_date, end_msoa;
    '''

msoa_destination_trips = pd.read_sql_query(query, cnxn) 

# number of unique dates in the data, expecting 26 weekends when ingestion is finished
msoa_destination_trips['start_date'].nunique()

# find average daily trips across series for each msoa and join average trips to full timeseries
avg_destination_trips = msoa_destination_trips[['end_msoa', 'daily_trips']].groupby(["end_msoa"]).mean().round(1).reset_index()
avg_destination_trips.rename(columns={"daily_trips": "avg_daily_trips"}, inplace=True)
msoa_destination_trips = pd.merge(left=msoa_destination_trips, right=avg_destination_trips, on="end_msoa")

# find ratio of daily trips / avg daily trips for each msoa and date
msoa_destination_trips.loc[:, 'ratio'] = msoa_destination_trips['daily_trips'] / msoa_destination_trips['avg_daily_trips']
msoa_destination_trips = msoa_destination_trips.sort_values(by=["end_msoa", "start_date"])

# to plot, use msoa shapefiles
msoas = get_all_small_areas()

#apply 4 week rolling avg method for all MSOAs
msoa_destination_trips_4_week_rolling_ratio = msoa_destination_trips.groupby(['end_msoa'])['ratio'].rolling(4, min_periods=1).mean().reset_index(level=0)
msoa_destination_trips_4_week_rolling_ratio.rename(columns={"ratio": "4_week_rolling_ratio"}, inplace=True)
# merge with existing MSOA destination dataframe
msoa_destinations_plot_data = pd.merge(left=msoa_destination_trips, right=msoa_destination_trips_4_week_rolling_ratio['4_week_rolling_ratio'], left_index=True, right_index=True)

msoa_destinations_season_check = msoa_destinations_plot_data.loc[msoa_destinations_plot_data.groupby('end_msoa')['4_week_rolling_ratio'].idxmax()][['end_msoa', 'start_date', '4_week_rolling_ratio']]

# find msoas with seasonal patterns, 25% and 50% plus above the long term average number of daily trips
threshold = 0.5
msoa_destinations_season_check.loc[:, "seasonal_flag"] = "Non-seasonal"
msoa_destinations_season_check.loc[msoa_destinations_season_check["4_week_rolling_ratio"] > (1.25), "seasonal_flag"] = "Seasonal"
msoa_destinations_season_check.loc[msoa_destinations_season_check["4_week_rolling_ratio"] > (1 + threshold), "seasonal_flag"] = "Highly seasonal"

#Find the end points of the time series.
end_start = [msoa_destinations_plot_data.start_date.min(), msoa_destinations_plot_data.start_date.max()]
ends_of_data = msoa_destinations_plot_data[msoa_destinations_plot_data.start_date.isin(end_start)]
early_data = msoa_destinations_plot_data[msoa_destinations_plot_data.start_date == end_start[0]][['end_msoa', '4_week_rolling_ratio']]
late_data = msoa_destinations_plot_data[msoa_destinations_plot_data.start_date == end_start[1]][['end_msoa', '4_week_rolling_ratio']]

early_data.columns = ['msoa11cd', 'start']
late_data.columns = ['msoa11cd', 'end']

compare_data = early_data.merge(late_data)
compare_data['ratio'] = compare_data.end / compare_data.start

#Exclude MSOAs we classify as seasonal
#compare_data = compare_data.merge(msoa_destinations_season_check, left_on='msoa11cd', right_on='end_msoa')
#compare_data = compare_data[compare_data.seasonal_flag == 'Non-seasonal']



#GBF data
gbf=pd.read_excel("Q:/SDU/SDU_real_time_indicators/data/raw/GBF_sites/GBF postcodes - 30_01_2024.xlsx")
gbf=gbf[gbf.postcode!="na"] #Drop places with na given as postcode as the long/lat may be less reliable
geo_gbf = gpd.GeoDataFrame(gbf, geometry=gpd.points_from_xy(gbf.long, gbf.lat), crs="EPSG:4326")
geo_gbf = geo_gbf.to_crs(msoas.crs)

msoa_gbf=gpd.overlay(geo_gbf, msoas, how='intersection')
gbf_places = list(msoa_gbf.msoa11cd)

gbf_compare = compare_data[compare_data.msoa11cd.isin(gbf_places)]

def shorten_name(string, words=15):
    short = " ".join(string.split()[0:words])
    return(short)

def get_project_per_msoa(msoa):
    if len(msoa_gbf[msoa_gbf.msoa11cd==msoa]) >1:
        return('Multiple projects')
    else:
        project = msoa_gbf[msoa_gbf.msoa11cd==msoa].iloc[0]['project']
        return (shorten_name(project))

def get_msoa_name(msoa):
    name = msoa_gbf[msoa_gbf.msoa11cd==msoa].iloc[0]['msoa11nm']
    return (name)

gbf_compare["project"] = gbf_compare["end_msoa"].apply(lambda x: get_project_per_msoa(x))
gbf_compare["MSOA"] = gbf_compare["end_msoa"].apply(lambda x: get_msoa_name(x))

#Let's look at the 25 cases with most increase/decrease
#Although, also would be interested in places where building is done entirely in the time series.
places = list(gbf_compare.sort_values('ratio').tail(15).msoa11cd) + list(gbf_compare.sort_values('ratio').head(15).msoa11cd)
example_seasonal_destinations = msoa_destinations_plot_data.copy()
example_seasonal_destinations = example_seasonal_destinations[example_seasonal_destinations["end_msoa"].isin(places)]
example_seasonal_destinations = example_seasonal_destinations.sort_values(by=["end_msoa", "start_date"])
example_seasonal_destinations = example_seasonal_destinations.merge(gbf_compare[['msoa11cd', 'project', 'MSOA']], left_on='end_msoa', right_on="msoa11cd")

example_seasonal_destinations['label'] = example_seasonal_destinations['project']+ ": "+ example_seasonal_destinations['MSOA']

#fig = line_chart(data=example_seasonal_destinations, fig_title="Ratio of daily trips to yearly average daily trips in MSOAs",x_col= "start_date", y_col="4_week_rolling_ratio", y_lab="Ratio", colour_col="label", colour_col_label="GBF project")
#fig.update_layout(autosize=False, width=1600, height=800)

for i in range(len(places)):
    local_data = example_seasonal_destinations[example_seasonal_destinations.end_msoa==places[i]]
    fig = line_chart(data=local_data, fig_title=local_data.iloc[0]['label'], x_col= "start_date", y_col="4_week_rolling_ratio", y_lab="Footfall (scaled to annual average)")
    fig.update_layout(autosize=False, width=2000, height=800) 
    fig.show()
