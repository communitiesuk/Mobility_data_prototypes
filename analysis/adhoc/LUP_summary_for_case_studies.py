# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 12:55:09 2023

@author: gordon.donald
"""

import geopandas as gpd
lads = gpd.read_file("Q:/SDU/Mobility/Data/Boundaries/LAD_2023_coastline_clipped/LAD_MAY_2023_UK_BFC_V2.shp")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from src.utils.constants import map_lu_partnership_colour_scale_unordered


LUPs = ["Kingston upon Hull, City of","Sandwell","Mansfield","Middlesbrough","Blackburn with Darwen","Hastings","Torbay","Tendring","Stoke-on-Trent","Boston","Redcar and Cleveland","Wakefield","Oldham","Rother","Torridge","Walsall","Doncaster","South Tyneside","Rochdale","Bassetlaw", "Blackpool", "Northumberland", "North East Lincolnshire"]
lads['IS_LUP'] = lads['LAD23NM'].isin(LUPs)

lads=lads[lads['LAD23CD'].str.startswith("E")]

def plot_LUPs(data=lads, single=False, title="Levelling Up Partnerships in England"):
    fig, ax = plt.subplots(figsize=(10, 10))
    if single:
        cmap =  ListedColormap([map_lu_partnership_colour_scale_unordered[2]])
    else:
        cmap =  ListedColormap(['lightgrey', map_lu_partnership_colour_scale_unordered[2]])
        
    data.plot(
        column='IS_LUP',
        edgecolor = 'k', 
        linewidth = 0.5,
        cmap = cmap,
        legend =False,
        k=2,
        ax=ax
        )
    plt.axis('off')
    fig.suptitle(title, fontsize=24)
    fig.text(0.2,0.14, 'DLUHC', fontsize=13);

plot_LUPs()

mb = lads[lads.LAD23NM=="Middlesbrough"]
torbay =lads[lads.LAD23NM=="Torbay"]
hastings =lads[lads.LAD23NM=="Hastings"]
hull =lads[lads.LAD23NM=="Kingston upon Hull, City of"]

plot_LUPs(mb, single=True, title="Middlesbrough")
plot_LUPs(torbay, single=True, title="Torbay")
plot_LUPs(hastings, single=True, title = "Hastings")
plot_LUPs(hull, single=True, title = "Hull")
