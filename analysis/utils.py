# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 14:33:23 2023

@author: gordon.donald
"""

#Move all code that does helpful utils to one place.

import geopandas
import pandas as pd

#The right shapefiles
def get_all_small_areas():
    msoas = geopandas.read_file("Q:\GI_Data\Boundaries\MSOA\Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp")
    izs = geopandas.read_file("Q:\SDU\Mobility\Data\Boundaries\SG_IntermediateZoneBdry_2011\SG_IntermediateZone_Bdry_2011.shp")
    ni_soa = geopandas.read_file("Q:\GI_Data\BoundariesNI\SOA2011_Esri_Shapefile_0\SOA2011.shp")

    #Get the consistent columns
    msoas = msoas[['msoa11cd', 'msoa11nm', 'geometry']]
    izs = izs[['InterZone', 'Name', 'geometry']]

    #Just give Scotland and NI same col names as EW
    izs.columns = ['msoa11cd', 'msoa11nm', 'geometry']
    ni_soa.columns = ['msoa11cd', 'msoa11nm', 'geometry']

    #Join them on
    msoas = pd.concat([msoas, izs.to_crs(msoas.crs), ni_soa.to_crs(msoas.crs)])
    return(msoas)

#The right shapefiles
def get_all_tiny_areas():
    lsoas = geopandas.read_file("Q:\GI_Data\Boundaries\LSOA\Lower_Layer_Super_Output_Areas_December_2011_Full_Clipped__Boundaries_in_England_and_Wales.shp")
    dzs = geopandas.read_file("Q:\SDU\Mobility\Data\Boundaries\SG_DataZoneBdry_2011\SG_DataZone_Bdry_2011.shp")
    ni_soa = geopandas.read_file("Q:\GI_Data\BoundariesNI\SOA2011_Esri_Shapefile_0\SOA2011.shp")

    #Get the consistent columns
    lsoas = lsoas[['lsoa11cd', 'lsoa11nm', 'geometry']]
    dzs = dzs[['DataZone', 'Name', 'geometry']]

    #Just give Scotland and NI same col names as EW
    dzs.columns = ['lsoa11cd', 'lsoa11nm', 'geometry']
    ni_soa.columns = ['lsoa11cd', 'lsoa11nm', 'geometry']

    #Join them on
    lsoas = pd.concat([lsoas, dzs.to_crs(lsoas.crs), ni_soa.to_crs(lsoas.crs)])
    return(lsoas)

def get_pop_for_all_small_areas():
    msoa_pop = pd.read_excel("Q:/SDU/Mobility/Data/Auxiliary_data/msoa_2011_2020_pop_estimates.xlsx", sheet_name = "Mid-2020 Persons", skiprows=4)
    iz_pop = pd.read_csv("Q:/SDU/Mobility/Data/Auxiliary_data/iz2011-pop-est_09092022.csv")
    soa_pop = pd.read_excel("Q:/SDU/Mobility/Data/Auxiliary_data/MYE20-SOA-WARD.xlsx",  sheet_name="Flat")

    #Process to get rid of stuff we don't want.
    soa_pop = soa_pop[(soa_pop['age']=="All ages") * (soa_pop['gender']=="All persons") * (soa_pop['area']=="1. Super Output Areas") * (soa_pop['year']==2020)]
    iz_pop = iz_pop[(iz_pop['Year']==2020) * (iz_pop['Sex']=="All") * (iz_pop['IntZone']!="S92000003")]

    #Get the columns we want
    iz_pop = iz_pop[['IntZone', 'AllAges']]
    soa_pop = soa_pop[['area_code', 'MYE']]
    msoa_pop = msoa_pop[['MSOA Code', 'All Ages']]
    #Rename consistently and join
    msoa_pop.columns = ['msoa11cd', 'pop']
    soa_pop.columns = ['msoa11cd', 'pop']
    iz_pop.columns = ['msoa11cd', 'pop']
    msoa_pop = pd.concat([msoa_pop, iz_pop, soa_pop])
    
    return(msoa_pop)

#The right shapefiles
def get_all_small_areas_PWCs():
    msoa_PWCs = pd.read_csv("Q:/SDU/Mobility/Data/PWCs/MSOA_Dec_2011_PWC_in_England_and_Wales_2022_-7657754233007660732.csv")
    msoa_PWCs = geopandas.GeoDataFrame(msoa_PWCs, crs = "EPSG:27700", geometry=geopandas.points_from_xy(msoa_PWCs.x, msoa_PWCs.y))

    iz_PWCs = geopandas.read_file("Q:\SDU\Mobility\Data\PWCs\SG_IntermediateZoneCent_2011\SG_IntermediateZone_Cent_2011.shp")
    
    ni_soa_PWCs = geopandas.read_file("Q:/SDU/Mobility/Data/PWCs/OA_ni ESRI/OA_ni.shp")
    ni_soa_PWCs = geopandas.GeoDataFrame(ni_soa_PWCs, crs = "EPSG:27700", geometry=geopandas.points_from_xy(ni_soa_PWCs.X_POPCOORD, ni_soa_PWCs.Y_POPCOORD))
    ni_soa_PWCs.insert(1 ,'name', 'Not needed here')

    #Get the consistent columns
    msoa_PWCs = msoa_PWCs[['MSOA11CD', 'MSOA11NM', 'geometry']]
    iz_PWCs = iz_PWCs[['InterZone', 'Name', 'geometry']]
    ni_soa_PWCs = ni_soa_PWCs[['OA_CODE', 'name', 'geometry']]

    #Just give Scotland and NI same col names as EW
    iz_PWCs.columns = ['MSOA11CD', 'MSOA11NM', 'geometry']
    iz_PWCs.columns = ['MSOA11CD', 'MSOA11NM', 'geometry']

    #Join them on
    msoa_PWCs = pd.concat([msoa_PWCs, iz_PWCs.to_crs(msoa_PWCs.crs), iz_PWCs.to_crs(msoa_PWCs.crs)])
    return(msoa_PWCs)



#Lookup to LAD and region.
def build_msoa_lad_itl_lookup(RESOLVE_AMBIGUITY=True):
    msoa_lad = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/MSOA_(2011)_to_MSOA_(2021)_to_Local_Authority_District_(2022)_Lookup_for_England_and_Wales_(Version_2).csv")
    iz_lad = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/DataZone2011lookup.csv", encoding='ANSI') #Need to specify non-standard encoding... ffs
    soa_lad = pd.read_excel("Q:/SDU/Mobility/Data/Lookups/11DC_Lookup_1_1.xls", sheet_name = 'SOA2001_2_LGD2014') #Despite sheet name, these are from 2011 census in the metadata -- think this just hasn't been updated before publication.

    #These are all we want for msoas
    msoa_lad = msoa_lad[['MSOA11CD','MSOA11NM','LAD22CD','LAD22NM']].drop_duplicates()
    iz_lad = iz_lad[['IZ2011_Code', 'IZ2011_Name','LA_Code', 'LA_Name']].drop_duplicates()
    iz_lad.columns = ['MSOA11CD','MSOA11NM','LAD22CD','LAD22NM']
    soa_lad.insert(1 ,'name', 'Not needed here')
    soa_lad.columns = ['MSOA11CD','MSOA11NM','LAD22CD','LAD22NM']
    
    msoa_lad = pd.concat([msoa_lad, iz_lad, soa_lad])
    lad_region = pd.read_csv("Q:/SDU/SDU_real_time_indicators/data/lookups/Local_Authority_District_(April_2021)_to_LAU1_to_ITL3_to_ITL2_to_ITL1_(January_2021)_Lookup_in_United_Kingdom.csv")
    lad_region = lad_region[['LAD21CD', 'ITL121CD', 'ITL121NM']]

    #We get away with this OK, don't we?
    msoa_lad_region = msoa_lad.merge(lad_region, left_on='LAD22CD', right_on='LAD21CD').drop_duplicates().reset_index()
    #There are 4 2011 MSOAs which map to 2 LADs (2022)
    #By inspection, we can tell which is best for each.
    if RESOLVE_AMBIGUITY:
        msoa_lad_region = msoa_lad_region.drop(msoa_lad_region.index[[2085, 4614, 4864, 5711]])
    return(msoa_lad_region)


#A quick check on MSOAs with some ambiguity for the LAD (2022 boundaries)
def look_at_2011_msoa_to_2022_lad_issues():
    msoa_lad_region = build_msoa_lad_itl_lookup(RESOLVE_AMBIGUITY=False)
    msoas= get_all_small_areas()
    lads = geopandas.read_file("Q:/GI_Data/Boundaries/LAD_MAY_2021_UK_BFE_V2.shp")
    msoas_issues = msoa_lad_region[msoa_lad_region['MSOA11CD'].duplicated()]['MSOA11CD']
    shapes_issues = msoas[msoas['msoa11cd'].isin(msoas_issues)]
    overlaps = geopandas.overlay(lads, shapes_issues)
    overlaps['area'] = overlaps.area
    #For each MSOA, there is an unambiguous by far biggest overlap.
    best_fit = overlaps[overlaps['area']>1e6][['msoa11cd', 'LAD21CD']]
    best_fit.columns = ['MSOA11CD', 'LAD22CD']
    x=msoa_lad_region[msoa_lad_region['MSOA11CD'].duplicated(keep=False)][['MSOA11CD', 'LAD22CD']]
    return([best_fit, x])


#Database queries.
import pyodbc                              
server = 'DAP-SQL01\CDS' 
database = 'Place'

# ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
cnxn = pyodbc.connect(driver='{SQL Server Native Client 11.0}', 
                      host=server, database=database, trusted_connection='yes')

def query_wrapped_check(query, force_override=False):
    SQL_KEYWORDS = ['WHERE', 'GROUPBY', 'SUM']
    safe=False
    if any(keyword in query for keyword in SQL_KEYWORDS):
        safe=True
    #Return True
    go_ahead = safe or force_override
    return(go_ahead)
    

def submit_sql_query(query, force_override=False):
    if query_wrapped_check(query, force_override):
        return(pd.read_sql_query(query, cnxn))
    else:
        print("SQL query failed our wrapper check for filtering or aggregation. Use force_override=True if you know what you're doing and you really want to run that query")
        return(0)

def get_BUA_pop(ADD_LONDON=True):
    bua_pop = pd.read_excel("Q:/SDU/Towns_indicative_selection_QA/Data/OFF-SEN - BUA Analysis - LUWPs Ranking v01.02.xlsx", sheet_name='BUA_Population', skiprows=2)
    bua_pop_wales = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Data/BUA_pop-wales.csv", skiprows=2, encoding = 'unicode_escape') #Wales sheet of this data)
    bua_pop_scotland = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Data/Scotland_settlement_pop.csv")

    bua_pop = bua_pop[['BUA name', 'BUA code', 'Counts']]
    bua_pop_wales = bua_pop_wales[['BUA name', 'BUA code', ' Counts ']]
    bua_pop_scotland = bua_pop_scotland[['Settlement name', 'Settlement code', 'population']]

    bua_pop.columns = ['BUA22NM', 'BUA22CD', 'Population']
    bua_pop_wales.columns = ['BUA22NM', 'BUA22CD', 'Population']
    bua_pop_scotland.columns = ['BUA22NM', 'BUA22CD', 'Population']

    bua_pop_all = pd.concat([bua_pop, bua_pop_scotland, bua_pop_wales])
    if ADD_LONDON:
        gl_pop = pd.DataFrame(['London', 'E12000007', 9468000]).T
        gl_pop.columns=bua_pop_all.columns
        bua_pop_all = pd.concat([bua_pop_all, gl_pop])

    return(bua_pop_all)


def get_BUAs(ADD_LONDON=True):
    #We also need Greater London for this, which isn't in BUAs methodology.
    BUAs = geopandas.read_file("Q:\SDU\Towns_indicative_selection_QA\Shapefiles\BUA_2022_GB_2824430073212747649\BUA_2022_GB.shp")
    if ADD_LONDON:
        regions = geopandas.read_file("Q:\GI_Data\Boundaries\Regions\Regions2019.shp")
        gl = regions.iloc[6:7]
        gl.columns = ['id', 'BUA22CD', 'BUA22NM', 'BNG_E', 'BNG_N', 'LONG', 'LAT', 'AREA', 'LEN', 'geometry']
        BUAs = pd.concat([BUAs, gl])
    return(BUAs)