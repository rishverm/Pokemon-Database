import sqlite3
import requests
import json
import random
from bs4 import BeautifulSoup
import requests
import unicodedata
import matplotlib.pyplot as plt


class Pokemon:

    # TLDR of what has been done: dictionaries of information have been created linking pokemon to their types and moves. A dictionary has also been created that gives more 
    # information about pokemon moves. A dictionary has also been created that connects pokemon to their ability names. 
    # I have also created the database declaration with the appropriate tables, and inserted data into all 4 tables.
    # I believe these are all the functions we need for the python portion of this project but I could be wrong.
    # I understand that this is a lot of changes and new information, but please feel free to change whatever you feel is necessary.
    # What still has to be done: Process the Data, Visualize the Data, and Report (Part 3-5) 

    # initializes database and tables
    def createStructure(self,cur,conn):
        cur.execute("CREATE TABLE IF NOT EXISTS Pokemon (PokemonID INTEGER PRIMARY KEY, TypeID INTEGER, AbilityIDs CHAR, MoveIDs CHAR, PokemonName STRING UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS Moves (MoveID INTEGER PRIMARY KEY, TypeID INTEGER, MoveName STRING UNIQUE, Accuracy FLOAT, Power INTEGER, OverallStrength FLOAT)")
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

    # requires pokemonDiction returned from getPokemonNameTypes
    # returns a dictionary where the key is pokemon and value are their list of moves
    # {pokemon1: [ability1,ability2,ability3], pokemon2: [ability1,ability2,ability3,ability4], pokemon3:[ability1,ability2,ability3,ability4]}
    def getPokemonAbilities(self,pokemonDiction):
        pokemonNames= list(pokemonDiction.keys())
        returnedPokemonAbilityDiction={}
        for pokemon in pokemonNames:
            url= "https://pokeapi.co/api/v2/pokemon/" + pokemon.lower() + "/"
            r=requests.get(url)
            if r.ok:
                diction=json.loads(r.text)
                abilitylist=[]
                for ability in diction['abilities']:
                    abilitylist.append(ability['ability']['name'])
                    returnedPokemonAbilityDiction[pokemon]=abilitylist
        return returnedPokemonAbilityDiction

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


    #inserts data into type table using dictionary returned from getPokemonNameTypes (pogoAPI) and getMoveInfo (bulbapedia)
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

    #inserts data into moves table using dictionary returned from getMoveInfo (bulbapedia requirement), as well as Types Table for foreign key
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
                    cur.execute("INSERT OR IGNORE INTO Moves (TypeID,MoveName,Accuracy,Power,OverallStrength) VALUES (?,?,?,?,?)",(int(row[0]),name,accuracy,power,strength))
                    break
        conn.commit()

    #inserts data into ability table using dictionary returned from getPokemonAbilities (pokeAPI requirement)
    def insertAbilityData(self,cur,conn,pokemonAbilityDiction):
        for abilityList in pokemonAbilityDiction.values():
            for ability in abilityList:
                cur.execute("INSERT OR IGNORE INTO Ability (AbilityName) VALUES (?)",(ability,))
        conn.commit()

    #Inserts data into pokemon table using dictionary returned from getPokemonNameTypes (pogoAPI requirement), getPokemonMoves (pokeAPI), and getPokemonAbilities (pokeAPI)
    #Also uses Type, Moves, and Ability table for foreign keys
    # cur.execute("CREATE TABLE IF NOT EXISTS Pokemon (PokemonID INTEGER PRIMARY KEY, TypeID INTEGER, AbilityIDs LIST, MoveIDs LIST, PokemonName STRING UNIQUE")
    
    def insertPokemonData(self,cur,conn,pokemonDiction, pokemonMoveDiction, pokemonAbilityDiction):
        for pokemonName,pokemonVals in pokemonDiction.items():
            try:
                name=pokemonName
                type=pokemonVals
                typeID=0
                moveNames=pokemonMoveDiction[name]
                abilityNames=pokemonAbilityDiction[name]
                moveIDs=[]
                abilityIDs=[]
                for move in moveNames:
                    cur.execute("Select * from Moves")
                    for row in cur:
                        if row[2]== move:
                            moveIDs.append(str(row[0]))
                            break
                for ability in abilityNames:
                    cur.execute("Select * from Ability")
                    for row in cur:
                        if row[1]== ability:
                            abilityIDs.append(str(row[0]))
                            break
                cur.execute("Select * from Type")
                for row in cur:
                    if row[1]==type:
                        typeID= int(row[0])
                        break
                moveIDs=','.join(moveIDs)
                abilityIDs=','.join(abilityIDs)
                cur.execute("INSERT OR IGNORE INTO Pokemon (TypeID,AbilityIDs,MoveIDs,PokemonName) VALUES (?,?,?,?)",(typeID,abilityIDs,moveIDs,name))
            except:
                continue
        conn.commit()

    #creates file ADD MORE HERE WHEN YOU ARE DONE
    # TALK ABOUT WHAT THE FUNCTION DOES HERE
    # ...............

    def calculations_file(self,):
        pass
    #You must select some data from all of the tables in your database and calculate
    #something from that data (20 points). You could calculate the count of how many items
     #occur on a particular day of the week or the average of the number of items per day.
     #● You must do at least one database join to select your data (20 points).
     #● Write out the calculated data to a file as text (10 points) 

    # add documentation here too
    def visualization_move_data(self, cur, conn):
        cur.execute("SELECT Accuracy, Power FROM Moves")
        move_info_lst = cur.fetchall()
        accuracy_lst = []
        power_lst = []
        for tup in move_info_lst:
            accuracy_lst.append(tup[0])
            power_lst.append(tup[1])

        plt.figure()
        plt.scatter(x=accuracy_lst,y=power_lst,alpha=0.3)

        plt.title("Move Accuracy to Power Comparison")
        plt.xlabel("Accuracy")
        plt.ylabel("Power")

        plt.show()

        return "Move Power to Accuracy Comparison Graph has finished"

def main():
    conn = sqlite3.connect('PokeDatabase')
    cur=conn.cursor()
    server = Pokemon()
    server.createStructure(cur,conn)
    print("Create structure has finished")
    pokemonDiction= server.getPokemonNameTypes(25)
    print("Pokemon Name Types has finished")
    pokemonMoveDiction=server.getPokemonMoves(pokemonDiction)
    print("Pokemon moves has finished")
    pokemonAbilityDiction=server.getPokemonAbilities(pokemonDiction)
    print("Pokemon Abilities has finished")
    mnapDiction=server.getMoveInfo(pokemonMoveDiction)
    print("Pokemon move info has finished")
    # getMoveInfo takes a while (around 120 seconds), the other functions are quick
    server.insertTypeData(cur,conn,pokemonDiction,mnapDiction)
    print("Type table has finished")
    server.insertMoveData(cur,conn,mnapDiction)
    print("Move table has finished")
    server.insertAbilityData(cur,conn,pokemonAbilityDiction)
    print("Ability table has finished")
    server.insertPokemonData(cur,conn,pokemonDiction,pokemonMoveDiction,pokemonAbilityDiction)
    print("Pokemon table has finished")
    movevisual=server.visualization_move_data(cur, conn)
    print(movevisual)


main()