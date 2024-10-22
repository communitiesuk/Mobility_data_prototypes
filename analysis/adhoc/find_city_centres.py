# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 17:33:28 2023

@author: gordon.donald
"""

import sys
sys.path.append('..')

from src.visualise.map_at_sub_la import *
from src.visualise.line_chart import line_chart
from analysis.utils import *
import geopandas as gpd
import pandas as pd
import pyodbc
import matplotlib.pyplot as plt

import contextily as cx
from matplotlib.lines import Line2D
from src.utils.constants import map_lu_partnership_colour_scale_unordered


server = 'DAP-SQL01\CDS' 
database = 'Place'

# ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
cnxn = pyodbc.connect(driver='{SQL Server Native Client 11.0}', 
                      host=server, database=database, trusted_connection='yes')
# get timeseries of destination trips for all msoas
#Note - in this query DATEPART = 1 for weekdays, 6 for weekends
query = '''
    SELECT start_date, end_msoa, SUM(avg_daily_trips) daily_trips
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE DATEPART(dw, start_date) = 1
    GROUP BY start_date, end_msoa;
    '''
msoa_destination_trips = pd.read_sql_query(query, cnxn) 
msoa_destination_trips['start_date'].nunique()

# find average for each msoa 
avg_destination_trips = msoa_destination_trips[['end_msoa', 'daily_trips']].groupby(["end_msoa"]).mean().round(1).reset_index()


msoas= get_all_small_areas()
lads = gpd.read_file("Q:/GI_Data/Boundaries/LAD_MAY_2021_UK_BFE_V2.shp")

def get_name_from_code(la_code):
    name = list(lads[lads['LAD21CD']==la_code]['LAD21NM'])[0]
    return(name)



plot_at_small_area(avg_destination_trips, "daily_trips", lads, msoas, "E06000014", 'msoa11cd', 'end_msoa', suptitle=get_name_from_code("E06000014"), source="Source: O2 Motion")


#How to get urban core?
#Within a BUA, assume a cutoff (80-90%)
BUAs = gpd.read_file("Q:\SDU\Towns_indicative_selection_QA\Shapefiles\BUA_2022_GB_2824430073212747649\BUA_2022_GB.shp")

area_threshold_for_BUAs = 5e7
large_BUAs = BUAs[BUAs.area > area_threshold_for_BUAs][['BUA22CD', 'BUA22NM']]

#The map I want is contextillty basemap, with BUA in blue, and centre in orange (use LUP categorical colours)
#These MSOAs
def get_msoa_with_centre(BUA, threshold=0.8):
    BUA_shape = BUAs[(BUAs['BUA22CD']==BUA) | (BUAs['BUA22NM']==BUA)] #Can take either the name or code as an input here, why not?
    msoas_within = gpd.overlay(msoas, BUA_shape)
    msoa_trips = avg_destination_trips[avg_destination_trips['end_msoa'].isin(msoas_within['msoa11cd'])]
    max_vists = max(msoa_trips['daily_trips'])
    centre_msoas = msoa_trips[msoa_trips['daily_trips'] > threshold*max_vists]
    centre_msoas = msoas.merge(centre_msoas, left_on='msoa11cd', right_on='end_msoa')
    return(centre_msoas)

#PLot these for large BUAs in GB.
for i in range(len(large_BUAs)):
    BUA = large_BUAs.iloc[i]['BUA22NM']
    BUA_bounds = BUAs[(BUAs['BUA22CD']==BUA) | (BUAs['BUA22NM']==BUA)]
    centre_bounds = get_msoa_with_centre(BUA)

    f, ax = plt.subplots(figsize=(12, 12))
    BUA_bounds.plot(ax=ax, color=map_lu_partnership_colour_scale_unordered[0], alpha=0.3, label='BUA')
    centre_bounds.plot(ax=ax, color=map_lu_partnership_colour_scale_unordered[3], alpha=0.5, label='Centre')
    lines = [
        Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
        for t in ax.collections[0:]
        ]
    labels = [t.get_label() for t in ax.collections[0:]]
    ax.legend(lines, labels)
    plt.suptitle(BUA, fontsize=30)
    cx.add_basemap(ax, source=cx.providers.Esri.WorldStreetMap, zoom=12, crs=BUA_bounds.crs)
    plt.show()

#for i in range(len(large_BUAs)):
 #   plot_at_small_area(avg_destination_trips, "daily_trips", BUAs, msoas, large_BUAs.iloc[i]['BUA22CD'], 'msoa11cd', 'end_msoa', suptitle=large_BUAs.iloc[i]['BUA22NM'], source="Source: O2 Motion")

