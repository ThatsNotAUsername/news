#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 12:07:02 2022

@author: annika

Analyze data collected from different newspaper. 
We check how many articles are published in which topics and the gender of the 
authors. 

We have a deeper look into a given topic (for example "Afghanistan")

Inputs:
    - a dataframe containing meta data of published newsarticles. Can use the 
    function 'get_news_data' for that
    - time frame (defined by the data probably). Will be declared in this function
    - topic.  Will be declared in this function
    
Outputs: 
    - figures in folder 'output'

"""
   
import spiegel_scraper as spon
import pandas as pd
from datetime import date, timedelta, datetime
from wordcloud import WordCloud
import os
from matplotlib import pyplot as plt
import pickle
import seaborn as sns
import numpy as np
import timeit
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import create_dataframes

# %% declare dates
date_format = '%Y-%m-%d'
# start_date = datetime.today() - timedelta(days=30) # over last month
# start_date = start_date.strftime(date_format)
# end_date = datetime.today()# - timedelta(days=30) # last month
# end_date = end_date.strftime(date_format)
# time_frame = '30d'  # for Zeit

start_date = '2022-11-15'
end_date = '2022-12-15'
# start_date = '2022-10-17'
# end_date = '2022-11-16'

# start_date = '2022-11-15'  # datetime.today() - timedelta(days=1) # yesterday
# # start_date = start_date.strftime('%Y-%m-%d')
# end_date = '2022-12-15'  # datetime.today().strftime('%Y-%m-%d')  # today

# %%% data location and name:

folder_out_data = 'output/Data/'       
file_name = folder_out_data + 'several_newspaper_from_' + str(start_date) + '_until_' + str(end_date) + '.pkl'
df_all_articles = pickle.load(open(file_name, 'rb'))
df_all_articles = df_all_articles.replace(r'\n','', regex=True) 
df_all_articles = df_all_articles.replace(r'"','', regex=True) 
df_all_articles = df_all_articles.replace(r"'",'', regex=True) 
df_all_articles = df_all_articles.replace(r"'",'', regex=True) 
df_all_articles['just_date'].dropna(inplace=True)
df_all_articles = df_all_articles[df_all_articles['just_date'] != 'NaT']
df_all_articles = df_all_articles[df_all_articles['just_date'] >= start_date]
df_all_articles = df_all_articles[df_all_articles['just_date'] <= end_date]
df_all_articles.reset_index(inplace=True, drop=True)
if 'index' in df_all_articles.columns:
    df_all_articles.drop(labels='index', axis=1, inplace=True)

# clean dates, remove all which are not in the given time frame: 
dates = set(df_all_articles['just_date'])

names_newspaper = list(set(df_all_articles['newspaper']))

#  how many dates shown on x-axis of the figures
number_dates_show = np.round(len(set(df_all_articles['just_date'])))
if number_dates_show > 20:
    number_dates_show =20  # show every 20th date on xaxis
else:
    number_dates_show =1  # show each date on xaxis

# %% which topic is analyzed: 
thema = 'iran'
buzz_words = ['Iran', 'Mullahs', 'Masha Amini', 'Mahsa', 'Amini', 'Jina', 'Jina Amini', 'Kopftuch', 'Haare', 'Islam']
interesting_channels = ['Wirtschaft und Umwelt', 'Wirtschaft', 'International','Ausland', 'Politik']

# thema = 'afghanistan'
# buzz_words = ['Afghanistan', 'Taliban', 'Kabul']
# interesting_channels = ['Wirtschaft und Umwelt', 'Wirtschaft', 'International','Ausland', 'Politik']

# thema = 'abtreibung'
# buzz_words = ['Abtreibung', 'Roe v Wade', 'Roe v. Wade', 'Roe vs Wade', 'Roe vs. Wade', '§ 219a', '§219a', '§ 219', '§219']
# interesting_channels = ['Wirtschaft und Umwelt', 'Wirtschaft', 'International','Ausland', 'Politik', 'Panomara']

# thema = 'metoo'
# buzz_words = ['metoo','#metoo', 'Weinstein', 'Milano', 'me too']
# # interesting_channels = ['Wirtschaft', 'International','Ausland', 'Politik']
# interesting_channels = ['Wirtschaft und Umwelt', 'International','Ausland', 'Politik','Netzwelt', 'Panorama', 'Kultur']  #taz

# thema = 'metoo'
# buzz_words = ['metoo','#metoo', 'Weinstein', 'Milano', 'me too']
# interesting_channels = ['International','Ausland', 'Politik', 'Netzwelt', 'Panorama', 'Kultur']

# set colors:
dict_colors_gender = {'F':'indianred', 'M':'lightskyblue', 'both':'khaki', 'name unclear':'darkseagreen', 'NoAuthor':'thistle'}

# categories (or resorts?)), like "sports", 'politics'
channels = list(set(df_all_articles['channel']))
number_channels = len(channels)

# %% create some output folders:
folder_figures = 'output/figures/several_newspaper_' + thema + '_from_' + start_date +'_until_' + end_date + '/'
if not os.path.exists(folder_figures):
    os.mkdir(folder_figures)
    
folder_wordclouds = folder_figures + 'wordclouds/'
if not os.path.exists(folder_wordclouds):
    os.mkdir(folder_wordclouds)
    
folder_histplots = folder_figures + 'histplots/'
if not os.path.exists(folder_histplots):
    os.mkdir(folder_histplots)

folder_lineplots = folder_figures + 'lineplots/'
if not os.path.exists(folder_lineplots):
    os.mkdir(folder_lineplots)
    
folder_piecharts = folder_figures + 'piecharts/'
if not os.path.exists(folder_piecharts):
    os.mkdir(folder_piecharts)

# %% x-axis lables often too many and we want them rotated
def prep_xaxis(ax, n=number_dates_show):
    # n = 20; Keeps every nth label
    [l.set_visible(False) for (i,l) in enumerate(ax.xaxis.get_ticklabels()) if i % n != 0]
    
    # rotate ticks, better readible
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    
    # remove ticks (annoying, looks ugly)
    ax.tick_params(axis=u'both', which=u'both',length=0)
    # increase fontsize
    ax.xaxis.label.set_size(fontsize=14)  
    
# %% wordclouds figure
def generate_wordcloud(text, figure_name): 
    text = ' '.join(text)  # create string from list
    wordcloud = WordCloud(width=1600, height=800,
                           relative_scaling = 0.2,
                           stopwords = {'gegen', ' ', 'Ukraine', 'Russland', 'die', 'der', 'das', 'Die', 'am', 'in', 'und', 'Landkreis'} # set or space-separated string
                          ).generate(text)
    
    plt.axis('off')
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(figure_name)

# word cloud for topics
all_topics_ = [item for item in list(df_all_articles['topics']) if item==item]  # to remove nans
all_topics = [item for sublist in all_topics_ for item in sublist]  # it is usually a list, thus we have to create a flat list out of the list of lists

remove_wordcloud_words = ['dpa', 'Landkreis']

generate_wordcloud(text=all_topics, figure_name=folder_wordclouds + "WordCloud_topics.png")

for newspaper in names_newspaper:
    all_topics_ = [item for item in list(df_all_articles[df_all_articles['newspaper']==newspaper]['topics']) if item==item]  # to remove nans
    all_topics = [item for sublist in all_topics_ for item in sublist if not item in remove_wordcloud_words]  # it is usually a list, thus we have to create a flat list out of the list of lists
    generate_wordcloud(text=all_topics, figure_name=folder_wordclouds + "WordCloud_topics_" + newspaper + ".png")

# word cloud for author's first names
authors_first_names = []
for author in df_all_articles['author']:
    all_names = author.split(', ')  # names are sperated by comma and a space
    if len(author)>0:
        # all_names = author[0].split(', ')  # names are sperated by comma and a space
        for name in all_names:
            first_name = name.split(' ')[0]
            first_name.replace(" ", "")
            if not first_name=='NoAuthor':
                authors_first_names.append(first_name)
generate_wordcloud(text=authors_first_names, figure_name=folder_wordclouds + "WordCloud_firstNames.png")

for newspaper in names_newspaper:
    authors_first_names = []
    # authors = list(set(list(df_all_articles['author'])))
    for author in df_all_articles[df_all_articles['newspaper']==newspaper]['author']:
        all_names = author.split(', ')  # names are sperated by comma and a space
        if len(author)>0:
            # all_names = author[0].split(', ')  # names are sperated by comma and a space
            for name in all_names:
                first_name = name.split(' ')[0]
                first_name.replace(" ", "")
                if not first_name=='NoAuthor':
                    authors_first_names.append(first_name)
    generate_wordcloud(text=authors_first_names, figure_name=folder_wordclouds + "WordCloud_firstNames_" + newspaper + ".png")

# %% Histplot for each channel: x-axis days, y-axis: number articles published, colors: gender of author
hue_order=['name unclear', 'NoAuthor', 'both', 'M', 'F']  # differentiate between the genders. NoAuthor means it is from an agency like DPA
hue_order_noNoAuthor=['name unclear', 'both', 'M', 'F']  # remove the articles from the agency, since they are not written by people


fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
sns.histplot(df_all_articles, x="just_date", hue="gender", hue_order=hue_order, multiple='stack', palette=dict_colors_gender)#'Set2')#  stack the different values for genders
prep_xaxis(ax,n=number_dates_show) # show only 20th xlabel
plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen', fontsize=12)  # title
plt.tight_layout()  # make the figure, such that you can see everything
# save figure
plt.savefig(folder_histplots + 'number_articles_published.png')
plt.close()


#remove No Author
fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
sns.histplot(df_all_articles, x="just_date", hue="gender", hue_order=hue_order_noNoAuthor, multiple='stack', palette=dict_colors_gender)#  stack the different values for genders
prep_xaxis(ax,n=number_dates_show) # show only 20th xlabel
plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen', fontsize=12)  # title
plt.tight_layout()  # make the figure, such that you can see everything
# save figure
plt.savefig(folder_histplots + 'number_articles_published_noNoAuthor.png')
plt.close()

# divided by newspapers
fig, axs = plt.subplots(nrows=len(names_newspaper), figsize=(6, 16))  # for each channel one plot
for i, newspaper in enumerate(names_newspaper):
    if i==0:
        legend=True  # only want the legend once. 
    else:
        legend=None
    df_to_use = df_all_articles[df_all_articles['newspaper']==newspaper]  # use only dataframe part which belongs to the current channel
    sns.histplot(df_to_use, x="just_date", hue="gender", hue_order=hue_order, multiple='stack', palette=dict_colors_gender,ax=axs[i], legend=legend)#  stack the different values for genders
    axs[i].set_ylabel(newspaper)  # ylabel is name of the channel
    plt.tight_layout()  # make the figure, such that you can see everything
plt.title('Anteil veröffentlichter Artikel', fontsize=12)  # title

# save figure
plt.savefig(folder_histplots + 'number_articles_published_separeted_by_newspaper.png')
plt.close()

# put dates together, since too few articles

fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
sns.histplot(df_all_articles, x="channel", hue="gender", hue_order=hue_order, multiple='stack', palette=dict_colors_gender)
prep_xaxis(ax,n=1)
plt.title('Anteil veröffentlichter Artikel', fontsize=12)  # title
plt.tight_layout()  # make the figure, such that you can see everything
# save figure
plt.savefig(folder_histplots + 'number_articles_published_channels.png')
plt.close()

#remove No Author
fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
sns.histplot(df_all_articles, x="channel", hue="gender", hue_order=hue_order_noNoAuthor, multiple='stack', palette=dict_colors_gender)#, element="step")
prep_xaxis(ax,n=1)
plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen', fontsize=12)  # title
plt.tight_layout()  # make the figure, such that you can see everything
# save figure
plt.savefig(folder_histplots + 'number_articles_published_channels_noNoAuthor.png')
plt.close()

# %% pie and tree charts

# have to define the figure for thepie charts beforehand:
specs = [[{'type':'domain'}, {'type':'domain'}], [{'type':'domain'}, {'type':'domain'}]]  # for eacht pie chart
fig = make_subplots(rows=2, cols=2, specs=specs)
index_row = 1
index_col = 1
for i, newspaper in enumerate(names_newspaper): # create for each newspaper one pie chart
    if i==0:
        legend=True  # only want the legend once. 
    else:
        legend=None
    df_to_use = df_all_articles[df_all_articles['newspaper']==newspaper]  # use only dataframe part which belongs to the current channel
    df_to_use = df_to_use[df_to_use['gender'].isin(['M', 'F', 'both'])] 
    df_to_use_g = df_to_use.groupby(['gender', 'channel']).size()   # count number of channels and publication of gender in this channel
    s = df_to_use['gender'].value_counts()   
    if not 'both' in s.index:
        s=s.append(pd.Series([0], index=['both']))
    s.sort_index(inplace=True)
    
    colors_use = [dict_colors_gender[key] for key in s.index]
    
    fig.add_trace(go.Pie(labels=s.index, values=s, name=newspaper, title=newspaper, marker_colors=colors_use), index_row, index_col)
    index_col+=1
    if index_col>2:
        index_col=1
        index_row+=1
    
fig.update_layout(title='Anteil veröffentlichter Artikel unterteilt nach Geschlecht', font=dict(size=15))
fig.write_image(folder_piecharts + 'piechart_articles_published_separeted_by_newspaper.png') 


# nested pie chart and tree maps. Content of nested pie chart and treemap is the same

# have to define the figure for the pie charts beforehand:
specs = [[{'type':'domain'}, {'type':'domain'}], [{'type':'domain'}, {'type':'domain'}]]  # for eacht pie chart
fig = make_subplots(rows=2, cols=2, specs=specs)  # nested piechart
fig2 = make_subplots(rows=2, cols=2, specs=specs, subplot_titles=tuple(names_newspaper))  # nested tree map
index_row = 1
index_col = 1
for i, newspaper in enumerate(names_newspaper):
    if i==0:
        legend=True  # only want the legend once. 
    else:
        legend=None
    
    df_to_use = df_all_articles[df_all_articles['newspaper']==newspaper]  # use only dataframe part which belongs to the current channel
    df_to_use = df_to_use[df_to_use['gender'].isin(['M', 'F', 'both'])] 
    df_to_use_g = df_to_use.groupby(['gender', 'channel']).size()   # count number of channels and publication of gender in this channel
    df_to_use_g = df_to_use_g.reset_index()
    
    for gender in ['M', 'F', 'both']:  # otherwise the colors will change
        if not gender in df_to_use_g['gender']:
            df_to_use_g = pd.concat([df_to_use_g, pd.DataFrame([[gender, 'ignore', 0]], columns = ['gender', 'channel',0])])
    
    df_to_use_g.sort_values(by='gender', axis=0,inplace=True)

    sb = px.sunburst(df_to_use_g, path=['gender', 'channel'], values=0, color='gender', title=newspaper,width=750, height=750, color_discrete_map=dict_colors_gender)#, color_discrete_map=px.colors.qualitative.Dark2)#, color_discrete_map=px.colors.qualitative.Safe) 
    
    tm = px.treemap(df_to_use_g, path=['gender', 'channel'], values=0, color='gender', title=newspaper,width=750, height=750, color_discrete_map=dict_colors_gender)
    
    fig.add_trace(sb.data[0], index_row, index_col)
  
    fig2.add_trace(tm.data[0], index_row, index_col)
    index_col+=1
    if index_col>2:
        index_col=1
        index_row+=1
    
    sb.write_image(folder_piecharts + newspaper + '_piechart_articles_published_separeted_by_newspaper_and_topics.png')
    tm.write_image(folder_piecharts + newspaper + '_treemap_articles_published_separeted_by_newspaper_and_topics.png')

fig.update_layout(title='Anteil veröffentlichter Artikel unterteilt nach Geschlecht', font=dict(size=15))
fig.write_image(folder_piecharts + 'piechart_articles_published_separeted_by_newspaper_and_topics.png') 

fig2.update_layout(title='Anteil veröffentlichter Artikel unterteilt nach Geschlecht', font=dict(size=15))
fig2.write_image(folder_piecharts + 'treemap_articles_published_separeted_by_newspaper_and_topics.png') 



# %% count per day and percentage:
df_all_articles['index'] = df_all_articles.index
# create dataframe (add percentage and number columns):
df_count_channel, df_count_channel_noNoAuthor, df_count_channel_days, df_count_channel_noNoAuthor_days = create_dataframes.percentage_df(df_all_articles, hue_order_noNoAuthor=hue_order_noNoAuthor)

# create figure for each newspape
for newspaper in names_newspaper:
    df_to_use = df_count_channel_noNoAuthor[df_count_channel_noNoAuthor['newspaper']==newspaper]
    genders_in_use = list(set(df_to_use['gender']))
    
    for gender in hue_order_noNoAuthor:  # otherwise the colors will change
        if not gender in df_to_use['gender']:
            df_to_use = pd.concat([df_to_use, pd.DataFrame([['ignore',gender, newspaper, 0, 0]], columns = ['channel', 'gender', 'newspaper' , 'count', 'percentage'])])
    
    df_p = df_to_use.pivot(index='channel', columns=['gender'])['percentage']
    df_p.reset_index(inplace=True)
    df_p.sort_values(by='F',axis=0, inplace=True, ascending=True)
    fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width

    df_p.plot(x='channel', y=hue_order_noNoAuthor, kind='bar', stacked=True, color=dict_colors_gender,alpha=.6)

    plt.legend(loc=(1.04, 0.3), fancybox=True, shadow=True)
    plt.title('Anteil veröffentlichter Artikel (ohne DPA) in ' + newspaper, fontsize=12)  # title
    plt.tight_layout()  # make the figure, such that you can see everything
    # save figure
    plt.savefig(folder_histplots + newspaper + '_number_articles_published_channels_noNoAuthor_percent.png')
    plt.close()

# %% Same thing as above, but using only articles related to the given topic

# create dataframe containing all information about the articles containing the buzz words in their topic list
df_given_topics = create_dataframes.df_for_given_buzzwords(df_all_articles=df_all_articles,buzz_words=buzz_words, hue_order_noNoAuthor=hue_order_noNoAuthor)

# create figure:
fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
sns.histplot(df_given_topics, x="channel", hue="gender", hue_order=hue_order, multiple='stack', palette=dict_colors_gender)#, element="step")
prep_xaxis(ax,n=1)
plt.title('Anteil veröffentlichter Artikel zu ' + thema, fontsize=12)  # title
plt.tight_layout()  # make the figure, such that you can see everything
# save figure
plt.savefig(folder_histplots + 'number_articles_published_channels_' + thema + 'Topics.png')
plt.close()

#remove No Author
fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
sns.histplot(df_given_topics, x="channel", hue="gender", hue_order=hue_order_noNoAuthor, multiple='stack', palette=dict_colors_gender)#, element="step")
prep_xaxis(ax,n=1)
plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen zu ' + thema, fontsize=12)  # title
plt.tight_layout()  # make the figure, such that you can see everything
# save figure
plt.savefig(folder_histplots + 'number_articles_published_channels_noNoAuthor_' + thema + 'Topics.png')
plt.close()



specs = [[{'type':'domain'}, {'type':'domain'}], [{'type':'domain'}, {'type':'domain'}]]  # for eacht pie chart
fig = make_subplots(rows=2, cols=2, specs=specs)#, subplot_titles=tuple(names_newspaper))
fig2 = make_subplots(rows=2, cols=2, specs=specs, subplot_titles=tuple(names_newspaper))
index_row = 1
index_col = 1
for i, newspaper in enumerate(names_newspaper):
    if i==0:
        legend=True  # only want the legend once. 
    else:
        legend=None
    
    df_to_use = df_given_topics[df_given_topics['newspaper']==newspaper]  # use only dataframe part which belongs to the current channel
    df_to_use = df_to_use[df_to_use['gender'].isin(['M', 'F', 'both'])] 
    df_to_use_g = df_to_use.groupby(['gender', 'channel']).size()   # count number of channels and publication of gender in this channel
    df_to_use_g = df_to_use_g.reset_index()
    
    for gender in ['M', 'F', 'both']:  # otherwise the colors will change
        if not gender in df_to_use_g['gender']:
            df_to_use_g = pd.concat([df_to_use_g, pd.DataFrame([[gender, 'ignore', 0]], columns = ['gender', 'channel',0])])
    
    df_to_use_g.sort_values(by='gender', axis=0,inplace=True)
    

    sb = px.sunburst(df_to_use_g, path=['gender', 'channel'], values=0, color='gender', title=newspaper + ' zum Thema ' + thema,width=750, height=750, color_discrete_map=dict_colors_gender)#, color_discrete_map=px.colors.qualitative.Dark2)#, color_discrete_map=px.colors.qualitative.Safe) 
    
    tm = px.treemap(df_to_use_g, path=['gender', 'channel'], values=0, color='gender', title=newspaper+ ' zum Thema ' + thema,width=750, height=750, color_discrete_map=dict_colors_gender)
    
    fig.add_trace(sb.data[0], index_row, index_col)
  
    fig2.add_trace(tm.data[0], index_row, index_col)
    index_col+=1
    if index_col>2:
        index_col=1
        index_row+=1
    
    sb.write_image(folder_piecharts + newspaper + '_piechart_articles_published_separeted_by_newspaper_given_Topic.png')
    tm.write_image(folder_piecharts + newspaper + '_treemap_articles_published_separeted_by_newspaper_given_Topic.png')
    
fig.update_layout(title='Anteil veröffentlichter Artikel unterteilt nach Geschlecht zum Thema ' + thema, font=dict(size=15))
fig.write_image(folder_piecharts + 'piechart_articles_published_separeted_by_newspaper_given_Topic.png') 

fig2.update_layout(title='Anteil veröffentlichter Artikel unterteilt nach Geschlecht zum Thema ' + thema, font=dict(size=15))
fig2.write_image(folder_piecharts + 'treemap_articles_published_separeted_by_newspaper_given_Topic.png') 


# %% percentage wise the given topic

df_count_channel_given_topics, df_count_channel_given_topics_noNoAuthor, df_count_channel_given_topics_days, df_count_channel_given_topics_noNoAuthor_days = create_dataframes.percentage_df(df_given_topics, hue_order_noNoAuthor=hue_order_noNoAuthor)

for newspaper in names_newspaper:
    df_to_use = df_count_channel_given_topics_noNoAuthor[df_count_channel_given_topics_noNoAuthor['newspaper']==newspaper]
    genders_in_use = list(set(df_to_use['gender']))
    
    for gender in hue_order_noNoAuthor:  # otherwise the colors will change
        if not gender in df_to_use['gender']:
            df_to_use = pd.concat([df_to_use, pd.DataFrame([['ignore',gender, newspaper, 0, 0]], columns = ['channel', 'gender', 'newspaper' , 'count', 'percentage'])])
    
    df_p = df_to_use.pivot(index='channel', columns=['gender'])['percentage']  # pivoted df for figure
    df_p.reset_index(inplace=True)
    df_p.sort_values(by='F',axis=0, inplace=True, ascending=True)
    fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
    df_p.plot(x='channel', y=hue_order_noNoAuthor, kind='bar', stacked=True, color=dict_colors_gender,alpha=.6)

    plt.legend(loc=(1.04, 0.3), fancybox=True, shadow=True)
    plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen zu' + thema + ' in ' + newspaper, fontsize=12)  # title
    plt.tight_layout()  # make the figure, such that you can see everything
    # save figure
    plt.savefig(folder_histplots + newspaper + '_number_articles_published_channels_noNoAuthor_percent_' + thema + '_topics.png')
    plt.close()


# %% per day, given topic male,  given topic female, all male, all female
# cerate df containing info of  given topic:
channels = list(set(df_count_channel_days['channel']))
# all_dates = list(set(df_count_channel_given_topics_noNoAuthor_days['just_date']))
all_dates = list(set(df_count_channel_noNoAuthor_days['just_date']))

# function to 
def re_do_df(given_df, col_name='just_date', all_weeks=[]):
    given_df = given_df.set_index(col_name)
    if col_name == 'just_date':
        df_new = pd.DataFrame({"just_date":all_dates, "count": 0}).set_index(col_name)
    else:
        df_new = pd.DataFrame({"week":all_weeks, "count": 0}).set_index(col_name)
    df_new["count"]=given_df["count"]
    df_new.fillna(0, inplace=True)
    return df_new


# create figure for each newspaper
for newspaper in names_newspaper:
    df_to_use = df_count_channel_noNoAuthor_days[df_count_channel_noNoAuthor_days['newspaper']==newspaper]
    df_to_use_topics = df_count_channel_given_topics_noNoAuthor_days[df_count_channel_given_topics_noNoAuthor_days['newspaper']==newspaper]
    for channel in interesting_channels: #df_count_channel_days['channel']:
        fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
        
        y_all_female = df_to_use[(df_to_use['channel']==channel)&(df_to_use['gender']=='F')]  # df for females
        y_all_male = df_to_use[(df_to_use['channel']==channel)&(df_to_use['gender']=='M')]  # df for males
        
        y_all_female_given = df_to_use_topics[(df_to_use_topics['channel']==channel)&(df_to_use_topics['gender']=='F')]  # y vector for females and given topic
        y_all_male_given = df_to_use_topics[(df_to_use_topics['channel']==channel)&(df_to_use_topics['gender']=='M')]  # y vector for males and given topic
        
        y_all_female = re_do_df(y_all_female)  # add 0 for days where no article was published at all
        y_all_male = re_do_df(y_all_male)
        y_all_female_given = re_do_df(y_all_female_given)
        y_all_male_given = re_do_df(y_all_male_given)
        
        y_all_female.rename({'count':'females'}, inplace =True, axis=1)
        y_all_male.rename({'count':'males'}, inplace =True, axis=1)
        y_all_female_given.rename({'count':thema + ' females'}, inplace =True, axis=1)
        y_all_male_given.rename({'count': thema + ' males'}, inplace =True, axis=1)
        
        dfs = [y_all_female, y_all_male, y_all_female_given, y_all_male_given]
        df_draw = pd.concat(dfs, join='outer', axis=1)
        df_draw.plot.line()
        prep_xaxis(ax=ax, n=1)
        plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen pro Woche in ' + channel + ' zu ' + thema + ' in ' + newspaper, fontsize=12)  # title
        plt.tight_layout()  # make the figure, such that you can see everything
    
        plt.savefig(folder_lineplots + newspaper + '_' + channel + '_gender_and_' + thema + '_time.png')
        plt.close()

    # same figure, but the interesting channels all together:
    fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
    
    df_to_use = df_count_channel_noNoAuthor_days[df_count_channel_noNoAuthor_days['newspaper']==newspaper]
    df_to_use_topics = df_count_channel_given_topics_noNoAuthor_days[df_count_channel_given_topics_noNoAuthor_days['newspaper']==newspaper]
    
    y_all_female = df_to_use[(df_to_use['channel'].isin(interesting_channels))&(df_to_use['gender']=='F')]
    y_all_male = df_to_use[(df_to_use['channel'].isin(interesting_channels))&(df_to_use['gender']=='M')]
    
    y_all_female_given = df_to_use_topics[(df_to_use_topics['channel'].isin(interesting_channels))&(df_to_use_topics['gender']=='F')]
    y_all_male_given = df_to_use_topics[(df_to_use_topics['channel'].isin(interesting_channels))&(df_to_use_topics['gender']=='M')]
    
    y_all_female = y_all_female.groupby(['just_date', 'gender']).sum()
    y_all_female.reset_index(inplace=True)
    y_all_male = y_all_male.groupby(['just_date', 'gender']).sum()
    y_all_male.reset_index(inplace=True)
    y_all_female_given = y_all_female_given.groupby(['just_date', 'gender']).sum()
    y_all_female_given.reset_index(inplace=True)
    y_all_male_given = y_all_male_given.groupby(['just_date', 'gender']).sum()
    y_all_male_given.reset_index(inplace=True)
    
    y_all_female = re_do_df(y_all_female)
    y_all_male = re_do_df(y_all_male)
    y_all_female_given = re_do_df(y_all_female_given)
    y_all_male_given = re_do_df(y_all_male_given)
    
    y_all_female.rename({'count':'females'}, inplace =True, axis=1)
    y_all_male.rename({'count':'males'}, inplace =True, axis=1)
    y_all_female_given.rename({'count':thema + ' females'}, inplace =True, axis=1)
    y_all_male_given.rename({'count':thema + ' males'}, inplace =True, axis=1)
    
    dfs = [y_all_female, y_all_male, y_all_female_given, y_all_male_given]
    df_draw = pd.concat(dfs, join='outer', axis=1)
    df_draw.plot.line()
    prep_xaxis(ax=ax, n=number_dates_show)
    plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen pro Woche zu ' + thema + ' in ' + newspaper, fontsize=12)  # title
    plt.tight_layout()  # make the figure, such that you can see everything
    
    plt.savefig(folder_lineplots + newspaper + '_most_interesting_channel_gender_and_' + thema + '_time.png')
    plt.close()

# %% same same but with weeks: 
df_count_channel_noNoAuthor_days['week'] = pd.to_datetime(df_count_channel_noNoAuthor_days['just_date']).apply(lambda x: x.weekofyear)
df_count_channel_noNoAuthor_week = df_count_channel_noNoAuthor_days.groupby(['week', 'gender', 'channel', 'newspaper']).sum()
df_count_channel_noNoAuthor_week.reset_index(inplace=True)

df_count_channel_given_topics_noNoAuthor_days['week'] = pd.to_datetime(df_count_channel_given_topics_noNoAuthor_days['just_date']).apply(lambda x: x.weekofyear)
df_count_channel_given_topics_noNoAuthor_week = df_count_channel_given_topics_noNoAuthor_days.groupby(['week', 'gender', 'channel', 'newspaper']).sum()
df_count_channel_given_topics_noNoAuthor_week.reset_index(inplace=True)

all_weeks = list(set(df_count_channel_noNoAuthor_days['week']))
dict_colors_gender['females'] = dict_colors_gender['F']
dict_colors_gender['males'] = dict_colors_gender['M']
dict_colors_gender[thema + ' males'] = 'steelblue'
dict_colors_gender[thema + ' females'] = 'darkred'

for newspaper in names_newspaper:
    df_to_use = df_count_channel_noNoAuthor_week[df_count_channel_noNoAuthor_week['newspaper']==newspaper]
    df_to_use_topics = df_count_channel_given_topics_noNoAuthor_week[df_count_channel_given_topics_noNoAuthor_week['newspaper']==newspaper]
    for channel in interesting_channels: #df_count_channel_days['channel']: 
        fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
    
        y_all_female = df_to_use[(df_to_use['channel']==channel)&(df_to_use['gender']=='F')]
        y_all_male = df_to_use[(df_to_use['channel']==channel)&(df_to_use['gender']=='M')]
        
        y_all_female_given = df_to_use_topics[(df_to_use_topics['channel']==channel)&(df_to_use_topics['gender']=='F')]
        y_all_male_given = df_to_use_topics[(df_to_use_topics['channel']==channel)&(df_to_use_topics['gender']=='M')]
        
        y_all_female = re_do_df(y_all_female, col_name='week', all_weeks=all_weeks)
        y_all_male = re_do_df(y_all_male, col_name='week', all_weeks=all_weeks)
        y_all_female_given = re_do_df(y_all_female_given, col_name='week', all_weeks=all_weeks)
        y_all_male_given = re_do_df(y_all_male_given, col_name='week', all_weeks=all_weeks)
          
        y_all_female.rename({'count':'females'}, inplace =True, axis=1)
        y_all_male.rename({'count':'males'}, inplace =True, axis=1)
        y_all_female_given.rename({'count':thema + ' females'}, inplace =True, axis=1)
        y_all_male_given.rename({'count':thema + ' males'}, inplace =True, axis=1)
        
        dfs = [y_all_female, y_all_male, y_all_female_given, y_all_male_given]
        df_draw = pd.concat(dfs, join='outer', axis=1)
        df_draw.sort_values(by='week', axis=0, inplace=True, ascending=True)
        df_draw.plot.line()
        # df_draw.plot(kind='bar', stacked=True)
        
        prep_xaxis(ax=ax, n=1)
        plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen pro Woche in ' + channel + ' zu ' + thema + ' in ' + newspaper, fontsize=12)  # title
        plt.tight_layout()  # make the figure, such that you can see everything
        plt.savefig(folder_lineplots + newspaper + '_' + channel + '_gender_and_' + thema + '_weeks.png')
        plt.close()
        
        # percentage and stacked:
        fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
        df_draw_percentage = df_draw[['females', 'males']].divide(df_draw[['females', 'males']].sum(axis=1), axis=0)
        df_draw_percentage.sort_values(by='week', axis=0, inplace=True, ascending=True)
        # ['m', 'c']
        df_draw_percentage.plot(kind='bar', stacked=True, color=dict_colors_gender ,alpha=.6)
        plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen pro Woche in ' + channel + ' in ' + newspaper, fontsize=12)  # title
        prep_xaxis(ax=ax, n=1)
        plt.tight_layout()  # make the figure, such that you can see everything
        plt.savefig(folder_histplots +  newspaper + '_' + channel + '_gender_weeks_percentage.png')
        plt.close()
        
# same figure, but the interesting channels all together:
for newspaper in names_newspaper:
    df_to_use = df_count_channel_noNoAuthor_week[df_count_channel_noNoAuthor_week['newspaper']==newspaper]
    df_to_use_topics = df_count_channel_given_topics_noNoAuthor_week[df_count_channel_given_topics_noNoAuthor_week['newspaper']==newspaper]
    
    fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
    
    y_all_female = df_to_use[(df_to_use['channel'].isin(interesting_channels))&(df_to_use['gender']=='F')]
    y_all_male = df_to_use[(df_to_use['channel'].isin(interesting_channels))&(df_to_use['gender']=='M')]
    
    y_all_female_given = df_to_use_topics[(df_to_use_topics['channel'].isin(interesting_channels))&(df_to_use_topics['gender']=='F')]
    y_all_male_given = df_to_use_topics[(df_to_use_topics['channel'].isin(interesting_channels))&(df_to_use_topics['gender']=='M')]
    
    y_all_female = y_all_female.groupby(['week', 'gender']).sum()
    y_all_female.reset_index(inplace=True)
    y_all_male = y_all_male.groupby(['week', 'gender']).sum()
    y_all_male.reset_index(inplace=True)
    y_all_female_given = y_all_female_given.groupby(['week', 'gender']).sum()
    y_all_female_given.reset_index(inplace=True)
    y_all_male_given = y_all_male_given.groupby(['week', 'gender']).sum()
    y_all_male_given.reset_index(inplace=True)
    
    y_all_female = re_do_df(y_all_female, col_name='week', all_weeks=all_weeks)
    y_all_male = re_do_df(y_all_male, col_name='week', all_weeks=all_weeks)
    y_all_female_given = re_do_df(y_all_female_given, col_name='week', all_weeks=all_weeks)
    y_all_male_given = re_do_df(y_all_male_given, col_name='week', all_weeks=all_weeks)
    
    
    y_all_female.rename({'count':'females'}, inplace =True, axis=1)
    y_all_male.rename({'count':'males'}, inplace =True, axis=1)
    y_all_female_given.rename({'count':thema + ' females'}, inplace =True, axis=1)
    y_all_male_given.rename({'count':thema + ' males'}, inplace =True, axis=1)
    
    dfs = [y_all_female, y_all_male, y_all_female_given, y_all_male_given]
    df_draw = pd.concat(dfs, join='outer', axis=1)
    df_draw.sort_values(by='week', axis=0, inplace=True, ascending=True)
    df_draw.plot.line()
    prep_xaxis(ax=ax, n=1)
    plt.tight_layout()  # make the figure, such that you can see everything
    
    plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen pro Woche in wichtigen Resorts zu ' + thema + ' in ' + newspaper, fontsize=12)  # title
    
    plt.savefig(folder_lineplots + newspaper + '_most_interesting_channel_gender_and_' + thema + '_week.png')
    plt.close()

    
     
    # percentage and stacked:
    fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
    df_draw_percentage = df_draw[['females', 'males']].divide(df_draw[['females', 'males']].sum(axis=1), axis=0)
    df_draw_percentage.sort_values(by='week', axis=0, inplace=True, ascending=True)
    df_draw_percentage.plot(kind='bar', stacked=True, color=dict_colors_gender,alpha=.6)
    plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen pro Woche in wichtigen Resorts', fontsize=12)  # title
    prep_xaxis(ax=ax, n=1)
    plt.tight_layout()  # make the figure, such that you can see everything
    plt.savefig(folder_histplots + 'most_interesting_channel_gendee_week_percentage.png')
    plt.close()
    
    # percentage and stacked:
    fig, ax = plt.subplots(figsize=(16, 6))  # set the figure height and width
    df_draw_percentage = df_draw[[thema + ' females', thema + ' males']].divide(df_draw[[thema + ' females', thema+' males']].sum(axis=1), axis=0)
    df_draw_percentage.sort_values(by='week', axis=0, inplace=True, ascending=True)
    df_draw_percentage.plot(kind='bar', stacked=True, color=dict_colors_gender,alpha=.6)
    plt.title('Anteil veröffentlichter Artikel ohne DPA Meldungen pro Woche in wichtigen Resorts zu ' + thema+ ' in ' + newspaper, fontsize=12)  # title
    prep_xaxis(ax=ax, n=1)
    plt.tight_layout()  # make the figure, such that you can see everything
    plt.savefig(folder_histplots + newspaper + '_most_interesting_channel_gendee_and_'  + thema + 'week_percentage.png')
    plt.close()

