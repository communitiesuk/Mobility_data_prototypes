"""
File: ComparingCommuterFlowsatBUAlevel_MobileDerived2022toCensusDerived2011.py

Author: Gianfranco Gliozzo

Date: 15/02/2024

Description: This file delivers two image files. One includes two tables to compare all main flows involving an handpicked town.
A second image files provides two scatterplots and a table for a picked town comparing only outgoing and internal flows.
It is a first attempt to visualise a comparison between commuter flows aggregated at BUA level from Census 2011 data and O2 derived mobile data.
Commuter flows from census 2011 has been created aggregating census data at OA level using a ONS generated lookup. It covers only England and Wales
Commuter flows from O2 mobile data has been obtained aggregating the MSOA level data provided by O2. the lookup has been created internally in SDU.
outcomes are saved here: Q:\SDU\Mobility\Data\CommuterFlows\AnalyticalOutputs

Assumptions:This file just visualises one BUA a time, it currently visualises only internal flows and outgoing flows.
The BUA considered are the ones where both incoming and outgoing flows reach a minimum of 50 people.
The threshold between the main scatterplot and the outliers one is set to 2000 people.

Limitations: BUA2011 and BUA2022 are different and no lookup has been provided by ONS. The matching between the two has been obtained matching names.
Several BUA remained unmatched.
BUA2011 was created for England and Wales only while the BUA2022 we use is a mix between the 2022 GB wide ONS created BUAs and other data for NI.
Internal flows are always much larger than outgoing flows. To avoid having scatterplot flattened by outliers I created two scatterplots.
The threshold between the two diagrams has been handpicked for a specific BUA and its calculation needs to be automated.
The scatterplots needs to have names overlaid but I haven't been successfull in delivering this.
The two tables to compare all main flows involving the handpicked town, needs formatting improvement.
"""




import pandas as pd
import numpy as np
import git
import os
from pandas.plotting import table
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)
sys.path.insert(1, '/Mobility/src/analysis')
from analysis.utils import *
from IPython.display import display_html
import matplotlib.pyplot as plt
import pyodbc
pd.options.display.float_format = lambda x : '{:.0f}'.format(x) if round(x,0) == x else '{:,.2f}'.format(x)
plt.style.use('ggplot')
pd.set_option("display.precision", 4)

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=add-live;'
                      'Database=GI_Team;'
                      'Trusted_Connection=yes;')

cursor = conn.cursor()

#Loading BUA level data for Engaland and Wales from census 2011
od_Town_level_data_2011=pd.read_sql_query('SELECT * FROM [GI_Team].[dbo].[ResidenceWorkOriginDestinationAtBUALevel_Basic_v1]',conn)

#select only relevant columns
View_od_Town_level_data_2011=od_Town_level_data_2011[['TownResNM','TownWorkNM','People']]

#remove BUA and BUASD from town names
View_od_Town_level_data_2011_1=View_od_Town_level_data_2011.replace({' BUASD':'', ' BUA': ''},regex=True)

#Give more meaningful names to columns, BUA/BUSD for 2011 are called towns in this context
View_od_Town_level_data_2011_2=View_od_Town_level_data_2011_1.rename(columns={"TownResNM": "TownRes_11_NM","TownWorkNM":"TownWork_11_NM", "People":"People_11"} )

#commuter flows 2011 for tabular visualisations saved in CSV
View_od_Town_level_data_2011_1.to_csv(r"Q:\SDU\Mobility\Data\CommuterFlows\No_codes_EW_wide_2011_CommuterFlows_BUA_LEVEL.csv", mode='w')

# load commuter flows from mobile phones
GB_bua_mobile_commuter_flows=pd.read_csv(r"Q:\SDU\Mobility\Data\CommuterFlows\GB_wide_CommuterFlows_BUA_LEVEL.csv")

#select only relevant columns
view_GB_bua_mobile_commuter_flows=GB_bua_mobile_commuter_flows[['Origin_BUA_nm','Destination_BUA_nm','total_average_journeys']]

#make column names more explicit about data
view_GB_bua_mobile_commuter_flows_1=view_GB_bua_mobile_commuter_flows.rename(columns={"Origin_BUA_nm": "Origin_BUA22_NM", "Destination_BUA_nm": "Destination_BUA22_NM", "total_average_journeys":"Journeys_22"})

#test areas to visualise comparisons
analysis_town='Stoke-on-Trent'#'York'#Wakefield'

#select only mobile phone data related to the chosen town
TwonflowsMobileData22_23 = view_GB_bua_mobile_commuter_flows_1[(view_GB_bua_mobile_commuter_flows_1['Origin_BUA22_NM'].isin([analysis_town]))|(view_GB_bua_mobile_commuter_flows_1['Destination_BUA22_NM'].isin([analysis_town]))].sort_values(by='Journeys_22',ascending=False).head()

