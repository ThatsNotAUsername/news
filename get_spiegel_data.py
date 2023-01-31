#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 13 11:54:03 2022

@author: annika

Get data from newspaper and store them. 
So far only Spiegel

data is stored as dataframe at:
    
folder_out_data + 'from_' + start_date +'_until_' + end_date + '_df_all_articles.pkl

"""

# API key for newsapi
# 85252ef44e6a4b18ac21b1c25569477e  
    
    
import spiegel_scraper as spon
import pandas as pd
from datetime import date, timedelta, datetime
import pickle
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def obtain_data(out_folder, start_date, end_date):

    
    # all dates between given dates: 
    date_format = '%Y-%m-%d'
    
   
    # %% names and gender
    path_names = '../../Daten/Names/wgnd_langctry.tab'
    df_names = pd.read_csv(path_names, delimiter='\t')

    # get all articles from 2022, put them in a dataframe wiht columns:
    
    columns = ['newspaper', 'date_published', 'url', 'channel', 'headline', 'topics',
               'author', 'abbreviation']
    
    df_all_articles = pd.DataFrame(columns=columns)
    
    delta = datetime.strptime(end_date, date_format).date() - datetime.strptime(start_date, date_format).date()
    for i in range(delta.days + 1):
        day = datetime.strptime(start_date, date_format).date() + timedelta(days=i)  # day we get the articles from
        archive_entries = spon.archive.by_date(day)  # the articles from that day
        for key in archive_entries:  # dictionary, each key refres to information of the article
            
            article_url = key['url']  # url of the article
            try:
                article = spon.article.by_url(article_url)  # all information I need as a dictionary
                article['newspaper'] = 'Spiegel'  # add newspaper name
                article['abbreviation'] = article['author']['abbreviation']  # some articles do not have authors name but the source (like dpa)
                article['author'] = article['author']['names']  # I only want the authors name. If more than 1 author, it is a list of names
                df_all_articles = df_all_articles.append(article, ignore_index=True)  # add information as row to the dataframe
            except:
                pass
    
    df_all_articles['author'] = [','.join(map(str, l)) for l in df_all_articles['author']]
    df_all_articles['author'] = df_all_articles['author'].apply(lambda y: np.nan if len(y)==0 else y)
    
    all_names = list(set(df_all_articles['author']))  # all combinations of names
    all_names = [x for x in all_names if x==x ] # remove nans
    
    # create dictionary of first names to gender: 
    dict_name2gender = {}
    dict_name2gender_list = {}
    dict_name2firstnames = {}
        
    for name_list in all_names:
        first_list = []
        gender_list = []
        for name in name_list.split(','):
            first_name = name.split(' ')[0]
            if first_name == '':  # if space is at first name
                first_name = name.split(' ')[1]

            first_list.append(first_name)
            gender = list(set(df_names[df_names['name']==first_name.upper()]['gender']))
            if len(gender)==1:
                gender_list.append(gender[0])
            else:
                gender_list.append('name unclear')    
        dict_name2gender_list[name_list] = gender_list
        if len(set(gender_list))==1:
            dict_name2gender[name_list]= gender_list[0]
        else:
            dict_name2gender[name_list] = 'both'
        dict_name2firstnames[name_list] = first_list
    
    df_all_articles['gender'] = df_all_articles['author']
    df_all_articles['gender'].replace(dict_name2gender,inplace=True)
    
    pickle.dump(df_all_articles, open(out_folder + 'from_' + start_date +'_until_' + end_date + '_df_all_articles.pkl', 'wb'))
    
    
    return df_all_articles




