# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 13:55:59 2024

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
import time

import matplotlib.pyplot as plt
#use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
#Basemap
import contextily as cx

from analysis.Local_travel_areas.LTA_queries import *
from analysis.Local_travel_areas.LTA_functions import *
from analysis.Local_travel_areas.LTA_plot_functions import *
from analysis.Auxiliary_msoa_data_functions import *
from analysis.utils import *

#This takes a while.
weekday_data = get_data_for_all_weekdays()

BUAs = get_BUAs()
bua_pop = get_BUA_pop()

BUAs = BUAs.merge(bua_pop, on='BUA22NM')
#Take a cutoff for now.
pop_threshold = 25e3
BUAs_of_interest = BUAs[BUAs.Population > pop_threshold]

#Get PUA areas
lad_pua_lookup = pd.read_excel("Q:/SDU/Mobility/Data/Processed/LAD_PUA_Lookup_300524.xlsx")
#Align PUA names to BUAs, as this just annoys me later
lad_pua_lookup.loc[lad_pua_lookup.PUANM=='Newcastle', 'PUANM'] = 'Newcastle upon Tyne'
lad_pua_lookup.loc[lad_pua_lookup.PUANM=='Hull', 'PUANM'] = 'Kingston upon Hull'
lad_pua_lookup.loc[lad_pua_lookup.PUANM=='Cambridge', 'PUANM'] = 'Cambridge (Cambridge)'

#Also add a PUA in Greater Lincolnshire -- here use Lincolnshire as it has the largest settlement (Lincoln).
lincoln = pd.DataFrame(['Lincoln', 'Lincolnshire','E07000138']).T
lincoln.columns = lad_pua_lookup.columns
lad_pua_lookup = pd.concat([lad_pua_lookup ,lincoln])

lad_bounds = gpd.read_file("Q:/GI_Data/Boundaries/LAD_MAY_2021_UK_BFE_V2.shp")

pua_bounds = lad_bounds.merge(lad_pua_lookup, right_on='LADCD', left_on='LAD21CD').dissolve(by ='PUANM').reset_index()
pua_bounds = pua_bounds[['PUANM', 'geometry']]

#For reference BUA to PUA we can skip
towns_in_PUAS = BUAs_of_interest.overlay(pua_bounds, keep_geom_type=False)
towns_in_PUAS = towns_in_PUAS[towns_in_PUAS.area>2e6]
town_PUA_lookup=towns_in_PUAS[['BUA22NM', 'PUANM']]

#MSOA to PUA lookup
msoa_to_lad_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/MSOA_(2011)_to_MSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_England_and_Wales_(Version_2).csv")
msoa_lad = msoa_to_lad_lookup[['MSOA11CD', 'LAD22CD']]
msoa_pua = msoa_lad.merge(lad_pua_lookup, left_on='LAD22CD', right_on='LADCD').drop_duplicates()

msoa_bua_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA_lookup.csv")

def get_BUA_to_PUA(our_bua, data):
    #Get MSOAs.
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
    bua_journeys = data[data.start_msoa.isin(our_msoas)]
    bua_destination = bua_journeys[['end_msoa', 'daily_trips']].groupby('end_msoa').sum().reset_index()
    bua_to_pua = bua_destination.merge(msoa_pua, left_on='end_msoa', right_on='MSOA11CD').groupby('PUANM').sum(numeric_only=True).reset_index()
    bua_total = bua_destination.daily_trips.sum()
    bua_to_pua['Percent'] = bua_to_pua['daily_trips']/bua_total*100
    bua_to_pua['BUANM'] = our_bua
    bua_to_pua.columns = ['dest_PUA', 'trips', 'percent', 'origin_BUA']
    return (bua_to_pua)

BUA_to_PUA = []
for BUA in BUAs_of_interest.BUA22NM:
    BUA_to_PUA.append(get_BUA_to_PUA(BUA, weekday_data))

