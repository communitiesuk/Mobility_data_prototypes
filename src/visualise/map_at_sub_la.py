# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 10:29:31 2023

@author: gordon.donald
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import Normalize
import numpy as np
import matplotlib.patheffects as pe
from matplotlib.colors import ListedColormap
from osdatahub import NGD, Extent
from typing import List
from src.transform.ons_code_helpers import get_code_column

#use same colour scheme as lup packs
from src.utils.constants import diverging_colour_scale, map_lu_partnership_colour_scale, map_lu_partnership_colour_scale_unordered
map_lu_partnership_colour_scale_rev= map_lu_partnership_colour_scale.copy()
map_lu_partnership_colour_scale_rev.reverse()


def get_sub_la_areas_via_join(big_area, small_area, big_area_id):
    small_area = small_area.to_crs(big_area.crs)
    code_col = get_code_column(big_area)
    our_la = big_area[big_area[code_col]== big_area_id]    
    small_area_within = gpd.overlay(our_la, small_area, how='intersection')
    return(small_area_within)

#Remove excess columns from e.g., OA-LSOA-MSOA-LAD lookups
def simplify_lookup(lookup, input_col, output_col):
    simpler = lookup[[output_col, input_col]].drop_duplicates()
    return(simpler)


def get_sub_la_areas_via_lookup(lookup, big_area_id):
    #Assume for now that col 0 has the big area, col 1 has the small areas
    #So assumeing len col1 is larger than len_col0
    len_col0 = len(lookup.iloc[:,0].unique())
    len_col1 = len(lookup.iloc[:,1].unique())
    
    #But reverse the logic if needed.
    if len_col1 < len_col0:
        small_ids = lookup[lookup.iloc[:,1] == big_area_id].iloc[:,0]
    else:   
        small_ids = lookup[lookup.iloc[:,0] == big_area_id].iloc[:,1]
    
    
    
    return(small_ids)
    
def plot_at_small_area(dataset, data_column, big_area, small_areas, big_area_id,
                          small_area_lu_col, small_area_data_col, plot_title="", suptitle="",
                          source="", bbox_anchor=(1,0.5), loc='center left', REVERSE_SCALE=False):
    ''' 
    Plot data for small areas (such as postal sectors) within a larger area.
    NOTE: We will sum values within small areas -- but if you want any fancy stuff with ratios or means or whatever,
    preprocess that first and use a processed dataset with one row per sector!
    
    This function generates a plot of data values for specified small areas (such as postal sectors)
    within a given larger area. It aggregates the data by small areas and displays the data
    using a colored map.
    
    Args:
        dataset (pd.DataFrame): The input dataset containing relevant data.
        data_column (str): The column name for the data to be plotted.
        big_area (gpd.GeoDataFrame): The larger area geometry to be plotted.
        small_areas (gpd.GeoDataFrame): The geometry of the postal sectors (can be another small geometry).
        big_area_id (str): The column name in `big_area` containing area identifiers.
        small_area_lu_col (str): The column name in `small_areas` containing small area identifiers.
        small_area_data_col (str): The column name in `dataset` corresponding to small area data values.
        plot_title (str): Title for the generated plot.

    Returns:
        matplotlib.axes._subplots.AxesSubplot: The generated plot.
    '''
    sectors = get_sub_la_areas_via_join(big_area, small_areas, big_area_id)
    #Strip whitespace from small areas (useful for postal sectors which sometimes have whitespace and sometimes not).
    sectors[small_area_lu_col] = sectors[small_area_lu_col].str.replace(" ","")
    #Also strip whitespace for dataset col just in case.
    dataset[small_area_data_col] = dataset[small_area_data_col].str.replace(" ","")
    
    subset = dataset[dataset[small_area_data_col].isin(list(sectors[small_area_lu_col]))]
    data_to_plot = subset.groupby(small_area_data_col).sum()
    
    if len(data_to_plot) < len(subset):
        #Then the groupby and sum has done some summing of rows -- could be OK, but print warning to user
        print("WARNING: We have aggregated rows in the dataset in the same small area. \n Hope that's what you expected to happen, but if not have a look at the input data set.")
    
    data_to_plot = sectors.merge(data_to_plot, left_on = small_area_lu_col, right_on = small_area_data_col)
    our_plot = plot_map(data_to_plot, data_column, plot_title=plot_title, suptitle=suptitle, 
                            source=source, bbox_anchor=bbox_anchor, loc=loc, REVERSE_SCALE=REVERSE_SCALE)
    return(our_plot)

