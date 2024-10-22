# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 10:33:33 2023

@author: evan.baker
"""
import pandas as pd

def LA_to_Isochrone_region_finder(LAD_of_interest):
    #work out which isochrone we need to load
    LA_to_ITL_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/LA_to_Isochrone_region_lookup.csv")
    
    Region_selection = LA_to_ITL_lookup[LA_to_ITL_lookup["LAD21NM"] == LAD_of_interest]
 
    return(Region_selection["Isochrone_region"].values[0], Region_selection["Isochrone_folder_path"].values[0])






def exceedance_calculation(MSOA_geography_MSOA_lookup, trips):
    #This function calculates how many trips (using the trips object) are outside the provided geography.
    #the geography has to be provided via this slightly odd MSOA_geography_MSOA_lookup lookup dataframe.
    #this object should have a column "MSOA11CD_left", which has all the various starting MSOAs that we want to consider
    #It should also have a column "MSOA11CD_right", which has every MSOA that is within the destination geography we want to check the exceedance of
    #In practice, this means that the starting MSOAs, MSOA11CD_left, should be repeated many times, as we need one row for every MSOA11CD_left, MSOA11CD_right combination

    MSOA_geography_MSOA_lookup["trip_in_geography"] = 1 #by default we assume they are in the geography
    #add then check if each trip is within the geography
    trips_x = trips.merge(MSOA_geography_MSOA_lookup, left_on=['start_msoa','end_msoa'], right_on = ['MSOA11CD_left','MSOA11CD_right'], how = "left")
    trips_x = trips_x[["start_msoa", "end_msoa", "avg_daily_trips", "trip_in_geography"]]
    trips_x.loc[trips_x["trip_in_geography"].isna(), "trip_in_geography"] = 0 #we then record it not in the geography if its not

    #get avg trips within geography
    avg_trips_within_geography = trips_x.groupby("start_msoa").apply(lambda x: sum(x['avg_daily_trips']*(x['trip_in_geography']==1))).reset_index()
    avg_trips_outside_geography = trips_x.groupby("start_msoa").apply(lambda x: sum(x['avg_daily_trips']*(x['trip_in_geography']==0))).reset_index()

    trips_geography_ratio = avg_trips_within_geography.merge(avg_trips_outside_geography, on = "start_msoa")
    trips_geography_ratio.columns = ["start_msoa", "avg_trips_within_geography", "avg_trips_outside_geography"]
    trips_geography_ratio["trips_within_geography_perc"] = 100*trips_geography_ratio["avg_trips_within_geography"] / (trips_geography_ratio["avg_trips_within_geography"] + trips_geography_ratio["avg_trips_outside_geography"])

    return(trips_geography_ratio)

#check if trip is outside isochrone boundary
def isochrone_ratio_calculator(MSOA_isochrone_MSOA, trips, time_threshold = 15):
    if time_threshold not in [15,30,45,60]:
        raise ValueError("time_threshold must be one of %r." % [15,30,45,60])
    x = int(time_threshold*60) #convert minutes to seconds 
    MSOA_isochrone_MSOA_x = MSOA_isochrone_MSOA[MSOA_isochrone_MSOA["iso_cutoff"]==x]
    MSOA_isochrone_MSOA_x = MSOA_isochrone_MSOA_x[["MSOA11CD_left", "MSOA11CD_right"]]
    
    trips_isochrone_ratio = exceedance_calculation(MSOA_isochrone_MSOA_x, trips)

    return(trips_isochrone_ratio)