BUA_to_PUA = pd.concat(BUA_to_PUA)


#Get BUA_to_BUA within same PUA
def get_BUAs_in_same_PUA(bua):
    pua = town_PUA_lookup[town_PUA_lookup.BUA22NM==bua].PUANM
    if len(pua)>0:
        other_buas = town_PUA_lookup[town_PUA_lookup.PUANM==pua.iloc[0]].BUA22NM.to_list()
        return (other_buas)
    else:
        return ([])
    
def get_BUA_to_BUA(our_bua, other_buas, data):
    #Get MSOAs.
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
    bua_journeys = data[data.start_msoa.isin(our_msoas)]
    bua_destination = bua_journeys[['end_msoa', 'daily_trips']].groupby('end_msoa').sum().reset_index()
    bua_flow = bua_destination.merge(msoa_bua_lookup[msoa_bua_lookup.BUA22NM.isin(other_buas)], left_on='end_msoa', right_on='msoa11cd')
    bua_flow = bua_flow.groupby('BUA22NM').sum(numeric_only=True).reset_index()

    bua_total = bua_destination.daily_trips.sum()
    bua_flow['Percent'] = bua_flow['daily_trips']/bua_total*100
    bua_flow['BUANM'] = our_bua
    bua_flow = bua_flow[['BUA22NM', 'daily_trips', 'Percent', 'BUANM']]
    bua_flow.columns = ['dest_BUA', 'trips', 'percent', 'origin_BUA']
    return (bua_flow)
    
BUA_to_BUA = []
for BUA in BUAs_of_interest.BUA22NM:
    other_BUAs = get_BUAs_in_same_PUA(BUA)
    BUA_to_BUA.append(get_BUA_to_BUA(BUA, other_BUAs, weekday_data))

BUA_to_BUA = pd.concat(BUA_to_BUA)

BUA_to_BUA.to_csv("Q:/SDU/Mobility/Outputs/Regional_Economic_Plans/BUA_to_BUA.csv", index=False)
BUA_to_PUA.to_csv("Q:/SDU/Mobility/Outputs/Regional_Economic_Plans/BUA_to_PUA.csv", index=False)


#New MCAs?
MCA_lookup_24 = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/Local_Authority_District_to_Combined_Authority_(May_2024)_Lookup_in_EN.csv")
ltla_utla = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/Lower_Tier_Local_Authority_to_Upper_Tier_Local_Authority_(December_2022)_Lookup_in_England_and_Wales.csv")

ltla_mca_lu = ltla_utla.merge(MCA_lookup_24, right_on='LAD24CD', left_on='LTLA22CD')
ltla_mca_lu = ltla_mca_lu[['LTLA22CD', 'LTLA22NM', 'CAUTH24CD', 'CAUTH24NM']]

#Do this shitty hack to include North Yorkshire bits
north_yorks_lu = ltla_utla.merge(MCA_lookup_24, right_on='LAD24NM', left_on='UTLA22NM')
north_yorks_lu = north_yorks_lu[['LTLA22CD', 'LTLA22NM', 'CAUTH24CD', 'CAUTH24NM']]

ltla_mca_lu = pd.concat([ltla_mca_lu, north_yorks_lu]).drop_duplicates()

#Norfolk and Suffolk
new_mcas = ltla_utla[ltla_utla.UTLA22NM.isin(['Norfolk', 'Suffolk', 'East Riding of Yorkshire', 
                                                     'Lincolnshire', 'North Lincolnshire', 'North East Lincolnshire', 'Kingston upon Hull, City of'])]

new_mcas['CAUTH24CD'] = "E"
new_mcas['CAUTH24NM'] = new_mcas['UTLA22NM']

