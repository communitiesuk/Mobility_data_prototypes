
import git
import os

import pandas as pd
import geopandas as gpd
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)
sys.path.insert(1, '/Mobility/src/analysis')

from analysis.utils import *
import matplotlib.pyplot as plt

#obtain data from database
query="SELECT [start_msoa],[end_msoa],sum([avg_daily_trips])/52 as total_average_journeys FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE journey_purpose='Commute' group by [start_msoa],[end_msoa]"
msoa_OD_data_from_mobile=submit_sql_query(query)

#save as CSV for further analysis with data at MSOA level
msoa_OD_data_from_mobile.to_csv('Q:\SDU\Mobility\Data\CommuterFlows\AllWorkingWeeks.csv', mode='w')

#remove empty journeys where needed
msoa_OD_data_from_mobile=msoa_OD_data_from_mobile.loc[msoa_OD_data_from_mobile['total_average_journeys']!=0]


#Create commuter flows at BUA level

msoa_bua_bespoke_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA__NOGLA_lookup.csv")

merged_msoa_bua_bespoke=pd.merge(msoa_bua_bespoke_lookup, msoa_OD_data_from_mobile, how='right',left_on="msoa11cd", right_on="start_msoa").merge(msoa_bua_bespoke_lookup,how='left', left_on="end_msoa", right_on="msoa11cd")

uk_bua_mobile_commuter_flows=merged_msoa_bua_bespoke.groupby(['BUA22CD_x','BUA22NM_x','BUA22CD_y','BUA22NM_y']).sum('total_average_journeys').reset_index().sort_values(by='total_average_journeys', ascending=False)

#remove not more useful columns
uk_bua_mobile_commuter_flows_1=uk_bua_mobile_commuter_flows.drop(['Population_x', 'Population_y'], axis=1)
#give more meaningful names to columns
uk_bua_mobile_commuter_flows_2=uk_bua_mobile_commuter_flows_1.rename(columns={"BUA22NM_x":"Origin_BUA_nm","BUA22CD_x":"Origin_BUA_cd","BUA22CD_y":"Destination_BUA_cd","BUA22NM_y":"Destination_BUA_nm"})


uk_bua_mobile_commuter_flows_2.to_csv(r"Q:\SDU\Mobility\Data\CommuterFlows\GB_wide_CommuterFlows_BUA_LEVEL.csv", mode='w')
