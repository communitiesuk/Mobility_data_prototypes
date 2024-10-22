# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 09:40:58 2023

@author: evan.baker
"""

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import pandas as pd
import pyodbc 
import geopandas as gpd
from matplotlib.collections import LineCollection
from sklearn import preprocessing
LE = preprocessing.LabelEncoder()
from matplotlib.lines import Line2D
import time


import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
from analysis.unexpectedness.avg_non_inbound_trips import *
from analysis.utils import *


             
#commented out because this is SLOW (~48 mins for whole UK; ~4 mins for only Exeter)
whole_uk = True
LAD_of_interest = "Exeter" #only relevant at this point in script if whole_uk = False
#download_avg_non_inbound_trips(whole_uk = whole_uk, LAD_of_interest = LAD_of_interest)
trips = load_avg_non_inbound_trips(whole_uk = whole_uk, LAD_of_interest = LAD_of_interest)


#get total_avg-daily trips, weighted avg between weekend and weekday
trips = trips.pivot(index=["start_msoa", "end_msoa"],columns="day_type", values="avg_daily_trips").reset_index()
#replace NAs with 0
trips.loc[trips["weekday"].isna(), "weekday"] = 0
trips.loc[trips["weekend"].isna(), "weekend"] = 0
trips["avg_daily_trips"] = (5*trips["weekday"] + 4*trips["weekend"])/9 #get weighted avg, weekday trips are from 5 working days, weekend are from 4 weekend days
trips = trips.drop(columns = ["weekend", "weekday"]).reset_index(drop = True)


#I think different MSOAs have different amounts of trips (maybe from less movement in general, or fewer users in a place)
#either way, lets convert avg_daily_trips for each MSOA_MSOA pair to a proportion
#how many trips come from each MSOA? (including intra MSOA trips)
trips_MSOA_baseline = trips.groupby("start_msoa").sum()["avg_daily_trips"].reset_index()
trips_MSOA_baseline = trips_MSOA_baseline.rename(columns = {"avg_daily_trips":"trips_MSOA_baseline"})
trips = trips.merge(trips_MSOA_baseline, on = "start_msoa")
trips["avg_daily_trips_prop"] = trips["avg_daily_trips"]/trips["trips_MSOA_baseline"]



msoas = gpd.read_file("Q:\SDU\Mobility\Data\Boundaries\MSOA_Dec_2011_Boundaries_Generalised_Clipped_BGC_EW_V3_2022_-8564488481746373263/MSOA_2011_EW_BGC_V3.shp")

msoa_PWCs = pd.read_csv("Q:/SDU/Mobility/Data/PWCs/MSOA_Dec_2011_PWC_in_England_and_Wales_2022_-7657754233007660732.csv")
msoa_PWCs = gpd.GeoDataFrame(msoa_PWCs, crs = "EPSG:27700", geometry=gpd.points_from_xy(msoa_PWCs.x, msoa_PWCs.y))
msoa_PWCs.rename_geometry("MSOA_centroids", inplace=True)
msoa_PWCs = msoa_PWCs.drop(columns = ["OBJECTID", "GlobalID", "x", "y"]) #drop unneeded columns

trips = trips.merge(msoa_PWCs.add_suffix('_start'), #merge in shapes for satrt msoas
 left_on=["start_msoa"], 
 right_on=["MSOA11CD_start"],
 how = "left")

trips = trips.merge(msoa_PWCs.add_suffix('_end'), #merge in shapes for satrt msoas
 left_on=["end_msoa"], 
 right_on=["MSOA11CD_end"],
 how = "left")

#get distances for each trip
points_starts = gpd.GeoDataFrame({'geometry': trips["MSOA_centroids_start"]})
points_ends = gpd.GeoDataFrame({'geometry': trips["MSOA_centroids_end"]})

trips["trip_distance"] = points_starts.distance(points_ends)



#bring in external data
population_data = pd.read_excel("Q:\SDU\Mobility\Data\Auxiliary_data/msoa_2011_2020_pop_estimates.xlsx", skiprows = 4, sheet_name = "Mid-2020 Persons")
population_data = population_data.rename(columns={'MSOA Name': "MSOA11NM",
                                                  'MSOA Code' : "MSOA11CD",
                                                  "All Ages" : "Population"})


#drop unneeeded columns
population_data = population_data[["MSOA11CD", "Population"]]


#combine
trips = trips.merge(population_data.add_suffix('_start').rename(columns={'MSOA11CD_start': 'start_msoa'}), #merge in shapes for satrt msoas
 on=["start_msoa"],
 how = "left")

trips = trips.merge(population_data.add_suffix('_end').rename(columns={'MSOA11CD_end': 'end_msoa'}), #merge in shapes for satrt msoas
 on=["end_msoa"],
 how = "left")


#drop trips that have NAs (a lot coming because we dont have scottish datazone centroids included atm)
trips_no_na = trips.dropna()

#build NN to see which trips are suprisingly done
#get log trip distance
trips_no_na["trip_distance"] = trips_no_na["trip_distance"]/1000 #(convert to km)
trips_no_na["log_trip_distance"] = np.log(trips_no_na["trip_distance"]+1)


#convert binary string variables
#first plot our 1d input against our 1d output
X = trips_no_na[["log_trip_distance", "Population_start", "Population_end"]].values
y = np.log(trips_no_na["avg_daily_trips_prop"].values) #logging it to help NN, as trips seem to either be loads or very little
plt.scatter(X[:,0] , y)
plt.show()


# ids = np.random.randint(X.shape[0], size=20000)
# X_small = X[ids,:]
# y_small = y[ids]
#split into train and testing data
X_train, X_test, y_train, y_test = train_test_split(X,
                                                    y,
                                                    test_size=0.33,
                                                    random_state=42)


#normalise X
min_max_scaler = preprocessing.MinMaxScaler().fit(X_train)
X_train = min_max_scaler.transform(X_train)
X_test = min_max_scaler.transform(X_test)

#standardise y
standardise_scaler = preprocessing.StandardScaler().fit(y_train.reshape(-1, 1))
y_train = standardise_scaler.transform(y_train.reshape(-1, 1)).reshape(-1)
y_test = standardise_scaler.transform(y_test.reshape(-1, 1)).reshape(-1)


# build NN model
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(100, activation = 'relu', input_shape = (X.shape[1],)))
model.add(tf.keras.layers.Dense(100, activation = 'relu'))
model.add(tf.keras.layers.Dense(1))


#stop optimizer early if no more improvements
patience = 10
if whole_uk == False:
    patience = 50 #with less data, we need more patience
early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=patience, restore_best_weights=True)


model.compile(optimizer = 'adam', loss = 'mean_squared_error')
if whole_uk:
    save_suffix = "whole_UK"
else:
    save_suffix = LAD_of_interest
save_loc = "Q:/SDU/Mobility/Data/Processed/Processed_Mobility/NN_unexpected_query_results_"+save_suffix

# #commented out because this is SLOW (~108 mins for whole of UK; ~1.6 mins for Exeter)
# st_model_fit=time.time()
# history = model.fit(X_train, y_train, callbacks = [early_stop], epochs = 100000, verbose = 1, validation_data=(X_test, y_test))
# #save results
# model.save(save_loc)

# #plot loss history
# # summarize history for loss
# plt.plot(history.history['loss'])
# plt.plot(history.history['val_loss'])
# plt.title('model loss')
# plt.ylabel('loss')
# plt.xlabel('epoch')
# plt.legend(['train', 'test'], loc='upper left')
# plt.savefig(save_loc + "_training_accuracy.png")
# plt.show()
# et_model_fit=time.time()
# print(et_model_fit-st_model_fit)

#how to load
model = tf.keras.models.load_model(save_loc)




#plot 1d prediction
x_pred = np.linspace(-1,15, num = 100)
X_pred = X[0:100,:].copy()
X_pred[:,0] = x_pred
y_pred = model.predict(min_max_scaler.transform(X_pred))
plt.plot(X_pred[:,0], standardise_scaler.inverse_transform(y_pred.reshape(-1, 1)).reshape(-1))
plt.scatter(X[:,0], y, c = "red")
plt.xlim(-1,10.2)
plt.show()


LAD_of_interest = "Exeter"


#load in MSOA to LAD lookup
MSOA_LA_lookup = build_msoa_lad_itl_lookup()

MSOAs_in_LAD = MSOA_LA_lookup.loc[MSOA_LA_lookup["LAD22NM"]==LAD_of_interest]
MSOAs_in_LAD_sql_list = tuple(MSOAs_in_LAD["MSOA11CD"].unique())


#and only consider those within LA_of_interest
trips_pred = trips_no_na[pd.DataFrame(trips_no_na.start_msoa.tolist()).isin(MSOAs_in_LAD_sql_list).any(axis = 1).values]

X_pred = trips_pred[["log_trip_distance", "Population_start", "Population_end"]].values
pred_y = trips_pred["avg_daily_trips_prop"].values


#now get error (not mean squared error)
trips_pred["pred"] = model.predict(min_max_scaler.transform(X_pred))
unexpectedness = (pred_y - np.exp(standardise_scaler.inverse_transform(trips_pred["pred"].values.reshape(-1, 1)).reshape(-1)))

trips_pred["unexpectedness"] = unexpectedness
trips_pred["unexpectedness_exclude_internal"] = trips_pred["unexpectedness"].copy()
#not interested in within MSOA trips
trips_pred.loc[trips_pred["start_msoa"] == trips_pred["end_msoa"], "unexpectedness_exclude_internal"] = 0



#what are the top (5) most unexpected trip numbers (absolute terms)?

def return_top_n_journeys(trips_pred, top_n = 5, order = "abs", metric = "unexpectedness_exclude_internal"):
    #reorder trips in order of unexpectedness
    if order == "abs":
        unexpectedness_order = (-np.abs(trips_pred[metric])).argsort()
    elif order == "positive":
        unexpectedness_order = (-trips_pred[metric]).argsort()
    elif order == "negative":
        unexpectedness_order = (trips_pred[metric]).argsort()
    else:
        print("order must be one of \"abs\", \"positive\", or \"negative\"")
        
    trips_pred_unexpectedness_order = trips_pred.iloc[unexpectedness_order,:]
    
    #not interested in also highlighting the return journeys, so only get the first one for each MSOA-MSOA pair
    #create new combo for unique MSOA-MSOA pairing (in either order)
    #actually, now that we remove inbound trips from the SQL query, this can stay
    # MSOA_combo_namer = lambda n: "-".join(sorted(n))
    # trips_pred_unexpectedness_order['MSOA_combo_name'] = trips_pred_unexpectedness_order[['start_msoa','end_msoa']].apply(MSOA_combo_namer, axis=1)

    # trips_pred_unexpectedness_order = trips_pred_unexpectedness_order.drop_duplicates(subset=["MSOA_combo_name"])
    
    
    top_n_unexpected_trips = trips_pred_unexpectedness_order.iloc[:top_n,:]
    
    return(top_n_unexpected_trips)


top_n_unexpected_trips = return_top_n_journeys(trips_pred, top_n = 5, order = "abs")


#get background map
def get_MSOA_MSOA_unexpectedness_map(top_n_unexpected_trips, title_prefix = "Top 5 journeys of interest in "):
    colors = ["#12436D", "#28A197", "#801650", "#F46A25", "#3D3D3D", "#A285D1"]
    msoa_map_data = msoas[pd.DataFrame(msoas.MSOA11CD.tolist()).isin(list(MSOAs_in_LAD_sql_list)).any(axis = 1).values]
    
    msoa_map_data = msoas[
          pd.DataFrame(msoas.MSOA11CD.tolist()).isin(
              list(MSOAs_in_LAD_sql_list) #+ np.unique(trips_pred["MSOA11CD_start"])+ np.unique(trips_pred["MSOA11CD_end"])
    ).any(axis = 1).values]
    
    
    #plot these top n trips
    #bring in geography for top n trips
    top_n_unexpected_trips = top_n_unexpected_trips.merge(msoas.add_suffix('_geography_start'), #merge in shapes for satrt msoas
     left_on=["start_msoa"], 
     right_on=["MSOA11CD_geography_start"])
    top_n_unexpected_trips = top_n_unexpected_trips.merge(msoas.add_suffix('_geography_end'), #merge in shapes for satrt msoas
     left_on=["end_msoa"], 
     right_on=["MSOA11CD_geography_end"])
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    msoa_map_data.geometry.boundary.plot(edgecolor='k',linewidth = 1,ax=ax)
    gpd.GeoDataFrame(top_n_unexpected_trips, geometry=top_n_unexpected_trips.geometry_geography_start).plot(facecolor = colors[0],edgecolor=colors[0], linewidth = 2,ax=ax, alpha = 0.5, label = "Origins")
    gpd.GeoDataFrame(top_n_unexpected_trips, geometry=top_n_unexpected_trips.geometry_geography_end).plot(facecolor = colors[2],edgecolor=colors[2],linewidth = 2,ax=ax, alpha = 0.5, label = "Destinations")
    
    for slat,dlat, slon, dlon, unexpectedness in zip(top_n_unexpected_trips["MSOA_centroids_start"].apply(lambda p: p.y), top_n_unexpected_trips["MSOA_centroids_end"].apply(lambda p: p.y),
                                                  top_n_unexpected_trips["MSOA_centroids_start"].apply(lambda p: p.x), top_n_unexpected_trips["MSOA_centroids_end"].apply(lambda p: p.x),
                                                  top_n_unexpected_trips["unexpectedness"]):
        #plt.plot([slon , dlon], [slat, dlat], linewidth=1, colors[0], alpha=1)
        plt.arrow(slon, slat, dx = dlon-slon, dy = dlat -slat, width = 50, head_width = 300, color=colors[3], length_includes_head = True, zorder = 10)
    
    
    plt.axis('off')
    labels = [t.get_label() for t in ax.collections[1:]]
    lines = [
        Line2D([0], [0], linestyle="none", color = t.get_facecolor(), marker="s", markersize=10, markerfacecolor=t.get_facecolor())
        for t in ax.collections[1:]
        ]
    ax.legend(lines, labels)
    fig.suptitle(title_prefix+LAD_of_interest, fontsize=24)
    fig.text(0.2,0.14, 'Source: O2 Motion data, DLUHC internal analysis', fontsize=13)

get_MSOA_MSOA_unexpectedness_map(top_n_unexpected_trips)



#get the places people seem to avoid
top_n_unexpected_trips_underused = return_top_n_journeys(trips_pred, top_n = 5, order = "negative")
get_MSOA_MSOA_unexpectedness_map(top_n_unexpected_trips_underused, title_prefix = "Top 5 journeys avoided in ")




#and also just get top 5 trips (no fancy anything going on)
#These are often just the same - people don't travel to places far away, which we've captured, but they dont eactly just travel to the places closest
trips_pred["avg_daily_trips_prop_exclude_internal"] = trips_pred["avg_daily_trips_prop"].copy()
trips_pred.loc[trips_pred["start_msoa"] == trips_pred["end_msoa"], "avg_daily_trips_prop_exclude_internal"] = 0

top_n_trips = return_top_n_journeys(trips_pred, top_n = 5, order = "abs", metric = "avg_daily_trips_prop_exclude_internal")
get_MSOA_MSOA_unexpectedness_map(top_n_trips, title_prefix = "Top 5 journeys in ")
