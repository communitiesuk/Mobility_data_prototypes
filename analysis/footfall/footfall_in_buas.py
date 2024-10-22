import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pyodbc

from analysis.Local_travel_areas.LTA_queries import *
from analysis.Local_travel_areas.LTA_functions import *
from analysis.msoa_jobs_functions import *
from analysis.utils import *

def read_bua_data() -> pd.DataFrame:
    """
    Reads Built-Up Areas (BUAs) and BUA population data.

    Returns:
        pd.DataFrame: DataFrame containing BUAs and relevant population data.
    """
    buas = get_BUAs()
    bua_pop = get_BUA_pop()
    buas = buas.merge(bua_pop, on='BUA22NM')
    
    # Population threshold for BUAs
    pop_threshold = 10e3
    buas_of_interest = buas[buas.Population > pop_threshold]
    
    return buas_of_interest


def get_msoa_average_footfall(cnxn) -> pd.DataFrame:
    """
    Connects to the database and retrieves MSOA average footfall data.

    Args:
        cnxn (Any): Database connection.

    Returns:
        pd.DataFrame: MSOA average footfall data.
    """
    query = '''
        SELECT start_date, end_msoa, SUM(avg_daily_trips) daily_trips
        FROM Process.tb_O2MOTION_ODMODE_Weekly
        WHERE journey_purpose_direction = 'OB_HBO' OR journey_purpose_direction = 'NHBO'
        GROUP BY start_date, end_msoa;
        '''
    msoa_destination_trips = pd.read_sql_query(query, cnxn) 
    # get journey start date and day number
    msoa_destination_trips['start_date'] = pd.to_datetime(msoa_destination_trips['start_date'])
    msoa_destination_trips['weekday_weekend'] = msoa_destination_trips['start_date'].dt.dayofweek
    # calculate weighted daily journeys over the full year
    msoa_destination_trips.loc[msoa_destination_trips['weekday_weekend'] == 5, 'weekday_weekend'] = 4 # 2 weekend days, but multiply by 2 for two grouped weekends.
    msoa_destination_trips.loc[msoa_destination_trips['weekday_weekend'] == 0, 'weekday_weekend'] = 5 # And 5 weekdays
    # weighted sum of total journeys
    msoa_destination_trips['journeys'] = msoa_destination_trips['weekday_weekend'] * msoa_destination_trips['daily_trips']
    # group into destination MSOA trips
    msoa_total_footfall = msoa_destination_trips[['end_msoa', 'journeys']].groupby('end_msoa').sum().reset_index()
    # calc daily average
    msoa_total_footfall.journeys /= 365
    
    return msoa_total_footfall


def filter_and_merge_footfall_data(msoa_total_footfall: pd.DataFrame, our_msoas: pd.DataFrame) -> pd.DataFrame:
    """
    Filters and merges footfall data with BUA geography names/codes.

    Args:
        msoa_total_footfall (pd.DataFrame): MSOA total footfall data.
        our_msoas (pd.DataFrame): Our selected MSOAs.

    Returns:
        pd.DataFrame: Filtered and merged footfall data.
    """
    bua_destination = msoa_total_footfall[msoa_total_footfall.end_msoa.isin(our_msoas['msoa11cd'])]
    bua_destination = pd.merge(left=bua_destination, right=our_msoas[["BUA22NM", "BUA22CD", "msoa11cd"]], left_on="end_msoa", right_on="msoa11cd")
    return bua_destination


def calculate_total_footfall(bua_destination: pd.DataFrame, bua_pop: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates total footfall for each BUA and attaches LAD code, name, and BUA pop.

    Args:
        bua_destination (pd.DataFrame): Filtered and merged footfall data.
        bua_pop (pd.DataFrame): BUA population data.

    Returns:
        pd.DataFrame: DataFrame with total footfall for each BUA.
    """
    bua_totals = bua_destination.groupby(['BUA22NM', 'BUA22CD']).sum().reset_index()
    bua_totals['journeys'] = bua_totals['journeys'].round(1)
    
    bua_totals = bua_totals.merge(bua_pop, on='BUA22NM')
    return bua_totals


def calculate_overlap_and_write_csv(bua_totals: pd.DataFrame, overlap_threshold: float = 0.5) -> None:
    """
    Reads shapefiles, calculates overlap, and writes results to a CSV file.

    Args:
        bua_totals (pd.DataFrame): DataFrame with total footfall for each BUA.
        overlap_threshold (float): Proportion of BUA within lad threshold.

    Returns:
        None
    """
    bua_shp = gpd.read_file("Q:/GI_Data/Boundaries/BUAs/BUA_2022_GB.shp").to_crs(epsg=27700)
    bua_shp = bua_shp[bua_shp["BUA22CD"].isin(bua_totals["BUA22CD"])]
    bua_shp.rename(columns={"area": "bua_area"}, inplace=True)
    lad_shp = gpd.read_file("Q:/GI_Data/Boundaries/Districts/2022/Local_Authority_Districts_(December_2022)_Boundaries_UK_BGC/LAD_DEC_2022_UK_BGC.shp").to_crs(epsg=27700)
    # calc overlap
    res_intersection = bua_shp.overlay(lad_shp, how='intersection')
    res_intersection.loc[:, "perc_bua_in_lad"] = round(res_intersection.area / res_intersection["bua_area"], 3)
    
    # filter by threshold of overlap and ouput
    res_intersection = res_intersection[res_intersection["perc_bua_in_lad"] >= overlap_threshold]

    output_df = pd.DataFrame(res_intersection[["BUA22CD", "BUA22NM", "LAD22CD", "LAD22NM", "perc_bua_in_lad"]])
    output_df = pd.merge(left=output_df, right=bua_totals[["BUA22CD", "journeys"]], on="BUA22CD")
    output_df.to_csv("Q:/SDU/Mobility/Data/Processed/Processed_Mobility/footfall_in_buas.csv", index=False)
    return


if __name__ == "__main__":
    buas_of_interest = read_bua_data()
    msoa_bua_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Processed/MSOA_to_BUA_lookup.csv")

    our_buas = buas_of_interest['BUA22NM']
    our_msoas = msoa_bua_lookup[msoa_bua_lookup.BUA22NM.isin(our_buas)][['msoa11cd', 'BUA22CD', 'BUA22NM', 'Population']]
    
    server = 'DAP-SQL01\CDS' 
    database = 'Place'

    # ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
    cnxn = pyodbc.connect(driver='{SQL Server Native Client 11.0}', host=server, database=database, trusted_connection='yes')

    msoa_total_footfall = get_msoa_average_footfall(cnxn)
    
    bua_destination = filter_and_merge_footfall_data(msoa_total_footfall, our_msoas)
    
    bua_totals = calculate_total_footfall(bua_destination, buas_of_interest)
    
    calculate_overlap_and_write_csv(bua_totals, 0.1)