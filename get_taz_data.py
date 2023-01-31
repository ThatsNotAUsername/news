#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 12:06:50 2022

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

def obtain_data(out_folder, start_date, end_date):
        
    orig_url = 'https://taz.de/!s=&eTagAb='
    
    website = 'https://taz.de'
    newspaper = 'taz'
    date_format = '%d.\u2009%m.\u2009%Y, %H:%M Uhr'  # date format of taz
    
    delta = datetime.strptime(end_date, '%Y-%m-%d').date() - datetime.strptime(start_date, '%Y-%m-%d').date()  # days of the given time frame
    
    file_name = out_folder + newspaper + '_from_' + str(start_date) + '_until_' + str(end_date)
    df = pd.DataFrame()
    for i in range(delta.days + 1):
        day = datetime.strptime(start_date, '%Y-%m-%d').date() + timedelta(days=i)  # day we get the articles from
       
        for number_searches in range(300):
            print('number_searches ', number_searches )
            print('day ', day )
            print('\n')
            if number_searches==0:  # first result page has a bit different url
                url = orig_url  + str(day) + '/'
            else:
                url = orig_url  + str(day)  + '/' + '?search_page=' + str(number_searches)
            
            # that we dont get kicked out
            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter) 
             
            resp = requests.get(url)  # get the website
            soup = BeautifulSoup(resp.text, 'lxml')  # get text from website
    
            if len(soup.find_all(class_='report'))==0:  # stop if all articles for that date were found            
                break
            else:
                output = []
                out_entry = []
                # fill our dictionary with meta data on the article
                for entry in soup.find_all(class_='report'):  # for each article get the relevant information
                    channel = float('nan')
                    t = entry.find_all('p')
                    for a in t:
                        if 'Ressort: ' in a.text:
                            channel = a.text[9:]
                    item = {
                        'headline': e.text if(e := entry.find('h4')) else float('nan'),
                        'date_published': e.text if(e := entry.find(class_='date')) else float('nan'),
                        'url': e[-1]['href'] if(e:=entry.find_all('a', href=True)) else float('nan'),
                        'author': e.text if(e := entry.find(class_="author")) else float('nan'),
                        'newspaper': newspaper,
                        'channel': channel
                    }
                    if not isinstance(item['date_published'], float):  # otherwise its nan
                    
                        item['date_published'] = datetime.strptime(item['date_published'],date_format).date()
                        # the topics of the articles are in the text of the website of the article itself. Thus we have to call the website:
                        if not isinstance(item['url'], float):  # otherwise its nan
                            session = requests.Session()
                            retry = Retry(connect=3, backoff_factor=0.5)
                            adapter = HTTPAdapter(max_retries=retry)
                            session.mount('http://', adapter)
                            session.mount('https://', adapter) 
                        
                        
                            article = requests.get(website + item['url'])  # get the website
                            article_soup = BeautifulSoup(article.text, 'lxml')  # get text from website
                            article_entry = article_soup.find_all(class_='tag') # get the topics 
                            
                            list_e = []  # have to find the topics
                            for e in article_entry:
                                list_e.append(e.find_all('span'))
                
                            list_finally = []  # list_e is nested list and not text yet
                            for l in list_e:
                                for l2 in l:
                                    list_finally.append(l2.text)
                            
                            topics = list(set(list_finally))  # unique topics, dont need duplicates
                        item['topics'] = topics
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

