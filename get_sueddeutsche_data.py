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
import dateutil.parser as dparser


def obtain_data(out_folder, start_date, end_date):

    
    website = 'https://www.sueddeutsche.de/'
    newspaper = 'sueddeutsche'
    number_searches = 200
    date_format = '%Y-%m-%d'
    
    def create_url(start_date, end_date, search_page):
        
        if search_page>0:
            orig_url = 'https://www.sueddeutsche.de/news/page/' + str(search_page) + '?search=&sort=date&all%5B%5D=dep&all%5B%5D=typ&all%5B%5D=sys&time='
        else:
            orig_url = 'https://www.sueddeutsche.de/news?search=&sort=date&all%5B%5D=dep&all%5B%5D=typ&all%5B%5D=sys&time='
        start_date_part_one =  start_date + 'T00%3A00%2F' 
        end_date_part_one = end_date + 'T23%3A59&startDate='
        start_date_part_two = str(datetime.strptime(start_date, '%Y-%m-%d').strftime('%d.%m.%Y')) 
        end_date_part_two = '&endDate=' + str(datetime.strptime(end_date, '%Y-%m-%d').strftime('%d.%m.%Y'))
        url = orig_url + start_date_part_one + end_date_part_one + start_date_part_two + end_date_part_two
        return url
   
    
    file_name = out_folder + newspaper + '_from_' + str(start_date) + '_until_' + str(end_date)
    df = pd.DataFrame()
    
    for number_search in range(number_searches):
        print('number_searches ', number_search )
        print('\n')
        
        url = create_url(start_date, end_date, number_search)
        
        # that we dont get kicked out
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
    
        resp = requests.get(url)  # get the website
        soup = BeautifulSoup(resp.text, 'lxml')  # get text from website
        
        with open('out.txt', 'w') as file:
            file.write(soup.prettify())
        
        if len(soup.find_all(class_='entrylist__entry'))==0:  # stop if all articles for that date were found            
            break
        else:
            output = []
            out_entry = []
            for entry in soup.find_all(class_='entrylist__entry'):  # for each article get the relevant information
                item = {
                    'headline': e.text if(e := entry.find(class_='entrylist__title')) else float('nan'),
                    'url': e['href'] if(e:=entry.find(class_='entrylist__link', href=True)) else float('nan'),
                    'newspaper': newspaper,
                    'date_published': dparser.parse(e.text,fuzzy=True).strftime(date_format) if(e := entry.find(class_='entrylist__time')) else float('nan'),
                    
                    # author always contains "von" (from) so we reomove it
                    # different authors are seperated by "und"
                    # also contains place where it was written, last entry after comme (IFF there is a comma)
                }
    
    
                if not isinstance(item['url'], float):  # otherwise its nan
                    topics = []
                    for t in entry.find_all(class_='breadcrumb-list__item'):
                        topic = t.text.replace(' ', '')
                        topic = topic.replace('\n', '')
                        if not topic == 'SZ':
                            topics.append(topic)
                        
                    item['topics'] = list(set(topics))
                    item['channel'] = topics[0]
                    if len(topics)>2:
                        if not topics[0] =='dpa':
                            item['channel'] = topics[0]
                        else:
                            item['channel'] = topics[1]
                    
                    if entry.find(class_='entrylist__author'):
                        e = entry.find(class_='entrylist__author')
                        
                        list_authors = ' '.join(e.text.split(' ')[1:])   # remove "von"
                        list_authors = list_authors.split('und')
                        cleaned_names = []
                        # some contain spaces which shouldnt be there. 
                        for name in list_authors:
                            name = name.split(' ')
                            name = [n for n in name if len(n)>0]
                            if len(name):
                                if name[0] =='von':
                                    del name[0]
                                
                                name = ' '.join(name)
                                name = name.split(',')
                                name = name[0]
                                cleaned_names.append(name)
                        item['author'] = ', '.join(cleaned_names)
                    else:
                        item['author'] = float('nan')
                
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
        if len(name_list):
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
