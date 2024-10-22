# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 15:35:01 2023

@author: gordon.donald
"""

from analysis.utils import *

#Tests -- but these only work efficiently for a single MSOA.
def get_data_for_msoa(msoa_code):
    query = "SELECT * FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE start_msoa = '" +msoa_code+ "' AND start_date='2023-03-27' "
    return(submit_sql_query(query))

#Selecting journeys where msoa of interest is the destination
def get_data_for_msoa_origins(msoa_code):
    query = "SELECT * FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE end_msoa = '" +msoa_code+ "' AND start_date='2023-03-27' "
    return(submit_sql_query(query))

def get_data_for_msoa_weekend(msoa_code):
    query = "SELECT * FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE start_msoa = '" +msoa_code+ "' AND start_date='2023-03-18' "
    return(submit_sql_query(query))

#Selecting journeys where msoa of interest is the destination
def get_data_for_msoa_weekend_origins(msoa_code):
    query = "SELECT * FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE end_msoa = '" +msoa_code+ "' AND start_date='2023-03-18' "
    return(submit_sql_query(query))

def get_destinations(msoa_code):
    data = get_data_for_msoa(msoa_code)
    #Group by end_msoa and sum avg_daily_trips
    destinations = data[['end_msoa', 'avg_daily_trips']].groupby('end_msoa').sum()
    return(destinations)

def get_origins(data, msoa_code):
    #Filtering data for single msoa
    data =  data[data['end_msoa'] == msoa_code]
    #Group by start_msoa and sum avg_daily_trips
    origins = data[['start_msoa', 'daily_trips']].groupby('start_msoa').sum()
    return(origins)

def get_destinations_weekend(msoa_code):
    data = get_data_for_msoa_weekend(msoa_code)
    #Group by end_msoa and sum avg_daily_trips
    destinations = data[['end_msoa', 'avg_daily_trips']].groupby('end_msoa').sum()
    return(destinations)

def get_origins_weekend(data, msoa_code):
    #Filtering data for single msoa
    data =  data[data['end_msoa'] == msoa_code]
    #Group by start_msoa and sum avg_daily_trips
    origins = data[['start_msoa', 'daily_trips']].groupby('start_msoa').sum()
    return(origins)

#This is much preferred if we want to look at all MSOAs -- get all the data from a single query first
def get_data_for_weekdays():
    #This query takes about 4 mins, which is okay.
    query = "SELECT start_msoa, end_msoa, SUM(avg_daily_trips) daily_trips FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE start_date='2023-03-27' GROUP BY start_msoa, end_msoa"
    return(submit_sql_query(query))


#For these queries, we include outbound and non-home based trips, excluding return trips. This then amounts to travel to the services at the destination.
def get_data_for_all_weekdays():
    query = '''
    SELECT start_msoa, end_msoa, SUM(avg_daily_trips) daily_trips
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE (DATEPART(dw, start_date) = 1)
    AND (journey_purpose_direction NOT IN ('IB_HBW', 'IB_HBO'))
    GROUP BY start_msoa, end_msoa;
    '''
    return(submit_sql_query(query))

def get_data_for_all_weekends():
    query = '''
    SELECT start_msoa, end_msoa, SUM(avg_daily_trips) daily_trips
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE (DATEPART(dw, start_date) = 6)
    AND (journey_purpose_direction NOT IN ('IB_HBW', 'IB_HBO'))
    GROUP BY start_msoa, end_msoa;
    '''
    return(submit_sql_query(query))

def get_data_for_all_weekdays_tagged_commute():
    query = '''
    SELECT start_msoa, end_msoa, SUM(avg_daily_trips) daily_trips
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE (DATEPART(dw, start_date) = 1)
    AND (journey_purpose_direction NOT IN ('IB_HBW', 'IB_HBO'))
    AND (journey_purpose = 'Commute')
    GROUP BY start_msoa, end_msoa;
    '''
    return(submit_sql_query(query))

#Morning commute window defaults to between 6 and 10?
def get_data_for_all_weekdays_morning_commute_time(window_start=6, window_end=10):
    query = f'''
    SELECT start_msoa, end_msoa, SUM(avg_daily_trips) daily_trips
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE (DATEPART(dw, start_date) = 1)
    AND (journey_purpose_direction NOT IN ('IB_HBW', 'IB_HBO'))
    AND (hour_part > {window_start-1}) AND (hour_part < {window_end})
    GROUP BY start_msoa, end_msoa;
    '''
    return(submit_sql_query(query))

def get_data_for_all_weekdays_split_time_purpose():
    query = f'''
    SELECT start_msoa, end_msoa, SUM(avg_daily_trips) daily_trips, journey_purpose_direction, hour_part
    FROM Process.tb_O2MOTION_ODMODE_Weekly
    WHERE (DATEPART(dw, start_date) = 1)
    GROUP BY start_msoa, end_msoa, journey_purpose_direction, hour_part;
    '''
    return(submit_sql_query(query))



def get_data_for_weekends():
    #Also takes 4 or 5 mins, which is a bit long, but okay.
    query = "SELECT start_msoa, end_msoa, SUM(avg_daily_trips) FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE start_date='2023-03-18' GROUP BY start_msoa, end_msoa"
    return(submit_sql_query(query))


def get_destinations_from_big_df(msoa_code, big_df):
    destinations = big_df[big_df['start_msoa']==msoa_code]
    return(destinations)

def get_origins_from_big_df(msoa_code, big_df):
    origins = big_df[big_df['end_msoa']==msoa_code]
    return(origins)