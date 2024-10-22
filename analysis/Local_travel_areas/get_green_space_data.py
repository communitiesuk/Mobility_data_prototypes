import geopandas as gpd
import pandas as pd

def read_os_green_space_data():
    os_green_space = gpd.read_file(filename='Q:/GI_Data/Ordnance Survey/Greenspace/opgrsp_gb_api.gpkg',
                      # GPKG layer
                      layer='greenspace_site') 
    return os_green_space


def get_gb_oa_pop_weighted_centroids():
    # pop weighted OA centroids E/W
    ew_oa_centroids = gpd.read_file(filename="Q:/SDU/Mobility/Data/Boundaries/oa_pop_centroids_2011/OA_2011_EW_PWC.shp")
    # Scotland
    scotland_oa_centroids = gpd.read_file(filename="Q:/SDU/Mobility/Data/Boundaries/SG_oa_pw_centroids_2011/OutputArea2011_PWC.shp")
    # rename to match E/W
    scotland_oa_centroids = scotland_oa_centroids[["code", "OBJECTID", "geometry"]]
    scotland_oa_centroids.rename(columns={"code": "OA11CD", "OBJECTID": "GlobalID"}, inplace=True)
    # combine geographies
    oa_centroids = pd.concat([ew_oa_centroids, scotland_oa_centroids])
    return oa_centroids

def get_gb_oa_to_msoa_lookup():
    # england and wales
    ew_oa_msoa_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/Output_Area_to_Lower_layer_Super_Output_Area_to_Middle_layer_Super_Output_Area_to_Local_Authority_District_(December_2011)_Lookup_in_England_and_Wales.csv")
    ew_oa_msoa_lookup = ew_oa_msoa_lookup[["OA11CD", "MSOA11CD", "MSOA11NM", "LAD11CD",	"LAD11NM"]]
    # scotland msoas
    scotland_oa_msoa_lookup = pd.read_excel("Q:/SDU/Mobility/Data/Lookups/OA_DZ_IZ_2011.xlsx")  
    scotland_oa_msoa_lookup.rename(columns={"OutputArea2011Code": "OA11CD", "IntermediateZone2011Code": "MSOA11CD"}, inplace=True)
    scotland_oa_msoa_lookup[["MSOA11NM", "LAD11CD", "LAD11NM"]] = "Scotland"
    scotland_oa_msoa_lookup = scotland_oa_msoa_lookup[["OA11CD", "MSOA11CD", "MSOA11NM", "LAD11CD",	"LAD11NM"]]
    # combine
    oa_msoa_lookup = pd.concat([ew_oa_msoa_lookup, scotland_oa_msoa_lookup])
    return oa_msoa_lookup

def get_gb_msoa_boundaries():
    # get combined msoa boundaries
    scotland_msoa_boundaries = gpd.read_file("Q:/SDU/Mobility/Data/Boundaries/SG_IntermediateZoneBdry_2011/SG_IntermediateZone_Bdry_2011.shp")
    scotland_msoa_boundaries.rename(columns={"InterZone": "MSOA11CD", "Name": "MSOA11NM"}, inplace=True)
    scotland_msoa_boundaries = scotland_msoa_boundaries[["MSOA11CD", "MSOA11NM", "geometry"]]
    ew_msoa_boundaries = gpd.read_file("Q:/SDU/Mobility/Data/Boundaries/MSOA_Dec_2011_Boundaries_Generalised_Clipped_BGC_EW_V3_2022_-8564488481746373263/MSOA_2011_EW_BGC_V3.shp")[["MSOA11CD", "MSOA11NM", "geometry"]]
    msoa_boundaries = pd.concat([ew_msoa_boundaries, scotland_msoa_boundaries])
    return msoa_boundaries


def get_oa_green_space_distance(oa_centroids, os_green_space):
    # Spatially join the rows within the oa_centroids and the os_green_space data where pairs of geometries are within 2000m
    oa_green_space_distance = gpd.sjoin_nearest(left_df=oa_centroids,
                                right_df=os_green_space, 
                                how='left', 
                                max_distance=2000, # Maximum search radius
                                distance_col='distance')
    # remove duplicates
    oa_green_space_distance.drop_duplicates(subset="OA11CD", inplace=True)
    return oa_green_space_distance


def calc_greenspace_area_by_msoa(msoa_boundaries, os_green_space):
    # calc area of greenspace by MSOA
    greenspace_by_msoa = msoa_boundaries.overlay(os_green_space, how='intersection')
    greenspace_by_msoa['area'] = greenspace_by_msoa['geometry'].area
    return greenspace_by_msoa


def aggregate_and_output_msoa_summary(greenspace_by_msoa):
    msoa_greenspace_summary = greenspace_by_msoa.groupby(["MSOA11CD", "MSOA11NM"]).agg({'distance': ['mean', 'median', 'min', 'max', 'std'], 'area': ['count', 'sum']}).reset_index() 
    msoa_greenspace_summary.to_csv("Q:/SDU/Mobility/Data/Processed/Processed_Mobility/greenspace_by_msoa.csv", index=False)


if __name__ == '__main__':
    os_green_space = read_os_green_space_data()
    oa_centroids = get_gb_oa_pop_weighted_centroids()
    oa_msoa_lookup = get_gb_oa_to_msoa_lookup()
    msoa_boundaries = get_gb_msoa_boundaries()
    oa_green_space_distance = get_oa_green_space_distance(oa_centroids, os_green_space)

    # join green space data with lookup
    oa_green_space_distance = pd.merge(oa_green_space_distance[["OA11CD", "distance"]], 
                                    oa_msoa_lookup[["OA11CD", "MSOA11CD", "MSOA11NM", "LAD11CD", "LAD11NM"]],
                                    on="OA11CD")

    # get msoa greenspace area
    greenspace_area_by_msoa = calc_greenspace_area_by_msoa(msoa_boundaries, os_green_space)
    # combine with shortest distance data
    greenspace_by_msoa = pd.merge(left=oa_green_space_distance, right=greenspace_area_by_msoa[['MSOA11CD', 'area']], on='MSOA11CD', how="left")
    # aggregate and output
    aggregate_and_output_msoa_summary(greenspace_by_msoa)


