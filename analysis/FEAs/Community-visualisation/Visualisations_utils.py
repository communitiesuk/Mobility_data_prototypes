
import pandas as pd
import geopandas as gpd
import folium
import ast
import topojson as tp


def get_all_small_areas_coarse_resolution():
    #introduced as a temporary substitute of create_all_small_areas_coarse_resolution()
    readfile=gpd.read_file(r"Q:\SDU\Mobility\Outputs\NetworkAnalysis\QGIS\AllSmallareasCoarseResolution150.gpkg")
    return readfile


def create_all_small_areas_coarse_resolution():
    """This function is useful to draw large static maps as it simplifies geometries ans makes
    map making easier reducing considerably the numeber of vertices.
    It is derived from utils get_small_areas but english+Welsh geometries are sourced from the file with 200m resolution
    while Scottish and NI ones are simplified to resolution 150 (not 150 meters) using the function simplifyPolygonsTessellation.
    The resolution for simplified geometries is set to 150 as it most closely resembles the resolution 200m of EW data.
    The England/scotland border is a lot unclean should be improved """
    import geopandas as gpd

    #EW data comes already super generalised 
    msoas11bsc = gpd.read_file(r"Q:\GI_Data\Boundaries\MSOA\2011bsc200meters\MSOA_Dec_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V3_2022_-5226720295345559296.gpkg")
    
    #OS for Scotland and NI don't provide generalised dataset so we need to simplify NI and Scot geometries
    izs=simplifyPolygonsTessellation("Q:\SDU\Mobility\Data\Boundaries\SG_IntermediateZoneBdry_2011\SG_IntermediateZone_Bdry_2011.shp",150)
    ni_soa=simplifyPolygonsTessellation("Q:\GI_Data\BoundariesNI\SOA2011_Esri_Shapefile_0\SOA2011.shp",150)
    
    #Ensure the right CRS is in place for a unified map
    ni_soa1=ni_soa.to_crs(27700)

    #Get the consistent columns
    msoas11bsc1 = msoas11bsc[['MSOA11CD', 'MSOA11NM', 'geometry']]
    izs1 = izs[['InterZone', 'Name', 'geometry']]

    #Rename columns
    #Just give Scotland and NI same col names as EW  but all of them should be lowercase to be used intercheangeably with the full resolution dataset
    #msoas11bsc2=msoas11bsc1.rename(columns={"MSOA11CD": "msoa11cd", "MSOA11NM": "msoa11nm"})
    msoas11bsc1.columns = msoas11bsc1.columns.str.lower()
    izs2=izs1.rename(columns={"InterZone": "msoa11cd", "Name": "msoa11nm"})
    ni_soa2=ni_soa1.rename(columns={"SOA_CODE": "msoa11cd", "SOA_LABEL": "msoa11nm"})

    # Needed to introduce column matching as it unexplicably created unmatching columns in some previous runs
    columns_EW = set(msoas11bsc1.columns)
    columns_SCO = set(izs2.columns)
    columns_NI = set(ni_soa2.columns)

    # Check if column names match
    if columns_EW == columns_SCO == columns_NI:
        print("Column names match. Safe to concatenate.")
        allSmallAreasCoarse = pd.concat([msoas11bsc1, izs2, ni_soa2])
        return allSmallAreasCoarse

    else:
        return ("Column names do not match. Please check the column names.")



def prepare_communities_for_small_areas_geo_merge(df_with_communities, communitiesFieldWithStringList):
    """This function prepares a dataframe where there is a list of msoas from census 2011 associated in communities using the column 'community index'"
    to be merged with a geodataframe to obtain the maps"""
    #add index
    df_with_communities_and_index=df_with_communities.reset_index(names="community index")
    #string with list of msoas to list of strings
    df_with_communities_and_index["msoa11cd"] = df_with_communities_and_index[communitiesFieldWithStringList].apply(lambda x: frozenset(ast.literal_eval(x)))
    df_with_communities_and_index=df_with_communities_and_index.drop(columns=communitiesFieldWithStringList)
    df_exploded_communities=df_with_communities_and_index.explode("msoa11cd")
    #print(df_exploded_communities.head(1))
    return df_exploded_communities


