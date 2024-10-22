# -*- coding: utf-8 -*-
"""
Created on Wed May 29 13:36:19 2024

@author: gordon.donald
"""

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd

from analysis.Local_travel_areas.LTA_queries import *
from analysis.utils import *
from src.visualise.map_at_sub_la import *

import networkx as nx
from networkx.algorithms import community as community_networkX
from networkx.classes import function as networkX_function

import time
import contextily as cx
import gc

#Get data
#This takes a while.
read_start = time.time()
weekday_data = get_data_for_all_weekdays()
msoa_pop= get_pop_for_all_small_areas()
read_end = time.time()
print("Reading data took: ", read_end-read_start)

#Set up algorithms parameters to scan over 
jounrney_threshold=[20]
resolutions=[1]
seeds=[1]

SCAN=True
if SCAN:
    #jounrney_threshold=[50, 20, 10, 5]
    resolutions=[1, 0.5, 0.2, 0.1]
    seeds=[1,2,3,4,5,6,7,8,9]


#Process raw data and build graph
#this accepts only datasets with the "daily_trips" column
def apply_threshold(dataset, popthreshold):
    cut_data=dataset[dataset['daily_trips']>popthreshold]
    return cut_data

#Do we get better results without slef loops? Probably depends on hyperparamters.
def remove_self_loops(dataset):
    return dataset[dataset.start_msoa != dataset.end_msoa], dataset[dataset.start_msoa == dataset.end_msoa] 

REMOVE_SELF_LOOPS= True
if REMOVE_SELF_LOOPS:
    weekday_data, weekday_data_self_loop = remove_self_loops(weekday_data)    

#Functions to build graphs, run Louvain, and get metrics
def build_graph(nodes, edges):
    graph = nx.DiGraph()
    # Add nodes and their values to the graph
    #NODES ARE weighted by resident population
    for index, row in nodes.iterrows():
        graph.add_node(row['msoa11cd'], value=row['pop'])

    # Add edges and their values to the graph
    # edges are weighted by daily_trips
    for index, row in edges.iterrows(): 
        graph.add_edge(row['start_msoa'], row['end_msoa'], weight=row['daily_trips'])
        
    return(graph)

def partition_louvain(graph, resolution, seed):
    partition=community_networkX.louvain_communities(graph, resolution=resolution, threshold=1e-07, seed=seed)
    return partition
    
def partition_to_df(partition):
    dfpartition = pd.DataFrame({'msoa11cd': partition}).explode('msoa11cd').reset_index().rename(columns={"index":"communities"}) 
    return dfpartition

#Define community metrics

def partition_modularity(graph, partition):
    modularity = community_networkX.modularity(graph, partition)
    return modularity

def get_community_graph(graph, community):
    sg = networkX_function.subgraph(graph, community)
    return(sg)

def community_density(graph, community):
    sg = get_community_graph(graph, community)
    return nx.density(sg)
    
def get_journeys_within_community(dataset, community):
    trips = dataset[ (dataset.start_msoa.isin(community)) & (dataset.end_msoa.isin(community))].daily_trips.sum()
    return trips

def get_journeys_involving_community(dataset, community):
    trips = dataset[ (dataset.start_msoa.isin(community)) | (dataset.end_msoa.isin(community))].daily_trips.sum()
    return trips
    
def community_centrality(graph, community):
    sg = get_community_graph(graph, community)
    centrality = nx.degree_centrality(sg)
    # Find the node with the highest degree centrality
    main_node = max(centrality, key=centrality.get)
    return main_node
    
def community_population(community):
    total_pop = msoa_pop[msoa_pop.msoa11cd.isin(community)]['pop'].sum()
    return total_pop