new_mcas = new_mcas[['LTLA22CD', 'LTLA22NM', 'CAUTH24CD', 'CAUTH24NM']]
new_mcas.loc[new_mcas.CAUTH24NM.str.contains('Lincoln'), 'CAUTH24NM'] = 'Greater Lincolnshire'
new_mcas.loc[new_mcas.CAUTH24NM.str.contains('East Riding of Yorkshire'), 'CAUTH24NM'] = 'Hull and East Yorkshire'
new_mcas.loc[new_mcas.CAUTH24NM.str.contains('Kingston upon Hull, City of'), 'CAUTH24NM'] = 'Hull and East Yorkshire'

mca_future = pd.concat([ltla_mca_lu, new_mcas])
mca_shape = lad_bounds.merge(mca_future, left_on='LAD21CD', right_on='LTLA22CD').dissolve(by ='CAUTH24NM').reset_index()
mca_shape = mca_shape[['CAUTH24NM', 'geometry']]

#Here add Greater London to the MCA shapefile
london_shape = BUAs[BUAs.BUA22NM=='London']
london_shape = london_shape[['BUA22NM', 'geometry']]
london_shape.columns = mca_shape.columns
mca_shape = pd.concat([mca_shape, london_shape])

#Get largest city in each MCA -- this is easier than doing it by hand.
MCA_cities = BUAs.overlay(mca_shape).sort_values('Population', ascending=False).drop_duplicates('CAUTH24NM')[['CAUTH24NM', 'BUA22NM']]

#Then edit the ones which are wrong
MCA_cities.loc[MCA_cities.CAUTH24NM == 'East Midlands', 'BUA22NM'] = 'Nottingham'
MCA_cities.loc[MCA_cities.CAUTH24NM == 'Cambridgeshire and Peterborough', 'BUA22NM'] = 'Cambridge (Cambridge)'

#Check which of these are not PUAs
MCA_cities[~MCA_cities.BUA22NM.isin(pua_bounds.PUANM)]
#Lincoln is missing

#For plotting, I want to plot the connections in the MCA. And I want the top 5 connections from outside to the PUA.
#So I need a BUA to MCA lookup.
towns_in_MCAS = BUAs_of_interest.overlay(mca_shape, keep_geom_type=False)
towns_in_MCAS = towns_in_MCAS[towns_in_MCAS.area>2e6]
town_MCA_lookup=towns_in_MCAS[['BUA22NM', 'CAUTH24NM']]

#Get BUA_to_BUA within same MCA
def get_BUAs_in_MCA(MCA):
    buas = town_MCA_lookup[town_MCA_lookup.CAUTH24NM==MCA].BUA22NM.to_list()
    return (buas)
    

BUA_pop_lookup = BUAs[['BUA22NM', 'Population']]

#Manually tweak Cambridge population so it will be the centre of Cambridge and Peterborough MCA
BUA_pop_lookup.loc[BUA_pop_lookup.BUA22NM=='Cambridge (Cambridge)', 'Population'] = 200e3




MCA='North East'

#For plotting, I need the base map
key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key

#The number of towns outside the BUA to plot.
outside_count = 5

def get_arrow_weight(flow, minimum=1, maximum=21, CONSTANT=True):
    #Get a weight on 5 for 1.0 flow, and minimum of 1
    #Our flows are proportions, so already in [0,1] range
    weight = minimum + (maximum-minimum)*flow
    if CONSTANT:
        weight = 5
    return(weight)

def get_colour(flow):
    if flow > 20:
        return '#28A197'
    elif flow > 5:
        return '#801650'
    else:
        return '#A285D1'

def get_BUA_coords(our_bua):
    centroid = BUAs[BUAs.BUA22NM==our_bua].centroid
    return(centroid.x.iloc[0], centroid.y.iloc[0])

