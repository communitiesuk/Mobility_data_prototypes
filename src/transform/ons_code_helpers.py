# -*- coding: utf-8 -*-
"""
Created on Thu Feb 16 14:20:07 2023

@author: gordon.donald
"""

import pandas as pd

#Write some code to add in ONS codes to data with names only.
def get_code_column(dataset, flag="[ESWN][0-9]{8}"):
    """Usage: The flag is a substring that we want to identify geography codes. 
    Default is E0, which is the prefix of areas in England, 
    but can be specified otherwise if data isn't at that level."""
    #Note use of groupby here as there was a deprecation warning for all(level=1), suggesting groupby(level=1).all() is safer.
    #But beware that default behaviour of groupby is to sort alphabetically, which we very much don't want!
    col = dataset.columns[dataset.stack().str.contains(flag).groupby(level=1, sort=False).any()]
    if len(col)==0:
        print("ERROR: No columns that look like the contain geography codes found. Checking if the flag entered matches the expected pattern")
    return(col[0])

def check_for_code_column(dataset, flag='E0'):
    """Usage: Find out if we have codes in the df.
        The flag is a substring that we want to identify geography codes. 
    Default is E0, which is the prefix of areas in England, 
    but can be specified otherwise if data isn't at that level."""
    cols = dataset.columns[dataset.stack().str.contains(flag).groupby(level=1, sort=False).any()]
    if len(cols)==0:
        return(0)
    else:
        return(1)
    
lu22 = pd.read_csv("Q:/SDU/SDU_real_time_indicators/data/lookups/names_codes/Local_Authority_Districts_(December_2022)_Names_and_Codes_in_the_United_Kingdom.csv")
lu20 = pd.read_csv("Q:/SDU/SDU_real_time_indicators/data/lookups/names_codes/LAD_(Dec_2020)_Names_and_Codes_in_the_United_Kingdom.csv")
lu19 = pd.read_csv("Q:/SDU/SDU_real_time_indicators/data/lookups/names_codes/LAD_(Dec_2019)_Names_and_Codes_in_the_United_Kingdom.csv")
lu18 = pd.read_csv("Q:/SDU/SDU_real_time_indicators/data/lookups/names_codes/LAD_(Dec_2018)_Names_and_Codes_in_the_United_Kingdom.csv")
lu15 = pd.read_csv("Q:/SDU/SDU_real_time_indicators/data/lookups/names_codes/LAD_(April_2015)_Names_and_Codes_in_the_United_Kingdom.csv")


def what_are_my_LA_names(df, col):
    max_fit=len(df)
    best=df
    for option in [lu22, lu20, lu19, lu18, lu15]:
        lu_col = option.columns[option.columns.str.endswith('NM')][0]
        test = sum(df[col].isin(option[lu_col]))
        if test == len(df):
            print("Found ideal match!")
            return(option)
        if test > max_fit:
            best = option
            max_fit = test
            
    #If this doesn't get something perfect
    print("This matches for ", max_fit, "out of ", len(df), "rows!")
    return best
        

#Quick check -- can we easily find the differences.    
def which_LAs_have_changed(df1, df2):
    col1 = df1.columns[df1.columns.str.endswith('NM')][0]
    col2 = df2.columns[df2.columns.str.endswith('NM')][0]
    
    new = df1[df1[col1].isin(df2[col2])==False]
    old = df2[df2[col2].isin(df1[col1])==False]
    
    changes = new.merge(old, left_on=col1, right_on =col2, how="outer")
    return(changes)

which_LAs_have_changed(lu22, lu20)
which_LAs_have_changed(lu20, lu19)
which_LAs_have_changed(lu19, lu18)
which_LAs_have_changed(lu18, lu15)

