#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 12:06:50 2022

@author: annika

We collect for different newspaper articles and some metadata for a given time frame. 

Avaiable newspaper so far:
spiegel, taz, sueddeutsche, Zeit

Inputs:
    start and end dates for the time period from when the news articles are
    
Output:
    dataframe. Containing all meta data from the articles:
    - name of newspaper
    - headline of the article
    - date when published
    - url
    - authors name
    - topics (given by newspaper)
    - gender of author from their first names

"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import pickle
from datetime import date, timedelta, datetime
import os

import get_spiegel_data
import get_sueddeutsche_data
import get_zeit_data  # Zeit is with time frame, not dates... time_frame = '30d' # '30d' '1y' , '24h', '7d' and start date always today
import get_taz_data

#%%% Input: Dates and declare some variables
# in order to use the zeit data, it is best to stay in the possible time frames
start_date = datetime.today() - timedelta(days=14) # over last two weeks
start_date = start_date.strftime('%Y-%m-%d')
end_date = datetime.today()# - timedelta(days=30) # last month
end_date = end_date.strftime('%Y-%m-%d')
time_frame = '30d'  # for Zeit

date_format = '%Y-%m-%d'
dict_newspaper_functions = {'taz':get_taz_data, 'sueddeutsche':get_sueddeutsche_data, 
                            'spiegel':get_spiegel_data}#, 'zeit':get_zeit_data}

# dict_newspaper_functions = {'taz':get_taz_data,'spiegel':get_spiegel_data}#, 'zeit':get_zeit_data}
out_folder = 'output/Data/'  # where the data will be stored
if not os.path.exists(out_folder):
    os.makedirs(out_folder)

# path to store the data: 
file_name = out_folder + 'several_newspaper_from_' + str(start_date) + '_until_' + str(end_date)

# %% Collect the data
# for each newspaper we get a dataframe containing all relevant information, including the newspaper's name:

list_dfs = []  # we collect the dfs as list and create a large dataframe afterwards
for newspaper in dict_newspaper_functions:
    print('************************************')
    print('************************************')
    print('                 ' + newspaper)
    print('************************************')
    print('************************************')
    if newspaper=='zeit':
        df = dict_newspaper_functions[newspaper].obtain_data(out_folder, time_frame)
    else:
        df = dict_newspaper_functions[newspaper].obtain_data(out_folder, start_date, end_date)
        
    list_dfs.append(df)

# create the dataframe
df_all_articles = pd.concat(list_dfs)
df_all_articles.reset_index(inplace=True)  # otherwise index can be duplicates

# create dates as strings for later use
df_all_articles['just_date'] = df_all_articles['date_published'].astype(str)
df_all_articles['just_date'] = pd.to_datetime(df_all_articles.just_date, format='%Y-%m-%d')
df_all_articles['just_date'] = pd.to_datetime(df_all_articles['just_date'], errors='coerce', utc=True).dt.date # remove the time, keep only the day
df_all_articles['just_date'] = df_all_articles['just_date'].astype(str)

# replace "nan" in gender with "NoAuthor"
for c in ['gender', 'author']:  # firstNames, gender_list
    df_all_articles[c].fillna('NoAuthor', inplace=True)

# remove empty lines
df_all_articles = df_all_articles.replace(r'\n','', regex=True) 

# remove duplicated rows:
df_all_articles.drop_duplicates(subset = ['headline', 'date_published', 'url', 'author', 'newspaper', 'date_created', 'just_date'], inplace=True)
# print(list(df_all_articles.columns))


# store the dataframe
pickle.dump(df_all_articles, open(file_name+'.pkl', 'wb'))