#Loop over algorithm
for threshold in jounrney_threshold:
    build_nx_start = time.time()
    uk_network = build_graph(msoa_pop, apply_threshold(weekday_data, threshold))
    build_nx_end = time.time()
    print("Building graph took: ", build_nx_end - build_nx_start) #Note this will be quicker to build if threshold is higher

    for resolution in resolutions:
        for seed in seeds:
            partition = partition_louvain(uk_network, resolution, seed)
            N_communities = len(partition)
            print(f'We have {N_communities} in this partition ({threshold}, {resolution}, {seed})')
            #Only work throuhg the communities if there are fewer than 200, as more fractured partitions are not useful for us
            community_store=[]

            if N_communities < 200:
                for community_i in range(N_communities):
                    #print(community_i)
                    community = partition[community_i]
                    size = len(community)
                    modularity = partition_modularity(uk_network, partition)
                    density = community_density(uk_network, community)
                    central_node = community_centrality(uk_network, community)
                    if REMOVE_SELF_LOOPS:
                        travel_in_community = get_journeys_within_community(weekday_data, community) + get_journeys_within_community(weekday_data_self_loop, community)
                        travel_by_community = get_journeys_involving_community(weekday_data, community) + get_journeys_involving_community(weekday_data_self_loop, community)
                    else:
                        travel_in_community = get_journeys_within_community(weekday_data, community) 
                        travel_by_community = get_journeys_involving_community(weekday_data, community) 
                    prop_contained = travel_in_community/travel_by_community
                    population = community_population(community)
                    
                    community_store.append([size, modularity, density, central_node, prop_contained, population, community, seed, resolution, threshold])
                df_parition = partition_to_df(partition)
                df_parition[['alg_seed', 'alg_resolution', 'alg_threshold']] = [seed, resolution, threshold]
                communities_found = pd.DataFrame(community_store, columns=['size', 'modularity', 'density', 'centre', 'travel_within', 'population', 'members',
                                                                           'alg_seed', 'alg_resolution', 'alg_threshold'])

                communities_found.to_csv(f"Q:/SDU/Mobility/Outputs/NetworkAnalysis/community_candidates-{threshold}-{resolution}-{seed}.csv", index=False)
                df_parition.to_csv(f"Q:/SDU/Mobility/Outputs/NetworkAnalysis/partition_candidates-{threshold}-{resolution}-{seed}.csv", index=False)
    #So help us not crash out on DAP, include some garbage collection
                del partition, N_communities, community, size,  modularity, central_node, travel_in_community, travel_by_community, prop_contained, population
                gc.collect()
    del uk_network
    gc.collect()
          

#Plotting functions
def search_string(s, search):
    return search in str(s)

def get_candidates(msoas, communities=communities_found):
    mask = communities.apply(lambda x: x.map(lambda s: search_string(s, test_msoa)))
    filtered_df = communities.loc[mask.any(axis=1)]
    return(filtered_df)

def plot_a_community(target_msoa):
    communities = get_candidates(target_msoa)
    for option in range(len(communities)):
        community=communities.iloc[option]
        msoas_to_plot = msoas[msoas.msoa11cd.isin(community.members)]
        ax = msoas_to_plot.plot(alpha=0.7)
        cx.add_basemap(ax, source=basemap_url, crs=msoas.crs)
    return(0)

def plot_partitions_in_region(region, partition):
    region_bounds = regions[regions.rgn19nm == region]
    msoas_within = list(region_bounds.overlay(msoas).msoa11cd)
    communities_to_plot = partition[partition.msoa11cd.isin(msoas_within)].communities.drop_duplicates()
    msoas_to_plot = msoas[msoas.msoa11cd.isin(partition[partition.communities.isin(communities_to_plot)].msoa11cd)]
    plot_data= msoas_to_plot.merge(partition, on='msoa11cd')
    N_comm = len(plot_data.communities.drop_duplicates())
    plot_data['communities'] = plot_data['communities'].astype(str)
    ax = plot_data.plot('communities', cmap='tab20')
    ax.set_title(f'Contains {N_comm} communities')
    cx.add_basemap(ax, source=basemap_url, crs=msoas.crs)
    return 0

EXPERIMENT_WITH_PLOTS=False
if EXPERIMENT_WITH_PLOTS:
    #Find places in community candidates
    test_msoa = "E02000977"



    get_candidates(test_msoa)

    #Plotting
    msoas = get_all_small_areas()

    key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
    basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key


    
    plot_a_community(test_msoa)

    regions = gpd.read_file("Q:/GI_Data/Boundaries/Regions/Regions2019.shp")


    plot_partitions_in_region('North West', partitions_found)
    plot_partitions_in_region('North East', partitions_found)