#select only census 2011 data related to the chosen town
TwonflowsCensusData11 = View_od_Town_level_data_2011_2[(View_od_Town_level_data_2011_2['TownRes_11_NM'].isin([analysis_town]))|(View_od_Town_level_data_2011_2['TownWork_11_NM'].isin([analysis_town]))].sort_values(by='People_11', ascending=False).head()	


#make a visual where the top flows of the same town are compared
def display_side_by_side(*args):
    #Create a new figure
    fig, axs = plt.subplots(1, len(args), figsize=(16, 8))
    
    for i, df in enumerate(args):
        # Create a table in each subplot
        tab=table(axs[i], df, loc='center', colWidths=[0.5]*len(df.columns),fontsize=20)
        for key, cell in tab.get_celld().items():
            axs[i].axis('off')
    # Adjust the layout to prevent overlapping
            plt.tight_layout()
    
    # Save the figure
    plt.savefig('Q:/SDU/Mobility/Data/CommuterFlows/AnalyticalOutputs/table_comparing_main_flows_involving_'+analysis_town+'.png')
    
# Use the function
display_side_by_side(TwonflowsMobileData22_23, TwonflowsCensusData11)


#Create a Scatterplot to compare the two dataset focused on outgoing people from the picked town it filters out flows involving less than 50 people

#extract data from mobile phones
analysis_town_outgoing22=view_GB_bua_mobile_commuter_flows_1[view_GB_bua_mobile_commuter_flows_1['Origin_BUA22_NM'].isin([analysis_town])]
outgoing22=(analysis_town_outgoing22[["Destination_BUA22_NM","Journeys_22"]])
#focus on flows involving more or equal than 50 people, the usual filter is 100 but this way we keep the possibility to compare
outgoing22_50plus=outgoing22[outgoing22['Journeys_22']>=50]#23 when set to more than 100, it's 35 when filter is more than 50

#extract data from census 2011
analysis_town_outgoing11=View_od_Town_level_data_2011_2[View_od_Town_level_data_2011_2['TownRes_11_NM'].isin([analysis_town])]

outgoing11=analysis_town_outgoing11 [["TownWork_11_NM","People_11"]]
#apply 50 filter
outgoing11_50plus=outgoing11[outgoing11['People_11']>=50]

# Merge the two DataFrames on the town names/destination/work column
df = pd.merge(outgoing22_50plus, outgoing11_50plus, how='inner', left_on='Destination_BUA22_NM', right_on='TownWork_11_NM')

#draw  two scatterplots as internal flows are big outliers and skew too much the scatterplot.
# Also added a table to show how they interact regardless of the outliers and thresholds

#the 2000 threshold has been selected specifically for Stoke on Trent
outliers=df[(df["Journeys_22"]>2000 ) & (df["People_11"]>2000) ]

coreofdata=df[(df["Journeys_22"]<=2000 ) &(df["People_11"]<=2000) ]

fig=plt.figure()
#fig, axs = plt.subplots(1, 3, figsize=(12, 4))


ax1 = fig.add_subplot(131)
ax2 = fig.add_subplot(132)
ax3= fig.add_subplot(233)

plt.tight_layout()

#ax1.set_xlim(0,2)
#ax1.set_ylim(0,2)
#plt.set_title('Core data more than 100 people any dataset')
ax1.set_title('Core data')
ax1.set_xlabel('Mobile data 2022')
ax1.set_ylabel('Census data 2011')

# Generate scatter plot
#outliers ould be chosen making a calculation on quintiles if one class 
#or any range equal to a quintile is empty we can consider the presence of some outliers
#this needs to be improved as names should be in the scatterplot

ax1.scatter(coreofdata['Journeys_22'], coreofdata['People_11'])
ax2.scatter(outliers['Journeys_22'], outliers['People_11'])


# Add names to the scatter plot

ax2.set_title('Outliers')
ax2.set_xlabel('Mobile data 2022')


cell_text = []
for row in range(len(df)):
    cell_text.append(df.iloc[row])

toptable=ax3.table(cellText=cell_text, colLabels=df.columns, loc='right')
toptable.auto_set_font_size(False)
toptable.auto_set_column_width(col=list(range(len(df.columns))))
toptable.set_fontsize(8)
toptable.scale(2, 2)
toptable.scale(1, 0.75)
ax3.axis('off')
plt.suptitle('Outgoing flows comparison for '+analysis_town+' at BUA  level between census 2011 and mobile derived 2022')
plt.subplots_adjust(top=0.5)

#plt.show()
plt.savefig('Q:\SDU\Mobility\Data\CommuterFlows\AnalyticalOutputs\Scatterplot_comparing_commuter_flows_Outgoing_from '+analysis_town+'.png', bbox_inches='tight')
