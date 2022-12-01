import requests
import json
import os
import sqlite3
import random 

def get_pokemon_move_data(data_limit):
    if data_limit > 905:
        print("Too much data requested, please reduce data requested and run again")
        return(None)
    else:
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
                poke_id = random_num
                name = content["forms"][0]["name"]
                moves = []
                for move in content["moves"]:
                    moves.append(move["move"]["name"])
                pokemon_move_data.append((poke_id, name, moves))

    return pokemon_move_data

    
def get_habitat_data(data_limit):
    if data_limit > 9:
        print("Too much data requested, please reduce data requested and run again")
        return(None)
    else:
        habitat_list = []
        habitat_data = []
        while len(habitat_list) < data_limit:
        ## there are a total of 9 habitats in the pokeapi database
            random_num = random.randint(1,9)
            if random_num not in habitat_list:
                habitat_list.append(random_num)
                url = "https://pokeapi.co/api/v2/pokemon-habitat/" + str(random_num) + "/"
                r = requests.get(url)
                content = json.loads(r.text)
                habitat_id = random_num
                name = content["name"]
                pokemon_lst = []
                for pokemon in content["pokemon_species"]:
                    pokemon_lst.append(pokemon["name"])
                habitat_data.append((habitat_id, name, pokemon_lst))
    
    return habitat_data


get_pokemon_move_data(25)
get_habitat_data(5)



# database set up function like make database and table

# database maker function

# visualization comparing pokemon and SOMETHING to number of moves it has?