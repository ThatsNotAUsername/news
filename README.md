# news

## what it does
Scraping metadata about articles from 4 different german newspaper for a given time period. Make some first rough analyses. 


### Download data: *get_news_data.py*
First, data has to be downloaded using the get_news_data.py function

### First rough analyses: *analyze_different_newspaper_main.py*
The data can then be analyzed using analyze_different_newspaper_main.py

This can be done for 4 newspapers (taz, zeit, spiegel and sueddeutsche). Time can be given, whereas newspapers only go back until one month (except for spiegel), and zeit only uses time frames (1 day, 1 month, 1 week) and not dates. 


## functions:
  - get_news_data.py: scrapes the web for the given newspaper and timeframe. I use the module for SPON  (get_spiegel_data.py) and wrote web scrapers for TAZ (get_taz_data.py), Sueddeutsche  (get_sueddeutsche_data.py) and Zeit (get_zeit_data.py)
  - analyze_different_newspaper_main.py: create basic figures on how many articles were published, from which authors (gender), in which resorts. You can give a topic and buzzword for specific analyses on this (function uses create_dataframes.py)
  
 
 ## notes:
 The **spiegel scraper module** has to be downloaded: 
 An API Key for the spiegel scraper is needed
 
 
 For **Zeit** oly time frames, not dates can be given. 
 
 
