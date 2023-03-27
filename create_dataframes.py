#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 12:31:33 2022

@author: annika

Create different dataframes

We need the number of articles published per day given by gender etc. 

Also, for topics like iran etc. 

"""

   
import pandas as pd
import timeit
import pickle


def original_df(start_date = '2022-9-15', end_date = '2022-11-16', folder_out_data = 'output/Data/', newspaper='Spiegel' ):
    # reads in the data given between the start and end date (if available).
    # if not available, see "get_the_data" function    
    
    # all dates between given dates: 
    date_format = '%Y-%m-%d'

    # read in the data, for this we have to use those dates which were also used to generate the data
    if newspaper=='Spiegel':
        path_data = folder_out_data + 'from_' + start_date +'_until_' + end_date + '_df_all_articles.pkl'
    elif newspaper=='taz':
        path_data = folder_out_data + 'taz_from_' + start_date +'_until_' + end_date + '.pkl'
        
    df_all_articles = pickle.load(open(path_data, 'rb'))
    df_all_articles['just_date'] = pd.to_datetime(df_all_articles.date_published, format='%Y-%m-%d')
    df_all_articles['just_date'] = pd.to_datetime(df_all_articles['just_date'], errors='coerce', utc=True).dt.date # remove the time, keep only the day
    df_all_articles['just_date'] = df_all_articles['just_date'].astype(str)
   
    for c in ['gender', 'author']:  # firstNames, gender_list
        df_all_articles[c].fillna('NoAuthor', inplace=True)

    return df_all_articles
    

def percentage_df(df_all_articles, hue_order_noNoAuthor=['name unclear', 'both', 'M', 'F']):
    # # create from given df number of published articles and percentage wrt gender
    
    # percentage for the whole time given: 
    df_count_channel = df_all_articles.groupby(['channel', 'gender', 'newspaper']).count()
    df_count_channel.reset_index(inplace=True)
    df_count_channel['count'] = df_count_channel['just_date']  # contains the number of times a gender published an article in a channel in the newspaper
    df_count_channel = df_count_channel[['channel', 'gender', 'newspaper','count']]
    df_count_channel['percentage'] = df_count_channel['count']
    
    # noNoAuthpr removes articles which are not written by an author but just a press release like dpa
    df_count_channel_noNoAuthor = df_count_channel[df_count_channel['gender'].isin(hue_order_noNoAuthor)]
    
    for newspaper in list(set(df_count_channel['newspaper'])):
        for channel in df_count_channel_noNoAuthor['channel']:
            sum_articles = df_count_channel_noNoAuthor[(df_count_channel_noNoAuthor['channel']==channel)&(df_count_channel_noNoAuthor['newspaper']==newspaper)]['count'].sum()  # all articles published in this channel
            df_count_channel_noNoAuthor.loc[(df_count_channel_noNoAuthor['channel']==channel)&(df_count_channel_noNoAuthor['newspaper']==newspaper),'percentage'] = df_count_channel_noNoAuthor.loc[(df_count_channel_noNoAuthor['channel']==channel)&(df_count_channel_noNoAuthor['newspaper']==newspaper)]['count']/sum_articles
            
            sum_articles = df_count_channel[(df_count_channel['channel']==channel)&(df_count_channel_noNoAuthor['newspaper']==newspaper)]['count'].sum()  # all articles published in this channel
            df_count_channel.loc[(df_count_channel['channel']==channel)&(df_count_channel_noNoAuthor['newspaper']==newspaper),'percentage'] = df_count_channel.loc[(df_count_channel['channel']==channel)&(df_count_channel_noNoAuthor['newspaper']==newspaper)]['count']/sum_articles

    # percentage for the each day given: 
    df_count_channel_days = df_all_articles.groupby(['channel', 'gender', 'just_date', 'newspaper']).count()
    df_count_channel_days.reset_index(inplace=True)
    df_count_channel_days['count'] = df_count_channel_days['index'] 
    df_count_channel_days = df_count_channel_days[['channel', 'gender', 'newspaper', 'just_date', 'count']]
    
    all_dates = list(set(df_count_channel_days['just_date']))
    
    
    # noNoAuthpr removes articles which are not written by an author but just a press release like dpa
    df_count_channel_noNoAuthor_days = df_count_channel_days[df_count_channel_days['gender'].isin(hue_order_noNoAuthor)]
    day = all_dates[0]
    
    for newspaper in list(set(df_count_channel_noNoAuthor_days['newspaper'])):
        for channel in df_count_channel_noNoAuthor_days['channel']:
            for day in all_dates:
                sum_articles = df_count_channel_noNoAuthor_days[(df_count_channel_noNoAuthor_days['channel']==channel)&(df_count_channel_noNoAuthor_days['just_date']==day)&(df_count_channel_noNoAuthor_days['newspaper']==newspaper)]['count'].sum()  # all articles published in this channel
                df_count_channel_noNoAuthor_days.loc[(df_count_channel_noNoAuthor_days['channel']==channel)&(df_count_channel_noNoAuthor_days['just_date']==day)&(df_count_channel_noNoAuthor_days['newspaper']==newspaper),'percentage'] = df_count_channel_noNoAuthor_days.loc[(df_count_channel_noNoAuthor_days['channel']==channel)&(df_count_channel_noNoAuthor_days['just_date']==day)&(df_count_channel_noNoAuthor_days['newspaper']==newspaper)]['count']/sum_articles
                
                sum_articles = df_count_channel_days[(df_count_channel_days['channel']==channel)&(df_count_channel_days['just_date']==day)&(df_count_channel_noNoAuthor_days['newspaper']==newspaper)]['count'].sum()  # all articles published in this channel
                df_count_channel_days.loc[(df_count_channel_days['channel']==channel)&(df_count_channel_days['just_date']==day)&(df_count_channel_noNoAuthor_days['newspaper']==newspaper),'percentage'] = df_count_channel_days.loc[(df_count_channel_days['channel']==channel)&(df_count_channel_days['just_date']==day)&(df_count_channel_noNoAuthor_days['newspaper']==newspaper)]['count']/sum_articles
    
    
    return df_count_channel, df_count_channel_noNoAuthor, df_count_channel_days, df_count_channel_noNoAuthor_days



def df_for_given_buzzwords(df_all_articles, buzz_words, hue_order_noNoAuthor=['name unclear', 'both', 'M', 'F']):
    
    list_df_topics = []
    for newspaper in list(set(df_all_articles['newspaper'])):
        df_to_use = df_all_articles[df_all_articles['newspaper']==newspaper]
        # look for topics, where a gender is overrepresnted
        all_topics_ = [item for item in list(df_to_use['topics']) if item==item]  # to remove nans
        topics = [item for sublist in all_topics_ for item in sublist]  # it is usually a list, thus we have to create a flat list out of the list of lists

        # check if words or part of it are in:
        words_in_topics = []
        topics_in_words = []
        for topic in topics:
            for word in buzz_words:
                if word.upper() in topic.upper():
                    words_in_topics.append(word)
                    topics_in_words.append(topic)
                
        # plot for these topics:
        index_topics = []
        for index in df_to_use.index:
            if df_to_use.loc[index]['topics']==df_to_use.loc[index]['topics']:  # check if nan
                if isinstance(df_to_use.loc[index]['topics'], list):
                    for topic in df_to_use.loc[index]['topics']:
                        if topic in topics_in_words:
                            index_topics.append(index)
                else:
                    if topic in df_to_use.loc[index]['topics']:
                        index_topics.append(index)
    
        list_df_topics.append(df_to_use.loc[index_topics])
    
    df_buzz_topics = pd.concat(list_df_topics)
    df_buzz_topics.reset_index(inplace=True)
    
    return df_buzz_topics



def df_add_given_buzzwords(df, buzz_words, name_buzzword):

    # look for topics, where a gender is overrepresnted
    topics = list(set([item for sublist in df['topics'] for item in sublist]))
    
    df[name_buzzword] = 0
    
    # check if words or part of it are in:
    words_in_topics = []
    topics_in_words = []
    for topic in topics:
        for word in buzz_words:
            if word.upper() in topic.upper():
                words_in_topics.append(word)
                topics_in_words.append(topic)
            
    # plot for these topics:
    index_topics = []
    for index in df.index:
        if isinstance(df.loc[index]['topics'], list):
            for topic in df.loc[index]['topics']:
                if topic in topics_in_words:
                    df.loc[index,name_buzzword] = 1
        else:
            if topic in df.loc[index]['topics']:
                df.loc[index,name_buzzword] = 1
    
    return df
    
