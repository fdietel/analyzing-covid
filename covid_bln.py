#!/usr/bin/env python
# coding: utf-8

# # Analyzing Covid
# In this Notebook I will take a closer look on the COVID-19 pandemic in Berlin since March 2020. As main tools I will use [DateTime](https://pypi.org/project/DateTime) and [Seaborn](https://seaborn.pydata.org).
# 
# The data are publicly provided by the Berlin Health Department (**La**ndesamt für **Ge**sundheit und **So**ziales, LaGeSo) and can be downloaded [here](https://www.berlin.de/lageso/gesundheit/infektionsepidemiologie-infektionsschutz/corona).
# 
# ## Importing libraries
# First of all, I dowload all important libraries for my project.

# In[1]:


import pandas as pd
import datetime as dt
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as  mdates
from matplotlib.dates import MonthLocator
import seaborn as sns


# ## Preparing the data
# ### New cases and 7-day incidence rate
# For my analyses I will use three data sets. First, I will use a data set with some core indicators for the whole city. Because I am interested in the development over time I will transform the date column *datum* into a datetime format and define it as index.
# 
# I need to calculate the 7-day mean of new cases as the values vary heavily from day to day. The 7-day incidence rate (new cases per 100,000 in the past 7 days) is already calculated in the data set.

# In[2]:


covid_bln = pd.read_csv(r'C:\Users\flori\Documents\covid_bln\covid_bln.csv', sep=';')

covid_bln = covid_bln.drop('id', 1)
covid_bln['datum'] = pd.to_datetime(covid_bln['datum'])
covid_bln = covid_bln.set_index('datum').sort_index(ascending=True)
covid_bln['7_tage_mittel'] = covid_bln['neue_faelle'].rolling(7).mean()
covid_bln = covid_bln['2020-03-01':'2021-05-21']
covid_bln = covid_bln[['fallzahl', 'neue_faelle', '7_tage_inzidenz', '7_tage_mittel']]

covid_bln


# ### 7-day incidence rate per borough
# Next, I will fetch and prepare a data set with cases per borough. Again, I have to transform the date column into a datetime format. Unfortunately, the 7-day incidence rate is not given here, so I have to calculate it by using the raw cases and the population per borough.

# In[3]:


covid_bor = pd.read_csv(r'C:\Users\flori\Documents\covid_bln\covid_bor.csv', sep=';')

boroughs={
    'columns': {
        'mitte': 'm',
        'friedrichshain_kreuzberg': 'fk',
        'pankow': 'p',
        'charlottenburg_wilmersdorf': 'cw',
        'spandau': 's',
        'steglitz_zehlendorf': 'sz',
        'tempelhof_schoeneberg': 'ts',
        'neukoelln': 'n',
        'treptow_koepenick': 'tk',
        'marzahn_hellersdorf': 'mh',
        'lichtenberg': 'l',
        'reinickendorf': 'r'}
        }

covid_bor = covid_bor.drop('id', 1).rename(**boroughs)
covid_bor['datum'] = pd.to_datetime(covid_bor['datum'])
covid_bor = covid_bor.set_index('datum').sort_index(ascending=True)
covid_bor = covid_bor['2020-03-01':'2021-05-21']

pop_bor = pd.read_csv(r'C:\Users\flori\Documents\covid_bln\pop_boroughs.csv', sep=';')
pop_bor = pop_bor.drop('jahr', 1).rename(**boroughs)
pop_bor_100k = pop_bor.div(100000).to_dict(orient='list')

for bor in covid_bor:
    covid_bor[bor] = covid_bor[bor].rolling(7).sum()
    covid_bor[bor] = round(covid_bor[bor]/pop_bor_100k[bor], 1)
    
covid_bor['2020-03-09':'2021-05-21']


# ### New cases by age group per week in percent
# Finally I will use a data set that deals with new cases of COVID-19 by age group per week. Because the data set only contains the week number and needs to be reordered it requires a little more preparation.

