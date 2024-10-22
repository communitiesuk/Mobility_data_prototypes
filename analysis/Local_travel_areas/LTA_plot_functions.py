# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 11:18:14 2023

@author: evan.baker
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot
from sklearn.neighbors import KernelDensity


#scatter plot for economic integration
def economic_integration_scatter_matplotlib_defunct(towns_data, towns, y_axis_var = "job_ratio", y_axis_lab = "Jobs per population in BUA", title = "Economic integration for sample towns"):
    towns_data.loc[towns_data.travel_to_bigger_area==0, 'travel_to_bigger_area'] = 0.5 #Add a small shift as we're plotting on a log scale so need to move away from exact zeroes.

    smaller = towns_data[towns_data.Town.isin(towns)]
    ax = smaller.plot.scatter(x='travel_to_bigger_area', y=y_axis_var)
    ax.set_xscale('log')
    ax.vlines(5, min(smaller[y_axis_var].min(), towns_data[y_axis_var].mean()), max(smaller[y_axis_var].max(), towns_data[y_axis_var].mean()), label="5%")
    ax.hlines(towns_data[y_axis_var].mean(), smaller.travel_to_bigger_area.min(), max(smaller.travel_to_bigger_area.max(),5), label="UK Average", color='red')
    ax.legend()
    smaller[['travel_to_bigger_area', y_axis_var,'Town']].apply(lambda row: ax.text(*row),axis=1);
    ax.set_xlabel("% of LTA travel to larger BUAs")
    ax.set_ylabel(y_axis_lab)
    ax.set_title(title)
    return(0)


def line_breaker(list_of_places): 
    """
    Given a long list of LAs
    add line breaks (<br>) after every 6th area
    """
    list_of_places_line_break = ''.join([i+';  <br>' if num%6==5 else i+';  ' for num,i in enumerate(list_of_places)]).strip(';  <br>').strip(';  ') 
    return ''.join(['<br>', list_of_places_line_break])