def plot_MCA_and_towns_outside(MCA, outside_count=5, town_cutoff=25e3, move_left=[], move_right=[]):
    MCA_bounds = mca_shape[mca_shape.CAUTH24NM==MCA]
    PUA_name = MCA_cities[MCA_cities.CAUTH24NM==MCA].BUA22NM.iloc[0]
    PUA_bounds = pua_bounds[pua_bounds.PUANM==PUA_name]
    
    towns_to_show = BUA_pop_lookup[BUA_pop_lookup.Population>town_cutoff].BUA22NM
    
    #Get travel to our PUA.
    our_travel = BUA_to_PUA[BUA_to_PUA.dest_PUA==PUA_name]
    our_travel = our_travel[our_travel.origin_BUA.isin(towns_to_show)]
    
    #Exclude the towns in same PUA
    our_travel = our_travel[~our_travel.origin_BUA.isin(get_BUAs_in_same_PUA(PUA_name))].sort_values('percent', ascending=False)
    travel_from_outside = our_travel[~our_travel.origin_BUA.isin(get_BUAs_in_MCA(MCA))].head(outside_count)
    
    travel_within_MCA = BUA_to_BUA[BUA_to_BUA.origin_BUA.isin(get_BUAs_in_MCA(MCA))]
    travel_within_MCA = travel_within_MCA[travel_within_MCA.origin_BUA.isin(towns_to_show)]
    other_travel_within_MCA = our_travel[our_travel.origin_BUA.isin(get_BUAs_in_MCA(MCA))]
    
    other_travel_within_MCA.columns = travel_within_MCA.columns
    travel_within_MCA = pd.concat([travel_within_MCA, other_travel_within_MCA])
    
    #Really want flow to larger population centres here.
    travel_w_pop = travel_within_MCA.merge(BUA_pop_lookup, left_on='origin_BUA', right_on='BUA22NM').merge(BUA_pop_lookup, left_on='dest_BUA', right_on='BUA22NM')
    #Use strict >; this will eliminate travel to same BUA
    travel_within_MCA = travel_w_pop[travel_w_pop.Population_y > travel_w_pop.Population_x]
    
    
    travel_within_MCA = travel_within_MCA.sort_values('percent', ascending=False).drop_duplicates('origin_BUA')[['dest_BUA', 'trips', 'percent', 'origin_BUA']]
    travel_from_inside = travel_within_MCA[~travel_within_MCA.origin_BUA.isin(get_BUAs_in_same_PUA(PUA_name))]
    travel_inside_PUA = travel_within_MCA[travel_within_MCA.origin_BUA.isin(get_BUAs_in_same_PUA(PUA_name))]

    plot_for_MCA(MCA, MCA_bounds, PUA_bounds, travel_from_inside, travel_from_outside, town_cutoff, move_left, move_right)
    plot_for_PUA(MCA, PUA_bounds, PUA_name, travel_inside_PUA, town_cutoff, move_left, move_right)
    
    return 0


def plot_for_MCA(MCA, MCA_bounds, PUA_bounds, travel_from_inside, travel_from_outside, town_cutoff, move_left=[], move_right=[]):
    f, ax = plt.subplots(figsize=(12, 12))
    BUAs.merge(pd.concat([travel_from_outside, travel_from_inside]), left_on='BUA22NM', right_on='origin_BUA').plot(ax=ax, alpha=0.0, edgecolor='#801650', facecolor='#801650')
    #BUAs.merge(pd.concat([travel_from_outside, travel_from_inside]), left_on='BUA22NM', right_on='dest_PUA').plot(ax=ax, alpha=0.7, edgecolor='#801650', facecolor='#12436D')
    PUA_bounds.plot(ax=ax, alpha=0.7, edgecolor='#12436D', facecolor='#12436D')
    MCA_bounds.boundary.plot(ax=ax, edgecolor="#3D3D3D")
    cx.add_basemap(ax, source=basemap_url, crs=MCA_bounds.crs)
    ax.set_title(f"Travel in {MCA}", fontsize=20)


