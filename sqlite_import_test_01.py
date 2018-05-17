# Importing libraries
import sqlite3
import pandas as pd
import requests
import time

##############################################################################
# OS PULL

# pull JWT
url_JWT = 'https://auth.opensensors.com/auth/login'
headers_JWT = { 'x-api-key': 'UoheJ3fp0w7CJisPi26NzNOw2rEPyMj67ovksMo1' }
API_access_token = requests.get(url_JWT, headers = headers_JWT, timeout = 1000).json()

# pulling data from opensensors api
url_GPM = 'https://api.opensensors.com/getProjectMessages';
headers_GPM = { 'Authorization': API_access_token.get('jwtToken') }
parameters = {'fromDate': '2018-02-23',
           'toDate': '2018-03-01',
           'projectUri': 'zaha-hadid',
           'size': '500',
           'type': 'modcamHeatmap',
           'cursor': ''}

os_data_request = requests.get(url_GPM, headers = headers_GPM, params = parameters).json()

##############################################################################
# PREPROCESS DATA

data = os_data_request['items']

x_len = 0
y_len = 0
empty_data_replacement = []

item_number = len(data)

for j in range(0, item_number):
    if not(len(data[j]['heatmap']) == 0):
        print(len(data[j]['heatmap']))
        x_len = data[j]['heatmap'][0]
        y_len = data[j]['heatmap'][1]
        empty_data_replacement.append(x_len)
        empty_data_replacement.append(y_len)
        empty_data_replacement += [0] * (len(data[j]['heatmap']) - 2)
        break

for k in range(0, item_number):
    if (len(data[k]['heatmap']) == 0):
        data[k]['heatmap'] = empty_data_replacement

heatmap_length = len(data[0]['heatmap'])

##############################################################################
# CREATE DATABASE + TABLE

conn = sqlite3.connect("os_reading_AUB_03.sqlite")
c = conn.cursor()
# table_name = '\'' + str(os_data_request["nextCursor"]) + '\''
table_name = 'OS_READING_AUB'
heatmap_values = [''] * (heatmap_length - 2)

for i in range(0, heatmap_length - 2):
    heatmap_values[i] = '\'' + str(i) + '\'' + ' INTEGER'

heatmap_values = str(heatmap_values)
heatmap_values = heatmap_values[1:-1]
heatmap_values = heatmap_values.replace('\"', '')


sql_create_table = """ CREATE TABLE IF NOT EXISTS """ + table_name + """ (
                                        date INTEGER UNIQUE,
                                        human_time TEXT,
                                        tags TEXT,
                                        x_res INTEGER,
                                        y_res INTEGER,
                                        """ + str(heatmap_values) + """); """

c.execute(sql_create_table)

##############################################################################
# INSERT DATA

heatmap_column_names = []
for v in range(0, heatmap_length - 2):
    heatmap_column_names.append(str(v))

for p in range(0, item_number):
    sql_replace_or_insert = """INSERT OR IGNORE INTO """ + table_name + """ (
                                        date,
                                        human_time,
                                        tags,
                                        x_res,
                                        y_res,
                                        """ + str(heatmap_column_names)[1:-1] + """)
                                        VALUES (
                                        """ + str(data[p]['date']) + """,
                                        """ + '\'' + str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data[p]['date']) / 1000))) + '\'' + """,
                                        """ + '\'' + str(data[p]['tags'][1]) + '\'' + """,
                                        """ + str(data[p]['heatmap'][0]) + """,
                                        """ + str(data[p]['heatmap'][1]) + """,
                                        """ + str(data[p]['heatmap'][2:])[1:-1] + """); """

    c.execute(sql_replace_or_insert)

conn.commit()
conn.close()

