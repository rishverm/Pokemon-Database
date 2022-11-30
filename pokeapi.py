import requests
import json
import os
import sqlite3
import random 

def get_move_data(data_limit):
    move_list = []
    move_data = []
    while len(move_list) < data_limit:
    ## there are a total of 826 moves in pokemon
        random_num = random.randint(1,826)
        if random_num not in move_list:
            move_list.append(random_num)
            url = "https://pokeapi.co/api/v2/move/" + str(random_num) + "/"
            r = requests.get(url)
            content = json.loads(r.text)
            id = random_num
            accuracy = content["accuracy"]
            name = content["name"].split("--")[0]
            type = content["type"]["name"]
            move_data.append((id, name, type, accuracy))

    print(move_list)
    print(len(move_list))
    print(move_data)

get_move_data(25)