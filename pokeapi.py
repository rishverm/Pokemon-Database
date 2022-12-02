import requests
import json
import os
import sqlite3
import random 

def get_pokemon_move_data(data_limit=25):
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
                name = content["forms"][0]["name"]
                moves = []
                for move in content["moves"]:
                    moves.append(move["move"]["name"])
                pokemon_move_data.append((name, moves))

    return pokemon_move_data

    
def get_abilities_data(data_limit=25):
    if data_limit > 267:
        print("Too much data requested, please reduce data requested and run again")
        return(None)
    else:
        abilities_tracker_lst = []
        abilities_data = []
        while len(abilities_tracker_lst) < data_limit:
        ## there are a total of 267 abilities in the pokeapi database
            random_num = random.randint(1,267)
            if random_num not in abilities_tracker_lst:
                abilities_tracker_lst.append(random_num)
                url = "https://pokeapi.co/api/v2/ability/" + str(random_num) + "/"
                r = requests.get(url)
                content = json.loads(r.text)
                name = content["name"]
                pokemon_lst = []
                for pokemon in content["pokemon"]:
                    pokemon_lst.append(pokemon["pokemon"]["name"])
                rarity = len(pokemon_lst)
                abilities_data.append((name, rarity, pokemon_lst))
    
    return abilities_data


#print(get_pokemon_move_data(25))
for x in range(5):
    print(get_abilities_data(1))
    print("--------------------------------------------------")



# database set up function like make database and table

# database maker function

# visualization comparing pokemon and SOMETHING to number of moves it has?