# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 15:31:23 2023

@author: gordon.donald
"""

#Get the LTAs for Built Up Areas.

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
pop_threshold = 10e3
BUAs_of_interest = BUAs[BUAs.Population > pop_threshold]


#MSOA-BUA lookup
msoa_bua_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA_lookup.csv")
lsoa_bua_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/LSOA_to_BUA_lookup.csv")

#Get the LTA for a BUA.
our_bua = BUAs_of_interest.iloc[0]['BUA22NM']
our_bua='Hastings'

def get_BUA_LTA(our_bua, data, threshold=0.9):
    #Get MSOAs.
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
    bua_journeys = data[data.start_msoa.isin(our_msoas)]
    bua_destination = bua_journeys[['end_msoa', 'daily_trips']].groupby('end_msoa').sum().reset_index()


    #Alright -- let's find the destinations accounting for up to X% of total trips.
    bounds = get_bounds(bua_destination, 'daily_trips', threshold)
    
    return(bounds)

def get_travel_from_bigger_towns(our_bua, main_town='None'):
    our_rev_lta = get_BUA_origins(our_bua, weekday_data, threshold=1)
    our_rev_lta_w_pop = our_rev_lta.merge(msoa_bua_lookup)
    our_bua_pop = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['Population'].iloc[0]
    travel_from_bigger_buas = our_rev_lta_w_pop[our_rev_lta_w_pop.Population > our_bua_pop]['Percent'].sum()
    
    if main_town!='None':
        main_place_rev_perc = our_rev_lta_w_pop[our_rev_lta_w_pop.BUA22NM==main_town].Percent.sum()
    else:
        main_place_rev_perc = 0 
    return([travel_from_bigger_buas, main_place_rev_perc])
    

def get_travel_to_bigger_towns(our_bua):
    our_lta = get_BUA_LTA(our_bua, weekday_data, threshold = 1)
    our_lta_w_pop = our_lta.merge(msoa_bua_lookup)
    our_bua_pop = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['Population'].iloc[0]
    travel_to_bigger_buas = our_lta_w_pop[our_lta_w_pop.Population > our_bua_pop]['Percent'].sum()
    
    travel_to_smaller_buas = our_lta_w_pop[our_lta_w_pop.Population < our_bua_pop]['Percent'].sum()
    travel_to_same_bua = our_lta_w_pop[our_lta_w_pop.BUA22NM==our_bua]['Percent'].sum()
    
    
    if travel_to_bigger_buas > 0:
        main_place = our_lta_w_pop[our_lta_w_pop.Population > our_bua_pop].groupby('BUA22NM').sum('Percent').reset_index().sort_values(by='Percent', ascending=False).iloc[0]['BUA22NM']
        main_place_perc = our_lta_w_pop[our_lta_w_pop.Population > our_bua_pop].groupby('BUA22NM').sum('Percent').reset_index().sort_values(by='Percent', ascending=False).iloc[0]['Percent']
        main_place_pop = our_lta_w_pop[our_lta_w_pop.Population > our_bua_pop].groupby(['BUA22NM', "Population"]).sum('Percent').reset_index().sort_values(by='Percent', ascending=False).iloc[0]['Population']

        #and also work out if there's travel to a city
        if our_lta_w_pop.Population.max() >= 100000:
            main_city = our_lta_w_pop[(our_lta_w_pop.Population > our_bua_pop) & (our_lta_w_pop.Population > 100000)].groupby('BUA22NM').sum('Percent').reset_index().sort_values(by='Percent', ascending=False).iloc[0]['BUA22NM']
            main_city_perc = our_lta_w_pop[(our_lta_w_pop.Population > our_bua_pop) & (our_lta_w_pop.Population > 100000)].groupby('BUA22NM').sum('Percent').reset_index().sort_values(by='Percent', ascending=False).iloc[0]['Percent']
            main_city_pop = our_lta_w_pop[our_lta_w_pop.Population > our_bua_pop].groupby(['BUA22NM', "Population"]).sum('Percent').reset_index().sort_values(by='Percent', ascending=False).iloc[0]['Population']

        else:
            main_city = 'None'
            main_city_perc = 0
            main_city_pop = 0
    
    else:
        main_place='None'
        main_place_perc = 0
        main_place_pop = 0
        main_city = 'None'
        main_city_perc = 0
        main_city_pop = 0


    return([travel_to_bigger_buas, main_place, main_place_perc, main_place_pop, main_city, main_city_perc, main_city_pop, travel_to_smaller_buas, travel_to_same_bua])



lsoa_gva = get_total_gva_by_lsoa()
def get_gva_in_BUA(our_bua, lsoa_bua_lookup, lsoa_gva):
    our_lsoas = lsoa_bua_lookup[lsoa_bua_lookup.BUA22NM == our_bua]['lsoa11cd']
    our_gva = lsoa_gva[lsoa_gva.lsoa11cd.isin(our_lsoas)]
    total_gva = our_gva.gva.sum()
    return(total_gva)

msoa_jobs = get_total_jobs_by_msoa()
def get_jobs_in_BUA(our_bua, msoa_bua_lookup, msoa_jobs):
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
    our_jobs = msoa_jobs[msoa_jobs.msoa11cd.isin(our_msoas)]
    total_jobs = our_jobs.jobs.sum()
    return(total_jobs)

def get_total_population_in_BUA(our_bua, BUAs):
    #Sometimes we might have two towns with the same name (one in Scotland). In these edge cases, we're interested in the bigger one.
    return(max(BUAs[BUAs.BUA22NM==our_bua]['Population']))


def get_GVA_per_job_BUA():
    lookup_rows=[]
    for unique_bua in msoa_bua_lookup.BUA22NM.drop_duplicates():
        gva = get_gva_in_BUA(unique_bua, lsoa_bua_lookup, lsoa_gva)*1e6
        jobs = get_jobs_in_BUA(unique_bua, msoa_bua_lookup, msoa_jobs)
        lookup_rows.append([unique_bua, gva/jobs])
    lookup = pd.DataFrame(lookup_rows, columns=['BUA22NM', 'GVA_per_job'])
    return(lookup)

#Get the GVA per job for all BUAs, and join
bua_gva=get_GVA_per_job_BUA()
bua_msoa_w_gva = msoa_bua_lookup.merge(bua_gva)

#Benchmark with the GB average as the NOMIS jobs data doesn't include Northern Ireland.
GB_GVA_total = lsoa_gva[~lsoa_gva.lsoa11cd.str.startswith('9')].gva.sum()*1e6
GB_jobs_total = msoa_jobs.jobs.sum()
average_GVA_per_job = GB_GVA_total/GB_jobs_total

#Further request is then to get the proportion of journeys to larger BUAs which have high/low GVA based on national averages.
def get_travel_to_areas_by_pop_gva_ratio(our_bua, POP='Higher', GVA='Higher'):
    our_lta = get_BUA_LTA(our_bua, weekday_data, threshold = 1)
    our_lta_w_pop = our_lta.merge(bua_msoa_w_gva)
    our_bua_pop = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['Population'].iloc[0]

    if POP=='Higher':
        lta_subset = our_lta_w_pop[our_lta_w_pop.Population> our_bua_pop]
    else: #Assume we want lower population
        lta_subset = our_lta_w_pop[our_lta_w_pop.Population< our_bua_pop]

    if GVA=='Higher':
        lta_further_subset = lta_subset[lta_subset.GVA_per_job > average_GVA_per_job]
    else: #Assume we want lower GVA
        lta_further_subset = lta_subset[lta_subset.GVA_per_job < average_GVA_per_job]

    return(lta_further_subset.Percent.sum() / lta_subset.Percent.sum() *100 )

#We can also get total household income (for now) all households.
msoa_inc = get_gross_household_income_by_msoa11()
msoa_hhlds = get_total_households_by_msoa11()
msoa_inc_hhlds = msoa_inc.merge(msoa_hhlds, on='MSOA11CD')
msoa_inc_hhlds["total_income"] = msoa_inc_hhlds["income"]*msoa_inc_hhlds["households"]

msoa2021_bua_lookup = pd.read_csv("Q:\SDU\Mobility\Data\Lookups\MSOA_(2021)_to_Built-up_Area_to_Local_Authority_District_to_Region_(December_2022)_Lookup_in_England_and_Wales_v2.csv")
#include London as a BUA
msoa2021_bua_lookup.loc[msoa2021_bua_lookup["RGN22CD"] =="E12000007", "BUA22CD"] = "E12000007"
msoa2021_bua_lookup.loc[msoa2021_bua_lookup["RGN22CD"] =="E12000007", "BUA22NM"] = "London"
msoa2021_bua_lookup = msoa2021_bua_lookup.drop_duplicates(subset=['MSOA21CD', 'BUA22CD'])

def get_income_in_BUA(our_bua, BUAs, msoa_bua_lookup, msoa_inc_hhlds):
    our_bua_code = BUAs[BUAs["BUA22NM"] == our_bua].BUA22CD_x.values[0]
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22CD == our_bua_code]['msoa11cd']
    our_income = msoa_inc_hhlds[msoa_inc_hhlds.MSOA11CD.isin(our_msoas)]
    total_income = our_income.sum()
    if len(our_income) > 0:
        total_income["average_income"] = total_income["total_income"]/total_income["households"]
    else:
        print("No income data for " + our_bua)
        total_income["average_income"] = np.nan

    return(total_income.average_income)




# Function to plot origins of journeys to a BUA.
# Args:
# our_bua ~ name of chosen bua (str)
# data ~ data to be plotted (df)
# BUA_boudary ~ default True. This will use the BUA boundary. If false, will use the set of MSOAs which intersect the BUA as the boundary (bool)
#For plot, use OS API
# read in SDU OS API key
key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key


def plot_LTAs_around_BUA(our_bua, data, BUA_boundary=True):

    # Finding start MSOAs with 50, 80, 90% of trips
    bounds90 = get_BUA_LTA(our_bua, data, 0.9)    
    bounds80 = get_BUA_LTA(our_bua, data, 0.8) 
    if BUA_boundary:   
        bounds50 = get_BUA_LTA(our_bua, data, 0.5)    

    # Get BUA/MSOA intersection with BUA boundary.
    # Reading in BUA shp file if not already in global scope
    if BUA_boundary:   
        if "BUAs" not in globals():
            global BUAs
            BUAs=get_BUAs()
        chosen_BUA = BUAs[BUAs['BUA22NM']==our_bua]
    else:
        our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM == our_bua]['msoa11cd']
        bua_journeys = data[data.end_msoa.isin(our_msoas)]
        bua_origins = bua_journeys[['start_msoa', 'daily_trips']].groupby('start_msoa').sum().reset_index()
        bounds_cen = get_bounds_central(bua_origins, our_msoas, msoa_pos="start_msoa")

    # Plot map
    f, ax = plt.subplots(figsize=(12, 12))
    bounds90.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.6, label='90% LTA')
    bounds80.plot(ax=ax, color=map_lu_partnership_colour_scale[2], alpha=0.9, label='80%')
    if BUA_boundary:
        bounds50.plot(ax=ax, color=map_lu_partnership_colour_scale[3], alpha=0.9, label='50%')
        chosen_BUA.plot(ax=ax, color=map_lu_partnership_colour_scale[4], alpha=0.9, label=our_bua)
    else:
        bounds_cen.plot(ax=ax, color= map_lu_partnership_colour_scale[4], alpha=0.9, label=our_bua)

    lines = [
        Line2D([0], [0], linestyle="none", marker="s", markersize=10, markerfacecolor=t.get_facecolor())
        for t in ax.collections[0:]
        ]
    labels = [t.get_label() for t in ax.collections[0:]]
    ax.legend(lines, labels)
    plt.suptitle("Area containing 90% of trips to "+ our_bua)
    cx.add_basemap(ax, source=basemap_url, crs=bounds90.crs)
    plt.show()
    plt.close()
    return(0)

#Examples
GET_PLOTS_FOR_EXAMPLES=False
if GET_PLOTS_FOR_EXAMPLES:
    plot_LTAs_around_BUA("York", weekday_data)
    plot_LTAs_around_BUA("Whitby", weekday_data)
    plot_LTAs_around_BUA("Scarborough", weekday_data)


#now lets get the full dataset for the economic integration for each BUA

#first lets create a function that produces the relevant dataframe for a provided set of towns
def get_LTA_bigger_area_travel_dataframe(towns):
    summary = []
    for town in towns:
        #print(town)
        travel_to_bigger_towns = get_travel_to_bigger_towns(town)
        travel_from_bigger_towns = get_travel_from_bigger_towns(town, travel_to_bigger_towns[1])
        

        summary.append([town, travel_to_bigger_towns[0], travel_to_bigger_towns[1], travel_to_bigger_towns[2], travel_to_bigger_towns[3],
                            travel_to_bigger_towns[4], travel_to_bigger_towns[5], travel_to_bigger_towns[6], travel_to_bigger_towns[7], travel_to_bigger_towns[8],
                            get_jobs_in_BUA(town, msoa_bua_lookup, msoa_jobs)/get_total_population_in_BUA(town, BUAs), get_income_in_BUA(town, BUAs, msoa_bua_lookup, msoa_inc_hhlds), get_gva_in_BUA(town, lsoa_bua_lookup, lsoa_gva)/get_total_population_in_BUA(town, BUAs),
                            get_gva_in_BUA(town, lsoa_bua_lookup, lsoa_gva)/get_jobs_in_BUA(town, msoa_bua_lookup, msoa_jobs),
                            travel_from_bigger_towns[0], travel_from_bigger_towns[1], get_travel_to_areas_by_pop_gva_ratio(town), get_travel_to_areas_by_pop_gva_ratio(town, GVA='Lower') ])
        towns_data = pd.DataFrame(summary, columns=['Town', 'travel_to_bigger_area', 'primary_bigger_BUA', 'primary_bigger_BUA_perc', 'primary_bigger_BUA_pop',
                                                        'primary_bigger_city', 'primary_bigger_city_perc', 'primary_bigger_city_pop', 'travel_to_smaller_area', 'travel_within_same_area',
                                                        'job_ratio', 'avg_total_income', 'total_gva_per_person', 'total_gva_per_job', 'travel_from_bigger_areas', 'travel_from_primary_bigger_area',
                                                        'perc_travel_to_bigger_areas_high_GVA', 'perc_travel_to_bigger_areas_low_GVA'])
       
    return(towns_data)

#Some timing tests -- first 10 takes 27 seconds to run; first 20 takes 50. Should only be 35-40 minutes to brute force all of these and save as a json.
import time
st=time.time()

STORE_LTAS=False

if STORE_LTAS:
    ltas = []
summary = []
towns3 = []

for town in BUAs_of_interest.BUA22NM:
    #print(town)
    if len(msoa_bua_lookup[msoa_bua_lookup.BUA22NM == town]) > 0:
       towns3.append(town)
       if STORE_LTAS:
           lta = get_BUA_LTA(town, weekday_data).iloc[:,[0,4]]
           ltas.append([town, lta])
    else:
        print("Skipping "+town+ ", presumably because all its MSOAs overlap with larger BUAs and it's too small.")

towns_data = get_LTA_bigger_area_travel_dataframe(towns3)

towns_data.to_csv("Q:/SDU/Mobility/Data/Processed/towns_ltas_add_travel_from_and_gva_details.csv", na_rep='nan')

if STORE_LTAS:
    ltas_to_save=pd.DataFrame(ltas, columns=['BUA22NM', 'LTA'])
    ltas_to_save.to_json("Q:/SDU/Mobility/Data/Processed/BUA_LTAs.json", orient='records')

#How to read in
#read = pd.read_json("Q:/SDU/Mobility/Data/Processed/BUA_LTAs.json")
#df = pd.DataFrame(read.iloc[0]['LTA'])

et=time.time()
print(et-st)




#Some examples -- these are based on economic integration chats with LU Analysis.


if GET_PLOTS_FOR_EXAMPLES:
    towns1 = ['York','Cheltenham','Ipswich','Hastings', 'Whitby','St Austell','Bradford','Warrington',
         'Royal Sutton Coldfield','Wakefield', "Barrow-in-Furness"]

    towns2 = ['York','Gloucester','Ipswich','Scarborough','Bradford','Warrington',
         'Wakefield', 'Eastbourne', 'Newquay', 'Glossop', "Barrow-in-Furness"]


    economic_integration_scatter(towns_data, towns1)

    economic_integration_scatter(towns_data, towns2, title = "Economic integration for sample towns (with changes)")


    