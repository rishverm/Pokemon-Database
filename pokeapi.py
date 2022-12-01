import requests
import json
import os
import sqlite3
import random 

def get_pokemon_move_data(data_limit):
    pokemon_move_list = []
    pokemon_move_data = []
    while len(pokemon_move_list) < data_limit:
    ## there are a total of 905 pokemon in the pokeapi database
        random_num = random.randint(1,905)
        if random_num not in pokemon_move_list:
            pokemon_move_list.append(random_num)
            url = "https://pokeapi.co/api/v2/pokemon/" + str(random_num) + "/"
            r = requests.get(url)
            content = json.loads(r.text)
            id = random_num
            name = content["forms"][0]["name"]
            moves = []
            for move in content["moves"]:
                moves.append(move["move"]["name"])
            pokemon_move_data.append((id, name, moves))

    print(pokemon_move_list)
    print(len(pokemon_move_list))
    print(pokemon_move_data)

get_pokemon_move_data(25)