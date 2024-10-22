# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 14:06:45 2024

@author: gordon.donald
"""

import pandas as pd
import geopandas as gpd
from analysis.utils import *

import matplotlib.pyplot as plt
#use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
#Basemap
import contextily as cx

communities = pd.read_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/Community_ranking.csv")
communities = communities.rename(columns={"Unnamed: 0": "Community_ID"})

#Want to find which BUA the centre is in (or closest to)
BUAs = get_BUAs(ADD_LONDON=True)
BUA_pop = get_BUA_pop(ADD_LONDON=True)
BUAs = BUAs.merge(BUA_pop)
#When plotting BUAs, let's restrict to those over 8k population
BUAs_plotting = BUAs[BUAs.Population > 8e3]

msoas = get_all_small_areas()

centre_msoas = msoas[msoas.msoa11cd.isin(communities.centre)]
centre_BUAs = centre_msoas.overlay(BUAs)
centre_BUAs['Area'] = centre_BUAs.area
centre_BUAs = centre_BUAs.sort_values('Area', ascending=True).drop_duplicates('msoa11cd', keep='first')

#Which centre MSOAs are not in BUAs?
missing_centres = centre_msoas[~centre_msoas.msoa11cd.isin(centre_BUAs.msoa11cd)]
missing_centres.msoa11cd # All in NI, that's fine.
#Merge these labels back in
communities = communities.merge(centre_BUAs[['msoa11cd', 'BUA22NM']], left_on='centre', right_on='msoa11cd')

best_mod = communities.modularity.max()
best_community = communities[communities.modularity==best_mod]

regions_gdf = gpd.read_file("Q:/GI_Data/Boundaries/Regions/Regions2019.shp")
#Which regions are each community in?
oa_msoa_lu = pd.read_csv("Q:/SDU/LDC/modelling/data/lookups/Output_Area_to_Lower_layer_Super_Output_Area_to_Middle_layer_Super_Output_Area_to_Local_Authority_District_(December_2011)_Lookup_in_England_and_Wales.csv")
oa_region_lu = pd.read_csv("Q:/SDU/LDC/modelling/data/lookups/Output_Area_to_Region_(December_2011)_Lookup_in_England.csv")
msoa_to_region_lu = pd.merge(left=oa_msoa_lu[["MSOA11CD", "OA11CD", "LAD11CD", "LAD11NM"]], right=oa_region_lu[["OA11CD", "RGN11CD", "RGN11NM"]], on="OA11CD")[["MSOA11CD", "LAD11CD", "LAD11NM", "RGN11CD", "RGN11NM"]].drop_duplicates()

#Get the regions each communitiy is in
def get_regions(community):
    our_msoas = community.members
    our_msoas_list=our_msoas.replace('"', '').replace('}', '').replace('{', '').replace(' ', '').replace("'", "").split(",")
    our_regions = list(msoa_to_region_lu[msoa_to_region_lu.MSOA11CD.isin(our_msoas_list)].RGN11NM.drop_duplicates())
    return our_regions

#Logic to return True/False for a given region
def is_community_in_region(community, region):
    comm_regions = get_regions(community)
    return (region in comm_regions)

regions  = list(msoa_to_region_lu.RGN11NM.drop_duplicates())
for region in regions:
    best_community['IN_'+region] = best_community.apply(lambda row: is_community_in_region(row, region), axis=1)
    #Also do this for all communities
    communities['IN_'+region] = communities.apply(lambda row: is_community_in_region(row, region), axis=1)
    
#Get best paritions in each region using travel within scores.
#Find the partitions which have the best travel within for the region
def get_best_partitions_for_region(communities, region, N_best=3):
    best_partitions_for_region = communities.groupby(['alg_seed', 'alg_resolution', 'alg_threshold', 'IN_'+region]).mean('travel_within').sort_values('travel_within', ascending=False).reset_index().drop_duplicates('population', keep='first')
    best_partitions_for_region = best_partitions_for_region.head(N_best).reset_index()
    best_partitions_for_region['Rank'] = best_partitions_for_region.travel_within.rank(ascending=False)
    return best_partitions_for_region

def get_best_communities_for_region(communities, region, N_best=3):
    partitions = get_best_partitions_for_region(communities, region, N_best)
    partitions_info = partitions[['alg_seed', 'alg_resolution', 'alg_threshold', 'Rank']]
    best_communities_in_region = communities.merge(partitions_info)
    best_communities_in_region = best_communities_in_region[best_communities_in_region['IN_'+region]]
    best_communities_in_region['Region'] = region
    return best_communities_in_region

best_communities_for_each_region=[]
for region in regions:
    best_communities_for_each_region.append(get_best_communities_for_region(communities, region))
best_communities_for_each_region = pd.concat(best_communities_for_each_region)


#Visualise the parititons
def get_shape(community):
    our_msoas = community.members
    our_msoas_list=our_msoas.replace('"', '').replace('}', '').replace('{', '').replace(' ', '').replace("'", "").split(",")
    community_shape = msoas[msoas.msoa11cd.isin(our_msoas_list)].dissolve()
    return community_shape.geometry

best_community['geometry'] = best_community.apply(lambda row: get_shape(row), axis=1)
best_community_gdf = gpd.GeoDataFrame(best_community, geometry='geometry', crs=msoas.crs)

best_communities_for_each_region['geometry'] = best_communities_for_each_region.apply(lambda row: get_shape(row), axis=1)
best_communities_for_each_region_gdf = gpd.GeoDataFrame(best_communities_for_each_region, geometry='geometry', crs=msoas.crs)


#A better approach than using the community centre would be to label the largest BUA within each community.
#Only need to use the larger towns, as our aim here is to get the largest BUA in each community.
towns_in_communities = best_communities_for_each_region_gdf.overlay(BUAs_plotting)
towns_in_modularity_best_communities = best_community_gdf.overlay(BUAs_plotting)

#Remove tiny slivers of town.
towns_in_communities = towns_in_communities[towns_in_communities.area>2e6]
towns_in_modularity_best_communities = towns_in_modularity_best_communities[towns_in_modularity_best_communities.area>2e6]

#Get the largest town
towns_in_communities = towns_in_communities.sort_values('Population', ascending=False).drop_duplicates("Community_ID", keep='first')
towns_in_modularity_best_communities = towns_in_modularity_best_communities.sort_values('Population', ascending=False).drop_duplicates("Community_ID", keep='first')

#Rename columns and merge back to the geo dataframe
towns_in_communities = towns_in_communities[['Community_ID', 'BUA22NM_2']].rename(columns={"BUA22NM_2": "Largest_BUA"})
towns_in_modularity_best_communities = towns_in_modularity_best_communities[['Community_ID', 'BUA22NM_2']].rename(columns={"BUA22NM_2": "Largest_BUA"})
best_community_gdf = best_community_gdf.merge(towns_in_modularity_best_communities)
best_communities_for_each_region_gdf = best_communities_for_each_region_gdf.merge(towns_in_communities)

#For plotting, I need the base map
key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key

#Get MCA bounds from Q drive, and covnert crs in case.
existing_MCA_gdf = gpd.read_file("Q:/GI_Data/Boundaries/CombinedAuthorities/Combined_Authorities_May_2024_Boundaries_EN_BUC_-4080581643524862463/CAUTH_MAY_2024_EN_BFE.shp")
existing_MCA_gdf = existing_MCA_gdf.to_crs(msoas.crs)

#To label BUAs
def get_BUA_coords(our_bua):
    centroid = BUAs[BUAs.BUA22NM==our_bua].centroid
    return(centroid.x.iloc[0], centroid.y.iloc[0])


def plot_communities_in_region(communities_df, region, BUA_LABELS=True, title="", savepath=""):
    f, ax = plt.subplots(figsize=(12, 12))
    #Get the communities to plot
    region_communities = communities_df[communities_df['IN_'+region]]
    region_communities.plot('Largest_BUA', ax=ax, alpha=0.9, linewidth=0.1, cmap='tab20')
    
    #Region boundaries
    region_shape = regions_gdf[regions_gdf.rgn19nm == region]
    region_shape.boundary.plot(ax=ax, edgecolor="black", linewidth = 5)
    
    #Plot existing MCAs
    region_mcas = region_shape.overlay(existing_MCA_gdf)
    region_mcas.boundary.plot(ax=ax, edgecolor="#12436D", linewidth = 3)
    
    #BUAs?
    BUAs_plotting.overlay(region_communities.dissolve()).plot(ax=ax, alpha=0.3, edgecolor='#12436D', facecolor='#12436D')
    cx.add_basemap(ax, source=basemap_url, crs=msoas.crs)

    ax.set_title(title, fontsize=20)

#Add some BUA labels
    if BUA_LABELS:
        for community in range(len(region_communities)):
            label_x, label_y = get_BUA_coords(region_communities.iloc[community]['Largest_BUA'])
            ax.annotate(region_communities.iloc[community]['Largest_BUA'].split('(')[0], xy=(label_x,label_y), ha='center', color='black', font='Arial', fontsize=10,
                       bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
    plt.axis('off')
    if savepath != "":
        plt.savefig(f"Q:/SDU/Mobility/Outputs/NetworkAnalysis/Regional_communities/{savepath}.png", bbox_inches="tight", dpi=600)
    plt.show()
    plt.close()
    return 0

def get_communities(communities, region, rank):
    region_comm = communities[(communities.Region==region) & (communities.Rank==rank)]
    return region_comm

#Loop over regions and options, to save outputs.
for region in regions:
    plot_communities_in_region(best_community_gdf, region, title=f"Communities in {region}: National best fit", savepath=f"{region}_best_modularity")

    for rank in [1,2,3]:
        plot_communities_in_region(get_communities(best_communities_for_each_region_gdf, region, rank), region, title=f"Best fit communities in {region}: Option {rank}", savepath=f"{region}_best_fit_{rank}")



#Apply functions for leaks to the  dataframes here
import numpy as np

def get_neighbours(our_id: str, bounds: pd.DataFrame, code_col: str = "Community_ID", BORDER=False) -> list[str]:  # Default to return 3 neighbours for comparison
    """Retrieve neighboring locations based on a given location code and boundary data.

    Args:
        our_la_code: a string representing the location code of interest.
        bounds: a DataFrame containing boundary data.
        code_col: a string indicating the column name that contains the location codes. Defaults to "community index".

    Returns:
        A list of neighboring location codes sorted by the length of shared borders in descending order.
    """
    row = np.where(bounds[code_col] == our_id)[0][0]
    neighbours = bounds[bounds.geometry.touches(bounds.iloc[row]["geometry"])][code_col].tolist()

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
        return output[["Community", "Neighbour"]].drop_duplicates()


#Leak calculation function
#Get the O2 data for this.
from analysis.Local_travel_areas.LTA_queries import *
weekday_data = get_data_for_all_weekdays()

def get_msoas_in_community(df, community_id):
    our_msoas = df[df['Community_ID'] == community_id].iloc[0].members
    #Clean out shit and process as list
    msoas_list = our_msoas.replace("{","").replace("}","").replace("'", "").replace(" ", "").split(",")
    return(msoas_list)


def get_total_leak(df, dataset, community_id):
    #This is the proportion of travel involving a community that is not wholly within
    community = get_msoas_in_community(df, community_id)
    total_trips = dataset[ (dataset.start_msoa.isin(community)) | (dataset.end_msoa.isin(community))].daily_trips.sum()
    #Trips leaing means either the origin or destination is outside
    trips_leaking = dataset[ (dataset.start_msoa.isin(community)) & (~dataset.end_msoa.isin(community))].daily_trips.sum() + dataset[ (~dataset.start_msoa.isin(community)) & (dataset.end_msoa.isin(community))].daily_trips.sum()
    leak_prop = trips_leaking / total_trips
    return(leak_prop)
    
def get_leak_to_neighbour(df, dataset, community_id1, community_id2):
    #This is the trips inolviving community1 which leak to community 2
    community1 = get_msoas_in_community(df, community_id1)
    community2 = get_msoas_in_community(df, community_id2)
    total_trips_1 = dataset[ (dataset.start_msoa.isin(community1)) | (dataset.end_msoa.isin(community1))].daily_trips.sum()
    #Trips leaking to 2 means one of the origin/destination is in each of community 1 and community 2
    trips_leaking_to2 = dataset[ (dataset.start_msoa.isin(community1)) & (dataset.end_msoa.isin(community2))].daily_trips.sum() + dataset[ (dataset.start_msoa.isin(community2)) & (dataset.end_msoa.isin(community1))].daily_trips.sum()
    leak_prop_2 = trips_leaking_to2/total_trips_1
    return(leak_prop_2)

def get_town_label_for_community(df, community_id):
    town_label = df[df.Community_ID==community_id].iloc[0]['Largest_BUA']
    return town_label

for rank in [1,2,3]:
    for region in regions:
        best_communities_for_each_region_gdf_rank = best_communities_for_each_region_gdf[(best_communities_for_each_region_gdf.Rank == rank) & (best_communities_for_each_region_gdf.Region == region)]
        list_neighbours=[]
        for community_id in best_communities_for_each_region_gdf_rank['Community_ID']:
            list_neighbours.append(get_neighbours(community_id, best_communities_for_each_region_gdf_rank))
        list_neighbours = pd.concat(list_neighbours)

        if len(list_neighbours>1): #If there's one community (e.g. in London), then we can skip.
            #These function are not super quick, so these apply statements may take up to 30-40 minutes. But should work: total leak matches 1-travel_within
            list_neighbours['total_leak'] = list_neighbours.apply(lambda x: get_total_leak(best_communities_for_each_region_gdf_rank, weekday_data, x['Community']), axis=1)
            list_neighbours['leak_to_neighbour'] = list_neighbours.apply(lambda row: get_leak_to_neighbour(best_communities_for_each_region_gdf_rank, weekday_data, row['Community'], row['Neighbour']), axis=1)
            #This should be the percentage leak to each neighbour then?
            list_neighbours['perc_leak'] = list_neighbours.leak_to_neighbour/list_neighbours.total_leak*100

            #Get more useful labels    
            list_neighbours['From_town_label'] = list_neighbours.apply(lambda row: get_town_label_for_community(best_communities_for_each_region_gdf, row['Community']), axis=1)
            list_neighbours['To_town_label'] = list_neighbours.apply(lambda row: get_town_label_for_community(best_communities_for_each_region_gdf, row['Neighbour']), axis=1)
            
            list_neighbours.to_csv(f"Q:/SDU/Mobility/Outputs/NetworkAnalysis/Regional_communities/neighbour_leaks_option_{region}_{rank}.csv", index=False)

#And do it again for the national version
list_neighbours=[]
for community_id in best_community_gdf['Community_ID']:
   list_neighbours.append(get_neighbours(community_id, best_community_gdf))
list_neighbours = pd.concat(list_neighbours)

#These function are not super quick, so these apply statements may take up to 30-40 minutes. But should work: total leak matches 1-travel_within
list_neighbours['total_leak'] = list_neighbours.apply(lambda x: get_total_leak(best_community_gdf, weekday_data, x['Community']), axis=1)
list_neighbours['leak_to_neighbour'] = list_neighbours.apply(lambda row: get_leak_to_neighbour(best_community_gdf, weekday_data, row['Community'], row['Neighbour']), axis=1)
list_neighbours['perc_leak'] = list_neighbours.leak_to_neighbour/list_neighbours.total_leak*100
list_neighbours['From_town_label'] = list_neighbours.apply(lambda row: get_town_label_for_community(best_community_gdf, row['Community']), axis=1)
list_neighbours['To_town_label'] = list_neighbours.apply(lambda row: get_town_label_for_community(best_community_gdf, row['Neighbour']), axis=1)
list_neighbours.to_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/Regional_communities/neighbour_leaks_option_national_fit.csv", index=False)

best_communities_for_each_region_gdf[['Community_ID', 'size', 'Largest_BUA', 'Region', 'Rank', 'population', 'travel_within']].to_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/Regional_communities/community_info.csv", index=False)
best_community_gdf[['Community_ID', 'size', 'Largest_BUA', 'centre', 'population', 'travel_within']].to_csv("Q:/SDU/Mobility/Outputs/NetworkAnalysis/Regional_communities/community_info_national_best_fit.csv", index=False)
