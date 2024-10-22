import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd



#We need to make a lookup from LA to isochrone region


#lets get an already extant lookup to use as our baseline
LA_to_ITL_lookup = pd.read_csv("Q:\SDU\SDU_real_time_indicators\data\lookups/Local_Authority_District_(April_2021)_to_LAU1_to_ITL3_to_ITL2_to_ITL1_(January_2021)_Lookup_in_United_Kingdom.csv")


#Initialise some empty columns
LA_to_ITL_lookup["Isochrone_region"] = np.nan
LA_to_ITL_lookup["Isochrone_folder_path"] = np.nan

#for some of these isochrone regions, the ONS are very explicit about what these are:
#https://geoportal.statistics.gov.uk/datasets/5f47f967f2424a5d93e241a577e5d066_0/about
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "East Midlands (England)", "Isochrone_region"] = "EastMidlands"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "East Midlands (England)", "Isochrone_folder_path"] = "East_Midlands_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "East", "Isochrone_region"] = "EastofEngland"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "East", "Isochrone_folder_path"] = "East_of_England_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "North East (England)", "Isochrone_region"] = "NorthEast"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "North East (England)", "Isochrone_folder_path"] = "North_East_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "Northern Ireland", "Isochrone_region"] = "NorthernIreland"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "Northern Ireland", "Isochrone_folder_path"] = "Northern_Ireland_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "South East (England)", "Isochrone_region"] = "SouthEast"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "South East (England)", "Isochrone_folder_path"] = "South_East_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "South West (England)", "Isochrone_region"] = "SouthWest"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "South West (England)", "Isochrone_folder_path"] = "South_West_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "Wales", "Isochrone_region"] = "Wales"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "Wales", "Isochrone_folder_path"] = "Wales_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "West Midlands (England)", "Isochrone_region"] = "WestMidlands"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "West Midlands (England)", "Isochrone_folder_path"] = "West_Midlands_Isochrones_Gen_10"

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "Yorkshire and The Humber", "Isochrone_region"] = "YorkshireHumber"
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["ITL121NM"] == "Yorkshire and The Humber", "Isochrone_folder_path"] = "Yorkshire_and_the_Humber_Isochrones_Gen_10"

#but then we have to manually find what the LA to isochrone region lookup is for the other areas, because the ONS dont say.

#%%            

#where is "LondonWest"?

Isochrone_region = "LondonWest"
Isochrone_folder_path = "UK_Travel_Area_Isochrones_(Nov_Dec_2022)_by_Public_Transport_and_Walking_for_London_West_-_Generalised_to_10m"

isochrone_test = gpd.read_file("Q:/GI_Data/ONS/Isochrones/Clean/" + Isochrone_region + "/" + Isochrone_folder_path + ".shp") 
#drop bits we dont need
isochrone_test = isochrone_test[["OA21CD"]]

#read shapefile 
OA_map = gpd.read_file("Q:\SDU\Mobility\Data\Boundaries\Output_Areas_2021_EW_BGC_V2_-6371128854279904124/OA_2021_EW_BGC_V2.shp")


#test if London fits nicely within - make this a function so we can re-do easily for other areas

def LAs_within_Iso_map_check(isochrone_test, OA_map, left_merge_col = "OA21CD", right_merge_col = "OA21CD"):
    
    OA_map_iso = isochrone_test.merge(OA_map, left_on = left_merge_col, right_on = right_merge_col, how = "left")
    OA_map_iso = gpd.GeoDataFrame(OA_map_iso, crs=OA_map.crs, geometry=OA_map_iso.geometry)
    
    LA_map = gpd.read_file("Q:/GI_Data/Boundaries/Counties and Unitaries/2021\LA_Dec2021/LAD_DEC_2021_GB_BGC.shp")
    
    ax = plt.gca()
    OA_map_iso.plot(ax = ax)
    xmin,xmax = ax.get_xlim()
    ymin,ymax = ax.get_ylim()
    LA_map.plot(ax = ax, facecolor = "none", edgecolor = "black")
    ax.set_xlim([xmin, xmax])
    ax.set_ylim([ymin, ymax])
    plt.show()
    
#blue is isochrone start points, black is 2021 LA boundaries
LAs_within_Iso_map_check(isochrone_test, OA_map, left_merge_col = "OA21CD", right_merge_col = "OA21CD")
#they are at least LAs, thank god, it at least stops at LA level.
#ONS have split London up via LA 2021 boundaries. SO we shall do the same

#And then also just ge tthe list of LAs we need to add to the lookup


#get OA to *things* lookup
OA_to_stuff = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/OA21_LSOA21_MSOA21_LAD22_EW_LU.csv", encoding='latin-1')


