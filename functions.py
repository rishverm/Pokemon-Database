import sqlite3
import requests
import json
import random
from bs4 import BeautifulSoup
import requests
import unicodedata


class Pokemon:

    # TLDR of what has been done: dictionaries of information have been created linking pokemon to their types and moves. A dictionary has also been created that gives more 
    # information about pokemon moves. I have also created the database declaration with the appropriate tables, and inserted data into Type and moves.
    # What still has to be done: A dictionary has to be created that connects pokemon to their ability names. We also have to insert data into the Pokemon and Ability table.
    # I understand that this is a lot of changes and new information, but please feel free to change whatever you feel is necessary.

    # initializes database and tables
    def createStructure(self,cur,conn):
        cur.execute("CREATE TABLE IF NOT EXISTS Pokemon (PokemonID INTEGER PRIMARY KEY, TypeID INTEGER, AbilityIDs LIST, MoveIDs LIST, PokemonName STRING UNIQUE")
        cur.execute("CREATE TABLE IF NOT EXISTS Moves (MoveID INTEGER PRIMARY KEY, TypeID INTEGER, MoveName STRING UNIQUE, Accuracy FLOAT, Power INTEGER, Strength FLOAT)")
        cur.execute("CREATE TABLE IF NOT EXISTS Type (TypeID INTEGER PRIMARY KEY, TypeName STRING UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS Ability (AbilityID INTEGER PRIMARY KEY, AbilityName STRING UNIQUE)")
        conn.commit()



    #requires limit of number of pokemon
    # chooses the pokemon being focused on, returns a dictionary where the key is pokemon and value are their types
    # {pokemon1: type, pokemon2: type, pokemon3: type}
    def getPokemonNameTypes(self,limit):
            url="https://pogoapi.net/api/v1/pokemon_types.json"
            r=requests.get(url)
            listing= json.loads(r.text)
            random.shuffle(listing)
            returnedPokemonDiction={}
            val=0
            for num in listing:
                if val >= limit:
                    break
                elif val < limit and num["form"]=="Normal":
                    val+=1
                    returnedPokemonDiction[num["pokemon_name"]]=num["type"][0]
                else:
                    continue
            return returnedPokemonDiction

    # requires pokemonDiction returned from getPokemonNameTypes
    # returns a dictionary where the key is pokemon and value are their list of moves
    # {pokemon1: [move1,move2,move3], pokemon2: [move1,move2,move3,move4], pokemon3:[move1,move2,move3,move4]}
    def getPokemonMoves(self,pokemonDiction):
        pokemonNames= list(pokemonDiction.keys())
        returnedPokemonMoveDiction={}
        limit=0
        for pokemon in pokemonNames:
            url= "https://pokeapi.co/api/v2/pokemon/" + pokemon.lower() + "/"
            r=requests.get(url)
            if r.ok:
                diction=json.loads(r.text)
                movelist=[]
                for move in diction['moves']:
                    movelist.append(move['move']['name'])
                random.shuffle(movelist)
                returnedPokemonMoveDiction[pokemon]=movelist[0:15]
                
        return returnedPokemonMoveDiction

    # requires pokemonMoveDiction returned from getPokemonMoves
    #returns a dictionary where the key is a pokemon move and value is a dictionary where type,power, accuracy are keys, and values are their actual values
    # {move1:
    #        {
    #          power: power1
    #          type: type1
    #          value: value1
    #        },
    #   move2:
    #        {
    #          power: power2
    #          type: type2
    #          value: value2
    #        },
    #  move3:
    #        {
    #          power: power3
    #          type: type3
    #          value: value3
    #        }
    # }
    def getMoveInfo(self,pokemonMoveDiction):
        pokemonMoves=list(pokemonMoveDiction.values())
        returnedMNAPDiction={}
        for moveList in pokemonMoves:
            for move in moveList:
                if move not in returnedMNAPDiction:
                    r= requests.get('https://bulbapedia.bulbagarden.net/wiki/' + move + "_(move)")
                    if r.ok:
                        soup= BeautifulSoup(r.content, 'html.parser')
                        tags= soup.find_all('td')
                        typer= soup.find_all('b')
                        power= tags[7].text
                        accuracy= tags[8].text
                        power = unicodedata.normalize('NFKD',power).strip()
                        accuracy = unicodedata.normalize('NFKD',accuracy).strip()
                        type= typer[3].text
                        diction={}
                        diction["power"]= power
                        diction["accuracy"]= accuracy[:-1]
                        try:
                            pow =int(power)
                            acc=int(accuracy[:-1])
                        except:
                            continue
                        diction["type"]= type
                        returnedMNAPDiction[move]= diction
        return returnedMNAPDiction


    # need to get abilities info for each pokemon <-pending task




    #inserts data into type table
    def insertTypeData(self,cur,conn, pokemonDiction, pokemonMNAPDiction):
        listing=[]
        for pokemon in pokemonDiction:
            if pokemonDiction[pokemon] not in listing:
                listing.append(pokemonDiction[pokemon])
        for move in pokemonMNAPDiction:
            if pokemonMNAPDiction[move]["type"] not in listing:
                listing.append(pokemonMNAPDiction[move]["type"])
        for type in listing:
            cur.execute("INSERT OR IGNORE INTO Type (TypeName) VALUES (?)",(type,))
        conn.commit()


    #inserts data into moves table
    def insertMoveData(self,cur,conn,pokemonMNAPDiction):
        for moveName, moveVals in pokemonMNAPDiction.items():
            name=moveName
            power=int(pokemonMNAPDiction[moveName]["power"])
            type= pokemonMNAPDiction[moveName]["type"]
            accuracy=(float(pokemonMNAPDiction[moveName]["accuracy"]))/100
            strength= float(power * accuracy)
            cur.execute("Select * from Type")
            for row in cur:
                if row[1]==type:
                    cur.execute("INSERT OR IGNORE INTO Moves (TypeID,MoveName,Accuracy,Power,Strength) VALUES (?,?,?,?,?)",(int(row[0]),name,accuracy,power,strength))
                    break
        conn.commit()



    # need to add data to Pokemon table, Ability table <-pending task


def main():
    conn = sqlite3.connect('PokeDatabase')
    cur=conn.cursor()
    server = Pokemon()
    server.createStructure(cur,conn)
    pokemonDiction= server.getPokemonNameTypes()
    pokemonMoveDiction=server.getPokemonMoves(pokemonDiction)
    mnapDiction=server.getMoveInfo(pokemonMoveDiction)
    server.insertTypeData(cur,conn,pokemonDiction,mnapDiction)
    server.insertMoveData(cur,conn,mnapDiction)


main()