def plot_map(data_to_plot: gpd.GeoDataFrame, 
             data_column: str, 
             plot_title: str = "", 
             suptitle: str = "", 
             source: str = "", 
             bbox_anchor: tuple = (1, 0.5), 
             loc: str = 'center left', 
             line_width: float = 0.4, 
             colour_scheme: str = 'equalinterval', 
             REVERSE_SCALE: bool = False, 
             cat_data: bool = False, 
             ordered_categories: list = None,
             colour_map: list = None) -> plt.Axes:
    """
    Create a thematic map plot.

    Args:
        data_to_plot (gpd.GeoDataFrame): The GeoDataFrame containing the data to be plotted.
        data_column (str): The column in the GeoDataFrame to use for coloring the map.
        plot_title (str, optional): Title for the plot. Defaults to an empty string.
        suptitle (str, optional): Super title for the plot. Defaults to an empty string.
        source (str, optional): Data source information. Defaults to an empty string.
        bbox_anchor (tuple, optional): Bounding box anchor for the legend. Defaults to (1, 0.5).
        loc (str, optional): Location of the legend. Defaults to 'center left'.
        line_width (float, optional): Width of lines in the map. Defaults to 0.4.
        colour_scheme (str, optional): Color scheme for the map. Defaults to 'equalinterval'.
        REVERSE_SCALE (bool, optional): Reverse the color scale. Defaults to False.
        cat_data (bool, optional): Whether the data is categorical. Defaults to False.
        ordered_categories (list, optional): Ordered categories for categorical data. Defaults to None.
        colour_map (list, optional): List of colours for map. Defaults to None.

    Returns:
        plt.Axes: The map plot.

    """
    fig, ax = plt.subplots(figsize=(10, 10))

    if not colour_map:
        cmap = ListedColormap(map_lu_partnership_colour_scale)
    else:
        cmap = ListedColormap(colour_map)
    
    if REVERSE_SCALE:
        cmap = ListedColormap(map_lu_partnership_colour_scale_rev)
    
    our_plot = data_to_plot.plot(
        column=data_column,
        edgecolor='k',
        linewidth=line_width,
        cmap=cmap,
        legend=True,
        scheme=colour_scheme,
        categorical=cat_data,
        categories=ordered_categories,
        k=5,
        legend_kwds={'bbox_to_anchor': bbox_anchor, 'loc': loc, 'markerscale': 2, 'title': plot_title, 'title_fontsize': 16, 'labelspacing': 0.8, 'edgecolor': 'white'},
        missing_kwds= {'color': 'lightgrey', 'alpha': 0.5},
        ax=ax
    )
    
    plt.axis('off')
    fig.suptitle(suptitle, fontsize=24)
    
    # Get the legend object
    legend = ax.get_legend()
    legend._legend_box.align = "left"
    fig.text(0.2, 0.14, source, fontsize=13, backgroundcolor=(1, 1, 1, 0.6))
    
    return our_plot


