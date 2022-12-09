import sqlite3
import requests
import json
import random
from bs4 import BeautifulSoup
import requests
import unicodedata
import matplotlib.pyplot as plt
import numpy as np

#SI 206 Final Project by Avery Feldman, Jonah Feldman, and Rishabh Verma
#Reports and visualizations are found under the Report folder
#Obtained data about Pokemon and their moves, abilities, and types
#Utilized 2 APIs (PokeAPI, Pokemon Go API) and 1 website (bulbapedia), limited to 25 with each run adding additional data

class Pokemon:

    # initializes database and tables
    # requires connection to database (cur,conn)
    def createStructure(self,cur,conn):
        cur.execute("CREATE TABLE IF NOT EXISTS Pokemon (PokemonID INTEGER PRIMARY KEY, TypeID INTEGER, AbilityIDs CHAR, MoveIDs CHAR, PokemonName STRING UNIQUE, OverallStrength FLOAT)")
        cur.execute("CREATE TABLE IF NOT EXISTS Moves (MoveID INTEGER PRIMARY KEY, TypeID INTEGER, MoveName STRING UNIQUE, Accuracy FLOAT, Power INTEGER, OverallStrength FLOAT)")
        cur.execute("CREATE TABLE IF NOT EXISTS Type (TypeID INTEGER PRIMARY KEY, TypeName STRING UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS Ability (AbilityID INTEGER PRIMARY KEY, AbilityName STRING UNIQUE, Count INTEGER)")
        conn.commit()

    # requires limit of number of pokemon (in main function, it is declared as 25) and connection to database (cor,conn)
    # chooses the pokemon being focused on, returns a dictionary where the key is pokemon and value are their types
    # {pokemon1: type, pokemon2: type, pokemon3: type}
    # there are only about 18 types of pokemon, so we will never go over 25 entries for this table.
    def getPokemonNameTypes(self,cur,conn,limit):
            url="https://pogoapi.net/api/v1/pokemon_types.json"
            r=requests.get(url)
            listing= json.loads(r.text)
            random.shuffle(listing)
            returnedPokemonDiction={}
            val=0
            for num in listing:
                cur.execute("Select PokemonName from Pokemon") #Checks to make sure pokemon isn't repeated from database
                check=False
                for row in cur:
                    if row[0]==num["pokemon_name"]:
                        check=True
                        break
                if check:
                    continue #Chooses another pokemon if pokemon selected was already found in database
                if val >= limit:
                    break
                elif val < limit and num["form"]=="Normal": #Only adding normal pokemon, otherwise move to the next entry
                    val+=1
                    returnedPokemonDiction[num["pokemon_name"]]=num["type"][0]
                else:
                    continue
            return returnedPokemonDiction 

    # requires pokemonDiction returned from getPokemonNameTypes and connection to datbase (cur, conn)
    # returns a dictionary where the key is pokemon and value are their list of moves
    # {pokemon1: [move1,move2,move3], pokemon2: [move1,move2,move3,move4], pokemon3:[move1,move2,move3,move4]}
    def getPokemonMoves(self,cur,conn,pokemonDiction):
        pokemonNames= list(pokemonDiction.keys())
        returnedPokemonMoveDiction={}
        moveList=[]
        for pokemon in pokemonNames:
            iter=0
            url= "https://pokeapi.co/api/v2/pokemon/" + pokemon.lower() + "/"
            r=requests.get(url)
            if r.ok:
                diction=json.loads(r.text)
                moveVal=[]
                for move in diction['moves']:
                    if move['move']['name'] in moveList: #appends moves to dictionary values that have been added already to the list for previous pokemon during code run
                        moveVal.append(move['move']['name'])
                        continue
                    checking=False
                    cur.execute("Select MoveName from Moves") #appends moves to dictionary values that have been added already to the database
                    for row in cur:
                        if row[0]==move['move']['name']:
                            moveVal.append(move['move']['name'])
                            checking=True
                            break
                    if checking:
                        continue
                    moveurl= "https://pokeapi.co/api/v2/move/" + move['move']['name'].lower() + "/"
                    moveurl= moveurl.replace(' ','-')
                    re=requests.get(moveurl)
                    moveDict=json.loads(re.text)
                    if moveDict['power']!=None and moveDict['accuracy']!=None and iter < 1: #appends new moves to list
                        iter+=1
                        moveVal.append(move['move']['name'])
                        moveList.append(move['move']['name'])
                    elif iter >= 1: #each pokemon adds 1 new move to the dictionary at the max, not including previously existing moves. That way we can only have 25 moves added at the max to the moves table per run.
                        break
                    else:
                        continue
                returnedPokemonMoveDiction[pokemon]=moveVal

                
        return returnedPokemonMoveDiction

    # requires pokemonDiction returned from getPokemonNameTypes and connection to database (cur,conn)
    # returns a dictionary where the key is pokemon and value are their list of moves
    # {pokemon1: [ability1,ability2,ability3], pokemon2: [ability1,ability2,ability3,ability4], pokemon3:[ability1,ability2,ability3,ability4]}
    def getPokemonAbilities(self,cur,conn,pokemonDiction):
        pokemonNames= list(pokemonDiction.keys())
        returnedPokemonAbilityDiction={}
        abilityList=[]
        for pokemon in pokemonNames:     
            iter=0
            url= "https://pokeapi.co/api/v2/pokemon/" + pokemon.lower() + "/"
            r=requests.get(url)
            if r.ok:
                diction=json.loads(r.text)
                abilityVal=[]
                for ability in diction['abilities']: #appends abilities to dictionary values that have been added already to the list for previous pokemon during code run
                    if ability['ability']['name'] in abilityList:
                        abilityVal.append(ability['ability']['name'])
                        continue
                    checking=False
                    cur.execute("Select AbilityName from Ability") #appends abilities to dictionary values that have been added already to the database
                    for row in cur:
                        if row[0]==ability['ability']['name']:
                            abilityVal.append(ability['ability']['name'])
                            checking=True
                            break
                    if checking:
                        continue
                    if iter < 1: #appends new abilities to list
                        abilityVal.append(ability['ability']['name'])
                        abilityList.append(ability['ability']['name'])
                        returnedPokemonAbilityDiction[pokemon]=abilityVal
                        iter+=1
                    else: #each pokemon adds 1 new ability to the dictionary at the max, not including previously existing abilities. That way we can only have 25 abilities added at the max to the moves table per run.
                        break
        return returnedPokemonAbilityDiction

    # requires returnedPokemonAbilityDiction from getPokemonAbilities
    # returns a dictonary where the key is an ability name and the value is how many pokemon have said ability in the pokeapi
    # {ability1: count, ability2: count, ability3: count...}
    def getAbilityCount(self,returnedPokemonAbilityDiction):
        returnedAbilityCountDiction={}
        dupChecker = []
        for lst in returnedPokemonAbilityDiction.values():
            for ability in lst:
                url= "https://pokeapi.co/api/v2/ability/" + ability.lower() + "/" # call pokeapi to get ability information
                r=requests.get(url)
                if r.ok:
                    diction=json.loads(r.text)
                    for pokemon in diction["pokemon"]:
                        if ability not in returnedAbilityCountDiction:
                            returnedAbilityCountDiction[ability] = 1
                        elif ability in returnedAbilityCountDiction and ability not in dupChecker:
                            returnedAbilityCountDiction[ability] += 1
                dupChecker.append(ability) # appends ability name to dupChecker list to make sure the ability is counted only once
        return returnedAbilityCountDiction

    # requires pokemonMoveDiction returned from getPokemonMoves
    # returns a dictionary where the key is a pokemon move and value is a dictionary where type,power, accuracy are keys, and values are their actual values
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
                if move not in returnedMNAPDiction: #Creating url for pokemon moves with more than 1 word
                    movement= move.split('-')
                    mod=[]
                    for mov in movement:
                        mov=mov.capitalize()
                        mod.append(mov)
                    mod='_'.join(mod)
                    url= 'https://bulbapedia.bulbagarden.net/wiki/' + mod + "_(move)"
                    r= requests.get(url)
                    if r.ok: #Searching for data on power, accuracy, and pokemon type from bulbapedia website
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


    #requires pokemonDiction returned from getPokemonNameTypes (pogoAPI), pokemonMNAPDiction returned from getMoveInfo (bulbapedia), and connection to database (cur, conn)
    #inserts data into type table
    def insertTypeData(self,cur,conn, pokemonDiction, pokemonMNAPDiction):
        listing=[]
        for pokemon in pokemonDiction: #adds all pokemon types
            if pokemonDiction[pokemon] not in listing: 
                listing.append(pokemonDiction[pokemon])
        for move in pokemonMNAPDiction: #adds all pokemon move types
            if pokemonMNAPDiction[move]["type"] not in listing:
                listing.append(pokemonMNAPDiction[move]["type"])
        for type in listing: #inserts data into Type Table
            cur.execute("INSERT OR IGNORE INTO Type (TypeName) VALUES (?)",(type,))
        conn.commit()

    #requires pokemonMNAPDiction returned from getMoveInfo (bulbapedia requirement), connection to database (cur, conn)
    #inserts data into moves table using Types Table for foreign key
    def insertMoveData(self,cur,conn,pokemonMNAPDiction):
        for moveName, moveVals in pokemonMNAPDiction.items():
            name=moveName
            power=int(pokemonMNAPDiction[moveName]["power"])
            type= pokemonMNAPDiction[moveName]["type"]
            accuracy=(float(pokemonMNAPDiction[moveName]["accuracy"]))/100 #changing accuracy from whole number to decimal
            strength= float(power * accuracy) #calculating strength from power and accuracy
            cur.execute("Select * from Type")
            for row in cur:
                if row[1]==type:
                    cur.execute("INSERT OR IGNORE INTO Moves (TypeID,MoveName,Accuracy,Power,OverallStrength) VALUES (?,?,?,?,?)",(int(row[0]),name,accuracy,power,strength)) #inserting data into Type
                    break
        conn.commit()

    #requires dictionary returned from getPokemonAbilities (pokeAPI requirement), dictionary returned from getAbilityCount (pokeAPI Requirement), and connection to database (cur,conn)
    #inserts data into ability table
    def insertAbilityData(self,cur,conn,pokemonAbilityDiction,abilityCountDiction):
        for abilityList in pokemonAbilityDiction.values():
            for ability in abilityList:
                cur.execute("INSERT OR IGNORE INTO Ability (AbilityName,Count) VALUES (?,?)",(ability,abilityCountDiction[ability])) #inserting into ability table with count of moves
        conn.commit()

    #Requires dictionaries returned from getPokemonNameTypes (pogoAPI requirement), getPokemonMoves (pokeAPI), getPokemonAbilities (pokeAPI), as well as connection to database (cur,conn)
    #Inserts data into pokemon table using Type, Moves, and Ability table for foreign keys    
    def insertPokemonData(self,cur,conn,pokemonDiction, pokemonMoveDiction, pokemonAbilityDiction):
        for pokemonName,pokemonVals in pokemonDiction.items():
            try: #coding in try catch block in case of errors. If coding fails, moves on to next pokemon.
                name=pokemonName
                type=pokemonVals
                typeID=0
                moveNames=pokemonMoveDiction[name]
                abilityNames=pokemonAbilityDiction[name]
                moveIDs=[]
                abilityIDs=[]
                total_moves_str = []
                for move in moveNames:
                    cur.execute("Select * from Moves") #assigning foreign move ids for each pokemon
                    for row in cur:
                        if row[2]== move:
                            moveIDs.append(str(row[0]))
                            total_moves_str.append(row[5])
                            break
                for ability in abilityNames:
                    cur.execute("Select * from Ability") #assigning foreign ability ids for each pokemon
                    for row in cur:
                        if row[1]== ability:
                            abilityIDs.append(str(row[0]))
                            break
                cur.execute("Select * from Type") #assigning foreign type ids for each pokemon
                for row in cur:
                    if row[1]==type:
                        typeID= int(row[0])
                        break
                pokemonOverallStr = round(sum(total_moves_str)/len(total_moves_str),2) #calculating pokemons overall strength from individual move strength
                moveIDs=','.join(moveIDs)
                abilityIDs=','.join(abilityIDs)
                if len(moveIDs)==0:
                    continue
                cur.execute("INSERT OR IGNORE INTO Pokemon (TypeID,AbilityIDs,MoveIDs,PokemonName,OverallStrength) VALUES (?,?,?,?,?)",(typeID,abilityIDs,moveIDs,name,pokemonOverallStr)) #insers data into Pokemon table
            except:
                continue #moves on to next pokemon in case of errors
        conn.commit()

    # requires connection to database (cur, con)
    # takes data from all tables that originate from all apis/website 
    # uses data to create "poke_calculations.txt" file that contains the calculations of
    # - the strongest pokemon type
    # - the weakest pokemon type
    # - the most common pokemon type
    # - the least common pokemon type
    #
    # - the strongest move type
    # - the weakest move type
    # - the most common move type
    # - the least common move type
    #
    # - the strongest ability
    # - the weakest ability
    # - the most common ability
    # - the least common ability
    # does so by averaging the calculated strengths by how length, and by counting type and ability occurrences
    def calculationsFile(self, cur, con):
        # selects some data from all of the tables
        cur.execute("SELECT Pokemon.OverallStrength, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID") # use of join
        type_pokestr_lst = cur.fetchall()
        cur.execute("SELECT Moves.OverallStrength, Type.TypeName FROM Moves JOIN Type ON Moves.TypeID = Type.TypeID") # use of join
        type_movestr_lst = cur.fetchall()
        cur.execute("SELECT AbilityIDs, OverallStrength FROM Pokemon")
        ability_lst = cur.fetchall()
        cur.execute("SELECT AbilityID, AbilityName FROM Ability")
        ability_names = cur.fetchall()
        cur.execute("SELECT Count, AbilityName FROM Ability")
        ability_count = cur.fetchall()
        cur.execute("SELECT Moves.TypeID, Type.TypeName FROM Moves JOIN Type ON Moves.TypeID = Type.TypeID") # use of join 
        type_move_count = cur.fetchall()
        cur.execute("SELECT Pokemon.TypeID, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID") # use of join
        type_poke_count = cur.fetchall()

        # iterating through each list to create a dictionary for each SELECT
        poke_combined_dict = {}
        for tup in type_pokestr_lst:
            if tup[1] not in poke_combined_dict:
                poke_combined_dict[tup[1]] = [tup[0]]
            else:
                poke_combined_dict[tup[1]].append(tup[0])

        move_combined_dict = {}
        for tup in type_movestr_lst:
            if tup[1] not in move_combined_dict:
                move_combined_dict[tup[1]] = [tup[0]]
            else:
                move_combined_dict[tup[1]].append(tup[0])

        ability_overallstr_dict = {}
        for tup in ability_lst:
            for abilityID in tup[0].split(","):
                if abilityID not in ability_overallstr_dict:
                    ability_overallstr_dict[abilityID] = [tup[1]]
                else:
                    ability_overallstr_dict[abilityID].append(tup[1])

        for key, value in ability_overallstr_dict.items():
            ability_overallstr_dict[key] = round(sum(value)/len(value),2)
            
        ability_name_dict = {}
        for tup in ability_names:
            if str(tup[0]) in list(ability_overallstr_dict.keys()):
                ability_name_dict[tup[1]] = ability_overallstr_dict[str(tup[0])]

        type_move_count_dict = {}
        for tup in type_move_count:
            if tup[1] not in type_move_count_dict:
                type_move_count_dict[tup[1]] = 1
            else:
                type_move_count_dict[tup[1]] += 1

        type_poke_count_dict = {}
        for tup in type_poke_count:
            if tup[1] not in type_poke_count_dict:
                type_poke_count_dict[tup[1]] = 1
            else:
                type_poke_count_dict[tup[1]] += 1

        # average the values (lists) of the poke type and move type dictionaries to obtain a "final" number
        for key, value in poke_combined_dict.items():
            poke_combined_dict[key] = round(sum(value)/len(value),2)

        for key, value in move_combined_dict.items():
            move_combined_dict[key] = round(sum(value)/len(value),2)

        # creates variables that sort the calculated dictionaries and take the last and first item from them (the largest and smallest)
        strongest_pokemon_type = sorted(poke_combined_dict, key=poke_combined_dict.get, reverse=True)[0]
        weakest_pokemon_type = sorted(poke_combined_dict, key=poke_combined_dict.get, reverse=True)[-1]
        most_common_poke_type = sorted(type_poke_count_dict, key=type_poke_count_dict.get, reverse=True)[0]
        least_common_poke_type = sorted(type_poke_count_dict, key=type_poke_count_dict.get, reverse=True)[-1]

        strongest_move_type = sorted(move_combined_dict, key=move_combined_dict.get, reverse=True)[0]
        weakest_move_type =  sorted(move_combined_dict, key=move_combined_dict.get, reverse=True)[-1]
        most_common_move_type = sorted(type_move_count_dict, key=type_move_count_dict.get, reverse=True)[0]
        least_common_move_type = sorted(type_move_count_dict, key=type_move_count_dict.get, reverse=True)[-1]

        strongest_ability = sorted(ability_name_dict, key=ability_name_dict.get, reverse=True)[0]
        weakest_ability = sorted(ability_name_dict, key=ability_name_dict.get, reverse=True)[-1]
        most_common_ability = sorted(ability_count)[-1][1]
        least_common_ability = sorted(ability_count)[0][1]

        # create the calculations file
        f = open("poke_calculations.txt", "w") # write out into file
        f.write("POKEMON TYPE:" + "\n")
        f.write("- Strongest Pokemon Type: " + strongest_pokemon_type + " (" + str(poke_combined_dict[strongest_pokemon_type]) + " Overall Strength)" + "\n")
        f.write("- Weakest Pokemon Type: " + weakest_pokemon_type  + " (" + str(poke_combined_dict[weakest_pokemon_type]) + " Overall Strength)" + "\n")
        f.write("- Most Common Poke Type: " + most_common_poke_type + " (Occurred " + str(type_poke_count_dict[most_common_poke_type]) + " Times)" + "\n")
        f.write("- Least Common Poke Type: " + least_common_poke_type + " (Occurred " + str(type_poke_count_dict[least_common_poke_type]) + " Times)" + "\n")
        f.write("--------------------------------------------------------" + "\n")
        f.write("MOVE TYPE:" + "\n")
        f.write("- Strongest Move Type: " + strongest_move_type + " (" + str(move_combined_dict[strongest_move_type]) + " Overall Strength)" + "\n")
        f.write("- Weakest Move Type: " + weakest_move_type + " (" + str(move_combined_dict[weakest_move_type]) + " Overall Strength)" + "\n")
        f.write("- Most Common Move Type: " + most_common_move_type + " (Occurred " + str(type_move_count_dict[most_common_move_type]) + " Times)" + "\n")
        f.write("- Least Common Move Type: " + least_common_move_type + " (Occurred " + str(type_move_count_dict[least_common_move_type]) + " Times)" + "\n")
        f.write("--------------------------------------------------------" + "\n")
        f.write("ABILITIES:" + "\n")
        f.write("- Strongest Ability: " + strongest_ability.capitalize() + " (" + str(ability_name_dict[strongest_ability]) + " Overall Strength)" + "\n")
        f.write("- Weakest Ability: " + weakest_ability.capitalize() + " (" + str(ability_name_dict[weakest_ability]) + " Overall Strength)" + "\n")
        f.write("- Most Common Ability: " + most_common_ability.capitalize() + " (Occurred " + str(sorted(ability_count)[-1][0]) + " Times)" + "\n")
        f.write("- Least Common Ability: " + least_common_ability.capitalize() + " (Occurred " + str(sorted(ability_count)[0][0]) + " Times)" + "\n")
        
        f.close()
        
    # requires connection to database (cur,con)
    # returns a scatterplot graph of each move's accuracy (x) to its power (y)
    # draws regression line and writes correlation coefficient of the data points on the upper left portion of the graph
    def powerAccuracyVisualization(self, cur, conn):
        cur.execute("SELECT Accuracy, Power FROM Moves")
        move_info_lst = cur.fetchall()
        accuracy_lst = []
        power_lst = []
        for tup in move_info_lst:
            accuracy_lst.append(tup[0])
            power_lst.append(tup[1])

        fig, ax, = plt.subplots()

        plt.scatter(x=accuracy_lst,y=power_lst,alpha=0.3,edgecolors='black')

        plt.title("Move Accuracy to Move Power", pad=15, weight="bold", color='#333333')
        plt.xlabel("Accuracy", labelpad=15, color='#333333')
        plt.ylabel("Power", labelpad=15, color='#333333')

        # Citation https://www.pythoncharts.com/matplotlib/beautiful-bar-charts-matplotlib/
        # cleans up and beautifies the graph 
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#EEEEEE')
        ax.xaxis.grid(True, color='#EEEEEE')
       
       # creation and graphing of regression line
        x = np.array(accuracy_lst)
        y = np.array(power_lst)

        m, b = np.polyfit(x, y, 1)
        plt.plot(x, (m*x+b))
        
        r = np.corrcoef(x, y)
        corr_coeff = (r[1, 0])

        # mapping of correlation coefficient text and number
        plt.text(.03, .96, 'Correlation Coefficient = ' + str(round(corr_coeff,2)), ha='left', va='top', transform=ax.transAxes, weight='semibold')

        plt.tight_layout()

        plt.show()

    # requires connection to database (cur,con)
    # graphs each move's overall strength (power * accuracy) relative to its type
    # returns graph of type (x) to move strength (y)
    def moveTypeStrVisualization1(self, cur, conn):
        cur.execute("SELECT Moves.OverallStrength, Type.TypeName FROM Moves JOIN Type ON Moves.TypeID = Type.TypeID")
        type_movestr_lst = cur.fetchall()
        type_lst = []
        overallstr_lst = []
        for tup in type_movestr_lst:
            type_lst.append(tup[1])
            overallstr_lst.append(tup[0])

        # keeps track of the type of each move to color code it properly
        color_lst = []
        for tup in type_movestr_lst:
            if tup[1] == "Normal":
                color_lst.append("#A8A77A")
            elif tup[1] == "Fire":
                color_lst.append("#EE8130")
            elif tup[1] == "Dark":
                  color_lst.append("#705746")
            elif tup[1] == "Bug":
                color_lst.append("#A6B91A")
            elif tup[1] == "Grass":
                color_lst.append("#7AC74C")
            elif tup[1] == "Psychic":
                color_lst.append("#F95587")
            elif tup[1] == "Ground":
                color_lst.append("#E2BF65")
            elif tup[1] == "Water":
                color_lst.append("#6390F0")
            elif tup[1] == "Steel":
                color_lst.append("#B7B7CE")
            elif tup[1] == "Electric":
                color_lst.append("#F7D02C")
            elif tup[1] == "Fighting":
                color_lst.append("#C22E28")
            elif tup[1] == "Dragon":
                color_lst.append("#6F35FC")
            elif tup[1] == "Fairy":
                color_lst.append("#D685AD")
            elif tup[1] == "Flying":
                color_lst.append("#A98FF3")
            elif tup[1] == "Ice":
                color_lst.append("#96D9D6")
            elif tup[1] == "Poison":
                color_lst.append("#A33EA1")
            elif tup[1] == "Ghost":
                color_lst.append("#735797")
            else:
                color_lst.append("#B6A136")

        fig, ax, = plt.subplots()

        plt.scatter(x=type_lst,y=overallstr_lst,alpha=0.5,c=color_lst,edgecolors='black')

        plt.title("Move Type to Overall Strength", pad=15, weight="bold", color='#333333')
        plt.xlabel("Move Type", labelpad=15, color='#333333')
        plt.ylabel("Overall Strength", labelpad=15, color='#333333')

        # Citation https://www.pythoncharts.com/matplotlib/beautiful-bar-charts-matplotlib/
        # cleans up and beautifies the graph 
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(False)
        ax.xaxis.grid(True, color='#EEEEEE')

        plt.tight_layout()

        plt.show()

    # requires connection to database (cur, conn)
    # graphs the average of each move's overall strength relative to its type
    # does so by dividing the total overall strength of all the moves of said type by the amount of moves of said type
    # returns bar graph of averages
    def moveTypeStrVisualization2(self, cur, conn):
        cur.execute("SELECT Moves.OverallStrength, Type.TypeName FROM Moves JOIN Type ON Moves.TypeID = Type.TypeID")
        type_movestr_lst = cur.fetchall()
        combined_dict = {}
        for tup in type_movestr_lst:
            if tup[1] not in combined_dict:
                combined_dict[tup[1]] = [tup[0]]
            else:
                combined_dict[tup[1]].append(tup[0])
        
        # finds average of each move type overall strength
        avg_lst = []
        for value in combined_dict.values():
            avg_lst.append(sum(value)/len(value))

        types = list(combined_dict.keys())
        
        # keeps track of the type of each move to color code it properly
        color_lst = []
        for key in combined_dict.keys():
            if key == "Normal":
                color_lst.append("#A8A77A")
            elif key == "Fire":
                color_lst.append("#EE8130")
            elif key == "Dark":
                  color_lst.append("#705746")
            elif key == "Bug":
                color_lst.append("#A6B91A")
            elif key == "Grass":
                color_lst.append("#7AC74C")
            elif key == "Psychic":
                color_lst.append("#F95587")
            elif key == "Ground":
                color_lst.append("#E2BF65")
            elif key == "Water":
                color_lst.append("#6390F0")
            elif key == "Steel":
                color_lst.append("#B7B7CE")
            elif key == "Electric":
                color_lst.append("#F7D02C")
            elif key == "Fighting":
                color_lst.append("#C22E28")
            elif key == "Dragon":
                color_lst.append("#6F35FC")
            elif key == "Fairy":
                color_lst.append("#D685AD")
            elif key == "Flying":
                color_lst.append("#A98FF3")
            elif key == "Ice":
                color_lst.append("#96D9D6")
            elif key == "Poison":
                color_lst.append("#A33EA1")
            elif key == "Ghost":
                color_lst.append("#735797")
            else:
                color_lst.append("#B6A136")
        
        fig, ax = plt.subplots()

        bars = plt.bar(types,avg_lst,edgecolor='black',color=color_lst)

        plt.title("Move Type to Average Overall Strength", pad=15, weight="bold", color='#333333')
        plt.xlabel("Move Type", labelpad=15, color='#333333')
        plt.ylabel("Average Overall Strength", labelpad=15, color='#333333')
        
        ## Citation https://www.pythoncharts.com/matplotlib/beautiful-bar-charts-matplotlib/
        # cleans up and beautifies the graph 
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#827E7E')
        ax.xaxis.grid(False)

        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                round(bar.get_height(), 1),
                horizontalalignment='center',
                color="#4B3F3F",
                weight='bold')

        plt.tight_layout()

        plt.show()

    # requires connection to database (cur,con)
    # graphs each pokemon's overall strength (by averaging the overall strength of its moves) relative to its type
    # returns graph of type (x) to pokemon strength (y)
    def pokemonTypeStrVisualization1(self, cur, conn):
        cur.execute("SELECT Pokemon.OverallStrength, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID")
        type_pokestr_lst = cur.fetchall()
        type_lst = []
        overallstr_lst = []
        for tup in type_pokestr_lst:
            type_lst.append(tup[1])
            overallstr_lst.append(tup[0])

        # keeps track of the type of each pokemon to color code it properly
        color_lst = []
        for tup in type_pokestr_lst:
            if tup[1] == "Normal":
                color_lst.append("#A8A77A")
            elif tup[1] == "Fire":
                color_lst.append("#EE8130")
            elif tup[1] == "Dark":
                  color_lst.append("#705746")
            elif tup[1] == "Bug":
                color_lst.append("#A6B91A")
            elif tup[1] == "Grass":
                color_lst.append("#7AC74C")
            elif tup[1] == "Psychic":
                color_lst.append("#F95587")
            elif tup[1] == "Ground":
                color_lst.append("#E2BF65")
            elif tup[1] == "Water":
                color_lst.append("#6390F0")
            elif tup[1] == "Steel":
                color_lst.append("#B7B7CE")
            elif tup[1] == "Electric":
                color_lst.append("#F7D02C")
            elif tup[1] == "Fighting":
                color_lst.append("#C22E28")
            elif tup[1] == "Dragon":
                color_lst.append("#6F35FC")
            elif tup[1] == "Fairy":
                color_lst.append("#D685AD")
            elif tup[1] == "Flying":
                color_lst.append("#A98FF3")
            elif tup[1] == "Ice":
                color_lst.append("#96D9D6")
            elif tup[1] == "Poison":
                color_lst.append("#A33EA1")
            elif tup[1] == "Ghost":
                color_lst.append("#735797")
            else:
                color_lst.append("#B6A136")

        fig, ax, = plt.subplots()

        plt.scatter(x=type_lst,y=overallstr_lst,alpha=0.5,c=color_lst,edgecolors='black')

        plt.title("Poke Type to Overall Strength", pad=15, weight="bold", color='#333333')
        plt.xlabel("Poke Type", labelpad=15, color='#333333')
        plt.ylabel("Overall Strength", labelpad=15, color='#333333')

        # Citation https://www.pythoncharts.com/matplotlib/beautiful-bar-charts-matplotlib/
        # beautifies the graph 
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(False)
        ax.xaxis.grid(True, color='#EEEEEE')

        plt.tight_layout()

        plt.show()
    

    # requires connection to database (cur, conn)
    # graphs the average of each pokemon's overall strength relative to its type
    # does so by dividing the total overall strength of all the moves of said type by the amount of moves of said type
    # returns bar graph of averages
    def pokemonTypeStrVisualization2(self, cur, conn):
        cur.execute("SELECT Pokemon.OverallStrength, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID")
        type_pokestr_lst = cur.fetchall()
        combined_dict = {}
        for tup in type_pokestr_lst:
            if tup[1] not in combined_dict:
                combined_dict[tup[1]] = [tup[0]]
            else:
                combined_dict[tup[1]].append(tup[0])

        # finds average of each pokemon type overall strength
        avg_lst = []
        for value in combined_dict.values():
             avg_lst.append(sum(value)/len(value))

        types = list(combined_dict.keys())
    
        # keeps track of the type of each move to color code it properly 
        color_lst = []
        for key in combined_dict.keys():
            if key == "Normal":
                color_lst.append("#A8A77A")
            elif key == "Fire":
                color_lst.append("#EE8130")
            elif key == "Dark":
                  color_lst.append("#705746")
            elif key == "Bug":
                color_lst.append("#A6B91A")
            elif key == "Grass":
                color_lst.append("#7AC74C")
            elif key == "Psychic":
                color_lst.append("#F95587")
            elif key == "Ground":
                color_lst.append("#E2BF65")
            elif key == "Water":
                color_lst.append("#6390F0")
            elif key == "Steel":
                color_lst.append("#B7B7CE")
            elif key == "Electric":
                color_lst.append("#F7D02C")
            elif key == "Fighting":
                color_lst.append("#C22E28")
            elif key == "Dragon":
                color_lst.append("#6F35FC")
            elif key == "Fairy":
                color_lst.append("#D685AD")
            elif key == "Flying":
                color_lst.append("#A98FF3")
            elif key == "Ice":
                color_lst.append("#96D9D6")
            elif key == "Poison":
                color_lst.append("#A33EA1")
            elif key == "Ghost":
                color_lst.append("#735797")
            else:
                color_lst.append("#B6A136")
        
        fig, ax = plt.subplots()

        bars = plt.bar(types,avg_lst,edgecolor='black',color=color_lst)

        plt.title("Poke Type to Average Overall Strength", pad=15, weight="bold", color='#333333')
        plt.xlabel("Poke Type", labelpad=15, color='#333333')
        plt.ylabel("Average Overall Strength", labelpad=15, color='#333333')
        
        ## Citation https://www.pythoncharts.com/matplotlib/beautiful-bar-charts-matplotlib/
        #beautifies the graph
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#827E7E')
        ax.xaxis.grid(False)

        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                round(bar.get_height(), 1),
                horizontalalignment='center',
                color="#4B3F3F",
                weight='bold')

        plt.tight_layout()

        plt.show()
    
    # requires connection to database (cur, con)
    # returns a scatterplot of each ability's occurrences/commonality (x) to its overall strength (y)
    # does so by averaging its overall strength based on the number of pokemon that have said ability and the overall strength of said pokemon
    # draws regression line and writes correlation coefficient of the data points on the upper left portion of the graph
    def AbilityCommonalityVisualization(self, cur, conn):
        cur.execute("SELECT AbilityIDs, OverallStrength FROM Pokemon")
        ability_lst = cur.fetchall()
        cur.execute("SELECT AbilityID, Count FROM Ability")
        count_lst = cur.fetchall()

        # creates dictionary of the overall strength of each pokemon that have said ability
        ability_overallstr_dict = {}
        for tup in ability_lst:
            for abilityID in tup[0].split(","):
                if abilityID not in ability_overallstr_dict:
                    ability_overallstr_dict[abilityID] = [tup[1]]
                else:
                    ability_overallstr_dict[abilityID].append(tup[1])

        # averages the overall strength of each ability
        for key, value in ability_overallstr_dict.items():
            ability_overallstr_dict[key] = round(sum(value)/len(value),2)

        y_lst = list(ability_overallstr_dict.values())

        # gets count of each ability
        x_lst = []
        for tup in count_lst:
            if str(tup[0]) in list(ability_overallstr_dict.keys()):
                x_lst.append(tup[1])
                
        fig, ax, = plt.subplots()

        plt.scatter(x=x_lst,y=y_lst,alpha=0.3,edgecolors='black')

        plt.title("Ability Commonality to Ability Overall Strength", pad=15, weight="bold", color='#333333')
        plt.xlabel("Ability Commonality", labelpad=15, color='#333333')
        plt.ylabel("Ability Overall Strength", labelpad=15, color='#333333')

        # Citation https://www.pythoncharts.com/matplotlib/beautiful-bar-charts-matplotlib/
        # beautifies graph
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#EEEEEE')
        ax.xaxis.grid(True, color='#EEEEEE')
       
       # creation and graphing of regression line
        x = np.array(x_lst)
        y = np.array(y_lst)

        m, b = np.polyfit(x, y, 1)
        plt.plot(x, (m*x+b))
        
        r = np.corrcoef(x, y)
        corr_coeff = (r[1, 0])

        # mapping of correlation coefficient text and number
        plt.text(.03, .96, 'Correlation Coefficient = ' + str(round(corr_coeff,2)), ha='left', va='top', transform=ax.transAxes, weight='semibold')

        plt.tight_layout()

        plt.show()

