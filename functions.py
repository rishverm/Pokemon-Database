import sqlite3
import requests
import json
import random
from bs4 import BeautifulSoup
import requests
import unicodedata
import matplotlib.pyplot as plt
import numpy as np



class Pokemon:

    # TLDR of what has been done: dictionaries of information have been created linking pokemon to their types and moves. A dictionary has also been created that gives more 
    # information about pokemon moves. A dictionary has also been created that connects pokemon to their ability names. 
    # I have also created the database declaration with the appropriate tables, and inserted data into all 4 tables.
    # I believe these are all the functions we need for the python portion of this project but I could be wrong.
    # I understand that this is a lot of changes and new information, but please feel free to change whatever you feel is necessary.
    # What still has to be done: Process the Data, Visualize the Data, and Report (Part 3-5) 

    # initializes database and tables
    def createStructure(self,cur,conn):
        cur.execute("CREATE TABLE IF NOT EXISTS Pokemon (PokemonID INTEGER PRIMARY KEY, TypeID INTEGER, AbilityIDs CHAR, MoveIDs CHAR, PokemonName STRING UNIQUE, OverallStrength FLOAT)")
        cur.execute("CREATE TABLE IF NOT EXISTS Moves (MoveID INTEGER PRIMARY KEY, TypeID INTEGER, MoveName STRING UNIQUE, Accuracy FLOAT, Power INTEGER, OverallStrength FLOAT)")
        cur.execute("CREATE TABLE IF NOT EXISTS Type (TypeID INTEGER PRIMARY KEY, TypeName STRING UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS Ability (AbilityID INTEGER PRIMARY KEY, AbilityName STRING UNIQUE, Count INTEGER)")
        conn.commit()

    #requires limit of number of pokemon
    # chooses the pokemon being focused on, returns a dictionary where the key is pokemon and value are their types
    # {pokemon1: type, pokemon2: type, pokemon3: type}
    def getPokemonNameTypes(self,cur,conn,limit):
            url="https://pogoapi.net/api/v1/pokemon_types.json"
            r=requests.get(url)
            listing= json.loads(r.text)
            random.shuffle(listing)
            returnedPokemonDiction={}
            val=0
            for num in listing:
                cur.execute("Select PokemonName from Pokemon")
                check=False
                for row in cur:
                    if row[0]==num["pokemon_name"]:
                        check=True
                        break
                if check:
                    continue
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
                    if move['move']['name'] in moveList:
                        moveVal.append(move['move']['name'])
                        continue
                    checking=False
                    cur.execute("Select MoveName from Moves")
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
                    if moveDict['power']!=None and moveDict['accuracy']!=None and iter < 1: 
                        iter+=1
                        moveVal.append(move['move']['name'])
                        moveList.append(move['move']['name'])
                    elif iter >= 1:
                        break
                    else:
                        continue
                returnedPokemonMoveDiction[pokemon]=moveVal

                
        return returnedPokemonMoveDiction

    # requires pokemonDiction returned from getPokemonNameTypes
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
                for ability in diction['abilities']:
                    if ability['ability']['name'] in abilityList:
                        abilityVal.append(ability['ability']['name'])
                        continue
                    checking=False
                    cur.execute("Select AbilityName from Ability")
                    for row in cur:
                        if row[0]==ability['ability']['name']:
                            abilityVal.append(ability['ability']['name'])
                            checking=True
                            break
                    if checking:
                        continue
                    if iter < 1:
                        abilityVal.append(ability['ability']['name'])
                        abilityList.append(ability['ability']['name'])
                        returnedPokemonAbilityDiction[pokemon]=abilityVal
                        iter+=1
                    else:
                        break
        return returnedPokemonAbilityDiction

    #documentation goes here
    def getAbilityCount(self,returnedPokemonAbilityDiction):
        returnedAbilityCountDiction={}
        dupChecker = []
        for lst in returnedPokemonAbilityDiction.values():
            for ability in lst:
                url= "https://pokeapi.co/api/v2/ability/" + ability.lower() + "/"
                r=requests.get(url)
                if r.ok:
                    diction=json.loads(r.text)
                    for pokemon in diction["pokemon"]:
                        if ability not in returnedAbilityCountDiction:
                            returnedAbilityCountDiction[ability] = 1
                        elif ability in returnedAbilityCountDiction and ability not in dupChecker:
                            returnedAbilityCountDiction[ability] += 1
                dupChecker.append(ability)
        return returnedAbilityCountDiction

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
                    movement= move.split('-')
                    mod=[]
                    for mov in movement:
                        mov=mov.capitalize()
                        mod.append(mov)
                    mod='_'.join(mod)
                    url= 'https://bulbapedia.bulbagarden.net/wiki/' + mod + "_(move)"
                    r= requests.get(url)
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
    def insertAbilityData(self,cur,conn,pokemonAbilityDiction,abilityCountDiction):
        for abilityList in pokemonAbilityDiction.values():
            for ability in abilityList:
                cur.execute("INSERT OR IGNORE INTO Ability (AbilityName,Count) VALUES (?,?)",(ability,abilityCountDiction[ability]))
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
                total_moves_str = []
                for move in moveNames:
                    cur.execute("Select * from Moves")
                    for row in cur:
                        if row[2]== move:
                            moveIDs.append(str(row[0]))
                            total_moves_str.append(row[5])
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
                pokemonOverallStr = round(sum(total_moves_str)/len(total_moves_str),2)
                moveIDs=','.join(moveIDs)
                abilityIDs=','.join(abilityIDs)
                if len(moveIDs)==0:
                    continue
                cur.execute("INSERT OR IGNORE INTO Pokemon (TypeID,AbilityIDs,MoveIDs,PokemonName,OverallStrength) VALUES (?,?,?,?,?)",(typeID,abilityIDs,moveIDs,name,pokemonOverallStr))
            except:
                continue
        conn.commit()

    # add documentation
    def calculationsFile(self, cur, con):
        cur.execute("SELECT Pokemon.OverallStrength, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID")
        type_pokestr_lst = cur.fetchall()
        cur.execute("SELECT Moves.OverallStrength, Type.TypeName FROM Moves JOIN Type ON Moves.TypeID = Type.TypeID")
        type_movestr_lst = cur.fetchall()
        cur.execute("SELECT AbilityIDs, OverallStrength FROM Pokemon")
        ability_lst = cur.fetchall()
        cur.execute("SELECT AbilityID, AbilityName FROM Ability")
        ability_names = cur.fetchall()

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

        for key, value in poke_combined_dict.items():
            poke_combined_dict[key] = round(sum(value)/len(value),2)

        for key, value in move_combined_dict.items():
            move_combined_dict[key] = round(sum(value)/len(value),2)

        f = open("poke.txt", "w")
        f.write("Strongest Pokemon Type: " + str(sorted(poke_combined_dict, key=poke_combined_dict.get, reverse=True)[0]) + "\n")
        f.write("Weakest Pokemon Type: " + str(sorted(poke_combined_dict, key=poke_combined_dict.get, reverse=True)[-1]) + "\n")
        f.write("Strongest Move Type: " + str(sorted(move_combined_dict, key=move_combined_dict.get, reverse=True)[0]) + "\n")
        f.write("Weakest Move Type: " + str(sorted(move_combined_dict, key=move_combined_dict.get, reverse=True)[-1]) + "\n")
        f.write("Strongest Ability: " + str(sorted(ability_name_dict, key=ability_name_dict.get, reverse=True)[0]).capitalize() + "\n")
        f.write("Weakest Ability: " + str(sorted(ability_name_dict, key=ability_name_dict.get, reverse=True)[-1]).capitalize() + "\n")
        
        f.close()
        
    # add documentation here too
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
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#EEEEEE')
        ax.xaxis.grid(True, color='#EEEEEE')
       
        x = np.array(accuracy_lst)
        y = np.array(power_lst)

        m, b = np.polyfit(x, y, 1)
        plt.plot(x, (m*x+b))
        
        r = np.corrcoef(x, y)
        corr_coeff = (r[1, 0])

        plt.text(.03, .96, 'Correlation Coefficent = ' + str(round(corr_coeff,2)), ha='left', va='top', transform=ax.transAxes, weight='semibold')

        plt.tight_layout()

        plt.show()

    #add documnetation here
    #change code so that each type has a different color for their overallstr points
    def moveTypeStrVisualization1(self, cur, conn):
        cur.execute("SELECT Moves.OverallStrength, Type.TypeName FROM Moves JOIN Type ON Moves.TypeID = Type.TypeID")
        type_movestr_lst = cur.fetchall()
        type_lst = []
        overallstr_lst = []
        for tup in type_movestr_lst:
            type_lst.append(tup[1])
            overallstr_lst.append(tup[0])

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

    # add documentation here

    def moveTypeStrVisualization2(self, cur, conn):
        cur.execute("SELECT Moves.OverallStrength, Type.TypeName FROM Moves JOIN Type ON Moves.TypeID = Type.TypeID")
        type_movestr_lst = cur.fetchall()
        combined_dict = {}
        for tup in type_movestr_lst:
            if tup[1] not in combined_dict:
                combined_dict[tup[1]] = [tup[0]]
            else:
                combined_dict[tup[1]].append(tup[0])
        
        avg_lst = []
        for value in combined_dict.values():
            avg_lst.append(sum(value)/len(value))

        types = list(combined_dict.keys())

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

