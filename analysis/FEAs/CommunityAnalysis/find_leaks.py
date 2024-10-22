# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 13:04:34 2024

@author: gordon.donald
"""

import geopandas as gpd
import pandas as pd
import numpy as np

from analysis.Local_travel_areas.LTA_queries import *
from analysis.utils import *
from src.visualise.map_at_sub_la import *
import matplotlib.pyplot as plt


#Get the best modularity file
geo_data = gpd.read_file("Q:/SDU/Mobility/Outputs/NetworkAnalysis/BestModularityCommunityStatsAndRanking.gpkg")
geo_data = geo_data.drop_duplicates('community index') # Remove duplicates here.
geo_data = geo_data[~pd.isna(geo_data['community index'])] #Also get rid of NaN thing.

#For reference, this has the MSOAs
communities = pd.read_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/Community_ranking.csv")
best_modularity = communities[communities.modularity == communities.modularity.max()]

def get_neighbours(our_id: str, bounds: pd.DataFrame, code_col: str = "community index", BORDER=False) -> list[str]:  # Default to return 3 neighbours for comparison
    """Retrieve neighboring locations based on a given location code and boundary data.

    Args:
        our_la_code: a string representing the location code of interest.
        bounds: a DataFrame containing boundary data.
        code_col: a string indicating the column name that contains the location codes. Defaults to "community index".

    Returns:
        A list of neighboring location codes sorted by the length of shared borders in descending order.
    """
    row = np.where(bounds[code_col] == our_id)[0][0]
    neighbours = geo_data[geo_data.geometry.touches(geo_data.iloc[row]["geometry"])][code_col].tolist()

    # We also want the length of the borders to select places.
    if BORDER:
        borders=[]
        for neighbour in neighbours:
            neighbour_row = np.where(bounds[code_col] == neighbour)[0][0]
            try:
                border = bounds.iloc[row]["geometry"].intersection(bounds.iloc[neighbour_row]["geometry"])
            except:
                print("Border off error")
            borders.append(border)

        output = pd.DataFrame([neighbours, borders]).T
        output.columns = ["Neighbour", "Border"]
        output['Community'] = our_id
        return output[["Community", "Border", "Neighbour"]]

    else:
        output = pd.DataFrame([neighbours]).T
        output.columns = ["Neighbour"]
        output['Community'] = our_id
        return output[["Community", "Neighbour"]]

list_neighbours=[]
for community_id in geo_data['community index']:
    list_neighbours.append(get_neighbours(community_id, geo_data))

#These are neighbouring communities    
list_neighbours = pd.concat(list_neighbours)

def get_msoas_in_community(community_id):
    msoas = best_modularity[best_modularity['Unnamed: 0'] == community_id].iloc[0].members
    #Clean out shit and process as list
    msoas_list = msoas.replace("{","").replace("}","").replace("'", "").replace(" ", "").split(",")
    return(msoas_list)

#Get the O2 data for this.
weekday_data = get_data_for_all_weekdays()

def get_total_leak(dataset, community_id):
    #This is the proportion of travel involving a community that is not wholly within
    community = get_msoas_in_community(community_id)
    total_trips = dataset[ (dataset.start_msoa.isin(community)) | (dataset.end_msoa.isin(community))].daily_trips.sum()
    #Trips leaing means either the origin or destination is outside
    trips_leaking = dataset[ (dataset.start_msoa.isin(community)) & (~dataset.end_msoa.isin(community))].daily_trips.sum() + dataset[ (~dataset.start_msoa.isin(community)) & (dataset.end_msoa.isin(community))].daily_trips.sum()
    leak_prop = trips_leaking / total_trips
    return(leak_prop)
    
def get_leak_to_neighbour(dataset, community_id1, community_id2):
    #This is the trips inolviving community1 which leak to community 2
    community1 = get_msoas_in_community(community_id1)
    community2 = get_msoas_in_community(community_id2)
    total_trips_1 = dataset[ (dataset.start_msoa.isin(community1)) | (dataset.end_msoa.isin(community1))].daily_trips.sum()
    #Trips leaking to 2 means one of the origin/destination is in each of community 1 and community 2
    trips_leaking_to2 = dataset[ (dataset.start_msoa.isin(community1)) & (dataset.end_msoa.isin(community2))].daily_trips.sum() + dataset[ (dataset.start_msoa.isin(community2)) & (dataset.end_msoa.isin(community1))].daily_trips.sum()
    leak_prop_2 = trips_leaking_to2/total_trips_1
    return(leak_prop_2)

#These function are not super quick, so these apply statements may take up to 30-40 minutes. But should work: total leak matches 1-travel_within
list_neighbours['total_leak'] = list_neighbours.apply(lambda x: get_total_leak(weekday_data, x['Community']), axis=1)
list_neighbours['leak_to_neighbour'] = list_neighbours.apply(lambda row: get_leak_to_neighbour(weekday_data, row['Community'], row['Neighbour']), axis=1)
#This should be the percentage leak to each neighbour then?
list_neighbours['perc_leak'] = list_neighbours.leak_to_neighbour/list_neighbours.total_leak*100

list_neighbours.to_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/best_modularity_neighbour_leak_numbers.csv")

#For visualisation, test the histogram of this?
list_neighbours.perc_leak.hist()

#For visuals, try getting borders as line segments?
list_neighbours_b=[]
for community_id in geo_data['community index']:
    list_neighbours_b.append(get_neighbours(community_id, geo_data, BORDER=True))

#These are neighbouring communities borders as line segments (file size kind of too large here for what we really need) 
list_neighbours_b = pd.concat(list_neighbours_b)

border_gdf = gpd.GeoDataFrame(list_neighbours_b, geometry='Border', crs=geo_data.crs)

border_weights = border_gdf.merge(list_neighbours)
border_weights.to_file("Q:/SDU/Mobility/Outputs/NetworkAnalysis/best_modularity_neighbour_leak_borders.geojson", driver="GeoJSON")


f, ax = plt.subplots(figsize=(12, 12))
geo_data.plot('travel_within', cmap='Greens', ax=ax) #Dark green should be highest travel_within
border_weights.plot('perc_leak', cmap='Reds_r', ax=ax) # Dark red is lowest percentage leaking over the line, so darker red mean stronger dividing line.
plt.axis('off')

plt.savefig("Q:/SDU/Mobility/Outputs/NetworkAnalysis/best_modularity_neighbour_leak_borders.png", dpi=600)
