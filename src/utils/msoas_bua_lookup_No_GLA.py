# %%
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 12:10:04 2023

@author: gordon.donald
"""

#Get MSOA to BUA lookup
#We're using the overlap method. All MSOAs which overlap the BUA will be included
#THIS IS JUST GB

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd
from analysis.utils import *

BUAs = gpd.read_file(r"Q:\SDU\Towns_indicative_selection_QA\Shapefiles\BUA_2022_GB_2824430073212747649\BUA_2022_GB.shp")


BUA_code = "E63000001"

def get_msoas_in_BUA(BUA_code):
    shape = BUAs[BUAs.BUA22CD == BUA_code]
    msoas_within = list(gpd.overlay(msoas, shape)['msoa11cd'])
    return(msoas_within)

def get_lsoas_in_BUA(BUA_code):
    shape = BUAs[BUAs.BUA22CD == BUA_code]
    lsoas_within = list(gpd.overlay(lsoas, shape)['lsoa11cd'])
    return(lsoas_within)

GET_MSOA_BUA_LOOKUP = True
GET_LSOA_BUA_LOOKUP = True

#For each MSOA, which BUA is it in?
if GET_MSOA_BUA_LOOKUP or GET_LSOA_BUA_LOOKUP:

   #THIS lookup is considering all BUAs as in the 2022 file including all london boroughs trated indipendently

    #Get BUA populations, to select largest BUA
    #NO Northern Ireland at the moment
    bua_pop = pd.read_excel("Q:/SDU/Towns_indicative_selection_QA/Data/OFF-SEN - BUA Analysis - LUWPs Ranking v01.02.xlsx", sheet_name='BUA_Population', skiprows=2)
    bua_pop_wales = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Data/BUA_pop-wales.csv", skiprows=2, encoding = 'unicode_escape') #Wales sheet of this data)
    bua_pop_scotland = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Data/Scotland_settlement_pop.csv")
    #need to add London's Boroughs pop from LAD21 stats as the data at BUA excludes all London Boroughs
    bua_pop_london=pd.read_csv(r"Q:\SDU\Mobility\Data\Processed\LondonBUApop2021_FromNomis.csv")
    bua_pop = bua_pop[['BUA name', 'BUA code', 'Counts']]
    bua_pop_wales = bua_pop_wales[['BUA name', 'BUA code', ' Counts ']]
    bua_pop_scotland = bua_pop_scotland[['Settlement name', 'Settlement code', 'population']]


    bua_pop.columns = ['BUA22NM', 'BUA22CD', 'Population']
    bua_pop_wales.columns = ['BUA22NM', 'BUA22CD', 'Population']
    bua_pop_scotland.columns = ['BUA22NM', 'BUA22CD', 'Population']
    bua_pop_london.columns=['BUA22NM', 'BUA22CD', 'Population']
    bua_pop_all = pd.concat([bua_pop, bua_pop_scotland, bua_pop_wales, bua_pop_london])
    print(bua_pop_all.columns)

    BUAs = BUAs.merge(bua_pop_all, left_on='BUA22NM', right_on='BUA22NM')
    
    if GET_MSOA_BUA_LOOKUP:
        
        msoas=get_all_small_areas()
        
        bua_by_msoa = gpd.overlay(BUAs, msoas)
        bua_by_msoa_largest_BUA = bua_by_msoa.sort_values('Population').drop_duplicates(['msoa11cd'], keep='last')
    
        bua_by_msoa_to_store = bua_by_msoa_largest_BUA[['msoa11cd', 'msoa11nm', 'BUA22CD_y', 'BUA22NM', 'Population']]
        bua_by_msoa_to_store.columns = ['msoa11cd', 'msoa11nm', 'BUA22CD', 'BUA22NM', 'Population']
    
        not_in_BUA_msoa = msoas[~msoas.msoa11cd.isin(bua_by_msoa_largest_BUA.msoa11cd)]
        not_in_BUA_msoa_to_store = not_in_BUA_msoa[['msoa11cd', 'msoa11nm']]
        not_in_BUA_msoa_to_store['BUA22CD'] = 'None'
        not_in_BUA_msoa_to_store['BUA22NM'] = 'None'
        not_in_BUA_msoa_to_store['Population'] = 0
        
        bua_by_msoa_to_store = pd.concat([bua_by_msoa_to_store, not_in_BUA_msoa_to_store])   
        
        bua_by_msoa_to_store.sort_values('BUA22CD').to_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA__NOGLA_lookup.csv", index=False, mode='w')

    if GET_LSOA_BUA_LOOKUP:
        
        lsoas=get_all_tiny_areas()
        bua_by_lsoa = gpd.overlay(BUAs, lsoas, keep_geom_type=False)
        bua_by_lsoa_largest_BUA = bua_by_lsoa.sort_values('Population').drop_duplicates(['lsoa11cd'], keep='last')
    
        bua_by_lsoa_to_store = bua_by_lsoa_largest_BUA[['lsoa11cd', 'lsoa11nm', 'BUA22CD_y', 'BUA22NM', 'Population']]
        bua_by_lsoa_to_store.columns = ['lsoa11cd', 'lsoa11nm', 'BUA22CD', 'BUA22NM', 'Population']
    
        not_in_BUA_lsoa = lsoas[~lsoas.lsoa11cd.isin(bua_by_lsoa_largest_BUA.lsoa11cd)]
        not_in_BUA_lsoa_to_store = not_in_BUA_lsoa[['lsoa11cd', 'lsoa11nm']]
        not_in_BUA_lsoa_to_store['BUA22CD'] = 'None'
        not_in_BUA_lsoa_to_store['BUA22NM'] = 'None'
        not_in_BUA_lsoa_to_store['Population'] = 0
        
        bua_by_lsoa_to_store = pd.concat([bua_by_lsoa_to_store, not_in_BUA_lsoa_to_store])   
        
        bua_by_lsoa_to_store.sort_values('BUA22CD').to_csv("Q:/SDU/Mobility/Data/Processed/LSOA_to_BUA_NOGLA_lookup.csv", index=False)