def get_square_bounds_coords(area_bounds: pd.DataFrame) -> tuple:
    """
    Calculate the coordinates of a square bounding box within a given area.

    This function takes a DataFrame `area_bounds` representing the bounding box of an area
    and returns the coordinates of a square bounding box within that area. The square bounding box is
    determined by finding the center of the given area and then creating a square bounding box based
    on the axis with the largest span.
    
    Parameters:
    area_bounds (pandas.DataFrame): A DataFrame containing the bounding box coordinates
        with columns 'minx', 'maxx', 'miny', and 'maxy'. Created using the .bounds attribute
        of a GeoPandas DataFrame. E.g. region_bounds = region_gdf.bound

    Returns:
    tuple: A tuple (x_min, y_min, x_max, y_max) representing the coordinates of the square bounding box.
    x_min (float): The minimum x-coordinate of the square.
    y_min (float): The minimum y-coordinate of the square.
    x_max (float): The maximum x-coordinate of the square.
    y_max (float): The maximum y-coordinate of the square.
    """
    area_center_x = (area_bounds.iloc[0]["maxx"] + area_bounds.iloc[0]["minx"]) / 2
    area_center_y = (area_bounds.iloc[0]["maxy"] + area_bounds.iloc[0]["miny"]) / 2
    x_min, x_max = area_bounds.iloc[0]["minx"], area_bounds.iloc[0]["maxx"]
    y_min, y_max = area_bounds.iloc[0]["miny"], area_bounds.iloc[0]["maxy"]
    area_x_span = x_max - x_min
    area_y_span = y_max - y_min
    if area_x_span > area_y_span:
        y_min = area_center_y - area_x_span / 2
        y_max = area_center_y + area_x_span / 2
    else: 
        x_min = area_center_x - area_y_span / 2
        x_max = area_center_x + area_y_span / 2
    return x_min, y_min, x_max, y_max


def plot_region_map(data_to_plot: gpd.GeoDataFrame, region_name: str, regions_gdf: gpd.GeoDataFrame,
                    data_column: str, plot_title: str = "", suptitle: str = "", source: str = "",
                    bbox_anchor: tuple = (0.70, 0.95), loc: str = 'center left', line_width: float = 0.4,
                    colour_scheme: str = 'equalinterval', REVERSE_SCALE: bool = False,
                    cat_data: bool = False, ordered_categories: list = None, 
                    place_names: gpd.GeoDataFrame = None,
                    colour_map: list = None) -> plt.Figure:
    """
    Plot a regional map with data.

    Args:
        data_to_plot (GeoDataFrame): GeoDataFrame containing data to plot.
        region_name (str): Name of the region to plot.
        regions_gdf (GeoDataFrame): GeoDataFrame containing region geometries.
        data_column (str): The column in data_to_plot to use for coloring the map.
        plot_title (str, optional): Title for the map. Defaults to an empty string.
        suptitle (str, optional): Supertitle for the map. Defaults to an empty string.
        source (str, optional): Source information for the map. Defaults to an empty string.
        bbox_anchor (tuple, optional): Bounding box anchor. Defaults to (0.70, 0.95).
        loc (str, optional): Location of the legend. Defaults to 'center left'.
        line_width (float, optional): Line width for the map. Defaults to 0.4.
        colour_scheme (str, optional): Color scheme for the map. Defaults to 'equalinterval'.
        REVERSE_SCALE (bool, optional): Reverse the color scale. Defaults to False.
        cat_data (bool, optional): Categorize the data. Defaults to False.
        ordered_categories (list, optional): Ordered categories for the legend. Defaults to None.
        place_names(GeoDataFrame, optional): GeoDataFrame containing place names to plot.
        colour_map (list, optional): List of colours for map. Defaults to None.

    Returns:
        plt.Figure: The generated plot.

    Example usage:
    plot_region_map(map_data, "North East", regions, 'seasonal_flag',
                   plot_title="Seasonal destination MSOAs",
                   suptitle="North East MSOAs with high seasonal trips",
                   source="Source: O2 Motion",
                   line_width=0,
                   colour_scheme=None,
                   cat_data=True,
                   ordered_categories=["Non-seasonal", "Seasonal", "Highly seasonal"]
                   place_names=names_gdf)
    """
    plot = plot_map(data_to_plot, data_column, plot_title, suptitle, source, bbox_anchor, loc,
                    line_width, colour_scheme, REVERSE_SCALE, cat_data, ordered_categories, colour_map)

    ax = plt.gca()

    region_gdf = regions_gdf.loc[regions_gdf["ITL121NM"] == region_name]
    region_gdf.boundary.plot(
        edgecolor = 'grey', 
        linewidth = 1,
        linestyle='--',
        ax=ax
    )

    # Set regional bounding box
    region_bounds = region_gdf.bounds
    x_min, y_min, x_max, y_max = get_square_bounds_coords(area_bounds=region_bounds)
    ax.set_xlim(x_min - 1000, x_max + 1000)
    ax.set_ylim(y_min - 1000, y_max + 1000)

    if place_names is not None:
        for x, y, label in zip(place_names.geometry.x, place_names.geometry.y, place_names.name1_text):
            ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points",
                        path_effects=[pe.withStroke(linewidth=2, foreground="white")])

    return plot


