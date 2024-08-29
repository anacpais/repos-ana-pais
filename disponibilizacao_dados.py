from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3
import json

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/hottest_planet':
            self.handle_hottest_planet()
        elif self.path == '/appears_most':
            self.handle_appears_most_count()
        elif self.path == '/fastest_ships':
            self.handle_fastest_ships_count()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_hottest_planet(self):
        planets = get_hottest_planets()
        response = json.dumps(planets)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def handle_appears_most(self):
        people_sorted = get_appears_most()
        response = json.dumps(people_sorted)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def handle_fastest_ship(self):
        ships = get_fastest_ships()
        response = json.dumps(ships)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

def get_hottest_planets():
    conn = sqlite3.connect('star_wars_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, surface_water
        FROM planets
        ORDER BY surface_water ASC
        LIMIT 3
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    planets = [{'name': row[0], 'surface_water': row[1]} for row in rows]
    return planets


def get_appears_most():
    conn = sqlite3.connect('star_wars_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, films
        FROM people
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    people = []
    for row in rows:
        name = row[0]
        films = row[1]
        films_list = json.loads(films) if films else []
        count_films = len(films_list)
        people.append({'name': name, 'max_films': count_films})

    people_sorted = sorted(people, key=lambda x: x['max_films'], reverse=True)[:3]
    
    return people_sorted

def get_fastest_ships():
    conn = sqlite3.connect('star_wars_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, max_atmosphering_speed
        FROM starships
        ORDER BY max_atmosphering_speed DESC
        LIMIT 3
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    ships = [{'name': row[0], 'max_atmosphering_speed': row[1]} for row in rows]
    return ships


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run(port=8000)