#Plot arrows first
    for town_i in range(len(travel_from_outside)):
            origin_x, origin_y = get_BUA_coords(travel_from_outside.iloc[town_i]['origin_BUA'])
            dest_x, dest_y = get_BUA_coords(travel_from_outside.iloc[town_i]['dest_PUA'])
            arrow_width = get_arrow_weight(travel_from_outside.iloc[town_i]['percent']/100)
            ax.annotate("", xy=(dest_x, dest_y), xytext=(origin_x, origin_y), arrowprops=dict(arrowstyle="->, head_length=1, head_width=0.5", color='#F46A25', lw=arrow_width, alpha=0.8))
    
    
    for town_i in range(len(travel_from_inside)):
            origin_x, origin_y = get_BUA_coords(travel_from_inside.iloc[town_i]['origin_BUA'])
            dest_x, dest_y = get_BUA_coords(travel_from_inside.iloc[town_i]['dest_BUA'])
            arrow_width = get_arrow_weight(travel_from_inside.iloc[town_i]['percent']/100)
            ax.annotate("", xy=(dest_x, dest_y), xytext=(origin_x, origin_y), arrowprops=dict(arrowstyle="->, head_length=1, head_width=0.5", color='#F46A25', lw=arrow_width, alpha=0.8))

#Then plot labels
    for town_i in range(len(travel_from_outside)):
        colour = get_colour(travel_from_outside.iloc[town_i]['percent'])
        BUAs[BUAs.BUA22NM == travel_from_outside.iloc[town_i]['origin_BUA']].plot(ax=ax, alpha=0.7, edgecolor=colour, facecolor=colour)
        origin_x, origin_y = get_BUA_coords(travel_from_outside.iloc[town_i]['origin_BUA'])
        dest_x, dest_y = get_BUA_coords(travel_from_outside.iloc[town_i]['dest_PUA'])
        if travel_from_outside.iloc[town_i]['origin_BUA'].split('(')[0] in move_left:
            ax.annotate(travel_from_outside.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='right', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
        elif travel_from_outside.iloc[town_i]['origin_BUA'].split('(')[0] in move_right:
            ax.annotate(travel_from_outside.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='left', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
        else:
            ax.annotate(travel_from_outside.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='center', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))

    for town_i in range(len(travel_from_inside)):
        colour = get_colour(travel_from_inside.iloc[town_i]['percent'])
        BUAs[BUAs.BUA22NM == travel_from_inside.iloc[town_i]['origin_BUA']].plot(ax=ax, alpha=0.7, edgecolor=colour, facecolor=colour)
        origin_x, origin_y = get_BUA_coords(travel_from_inside.iloc[town_i]['origin_BUA'])
        dest_x, dest_y = get_BUA_coords(travel_from_inside.iloc[town_i]['dest_BUA'])
        if travel_from_inside.iloc[town_i]['origin_BUA'].split('(')[0] in move_left:
            ax.annotate(travel_from_inside.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='right', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
        elif travel_from_inside.iloc[town_i]['origin_BUA'].split('(')[0] in move_right:
            ax.annotate(travel_from_inside.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='left', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
        else:
            ax.annotate(travel_from_inside.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='center', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))

#Destination label
    for destination in travel_from_outside.dest_PUA.drop_duplicates():
        dest_x, dest_y = get_BUA_coords(destination)
        ax.annotate(destination.split('(')[0], xy=(dest_x,dest_y), ha='center', color='black', font='Arial', fontsize=10,
                    bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
    
    plt.savefig(f"Q:/SDU/Mobility/Outputs/Regional_Economic_Plans/{MCA}_connections_in_MCA_{town_cutoff/1e3}k.png", bbox_inches="tight", dpi=600 )

    return 0

def plot_for_PUA(MCA, PUA_bounds, PUA_name, travel_inside_PUA, town_cutoff, move_left=[], move_right=[])  :  
    f, ax = plt.subplots(figsize=(12, 12))
    BUAs.merge(travel_inside_PUA, left_on='BUA22NM', right_on='origin_BUA').plot(ax=ax, alpha=0.0, edgecolor='#801650', facecolor='#801650')
    #To get the transparency to match, only plot one copy of the destination
    BUAs.merge(travel_inside_PUA[travel_inside_PUA.dest_BUA==PUA_name], left_on='BUA22NM', right_on='dest_BUA')[['geometry']].drop_duplicates().plot(ax=ax, alpha=0.7, edgecolor='#12436D', facecolor='#12436D')
    PUA_bounds.boundary.plot(ax=ax, edgecolor="#3D3D3D")
    cx.add_basemap(ax, source=basemap_url, crs=PUA_bounds.crs)
    ax.set_title(f"Travel in the {PUA_name} Primary Urban Area", fontsize=20)

#Plot arrows first   
    for town_i in range(len(travel_inside_PUA)):
            origin_x, origin_y = get_BUA_coords(travel_inside_PUA.iloc[town_i]['origin_BUA'])
            dest_x, dest_y = get_BUA_coords(travel_inside_PUA.iloc[town_i]['dest_BUA'])
            arrow_width = get_arrow_weight(travel_inside_PUA.iloc[town_i]['percent']/100)
            ax.annotate("", xy=(dest_x, dest_y), xytext=(origin_x, origin_y), arrowprops=dict(arrowstyle="->, head_length=1, head_width=0.5", color='#F46A25', lw=arrow_width, alpha=0.8))

#Then labels
    for town_i in range(len(travel_inside_PUA)):
        colour = get_colour(travel_inside_PUA.iloc[town_i]['percent'])
        BUAs[BUAs.BUA22NM == travel_inside_PUA.iloc[town_i]['origin_BUA']].plot(ax=ax, alpha=0.7, edgecolor=colour, facecolor=colour)
        origin_x, origin_y = get_BUA_coords(travel_inside_PUA.iloc[town_i]['origin_BUA'])
        dest_x, dest_y = get_BUA_coords(travel_inside_PUA.iloc[town_i]['dest_BUA'])
        if travel_inside_PUA.iloc[town_i]['origin_BUA'].split('(')[0] in move_left:
            ax.annotate(travel_inside_PUA.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='right', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
        elif travel_inside_PUA.iloc[town_i]['origin_BUA'].split('(')[0] in move_right:
            ax.annotate(travel_inside_PUA.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='left', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))
        else:
            ax.annotate(travel_inside_PUA.iloc[town_i]['origin_BUA'].split('(')[0], xy=(origin_x,origin_y), ha='center', color='black', font='Arial', fontsize=10,
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))

#Label destination too        
    for destination in [PUA_name]:
        dest_x, dest_y = get_BUA_coords(destination)
        ax.annotate(destination.split('(')[0], xy=(dest_x,dest_y), ha='center', color='black', font='Arial', fontsize=10,
                       bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.5))

    plt.savefig(f"Q:/SDU/Mobility/Outputs/Regional_Economic_Plans/{MCA}_connections_in_largest_PUA_{town_cutoff/1e3}k.png", bbox_inches="tight", dpi=600 )
 
    return 0      
    
MCA_list = mca_shape.CAUTH24NM.to_list()

for MCA in MCA_list:
    plot_MCA_and_towns_outside(MCA)
    plot_MCA_and_towns_outside(MCA, town_cutoff=50e3)
    plot_MCA_and_towns_outside(MCA, town_cutoff=75e3)


plot_MCA_and_towns_outside('London', town_cutoff=100e3)
plot_MCA_and_towns_outside('London', town_cutoff=125e3)
plot_MCA_and_towns_outside('London', town_cutoff=150e3)

#Some adjustments to labels
plot_MCA_and_towns_outside('North East', town_cutoff=50e3, move_right=['Middlesbrough', 'Sunderland'], move_left=['Stockton-on-Tees', 'Washington'])
plot_MCA_and_towns_outside('North East', town_cutoff=25e3, move_right=['Middlesbrough', 'Sunderland'], move_left=['Stockton-on-Tees', 'Washington'])
plot_MCA_and_towns_outside('West Yorkshire', town_cutoff=50e3, move_left=['Dewsbury'])
plot_MCA_and_towns_outside('Tees Valley', town_cutoff=50e3, move_right=['Sunderland'], move_left=['Washington'])
plot_MCA_and_towns_outside('Tees Valley', town_cutoff=25e3, move_right=['Sunderland'], move_left=['Washington'])
plot_MCA_and_towns_outside('Hull and East Yorkshire', town_cutoff=25e3, move_right=['Cleethorpes'], move_left=['Grimsby'])
plot_MCA_and_towns_outside('Greater Lincolnshire', town_cutoff=50e3, move_right=['Carlton'], move_left=['Nottingham'])


#Also get stats
greater_london = ltla_utla[ltla_utla.LTLA22CD.str.startswith("E09")][['LTLA22CD', 'LTLA22NM']]
greater_london[['CAUTH24CD', 'CAUTH24NM']] = ['E', 'London']
msoa_mca = pd.concat([mca_future, greater_london]).merge(msoa_lad, left_on='LTLA22CD', right_on='LAD22CD')

MCA_stats = []

for MCA in MCA_list:
    PUA_name = MCA_cities[MCA_cities.CAUTH24NM==MCA].BUA22NM.iloc[0]
    
    #Get journeys to the PUA as a proportopn of all from the MCA
    our_start_msoas = msoa_mca[msoa_mca.CAUTH24NM==MCA].MSOA11CD
    our_end_msoas = msoa_pua[msoa_pua.PUANM==PUA_name].MSOA11CD
    all_from_MCA = weekday_data[weekday_data.start_msoa.isin(our_start_msoas)].daily_trips.sum()
    from_MCA_to_PUA = weekday_data[weekday_data.start_msoa.isin(our_start_msoas) & weekday_data.end_msoa.isin(our_end_msoas)].daily_trips.sum()
    prop1 = from_MCA_to_PUA / all_from_MCA
    
    #Get proportion of travel from outside MCA whihc comes to the MCA
    our_start_msoas_op = msoa_mca[msoa_mca.CAUTH24NM==MCA].MSOA11CD
    our_end_msoas = msoa_mca[msoa_mca.CAUTH24NM==MCA].MSOA11CD
    
    all_to_MCA = weekday_data[weekday_data.end_msoa.isin(our_end_msoas)].daily_trips.sum()
    from_outside_to_MCA = weekday_data[~weekday_data.start_msoa.isin(our_start_msoas_op) & weekday_data.end_msoa.isin(our_end_msoas)].daily_trips.sum()
    prop2 = from_outside_to_MCA / all_to_MCA
    
    #Get proportion of travel to PUA which comes from outside the MCA
    our_start_msoas_op = msoa_mca[msoa_mca.CAUTH24NM==MCA].MSOA11CD
    our_end_msoas = msoa_pua[msoa_pua.PUANM==PUA_name].MSOA11CD
    
    all_to_PUA = weekday_data[weekday_data.end_msoa.isin(our_end_msoas)].daily_trips.sum()
    from_outside_to_PUA = weekday_data[~weekday_data.start_msoa.isin(our_start_msoas_op) & weekday_data.end_msoa.isin(our_end_msoas)].daily_trips.sum()
    prop3 = from_outside_to_PUA / all_to_PUA
     
    MCA_stats.append([MCA, PUA_name, prop1, prop2, prop3])

MCA_stats = pd.DataFrame(MCA_stats, columns = ['MCA', 'PUA', 'MCA_travel_to_PUA', 'outside_travel_to_MCA', 'outside_travel_to_PUA'])

MCA_stats.round(4).to_csv("Q:/SDU/Mobility/Outputs/Regional_Economic_Plans/Regional_economic_stats.csv", index=False)