def main():
    print("Beginning Run")
    print("---------------------------------------------------------------------")
    # Set up
    print("Started set up...")
    conn = sqlite3.connect('PokeDatabase.db')
    cur=conn.cursor()
    server = Pokemon()
    server.createStructure(cur,conn)
    print("Create structure has finished...")
    print("Set up complete")
    print("---------------------------------------------------------------------")
    
    # Data collection from APIs and website
    print("Started data collection...")
    pokemonDiction= server.getPokemonNameTypes(cur,conn,25)
    print("Pokemon Name Types has finished...")
    pokemonMoveDiction=server.getPokemonMoves(cur,conn,pokemonDiction)
    print("Pokemon Moves has finished...")
    pokemonAbilityDiction=server.getPokemonAbilities(cur,conn,pokemonDiction)
    print("Pokemon Abilities has finished...")
    abilityCountDiction=server.getAbilityCount(pokemonAbilityDiction)
    print("Ability Count has finished...")
    mnapDiction=server.getMoveInfo(pokemonMoveDiction)
    print("Pokemon Move info has finished...")
    print("Data collection complete")
    print("---------------------------------------------------------------------")

    
    # Data inserted into tables
    print("Started inserting data into database...")
    server.insertTypeData(cur,conn,pokemonDiction,mnapDiction)
    print("Type table has finished...")
    server.insertMoveData(cur,conn,mnapDiction)
    print("Move table has finished...")
    server.insertAbilityData(cur,conn,pokemonAbilityDiction,abilityCountDiction)
    print("Ability table has finished...")
    server.insertPokemonData(cur,conn,pokemonDiction,pokemonMoveDiction,pokemonAbilityDiction)
    print("Pokemon table has finished...")
    print("Data insertion complete")
    print("---------------------------------------------------------------------")

    # Calculations
    print("Started calculation file...")
    server.calculationsFile(cur, conn)
    print("Calculations file complete")
    print("---------------------------------------------------------------------")

    
    # Visualizations
    print("Started visualizations...")
    server.powerAccuracyVisualization(cur, conn)
    print("Move Power to Move Accuracy Graph has finished...")
    server.moveTypeStrVisualization1(cur, conn)
    print("Move Type to Overall Strength Graph (1) has finished...")
    server.moveTypeStrVisualization2(cur, conn)
    print("Move Type to Overall Strength Graph (2) has finished...")
    server.pokemonTypeStrVisualization1(cur, conn)
    print("Poke Type to Overall Strength Graph (1) has finished...")
    server.pokemonTypeStrVisualization2(cur, conn)
    print("Poke Type to Overall Strength Graph (2) has finished...")
    server.AbilityCommonalityVisualization(cur, conn)
    print("Ability Commonality to Overall Strength Graph has finished...")
    print("Data visualizations complete")
    print("---------------------------------------------------------------------")
    
    print("Run Complete")

main()