# add documentation 
    def pokemonTypeStrVisualization1(self, cur, conn):
        cur.execute("SELECT Pokemon.OverallStrength, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID")
        type_pokestr_lst = cur.fetchall()
        type_lst = []
        overallstr_lst = []
        for tup in type_pokestr_lst:
            type_lst.append(tup[1])
            overallstr_lst.append(tup[0])

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
    

# add documentation
    def pokemonTypeStrVisualization2(self, cur, conn):
        cur.execute("SELECT Pokemon.OverallStrength, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID")
        type_pokestr_lst = cur.fetchall()
        combined_dict = {}
        for tup in type_pokestr_lst:
            if tup[1] not in combined_dict:
                combined_dict[tup[1]] = [tup[0]]
            else:
                combined_dict[tup[1]].append(tup[0])

        avg_lst = []
        for value in combined_dict.values():
             avg_lst.append(sum(value)/len(value))

        types = list(combined_dict.keys())
    
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
    

    def AbilityCommonalityVisualization(self, cur, conn):
        cur.execute("SELECT AbilityIDs, OverallStrength FROM Pokemon")
        ability_lst = cur.fetchall()
        cur.execute("SELECT AbilityID, Count FROM Ability")
        count_lst = cur.fetchall()

        ability_overallstr_dict = {}
        for tup in ability_lst:
            for abilityID in tup[0].split(","):
                if abilityID not in ability_overallstr_dict:
                    ability_overallstr_dict[abilityID] = [tup[1]]
                else:
                    ability_overallstr_dict[abilityID].append(tup[1])

        for key, value in ability_overallstr_dict.items():
            ability_overallstr_dict[key] = round(sum(value)/len(value),2)

        y_lst = list(ability_overallstr_dict.values())

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
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#EEEEEE')
        ax.xaxis.grid(True, color='#EEEEEE')
       
        x = np.array(x_lst)
        y = np.array(y_lst)

        m, b = np.polyfit(x, y, 1)
        plt.plot(x, (m*x+b))
        
        r = np.corrcoef(x, y)
        corr_coeff = (r[1, 0])

        plt.text(.03, .96, 'Correlation Coefficent = ' + str(round(corr_coeff,2)), ha='left', va='top', transform=ax.transAxes, weight='semibold')

        plt.tight_layout()

        plt.show()

