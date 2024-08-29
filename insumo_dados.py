import urllib.request
import urllib.error
import sqlite3
import json

# Função para buscar dados usando urllib
def fetch_data(url):
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                return json.load(response).get('results', [])
            else:
                print(f"Problema ao ler os dados da URL: {url}")
                return []
    except urllib.error.URLError as e:
        print(f"Erro ao acessar a URL: {e}")
        return []
    except urllib.error.HTTPError as e:
        print(f"Erro HTTP: {e}")
        return []

# Função para criar uma tabela no banco de dados
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

# Função para sanitizar dados
def sanitize_data(data):
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            sanitized_data[key] = str(value)  # Converte objetos e listas para string
        elif value is None:
            sanitized_data[key] = 'NULL'  # Substitui None por NULL
        else:
            sanitized_data[key] = value
    return sanitized_data

# Função para inserir dados na tabela
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

# URL base da API
url_base = 'https://swapi.dev/api/'

# Dicionário com URLs para diferentes tipos de dados
data = {
    'people': url_base + 'people/',
    'planets': url_base + 'planets/',
    'films': url_base + 'films/',
    'species': url_base + 'species/',
    'vehicles': url_base + 'vehicles/',
    'starships': url_base + 'starships/'
}

# Buscar dados e inserir nas tabelas
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
