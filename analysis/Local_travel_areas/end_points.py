# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 17:04:19 2023

@author: gordon.donald
"""

import pandas as pd
from analysis.utils import *
import matplotlib.pyplot as plt
import contextily as cx

import git
import os
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)
import sys
sys.path.append(repo.working_tree_dir)
from analysis.Local_travel_areas.LTA_plot_functions import *


towns_data = pd.read_csv("Q:/SDU/Mobility/Data/Processed/towns_ltas.csv")
BUAs = get_BUAs()
bua_pop = get_BUA_pop()
BUAs = BUAs.merge(bua_pop, on='BUA22NM')

#On the towns_data, where are end_nodes?
#This is just these.
percent_threshold = 2 #Want slightly above zero to avoid examples like linking Manchester to Leeds.

end_pts = towns_data[towns_data.travel_to_bigger_area<percent_threshold]['Town']

#Connect end BUA to a town/city we say is the centre of it's economic area.
links = towns_data.copy()

def get_end_point_from_town(our_bua):
    if our_bua in list(end_pts):
        return(our_bua)
    else:
        new_bua = links[links.Town==our_bua].iloc[0]['primary_bigger_BUA']
        return(get_end_point_from_town(new_bua))

links['Centre'] = links['Town'].apply(lambda x: get_end_point_from_town(x))
links = links.merge(bua_pop, left_on='Town', right_on='BUA22NM')

centre_BUAs = BUAs[BUAs.BUA22NM.isin(links.Centre)].copy()
centre_BUAs['N_BUAs'] = centre_BUAs.BUA22NM.apply(lambda x: len(links[links.Centre==x]))

# read in SDU OS API key
key = pd.read_csv("Q:/SDU/Levelling Up Partnerships/data/annex b - 6 capitals/physical/Travel_Time_Isochrones/OS_API_KEY.csv")["OS_MAPS_API_KEY"].iloc[0]
basemap_url = "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=" + key

def get_BUA_coords(our_bua):
    centroid = BUAs[BUAs.BUA22NM==our_bua].centroid
    return(centroid.x.iloc[0], centroid.y.iloc[0])

#Could mess with labels a bit more. Or split this up by region to avoid being small.
PLOT=True
if PLOT:
    f, ax = plt.subplots(figsize=(12, 12))
    #Split by population
    high_pop = 225e3
    BUAs_high = centre_BUAs[centre_BUAs.Population>high_pop]
    BUAs_low =  centre_BUAs[centre_BUAs.Population<=high_pop]
    BUAs_low.plot(color='blue', alpha=0.5, ax=ax)
    BUAs_high.plot(color='red', alpha=0.5, ax=ax)
    cx.add_basemap(ax, source=basemap_url, crs=centre_BUAs.crs)
    ax.set_title("Centres of independent economic areas")
    for town_i in range(len(BUAs_low)):
        dest_x, dest_y = get_BUA_coords(BUAs_low.iloc[town_i]['BUA22NM'])
        ax.annotate(BUAs_low.iloc[town_i]['BUA22NM'].split("(")[0], xy=(dest_x,dest_y), ha='center', color='black', font='Arial', fontsize=8)
    plt.savefig("Q:/SDU/Mobility/Data/Processed/Economic_Integration/All_areas_summary_highlight_towns.png", bbox_inches="tight", dpi=300, )


    if percent_threshold > 5: #If we have larger threshold, also look to map out difference between 5 and 10.
        f, ax = plt.subplots(figsize=(12, 12))
        centres_w_pop = centre_BUAs.merge(links)
        new_centres = centres_w_pop[centres_w_pop.travel_to_bigger_area > 5]
        old_centres = centres_w_pop[centres_w_pop.travel_to_bigger_area <= 5]
        new_centres.plot(color='blue', alpha=0.5, ax=ax)
        old_centres.plot(color='red', alpha=0.5, ax=ax)
        cx.add_basemap(ax, source=basemap_url, crs=centre_BUAs.crs)
        ax.set_title("Centres of largely independent economic areas")
        for town_i in range(len(new_centres)):
            dest_x, dest_y = get_BUA_coords(new_centres.iloc[town_i]['BUA22NM'])
            ax.annotate(new_centres.iloc[town_i]['BUA22NM'].split("(")[0], xy=(dest_x,dest_y), ha='center', color='black', font='Arial', fontsize=8)
        plt.savefig("Q:/SDU/Mobility/Data/Processed/Economic_Integration/All_areas_summary_highlight_semi_independent.png", bbox_inches="tight", dpi=300, )

        centres_info = centres_w_pop[['BUA22CD_x', 'BUA22NM', 'Population', 'travel_to_bigger_area', 'primary_bigger_BUA']]
        centres_info.sort_values('Population').to_csv("Q:/SDU/Mobility/Data/Processed/Economic_Integration/All_areas_summary_data.csv", index=False)

def plot_around_endpoint(end_pt):
    end_pt_data = links[links.Centre==end_pt]

    f, ax = plt.subplots(figsize=(12, 12))
    BUAs.merge(end_pt_data, left_on='BUA22NM', right_on='Town').plot(ax=ax, cmap='YlGnBu', vmin=0, vmax=100, column='travel_to_bigger_area', alpha=0.7, legend=True)
    BUAs[BUAs.BUA22NM==end_pt_data.iloc[0]['Centre']].plot(ax=ax, color='darkblue', alpha=0.7)
    cx.add_basemap(ax, source=basemap_url, crs=BUAs.crs)
    ax.set_title("Economic integration for towns around " + end_pt+" \nTotal population: " + str(int(end_pt_data.Population.sum())))
    colorbar_ax = ax.get_figure().axes[-1] #to get the last axis of the figure, it's the colorbar axes
    colorbar_ax.set_title("Integration \n(% of travel)", size=10)
    
    for town_i in range(len(end_pt_data)):
        if (end_pt_data.iloc[town_i]['primary_bigger_BUA']!='None') & ~pd.isnull(end_pt_data.iloc[town_i]['primary_bigger_BUA']):
            origin_x, origin_y = get_BUA_coords(end_pt_data.iloc[town_i]['Town'])
            dest_x, dest_y = get_BUA_coords(end_pt_data.iloc[town_i]['primary_bigger_BUA'])
            ax.annotate("", xy=(dest_x, dest_y), xytext=(origin_x, origin_y), arrowprops=dict(arrowstyle="->", color='grey', alpha=0.8))
            #plt.arrow(origin_x, origin_y, dx = dest_x-origin_x, dy = dest_y-origin_y, width = scale, head_width = 100*scale, color='black', length_includes_head = True, zorder = 10)
            
    #Label towns with in-flow        
    unique_dests = end_pt_data.primary_bigger_BUA.drop_duplicates()
    for town_i in range(len(unique_dests)):
        if (unique_dests.iloc[town_i]!='None') & (~pd.isnull(unique_dests.iloc[town_i])):
            dest_x, dest_y = get_BUA_coords(unique_dests.iloc[town_i])
            ax.annotate(unique_dests.iloc[town_i], xy=(dest_x,dest_y), ha='center', color='black', font='Arial')
            
    return(0)

def scatter_around_endpoint(end_pt, y_axis_var = "job_ratio", y_axis_lab = "Jobs per population in BUA", save_loc = ""):
    end_pt_data = links[links.Centre==end_pt].copy()
    end_pt_towns = end_pt_data.Town
    economic_integration_scatter(towns_data, end_pt_towns, title = "Economic integration for towns around " + end_pt + " \n(up to 10 largest towns included)", save_loc = save_loc)
    return(0)



if PLOT:
    for end_pt in end_pts:
        plot_around_endpoint(end_pt)
        plt.savefig("Q:/SDU/Mobility/Data/Processed/Economic_Integration/end_pts_plots/"+end_pt+"_map.png", dpi=150)
        plt.close()
        scatter_around_endpoint(end_pt, save_loc = "Q:/SDU/Mobility/Data/Processed/Economic_Integration/end_pts_plots/"+end_pt+"_scatter_jobs")
        scatter_around_endpoint(end_pt, save_loc = "Q:/SDU/Mobility/Data/Processed/Economic_Integration/end_pts_plots/"+end_pt+"_scatter_income", y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA")
        scatter_around_endpoint(end_pt, save_loc = "Q:/SDU/Mobility/Data/Processed/Economic_Integration/end_pts_plots/"+end_pt+"_scatter_gva", y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA")


#Also want Levelling up need for towns.
bua_lad_lookup = pd.read_csv("Q:/SDU/Mobility/Data/Lookups/BUA_to_LAD_1-1_best_fit_by_pop.csv")
lu_need = pd.read_excel("Q:/SDU/Towns_indicative_selection_QA/Data/OFF-SEN - BUA Analysis - LUWPs Ranking v01.02.xlsx", sheet_name='LUWP', skiprows=1)
lu_need = lu_need[['Lower tier local authority code', 'Sum of normalised score (Smaller numbers = more LU need)']]
lu_need.columns = ['LAD22CD', 'LU_need']
bua_lu_need = bua_lad_lookup.merge(lu_need)
links = links.merge(bua_lu_need, left_on='Town', right_on='BUA22NM').drop_duplicates()

#and plot for all towns
economic_integration_scatter(links, links[links.travel_to_bigger_area>percent_threshold]['Town'], title = "Economic integration for towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/all_towns_scatter_jobs")
economic_integration_scatter(links, links[links.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/all_towns_scatter_income")
economic_integration_scatter(links, links[links.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/all_towns_scatter_GVA")
economic_integration_scatter(links, links[links.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "LU_need", y_axis_lab = "Levelling Up need", title = "Economic integration for towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/all_towns_scatter_LU_need")

#Filter by population to only show towns between 50k and 225k population
links_towns_we_recognise = links[(links.Population > 50e3) & (links.Population<225e3)]
percent_threshold=0.5
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_jobs")
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_income")
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_GVA")
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "LU_need", y_axis_lab = "Levelling Up need", title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_LU_need")

#Colour scatter plot by the destination population
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_jobs_colour_dest", HOME_POP=False)
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_income_color_dest", HOME_POP=False)
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_GVA_color_dest", HOME_POP=False)
economic_integration_scatter(links, links_towns_we_recognise[links_towns_we_recognise.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "LU_need", y_axis_lab = "Levelling Up need", title = "Economic integration for towns with population 50k - 225k", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/larger_towns_scatter_LU_need_color_dest", HOME_POP=False)

#Get towns in LUPs, and in the LTPfT.
#Do we have these somewhere?
LUPs = pd.read_csv("Q:/GI_Data/_GPA Jobs/20220505 DeepDives/Levelling_Up_Partnerships_Data/lup_data.csv")

#The 55 towns for the towns selection.
towns_england = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Outputs/summary_with_rank.csv")
towns_scotland = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Outputs/summary_with_rank_SCOTLAND.csv")
towns_wales = pd.read_csv("Q:/SDU/Towns_indicative_selection_QA/Outputs/Wales_summary_with_rank.csv")
#Filter the selction to get 55 towns
towns_england = towns_england[towns_england.new_score<45]
towns_scotland = towns_scotland[towns_scotland.new_score<8]
places_names = list(towns_england.most_deprived_town_rank) + list(towns_wales.most_deprived_town_rank) + list(towns_scotland['Settlement name\r\r\n[Note 1] [Note 3]'])

links_LUPs = links[links.LAD22CD.isin(LUPs.LTLA23CD)]
links_LTPFT = links[links.Town.isin(places_names)]

#Plot for LUPs
economic_integration_scatter(links, links_LUPs['Town'], title = "Economic integration for towns in LUP areas", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/lup_towns_scatter_jobs")
economic_integration_scatter(links, links_LUPs['Town'], y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for towns in LUP areas", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/lup_towns_scatter_income")
economic_integration_scatter(links, links_LUPs['Town'], y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for towns in LUP areas", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/lup_towns_scatter_GVA")
economic_integration_scatter(links, links_LUPs['Town'], y_axis_var = "LU_need", y_axis_lab = "Levelling Up need", title = "Economic integration for towns in LUP areas", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/lup_towns_scatter_LU_need")

#Plot for Long Term Plan for Towns towns
economic_integration_scatter(links, links_LTPFT['Town'], title = "Economic integration for towns selected in Long-Term Plan for Towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/ltpft_towns_scatter_jobs")
economic_integration_scatter(links, links_LTPFT['Town'], y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for towns selected in Long-Term Plan for Towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/ltpft_towns_scatter_income")
economic_integration_scatter(links, links_LTPFT['Town'], y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for towns selected in Long-Term Plan for Towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/ltpft_towns_scatter_GVA")
economic_integration_scatter(links, links_LTPFT['Town'], y_axis_var = "LU_need", y_axis_lab = "Levelling Up need", title = "Economic integration for towns selected in Long-Term Plan for Towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/ltpft_towns_scatter_LU_need")



#And also only show those that feed into a city
#If we filter twons first to only use those with population over 50k, this looks more or less the same as above, but do anyway.♣

links_subsetted = links_towns_we_recognise[links_towns_we_recognise["primary_bigger_BUA_pop"] >= 100000]

#and then obtain any town that docks in to the starting BUAs here (or dock into a town that docks into a starting BUA here, etc)

def get_docking_towns_from_town(current_bua_list, docking_towns = []):
    
    docking_towns_extra = links[links["primary_bigger_BUA"].isin(current_bua_list)].Town.values.tolist()
    #remove itself from this list (if applicable)
    docking_towns_extra = [x for x in docking_towns_extra if x not in current_bua_list]
    if len(docking_towns_extra) == 0:
        return(docking_towns)
    else:
        docking_towns = docking_towns + docking_towns_extra 
        current_bua_list = docking_towns_extra
        
        return(get_docking_towns_from_town(current_bua_list, docking_towns = docking_towns))

links_subsetted["list_of_docking_towns"] = links_subsetted['Town'].apply(lambda x: get_docking_towns_from_town([x]))

#and now plot for all towns, but only those that feed into cities
economic_integration_scatter(links_subsetted, links_subsetted[links_subsetted.travel_to_bigger_area>percent_threshold]['Town'], title = "Economic integration for towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/all_towns_scatter_jobs_cities_only", docking_towns = True )
economic_integration_scatter(links_subsetted, links_subsetted[links_subsetted.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/all_towns_scatter_income_cities_only", docking_towns = True )
economic_integration_scatter(links_subsetted, links_subsetted[links_subsetted.travel_to_bigger_area>percent_threshold]['Town'], y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/all_towns_scatter_GVA_cities_only", docking_towns = True )






#and then plot these only for the towns as specified before 
towns1 = ['York','Cheltenham','Ipswich','Hastings', 'Whitby','St Austell','Bradford','Warrington',
     'Royal Sutton Coldfield','Wakefield', "Barrow-in-Furness"]

towns2 = ['York','Gloucester','Ipswich','Scarborough','Bradford','Warrington',
     'Wakefield', 'Eastbourne', 'Newquay', 'Glossop', "Barrow-in-Furness"]


economic_integration_scatter(links, towns1, title = "Economic integration for selected towns (option 1)", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/towns1_scatter_jobs", kde_perc = 100)
economic_integration_scatter(links, towns1, y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for selected towns (option 1)", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/towns1_scatter_income", kde_perc = 100)
economic_integration_scatter(links, towns1, y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for selected towns (option 1)", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/towns1_scatter_GVA", kde_perc = 100)


economic_integration_scatter(links, towns2, title = "Economic integration for selected towns (option 2)", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/towns2_scatter_jobs", kde_perc = 100)
economic_integration_scatter(links, towns2, y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for selected towns (option 2)", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/towns2_scatter_income", kde_perc = 100)
economic_integration_scatter(links, towns2, y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for selected towns (option 2)", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/towns2_scatter_GVA", kde_perc = 100)



#and then LUPs?

#get BUA to LA lookup
BUA_LA_lookup = pd.read_csv("Q:\SDU\Mobility\Data\Lookups/Built_Up_Area_to_Local_Authority_District_(December_2022)_Lookup_in_Great_Britain.csv")
#only want LUPs BUAs
LUPs = ["Kingston upon Hull, City of", "Sandwell", "Mansfield", "Middlesbrough", "Blackburn with Darwen", "Hastings", "Torbay", 
        "Tendring", "Stoke-on-Trent", "Boston", "Redcar and Cleveland", "Wakefield", "Oldham", "Rother", "Torridge", "Walsall", 
        "Doncaster", "South Tyneside", "Rochdale", "Bassetlaw"] 


LUPs_BUAs = BUA_LA_lookup[(BUA_LA_lookup["LAD22NM"].isin(LUPs)) & (BUA_LA_lookup["BUA22NM"].isin(links[links.travel_to_bigger_area>percent_threshold].BUA22NM))]
LUPs_BUAs = LUPs_BUAs.BUA22NM.unique()


economic_integration_scatter(links, LUPs_BUAs, title = "Economic integration for LUP towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/LUPS_BUAs_scatter_jobs", kde_perc = 0)
economic_integration_scatter(links, LUPs_BUAs, y_axis_var = "avg_total_income", y_axis_lab = "average household income in BUA", title = "Economic integration for LUP towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/LUPS_BUAs_scatter_income", kde_perc = 10)
economic_integration_scatter(links, LUPs_BUAs, y_axis_var = "total_gva_per_person", y_axis_lab = "Total GVA per person in BUA", title = "Economic integration for LUP towns", save_loc =  "Q:/SDU/Mobility/Data/Processed/Economic_Integration/LUPS_BUAs_scatter_GVA", kde_perc = 10)

