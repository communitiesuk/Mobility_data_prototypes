# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 13:58:22 2023

@author: gordon.donald
"""

#Get some helpful data at MSOA level. Working age population? Jobs?
import pandas as pd

def get_total_jobs_by_msoa(sector=["Total"]):
    
    msoa_ind = pd.read_csv("Q:/SDU/Mobility/Data/Auxiliary_data/BRES_2022_Ind_class.csv", encoding="iso-8859-1", skiprows=8)
    msoa_ind = msoa_ind.dropna(axis=1, how='all')
    msoa_ind  = msoa_ind.drop(['Area', 'Unnamed: 3'], axis=1)
    msoa_ind = msoa_ind.dropna(axis=0, how='any')
    msoa_ind['Total'] = msoa_ind.sum(numeric_only=True, axis=1)

    msoa_ind = msoa_ind.melt(id_vars='mnemonic')
    msoa_ind.columns = ['msoa11cd', 'industry', 'jobs']
    msoa_ind.industry = msoa_ind.industry.str.split(" ").str[0]
    if type(sector) == str:
        sector = sector.split()
    msoa_jobs = msoa_ind[msoa_ind.industry.isin(sector)]

    return(msoa_jobs)


def get_gross_household_income_by_msoa11():
    
    msoa_inc = pd.read_excel("Q:/SDU/Mobility/Data/Auxiliary_data/ONS_small_area_gross_income.xlsx", sheet_name = "Total annual income", skiprows=4)
    msoa_inc = msoa_inc[['MSOA code', 'Total annual income (£)']]
    msoa_inc.columns = ['MSOA11CD', 'income']

    return(msoa_inc)

def get_total_households_by_msoa11():
    
    msoa_hhlds = pd.read_excel("Q:/SDU/Mobility/Data/Auxiliary_data/Census2011_pop_and_households.xlsx", sheet_name = "MSOA", skiprows=11)

    msoa_hhlds = msoa_hhlds[['MSOA Code', 'Households']]
    msoa_hhlds.columns = ['MSOA11CD', 'households']
    
    msoa_hhlds = msoa_hhlds.dropna(axis=1, how='all')
    msoa_hhlds = msoa_hhlds.dropna(axis=0, how='any')

    return(msoa_hhlds)


def get_gva_by_buasd2011():
    
    bua_gva = pd.read_excel("Q:/SDU/Mobility/Data/Auxiliary_data/ukgvaandproductivityestimatesforothergeographies1998to2020.xlsx", sheet_name = "Table 3", skiprows = 1)

    bua_gva = bua_gva[['Town code', '2020\n']]
    bua_gva.columns = ['BUA22CD', 'total_gva']

    return(bua_gva)


def get_total_gva_by_lsoa(sector=["Total"]):
    
    lsoa_gva = pd.read_csv("Q:/SDU/Mobility/Data/Auxiliary_data/GVA_2020_small_area_NOMIS.csv", encoding="iso-8859-1", skiprows=5)
    lsoa_gva = lsoa_gva.dropna(axis=1, how='all')
    lsoa_gva = lsoa_gva.dropna(axis=0, how='any')

    lsoa_gva.columns = ['lsoa11nm', 'lsoa11cd', 'gva']

    return(lsoa_gva)
