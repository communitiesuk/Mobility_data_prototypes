# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 14:10:14 2023

@author: evan.baker
"""

import numpy as np
import matplotlib.pyplot as plt
from src.utils.constants import map_lu_partnership_colour_scale_unordered
import scipy as sp
import seaborn as sns
from sklearn.neighbors import KernelDensity
from adjustText import adjust_text



def create_reg_scatter_plot(data, x_col, y_col, data_names, x_col_lab, y_col_lab, title, save_loc, footnote = "", perc_show_names = 1, lim_extender = 0.1):
    
    f, ax = plt.subplots(1, figsize=(8,8))
    reg_line = sns.regplot(x=x_col, 
               y=y_col, data = data, 
               scatter_kws= {"color": map_lu_partnership_colour_scale_unordered[0]},
               line_kws= {"color": map_lu_partnership_colour_scale_unordered[0]},
               ax = ax)
    # Fix axis
    ax.grid(axis='y')
    ax.set_xlabel(x_col_lab)
    ax.set_ylabel(y_col_lab)
    # Set title
    ax.set_title(title,weight="bold")
    # Remove outer box
    plt.box(False)
    
    
    #expand limits slightly
    x1,x2,y1,y2 = plt.axis()  
    xrange = x2-x1
    yrange = y2 - y1
    
    lim_extender = lim_extender #what % wider (gives txt labels some room)
    plt.axis((x1 - (lim_extender/2)*xrange,x2 + (lim_extender/2)*xrange,y1 - (lim_extender/2)*yrange,y2 + (lim_extender/2)*yrange))
    
    
    #remove NAs for correlation coefficients and pvalues
    data_no_na = data[[x_col, y_col]].dropna()
    r, p = sp.stats.pearsonr(data_no_na[x_col], data_no_na[y_col])
    ax = plt.gca()
    stats = ax.text(.7, 1, 'r={:.2f}, p={:.2g}'.format(r, p),
            transform=ax.transAxes)
        
    
    #add annotations for outliers
    #yoink https://stackoverflow.com/questions/55743251/how-to-identify-outliers-with-density-plot
    
        
    #kernel density doesnt account for differences in axis scales..., so lets try and manually do that a bit
    kde = KernelDensity(bandwidth = 0.1).fit(data_no_na)
    
    yvals = kde.score_samples(data_no_na)  # yvals are logs of pdf-values
    yvals[np.isinf(yvals)] = np.nan # some values are -inf, set them to nan
    
    # approx. 10 percent of smallest pdf-values: lets treat them as outliers 
    outlier_inds = np.where(yvals < np.percentile(yvals, perc_show_names))[0]
    
    
    #add labels and adjust text positions to try and avoid overlap
    texts = []
    for i in range(len(outlier_inds)):
        texts.append(plt.annotate(data[data_names][data_no_na.index[outlier_inds[i]]], (data[x_col][data_no_na.index[outlier_inds[i]]], data[y_col][data_no_na.index[outlier_inds[i]]]) ))
    adjust_text(x = data[x_col].copy().values, y = data[y_col].copy().values, add_objects = [reg_line.lines[0], stats], texts = texts, 
                arrowprops=dict(arrowstyle="-", lw=0.5), 
                ax = ax, 
                expand_text = (2.75, 2.75), 
                expand_points = (2.75, 2.75), 
                expand_objects = (1.5, 1.5), 
                expand_align = (1.05, 1.2),
                precision = 0.001,
                )

    #add footnote
    ax.annotate(footnote,
            xy = (1.0, -0.15),
            xycoords='axes fraction',
            ha='right',
            va="center",
            fontsize=8)
    # Save chart
    plt.savefig(save_loc)
    plt.show()