# In[4]:


covid_age = pd.read_csv(r'C:\Users\flori\Documents\covid_bln\covid_age.csv', sep=';')

covid_age_2020 = covid_age.drop(covid_age.loc[covid_age['jahr']==2021].index)
covid_age_2021 = covid_age.drop(covid_age.loc[covid_age['jahr']==2020].index)

covid_age_2020['datum_str'] = (covid_age_2020['jahr'].map(str) + ' ' +                          (covid_age_2020['meldewoche']-1).map(str) + ' 0').map(str)
    
covid_age_2020['datum'] = [dt.datetime.strptime(i, '%Y %W %w')                            for i in covid_age_2020['datum_str']]

covid_age_2021['datum_str'] = (covid_age_2021['jahr'].map(str) + ' ' +                                (covid_age_2021['meldewoche']).map(str) + ' 0').map(str)
    
covid_age_2021['datum'] = [dt.datetime.strptime(i, '%Y %W %w')                            for i in covid_age_2021['datum_str']]

covid_age_dates=covid_age_2020.append(covid_age_2021)

covid_age_piv=covid_age_dates.pivot_table(values='faelle', index='datum', 
                                    columns='altersgruppe')
covid_age_piv.index = covid_age_piv.index.strftime('%m/%d/%y')

covid_age_piv.columns = covid_age_piv.columns.str.replace(' ', '')

covid_age_piv['0-9'] = covid_age_piv['0-4'] + covid_age_piv['5-9']
covid_age_piv['10-19'] = covid_age_piv['10-14'] + covid_age_piv['15-19']
covid_age_piv['20-29'] = covid_age_piv['20-24'] + covid_age_piv['25-29']
covid_age_piv['80+'] = covid_age_piv['80-89'] + covid_age_piv['90+']

covid_age_piv = covid_age_piv.reindex(columns=['0-9', '10-19', '20-29', 
                                               '30-39', '40-49', '50-59', 
                                               '60-69', '70-79', '80+'])

covid_age_piv['gesamt'] = covid_age_piv.sum(1)

for age in covid_age_piv.columns:
    covid_age_piv[age] = covid_age_piv[age]/covid_age_piv['gesamt']*100

covid_age_piv = covid_age_piv.drop('gesamt', 1)
covid_age_piv


# ## Data visualization
# ### New cases

# In[6]:


fig, ax = plt.subplots(figsize=(16,9), dpi=150)

ax.bar(covid_bln.index, covid_bln['neue_faelle'], 
       color='lightsteelblue', label="per day", alpha=0.7, width=1)
ax.set_ylabel("new cases", fontsize=15)

ax.plot(covid_bln.index, covid_bln['7_tage_mittel'], 
        label='7-day mean')

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(MonthLocator())

ax.set_title("", fontsize=15)
ax.set_ylabel("new cases", fontsize=15)
ax.legend()

plt.style.use('seaborn')
plt.tight_layout()
plt.show()


# The maximum of 1,960 new registered cases was reached on November 12, 2020. The 7-day mean peaked on November 18, 2020 with 1,273.9 cases.

# ### 7-day incidence rate

# In[7]:


fig, ax = plt.subplots(figsize=(16,9), dpi=150)

ax.plot(covid_bln.index, covid_bln['7_tage_inzidenz'])
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(MonthLocator())

ax.set_title("", fontsize=15)
ax.set_ylabel("7-day incidence", fontsize=15)

arrow=dict(
    arrowprops=dict(
        arrowstyle='->', 
        color='grey', 
        lw=1, 
        connectionstyle='arc3,rad=0.2'
        )
    )
 
arrow_rev=dict(
    arrowprops=dict(
        arrowstyle='->', 
        color='grey', 
        lw=1, 
        connectionstyle='arc3,rad=-0.2'
        )
    )

