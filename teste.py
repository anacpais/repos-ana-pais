import requests
import sqlite3
import json

url = 'https://swapi.dev/api/'

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
else:
    print("Problema ao ler os dados")

def create_table_from_data(table_name, data):
    conn = sqlite3.connect('star_wars_database.db')
    cursor = conn.cursor()
    
    if not data:
        conn.close()
        return
    
    sample_item = data[0]
    columns = ', '.join(f'{key} TEXT' for key in sample_item.keys())
    
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {columns}
        )
    ''')
    
    conn.commit()
    conn.close()

def sanitize_data(data):
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            sanitized_data[key] = str(value)
        elif value is None:
            sanitized_data[key] = 'NULL'
        else:
            sanitized_data[key] = value
    return sanitized_data

def insert_data_into_table(table_name, data):
    conn = sqlite3.connect('star_wars_database.db')
    cursor = conn.cursor()
    
    if not data:
        conn.close()
        return
    
    sample_item = data[0]
    columns = ', '.join(sample_item.keys())
    placeholders = ', '.join('?' for _ in sample_item.keys())
    
    for item in data:
        sanitized_item = sanitize_data(item)
        values = [sanitized_item.get(key, 'NULL') for key in sample_item.keys()]
        cursor.execute(f'''
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
        ''', values)
    
    conn.commit()
    conn.close()

def fetch_data(url):
    response = requests.get(url)
    return response.json().get('results', [])

results = {}
for key, url in data.items():
    results[key] = fetch_data(url)

people_data = results['people']
planets_data = results['planets']
films_data = results['films']
species_data = results['species']
vehicles_data = results['vehicles']
starships_data = results['starships']

create_table_from_data('people', people_data)
insert_data_into_table('people', people_data)

create_table_from_data('planets', planets_data)
insert_data_into_table('planets', planets_data)

create_table_from_data('films', films_data)
insert_data_into_table('films', films_data)

create_table_from_data('species', species_data)
insert_data_into_table('species', species_data)

create_table_from_data('vehicles', vehicles_data)
insert_data_into_table('vehicles', vehicles_data)

create_table_from_data('starships', starships_data)
insert_data_into_table('starships', starships_data)
