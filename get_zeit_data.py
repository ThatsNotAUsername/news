#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 12:06:50 2022

@author: annika
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import pickle
from datetime import date, timedelta, datetime
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def obtain_data(out_folder, time_frame):

      
    # time_frame = '30d' # '30d' '1y' , '24h', '7d'
    orig_url = 'https://www.zeit.de/suche/index?q=&mode=' + time_frame + '&type=article&type=gallery&type=video&type=author&type=manualtopic'

    website = 'https://zeit.de'
    newspaper = 'zeit'
    number_searches = 5000
    date_format = '%Y-%m-%d'
    
    end_date = datetime.today().strftime('%Y-%m-%d')
    if time_frame == '24h':
        start_date = date.today() + timedelta(days=1)
    elif time_frame == '7d':
        start_date = date.today() + timedelta(days=7)
    elif time_frame == '30d':
        start_date = date.today() + timedelta(days=30)
    elif time_frame == '1y':
        start_date = date.today() + timedelta(days=365)
    
    start_date = start_date.strftime('%Y-%m-%d')
    
    file_name = out_folder + newspaper + '_from_' + str(start_date) + '_until_' + str(end_date)
    df = pd.DataFrame()
    number_search=0  
    for number_search in range(number_searches):
        print('number_searches ', number_search )
        print('\n')
        if number_search==0:
            url = orig_url 
        else:
            url = orig_url  + '&p=' + str(number_search)
          
        # that we dont get kicked out
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
            
        resp = requests.get(url)  # get the website
        soup = BeautifulSoup(resp.text, 'lxml')  # get text from website
        if len(soup.find_all(class_='zon-teaser-standard'))==0:  # stop if all articles for that date were found            
            break
        else:
            output = []
            out_entry = []
            for entry in soup.find_all(class_='zon-teaser-standard'):  # for each article get the relevant information
                item = {
                    'headline': e[0]['title'] if(e := entry.find_all('a', title=True)) else float('nan'),
                    'url': e[0]['href'] if(e:=entry.find_all('a', href=True)) else float('nan'),
                    'newspaper': newspaper,
                    'channel': e.text if(e := entry.find(class_='zon-teaser-standard__kicker')) else float('nan'),
                    
                }
    
                if not isinstance(item['url'], float):  # otherwise its nan
                
                    session = requests.Session()
                    retry = Retry(connect=3, backoff_factor=0.5)
                    adapter = HTTPAdapter(max_retries=retry)
                    session.mount('http://', adapter)
                    session.mount('https://', adapter)
                    
                    article = requests.get(item['url'])  # get the website
                    article_soup = BeautifulSoup(article.text, 'lxml')  # get text from website

                    tags = article_soup.find_all("meta")
                    topics = float('nan')
                    date_published = float('nan')
                    name = float('nan')
                    for tag in tags:
                        if tag.get('name',None)=='keywords':
                            topics = tag['content'].split(',')
                        if tag.get('name',None)=='date':
                            date_published = datetime.fromisoformat(tag['content']).strftime(date_format)
                        if tag.get('property',None)=='article:author':
                            t = tag['content'].split('_')
                            if len(t)>1:
                                name = t[0].split('/')[-1] + ' ' + t[1].split('/')[0]
                            else:
                                name = t[0].split('/')[-1]
                item['topics'] = topics
                item['author'] = name
                item['date_published'] = date_published
                out_entry.append(entry)
                output.append(item)
            df = pd.concat([df, pd.DataFrame(output)], ignore_index=True)
    
        pickle.dump(df, open(file_name+'.pkl', 'wb'))
    
    # %% names and gender
    path_names = '../../Daten/Names/wgnd_langctry.tab'
    df_names = pd.read_csv(path_names, delimiter='\t')  
    
    # add gender of authors.
    # to do so, we first get all the fist names, then map them to the genders given 
    # by list and add those to the dataframe
    
    all_names = list(set(df['author']))  # all combinations of names
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
    
    df['gender'] = df['author']
    df['gender'].replace(dict_name2gender,inplace=True)
    
    pickle.dump(df, open(file_name+'.pkl', 'wb'))
    
    return df
