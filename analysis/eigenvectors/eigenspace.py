# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 17:23:14 2023

@author: gordon.donald
"""


import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)

import pandas as pd
import geopandas
import time

from analysis.utils import *
msoas=get_all_small_areas()
from src.visualise.map_at_sub_la import *


import matplotlib.pyplot as plt
#use same colour scheme as lup packs
map_lu_partnership_colour_scale= ["#CDE594" , "#80C6A3", "#1F9EB7", "#186290", "#080C54"]
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
#Basemap
import contextily as cx

import numpy as np


#This is much preferred if we want to look at all MSOAs -- get all the data from a single query first
#This will get the data between 7 and 9 (start of journey)
def get_data_for_weekdays():
    #This query takes about 4 mins, which is okay.
    query = "SELECT start_msoa, end_msoa, SUM(avg_daily_trips) FROM Process.tb_O2MOTION_ODMODE_Weekly WHERE (start_date='2023-03-27' AND hour_part>6 AND hour_part<10) GROUP BY start_msoa, end_msoa"
    return(submit_sql_query(query))

test_weekdays = get_data_for_weekdays()
test_weekdays.columns = ['start_msoa', 'end_msoa', 'avg_daily_trips']

#There's one MSOA which is an end only (in NI)
weekdays2 = test_weekdays[test_weekdays['end_msoa'].isin(test_weekdays['start_msoa'])]
#In general, also need to ensure we deal with MSOAs which are only starts
weekdays2 = weekdays2[weekdays2['start_msoa'].isin(weekdays2['end_msoa'])]


matrix_form = weekdays2.pivot(index='end_msoa',columns='start_msoa', values='avg_daily_trips').fillna(0).astype(int)

my_matrix = np.matrix(matrix_form)
diag_elements = my_matrix.diagonal()
#Think we really want to normalise by resident population rather than internal journeys. 
msoa_pop = get_pop_for_all_small_areas()

msoa_pop = msoa_pop.sort_values(by='msoa11cd') #Sort alphabetically, as that's what the pivot table does.
msoa_pop_for_matrix = msoa_pop[msoa_pop['msoa11cd'].isin(matrix_form.index)]

NET_FLOW=True
NON_NET_FLOW=not(NET_FLOW)

#We have some options for how to build the flow matrix. We can use the net flow from A to B (so -20, 20 for M_{AB} and M_{BA}), so total flow (i.e. 100, 80)

if NET_FLOW:
    #Symmertric version
    m2 = (my_matrix-my_matrix.T) / msoa_pop_for_matrix['pop'].values.reshape(-1,1)
    #If we use net flow (M-M^T, then diagonal is one and we add subtract the net flow from original numbers.)
    #Or we can set the diagonal to zero -- this has the same eigenvectors, and the eigenvalues are just lambda -> 1+lambda
    np.fill_diagonal(m2, 0) 
    #Note: turns out this has pure imaginary eignevvalues (+/- i*lambda)! 
    #Would get this for an antisymmetric matrix, which this isn't explicitly. 
    #(M_{i,j} != -M_{j,i}, but we do have similar constraints due to conservation of people) and this matrix is traceless.


if NON_NET_FLOW:
#Non-sym version
    m2 = my_matrix/ msoa_pop_for_matrix['pop'].values.reshape(-1,1)
    #For the flow interpretation, the diagonal would be people remaining in the LA
    diag_remainder = 1- m2.sum(axis=0)
    np.fill_diagonal(m2, diag_remainder) 



N_eigs = 200

from scipy.sparse.linalg import eigs
vals, vecs = eigs(m2, k=N_eigs*2, which='LM')
#Eigenvalue spectrum is complex conjugate pairs, and pure imaginery.
#Matrix is not explicitly anti-symmetric, but is constrained.

#When using NET FLOW, we assume we have all the eigenvectors in CC pairs. So test that.
if NET_FLOW:
    for i in range(N_eigs): assert(vals[2*i] == vals[2*i+1].conj())

msoas_vecs = pd.DataFrame(matrix_form.index)
for i in range(N_eigs):
    if NET_FLOW: 
        ev=2*i #Here, can skip half the eigenvectors as they are CC pairs, so every second eigenvector has same information as the preceeding one.
    else:
        ev=i
    msoas_vecs['Rvec_'+str(i)] = vecs[:,ev].real
    msoas_vecs['Ivec_'+str(i)] = vecs[:,ev].imag
    msoas_vecs['vec_'+str(i)] = vecs[:,ev]
    #Remove huge values if helpful
    #msoas_vecs.loc[abs(msoas_vecs['vec_'+str(i)])>0.1, 'vec_'+str(i)] =0


###### Want to keep a subset which tell us about different functional economic areas -- these will be the one with distinct spans -- starting from the highest eigenvalue.
#Test the dot product for span of the eigenvectors being sufficiently distinct.
threshold=0.0001
#We pla to keep eigenvectors iff they are distinct from ALL other kept eigenvectors -- starting from 0.
our_ev = [0]

def scaled_dot(vec1, vec2):
    return( np.dot(vec1,vec2) / (np.dot(vec1,vec1)*(np.dot(vec2,vec2)))**0.5 )

def test_distinct(e1, e2, threshold=0.1):
    test = abs(scaled_dot(msoas_vecs['vec_'+str(e1)], msoas_vecs['vec_'+str(e2)]))<threshold
    return(test)

def keep_ev_i(kept_ev, i):
    for ev in kept_ev:
        if not test_distinct(ev, i):
            return(kept_ev)
    #if we get to this part of code without returning, we can add i to the list of kept eigenvectors
    kept_ev.append(i)
    return(kept_ev)

for i in range(N_eigs):
    our_ev = keep_ev_i(our_ev, i)


######Plot our vectors.
map_data = msoas.merge(msoas_vecs, left_on='msoa11cd', right_on='end_msoa')

#This will plot the real and imaginary part of the most prominent eigenvectors.

#Mask out some values?
mask_threshold=1e-4
#Do this for real and imag eigenevectors
#Move this so we have a copy, as we want to preserve these without the threshold for later analysis.
for i in range(N_eigs):
    map_data['Plot_Rvec_'+str(i)] = map_data['Rvec_'+str(i)]
    map_data['Plot_Ivec_'+str(i)] = map_data['Ivec_'+str(i)]
    map_data.loc[map_data['Rvec_'+str(i)]<mask_threshold, 'Plot_Rvec_'+str(i)] =None
    map_data.loc[map_data['Ivec_'+str(i)]<mask_threshold, 'Plot_Ivec_'+str(i)] =None


#Crashed the whole VM on memory in the loop the first time, so split this so we aren't storing a whole bunch of MSOA map at once.
for i in range(0,5):
    plot_map(map_data, 'Plot_Rvec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Real: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
             line_width=0, colour_scheme='fisherjenks')
    plot_map(map_data, 'Plot_Ivec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Imag: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
             line_width=0, colour_scheme='fisherjenks')
    
for i in range(5,10):
    plot_map(map_data, 'Plot_Rvec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Real: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
             line_width=0, colour_scheme='fisherjenks')
    plot_map(map_data, 'Plot_Ivec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Imag: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
             line_width=0, colour_scheme='fisherjenks')

for i in range(10,15):
    plot_map(map_data, 'Plot_Rvec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Real: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
             line_width=0, colour_scheme='fisherjenks')
    plot_map(map_data, 'Plot_Ivec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Imag: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
             line_width=0, colour_scheme='fisherjenks')
    
#Plot eigenvectors in a simple 'these places are in/out of the area'
within_thres = 0.01 #Crude, using fisher-jenks breaks might be smarter.
for i in range(len(our_ev)):
    map_data['In_'+str(our_ev[i])] = abs(map_data['Rvec_'+str(our_ev[i])])+abs(map_data['Ivec_'+str(our_ev[i])])>within_thres
    
for i in range(0,5):
    plot_map(map_data, 'In_'+str(our_ev[i]), plot_title="In/out", suptitle="Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
             line_width=0, colour_scheme='headtailbreaks' )
    
#PLot a bunch of the eigenvectors together -- this is our way to summarise the areas
#Which EV is each MSOA then in?
map_data['Main_EV']=None
for i in range(len(our_ev)):
    neg_iter = -1-i
    print(our_ev[neg_iter])
    map_data.loc[map_data['In_'+str(our_ev[neg_iter])], 'Main_EV']=our_ev[neg_iter]

map_data['Main_EV_plot1'] = map_data['Main_EV']
map_data.loc[map_data['Main_EV']>16, 'Main_EV_plot1']=None

map_data['Main_EV_plot2'] = map_data['Main_EV']
map_data.loc[map_data['Main_EV']<17, 'Main_EV_plot2']=None
map_data.loc[map_data['Main_EV']>45, 'Main_EV_plot2']=None
    
map_data['Main_EV_plot3'] = map_data['Main_EV']
map_data.loc[map_data['Main_EV']<46, 'Main_EV_plot3']=None

#Tweak these for higher plotting quality
fig, ax = plt.subplots(figsize=(10, 10))
our_plot =map_data.plot('Main_EV_plot1', cmap='tab10', missing_kwds= dict(color = "lightgrey", alpha=0.5,), ax=ax)
plt.axis('off')
fig.suptitle("Eigenvectors 1-9", fontsize=24)

fig, ax = plt.subplots(figsize=(10, 10))
our_plot =map_data.plot('Main_EV_plot2', cmap='tab10', missing_kwds= dict(color = "lightgrey", alpha=0.5,), ax=ax)
plt.axis('off')
fig.suptitle("Eigenvectors 10-18", fontsize=24)

fig, ax = plt.subplots(figsize=(10, 10))
our_plot =map_data.plot('Main_EV_plot3', cmap='tab10', missing_kwds= dict(color = "lightgrey", alpha=0.5,), ax=ax)
plt.axis('off')
fig.suptitle("Eigenvectors 19-27", fontsize=24)
 

    
#for i in range(20, len(our_ev)):
 #   plot_map(map_data, 'Rvec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Real: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
  #           line_width=0, colour_scheme='fisherjenks')
   # plot_map(map_data, 'Ivec_'+str(our_ev[i]), plot_title="Magnitude of eigenvector", suptitle="Imag: Eigenvector "+str(our_ev[i]), source="Source: O2 Motion",
    #         line_width=0, colour_scheme='fisherjenks')