def get_list_of_LAs(isochrone_test, OA_to_stuff, left_merge_col = "OA21CD", right_merge_col = "oa21cd", return_list_col = "lad22nm"):
    

    #merge
    isochrone_test = isochrone_test.merge(OA_to_stuff, left_on = left_merge_col, right_on = right_merge_col, how = "left")

    LAs_list = isochrone_test[return_list_col].unique().tolist()
    
    return(LAs_list)

LA_list = get_list_of_LAs(isochrone_test, OA_to_stuff, left_merge_col = "OA21CD", right_merge_col = "oa21cd")

LA_to_ITL_lookup.loc[LA_to_ITL_lookup["LAD21NM"].isin(LA_list), "Isochrone_region"] = Isochrone_region
LA_to_ITL_lookup.loc[LA_to_ITL_lookup["LAD21NM"].isin(LA_list), "Isochrone_folder_path"] = Isochrone_folder_path


#%%
#repeat for the other English divided regions


Isochrone_regions = ["LondonEast", "NorthWestNorth", "NorthWestSouth"]
Isochrone_folder_paths = ["London_East_Isochrones_Gen_10", "North_West_North_Isochrones_Gen_10", "North_West_South_Isochrones_Gen_10"] 


for i in range(len(Isochrone_regions)):
    
    isochrone_test = gpd.read_file("Q:/GI_Data/ONS/Isochrones/Clean/" + Isochrone_regions[i] + "/" + Isochrone_folder_paths[i] + ".shp") 
    #drop bits we dont need
    isochrone_test = isochrone_test[["OA21CD"]]
    
    LAs_within_Iso_map_check(isochrone_test, OA_map, left_merge_col = "OA21CD", right_merge_col = "OA21CD")
    
    LA_list = get_list_of_LAs(isochrone_test, OA_to_stuff, left_merge_col = "OA21CD", right_merge_col = "oa21cd")
    
    LA_to_ITL_lookup.loc[LA_to_ITL_lookup["LAD21NM"].isin(LA_list), "Isochrone_region"] = Isochrone_regions[i]
    LA_to_ITL_lookup.loc[LA_to_ITL_lookup["LAD21NM"].isin(LA_list), "Isochrone_folder_path"] = Isochrone_folder_paths[i]


#%%
#And then Scotland - they have OA2011s instead (thank god)
OA11_map = gpd.read_file("Q:\SDU\Mobility\Data\Boundaries\Scottish_2011_OAs/OutputArea2011_MHW.shp")

OA11_to_stuff = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/OA_TO_HIGHER_AREAS.csv")
OA11_CA_code_to_name = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/ca11_ca19.csv")[['CA', 'CAName']].drop_duplicates()
OA11_to_stuff = OA11_to_stuff.merge(OA11_CA_code_to_name, left_on = "CouncilArea2011Code", right_on = "CA")


Isochrone_regions = ["WestScotlandNorth", "WestScotlandSouth", "NorthScotland", "EastScotland"]
Isochrone_folder_paths = ["West_Scotland_North_-_Generalised_to_10m", "West_Scotland_South", "North_Scotland_Isochrones_Gen_10", "UK_Travel_Area_Isochrones_(Nov_Dec_2022)_by_Public_Transport_and_Walking_for_East_Scotland_-_Generalised_to_10m"] 


for i in range(len(Isochrone_regions)):
    
    isochrone_test = gpd.read_file("Q:/GI_Data/ONS/Isochrones/Clean/" + Isochrone_regions[i] + "/" + Isochrone_folder_paths[i] + ".shp") 
    #drop bits we dont need
    isochrone_test = isochrone_test[["OA11CD"]]
    
    LAs_within_Iso_map_check(isochrone_test, OA11_map, left_merge_col = "OA11CD", right_merge_col = "code")
    
    LA_list = get_list_of_LAs(isochrone_test, OA11_to_stuff, left_merge_col = "OA11CD", right_merge_col = "OutputArea2011Code", return_list_col = "CAName")
    
    LA_to_ITL_lookup.loc[LA_to_ITL_lookup["LAD21NM"].isin(LA_list), "Isochrone_region"] = Isochrone_regions[i]
    LA_to_ITL_lookup.loc[LA_to_ITL_lookup["LAD21NM"].isin(LA_list), "Isochrone_folder_path"] = Isochrone_folder_paths[i]


#wait, why are there gaps in the OAs here?
OA11_map.plot()
plt.xlim(220000, 280000)
plt.ylim(650000, 720000)
plt.show()
#hmm, it just exists in the base OA boundaries, they skip lakes. Sorry, they skip lochs.


#%%
#what, if anything, is missing
print(LA_to_ITL_lookup[LA_to_ITL_lookup["Isochrone_folder_path"].isna()])

#%%

#save results

LA_to_ITL_lookup.to_csv("Q:/SDU/Mobility/Data/Lookups/LA_to_Isochrone_region_lookup.csv")