def main():
    # Set up
    conn = sqlite3.connect('PokeDatabase.db')
    cur=conn.cursor()
    server = Pokemon()
    server.createStructure(cur,conn)
    print("Create structure has finished")
    
    # Data collection from APIs and website
    pokemonDiction= server.getPokemonNameTypes(cur,conn,25)
    print("Pokemon Name Types has finished")
    pokemonMoveDiction=server.getPokemonMoves(cur,conn,pokemonDiction)
    print("Pokemon moves has finished")
    pokemonAbilityDiction=server.getPokemonAbilities(cur,conn,pokemonDiction)
    print("Pokemon Abilities has finished")
    abilityCountDiction=server.getAbilityCount(pokemonAbilityDiction)
    print("Ability Count has finished")
    mnapDiction=server.getMoveInfo(pokemonMoveDiction)
    print("Pokemon move info has finished")
    
    # Data inserted into tables
    server.insertTypeData(cur,conn,pokemonDiction,mnapDiction)
    print("Type table has finished")
    server.insertMoveData(cur,conn,mnapDiction)
    print("Move table has finished")
    server.insertAbilityData(cur,conn,pokemonAbilityDiction,abilityCountDiction)
    print("Ability table has finished")
    server.insertPokemonData(cur,conn,pokemonDiction,pokemonMoveDiction,pokemonAbilityDiction)
    print("Pokemon table has finished")
    
    # Calculations
    server.calculationsFile(cur, conn)
    print("Calculations file has finished")
    
    # Visualizations
    server.powerAccuracyVisualization(cur, conn)
    print("Move Power to Move Accuracy Graph has finished")
    server.moveTypeStrVisualization1(cur, conn)
    print("Move Type to Overall Strength Graph (1) has finished")
    server.moveTypeStrVisualization2(cur, conn)
    print("Move Type to Overall Strength Graph (2) has finished")
    server.pokemonTypeStrVisualization1(cur, conn)
    print("Poke Type to Overall Strength Graph (1) has finished")
    server.pokemonTypeStrVisualization2(cur, conn)
    print("Poke Type to Overall Strength Graph (2) has finished")
    server.AbilityCommonalityVisualization(cur, conn)
    print("Ability Commonality to Overall Strength Graph has finished")


main()