ax.annotate("1st lockdown", xy=(dt.date(2020,3,18), covid_bln.at['2020-3-18', '7_tage_inzidenz']), 
            xytext=(dt.date(2020,3,23), 0), **arrow)

ax.annotate("1st lockdown ends", xy=(dt.date(2020,5,6), covid_bln.at['2020-5-6', '7_tage_inzidenz']), 
            xytext=(dt.date(2020,4,27), 23), **arrow)

ax.annotate("lockdown 'light'", xy=(dt.date(2020,11,2), covid_bln.at['2020-11-2', '7_tage_inzidenz']), 
            xytext=(dt.date(2020,9,25), 180), **arrow)

ax.annotate("2nd lockdown", xy=(dt.date(2020,12,16), covid_bln.at['2020-12-16', '7_tage_inzidenz']), 
            xytext=(dt.date(2020,11,25), 242), **arrow)

ax.annotate("Christmas Eve", xy=(dt.date(2020,12,24), covid_bln.at['2020-12-24', '7_tage_inzidenz']), 
            xytext=(dt.date(2020,12,30), 240), **arrow_rev)

ax.annotate("New Year's Day", xy=(dt.date(2021,1,1), covid_bln.at['2021-1-1', '7_tage_inzidenz']), 
            xytext=(dt.date(2020,12,10), 120), **arrow_rev)

ax.annotate("Good Friday (Easter)", xy=(dt.date(2021,4,2), covid_bln.at['2021-4-2', '7_tage_inzidenz']), 
            xytext=(dt.date(2021,3,18), 172), **arrow_rev)

plt.style.use('seaborn')
plt.tight_layout()
plt.show()


# The 7-day incidence rate per 100,000 reached it's maximum of 244.7 on November 18, 2020.

# ### 7-day incidence rate per borough

# In[8]:


bor_title = ["Mitte", "Friedrichshain-Kreuzberg", "Pankow",
             "Charlottenburg-Wilmersdorf", "Spandau", "Steglitz-Zehlendorf",
             "Tempelhof-Schöneberg", "Neukölln", "Treptow-Köpenick",
             "Marzahn-Hellersdorf", "Lichtenberg", "Reinickendorf"]

fig, axes = plt.subplots(4, 3, figsize=(16,9), sharey=True, sharex=True, dpi=150)

for i, ax in enumerate(axes.flatten()):
    ax.plot(covid_bor.iloc[:,0+i])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m'))
    ax.xaxis.set_major_locator(MonthLocator())
    ax.set_title(bor_title[0+i], fontsize=14)
    ax.tick_params('x', labelrotation=0)

plt.style.use('seaborn')
plt.tight_layout()
plt.show()


# Mitte and Friedrichshain-Kreuzberg show the highest 7-day incidence rate per 100,000 with 385.2 on November 17, 2020 and 379.8 on November 17, 2020. Only Lichtenberg never reaches a value of 200 and has similar maximum points in fall/winter 2020/21 and spring 2021.

# ### New cases by age group per week in percent

# In[9]:


fig, ax = plt.subplots(figsize=(18, 9), dpi=150)

sns.heatmap(covid_age_piv.transpose(), annot=True, cmap='rocket', vmax=45, 
            fmt='.0f', annot_kws=dict(size=8, rotation=0))

ax.set_title("share of new cases by age group per week in %", fontsize=15)
ax.set_xticklabels(covid_age_piv.index, rotation=90)
ax.set_yticklabels(labels=ax.get_yticklabels(), va='center', rotation=0)
ax.set_xlabel("week (Sunday)")
ax.set_ylabel("age group")

plt.style.use('seaborn')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()


# Overall, the age group of people from 20 to 29 years has the highest percentages of new cases, especially in summer 2020 between the first and the second wave. In the week of September 6, 2020 (Sunday) 41.8 percent of all new cases were registered in this age group.
# 
# The group of people aged 80 or older has it's peaks during the first and the second wave in spring 2020 and fall/winter 2020/21.