def economic_integration_scatter(towns_data, towns, y_axis_var = "job_ratio", y_axis_lab = "Jobs per population in BUA", title = "Economic integration for sample towns", save_loc = "", docking_towns = False, kde_perc = 1, independence_threshold=5, USE_MEDIAN=True, HOME_POP=True):
    towns_data_plot = towns_data.copy()
    towns_data_plot.loc[towns_data_plot.travel_to_bigger_area==0, 'travel_to_bigger_area'] = 0.5 #Add a small shift as we're plotting on a log scale so need to move away from exact zeroes.
    
    #We colour scatter plotm points based on either the town population (default behaviour), or the destination population
    if HOME_POP:
        towns_data_plot["pop_bands"] = pd.cut(towns_data_plot.Population,[float("-inf"),100e3, 200e3, float("inf")],labels=["0-100k","100-200k","200k+"]).astype(str)
    else:
        towns_data_plot["pop_bands"] = pd.cut(towns_data_plot.primary_bigger_BUA_pop,[float("-inf"),100000, 600000, float("inf")],labels=["0-100k","100-600k","600k+"]).astype(str)

    smaller = towns_data_plot[towns_data_plot.Town.isin(towns)].reset_index(drop = True)
    
    #use kde to find outliers (to label)
    smaller_xy = smaller[['travel_to_bigger_area', y_axis_var]].dropna()
    smaller_xy = (smaller_xy-smaller_xy.mean())/smaller_xy.std()
    kde = KernelDensity(kernel='tophat').fit(smaller_xy)
    yvals = kde.score_samples(smaller_xy)  # yvals are logs of pdf-values
    yvals[np.isinf(yvals)] = np.nan # some values are -inf, set them to nan
    yval_thresh =  np.percentile(yvals, kde_perc)
    if kde_perc == 0: #in the case of 0% of points, make sure we really do exclude everyone
        yval_thresh -= 100
    outlier_inds = smaller_xy.index[np.where(yvals <= yval_thresh)[0]]
    non_outlier_inds = smaller_xy.index[np.where(yvals > yval_thresh)[0]]
    
    smaller["Town_label"]= smaller["Town"].copy()
    smaller.loc[smaller.index[non_outlier_inds], "Town_label"]= "" #remove town forthose we dont want to annotate
    
    if docking_towns == False:
        docking_towns_var = []
    else:
        docking_towns_var = ["list_of_docking_towns"]
        smaller["list_of_docking_towns"] =  [line_breaker(sublist) for sublist in smaller["list_of_docking_towns"]] #add line breaks
        smaller.list_of_docking_towns = smaller.list_of_docking_towns.apply(lambda y: ["None"] if y == [] else y)
        
    if HOME_POP:
        scatter_colour_legend = "Population size of BUA"
    else:
        scatter_colour_legend = "Population size of<br> primary destination BUA"
        
    fig = px.scatter(smaller, x='travel_to_bigger_area', y=y_axis_var, text="Town_label", color = "pop_bands", 
                     color_discrete_map={'0-100k': '#12436D', '100-600k': '#28A197', '600k+': '#801650'},
                     custom_data=['primary_bigger_BUA', 'primary_bigger_BUA_perc', 'primary_bigger_BUA_pop', "Town"] + docking_towns_var,
                 labels={
                     'travel_to_bigger_area': "% of LTA travel to larger BUAs",
                     y_axis_var: y_axis_lab,
                     "pop_bands": scatter_colour_legend
                 },
                 category_orders={"pop_bands": np.sort(smaller["pop_bands"].unique())},
                title=title
                )
    
    fig.update_traces(
                textfont=dict(
                    size=10,
                    ))
    
    def improve_text_position(x):
        """ it is more efficient if the x values are sorted """
        # fix indentation 
        positions = ['top right', 'middle right', 'bottom right']  # you can add more: left center ...
        return [positions[i % len(positions)] for i in range(len(x))]

    fig.update_traces(textposition=improve_text_position(smaller['travel_to_bigger_area']))

    #fig.update_xaxes(type="log")
    if USE_MEDIAN:
        fig.add_trace(
            go.Scatter(x = [independence_threshold, independence_threshold], y = [min(smaller[y_axis_var].min(), towns_data_plot[y_axis_var].median()), max(smaller[y_axis_var].max(), towns_data_plot[y_axis_var].median())], 
                    mode='lines', line=dict(color='blue', width=2), name=str(independence_threshold)+"%")
            )
        fig.add_trace(
            go.Scatter(x = [min(smaller.travel_to_bigger_area.min(), independence_threshold), max(smaller.travel_to_bigger_area.max(),independence_threshold)], y = [towns_data_plot[y_axis_var].median(), towns_data_plot[y_axis_var].median()], 
                    mode='lines', line=dict(color='red', width=2), name="UK Median")
            )
        
    else:
        fig.add_trace(
            go.Scatter(x = [independence_threshold, independence_threshold], y = [min(smaller[y_axis_var].min(), towns_data_plot[y_axis_var].mean()), max(smaller[y_axis_var].max(), towns_data_plot[y_axis_var].mean())], 
                    mode='lines', line=dict(color='blue', width=2), name=str(independence_threshold)+"%")
            )
        fig.add_trace(
            go.Scatter(x = [min(smaller.travel_to_bigger_area.min(), independence_threshold), max(smaller.travel_to_bigger_area.max(),independence_threshold)], y = [towns_data_plot[y_axis_var].mean(), towns_data_plot[y_axis_var].mean()], 
                    mode='lines', line=dict(color='red', width=2), name="UK Average")
            )
    fig.update_traces(marker=dict(size=15))
    
    hover_text = [
        "Name: %{customdata[3]}",
        "% of LTA travel to larger BUAs: %{x:,.1f}",
        y_axis_lab +": %{y:,.1f}",
        "Primary bigger BUA: %{customdata[0]}",
        "% travel to primary bigger BUA: %{customdata[1]:,.1f}",
        "Population of primary bigger BUA : %{customdata[2]}",
    ]
    if docking_towns:
        hover_text = hover_text+  ["Towns that integrate into this BUA (or integrate into an integrated town) : %{customdata[4]}"]
        
    fig.update_traces(
        hovertemplate="<br>".join(hover_text)
    )

    
    if save_loc != "":
        plot(fig, filename = save_loc + '.html', auto_open=False)
        fig.write_image(save_loc + '.png', scale = 2, width=1600, height=900) 
    else:
        plot(fig, auto_open=True)