def create_regions_geopackage_from_list_msoas(csv_name_to_regionalise_in_current_directory, msoas):
   """ This function produces a gepackage file and a geodataframe where we have communities as large polygons.
   The csv should be saved in a hardcoded directory, in the same directory will be saved the geopackage.
   It takes the name of a csv file which has a column where communities are saved as list of msoas11 in the column 'members' 
   and another column 'community index' identifies which community every msoa belongs to.
   It requires that the geodataframe with geospatial data which has a column named 'msoa11cd' is picked as argument.
   REQUIRES  pandas and the geospatial layer with all msoas equivalents of the UK having a mosoa11cd column
   """
   df_data=pd.read_csv(f"Q:/SDU/Mobility/Outputs/NetworkAnalysis/{csv_name_to_regionalise_in_current_directory}.csv", index_col=0)
   df_msoas4communityStatsAndRanking=prepare_communities_for_small_areas_geo_merge(df_data, "members")
   gdf_msoas4communityStatsAndRanking=msoas.merge(df_msoas4communityStatsAndRanking , how='inner', on='msoa11cd', validate='one_to_many') 
   gdf_Regions4communityStatsAndRanking=gdf_msoas4communityStatsAndRanking.dissolve(by="community index")
   gdf_Regions4communityStatsAndRanking.to_file(f"Q:/SDU/Mobility/Outputs/NetworkAnalysis/{csv_name_to_regionalise_in_current_directory}_regionalised.gpkg", driver="GPKG")
   return gdf_Regions4communityStatsAndRanking



def create_regions_interactive_HTML_map(geofile, name4legend, target_column,html_name):
    """This function produces an interactive HTML file with a choropleth map, a lot of parameters are hardcoded.
    It is designed to run for the communities identified with our work on mobile phone data.
    It dislays a choropleth of the communities, the classification is based on "target column".
    The geofile should also have a "population" column that will be visualised hovering over communities.
    REQUIRES folium and geopandas
    """
    # For better tooltips and visualisations create two columns with Populations with thousands separators.. 
    geofile['population']=geofile['population'].apply(lambda x: "{:,}".format(x))
    geofile['population']
    #..and "travel_within" or target column with two decimals only
    geofile[target_column]=geofile[target_column].apply(lambda x: "{:.2f}".format(x))
    geofile[target_column]

    #ensure target column is still numeric
    geofile[target_column] = pd.to_numeric(geofile[target_column], errors='coerce')

    # Create a new map centered in England
    m = folium.Map(location=[51.5074, -0.1278], zoom_start=6)

    # Create a choropleth layer
    choropleth = folium.Choropleth(
        geo_data=geofile,
        data=geofile,
        columns=['id', target_column],
        key_on='feature.properties.id',
        fill_color='RdYlGn',#https://www.datanovia.com/en/blog/the-a-z-of-rcolorbrewer-palette/
        fill_opacity=0.3,
        line_opacity=0.2,
        legend_name='Self containment ratio',# could be linked with edited target_column name
        highlight=True
    ).add_to(m)

    # Add hover functionality
    style_function = lambda x: {'fillColor': '#ffffff', 'color':'#000000', 'fillOpacity': 0.3, 'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 'color':'#000000', 'fillOpacity': 0.5, 'weight': 0.1}
    NIL = folium.features.GeoJson(
        geofile,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=['population', target_column],#f"{'population':,}"
            aliases=['Community population', name4legend],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
            sticky=True
        )
    )
    m.add_child(NIL)
    m.keep_in_front(NIL)

    # Display the map
    #m
    # Save to an HTML file
    m.save(r'Q:/SDU/Mobility/Outputs/NetworkAnalysis/html_MAP/FoliumOutputs/'+html_name+'.html')


def simplifyPolygonsTessellation(geofile, mytolerance):
    """This function simplifies a geographic file.
    The mytolerance parameter is not a length in meters it represents a simplification factor with 0 means no simplification
    and 1 removing all possible vertices keeping intact the visual of topology(but very little improvement size wise)
    Tolerance 150 seems similar to UK BSC (200meters resolution) works well for very large maps and file sizes are much smaller.
    REQUIRES topojson and geopandas
    """
    import geopandas as gpd
    import topojson as tp

    #Reads the tessellation to simplify
    gdf_tessellation = gpd.read_file(geofile)# could be nice to trigger the function inputting a gdf
   
    #Simplifying
    # Prequantize reduces the precision of the input geometries before simplification it speeds up the process but could lead to some errors
    #I run one test and with preq=false it created some holes in the tessellation that should not be there so I keep prequantize=True
    topo = tp.Topology(gdf_tessellation, prequantize=True)
    simple = topo.toposimplify(mytolerance).to_gdf()

    return simple