def plot_map_manual_breakpoints(data_to_plot, data_column, plot_title="", suptitle="", source="", bbox_anchor=(1,0.5), loc='center left', line_width=0.4, colour_scheme='equalinterval',
             vmin = None, vmax = None, breakpoints = [0,1], colors = map_lu_partnership_colour_scale):

    labels = []
    for i in range(len(breakpoints)+1):
        if i == 0:
            labels.append("< " + str(breakpoints[0]))
        elif i < len(breakpoints):
            labels.append(str(breakpoints[i-1]) + " - " + str(breakpoints[i]))
        else:
            labels.append(str(breakpoints[len(breakpoints)-1]) + " <")
    bins = breakpoints + [np.inf]
    fig, ax = plt.subplots(figsize=(10, 10))
    our_plot = data_to_plot.plot(
    column=data_column,
    edgecolor = 'k', 
    linewidth = line_width,
    cmap = ListedColormap(colors),
    legend =True,
    scheme=colour_scheme,
    classification_kwds={'bins':bins}, 
    norm=Normalize(0, len(map_lu_partnership_colour_scale)),
    k=5,
    vmin = vmin,
    vmax = vmax,
    legend_kwds={'labels': labels, 'bbox_to_anchor':bbox_anchor, 'loc':loc, 'markerscale':2, 'title': plot_title, 'title_fontsize':16, 'labelspacing': 0.8, 'edgecolor': 'white'},
    missing_kwds= dict(color = "lightgrey", alpha=0.5,),
    ax=ax
    )
    plt.axis('off')
    fig.suptitle(suptitle, fontsize=24)
    # Get the legend object
    legend = ax.get_legend()
    legend._legend_box.align = "left"
    fig.text(0.2,0.14, source, fontsize=13);
    return(our_plot)


def get_location_name_data(api_key: str, towns_to_add: List[str], cities_to_remove: List[str], regions: str) -> gpd.GeoDataFrame:
    """
    Filter location name data from OS Names based on the towns_to_add and cities_to_remove list provided

    Args:
        api_key (str): Your API key.
        collection (str): The name of the collection to query.
        cities_to_add (List[str]): A list of town names to include.
        towns_to_remove (List[str]): A list of city names to exclude.
        regions (str): The regions data.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing the filtered data.
    """
    # OS API to get place names
    collection = "gnm-fts-namedpoint"
    namedpoint = NGD(api_key, collection)

    # Make the query and contact the API
    features = namedpoint.query(max_results=100000, cql_filter="description IN ('City', 'Town')")

    names_gdf = gpd.GeoDataFrame.from_features(features, crs="WGS84")
    names_gdf.to_crs(crs=regions.crs, inplace=True)

    # Filter the data
    filtered_gdf = names_gdf.loc[(names_gdf["name1_text"].isin(towns_to_add) | (names_gdf["description"] == "City")) & ~(names_gdf["name1_text"].isin(cities_to_remove))]

    return filtered_gdf