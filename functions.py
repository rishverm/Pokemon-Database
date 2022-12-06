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
    def getPokemonMoves(self,cur,conn,pokemonDiction):
        pokemonNames= list(pokemonDiction.keys())
        returnedPokemonMoveDiction={}
        for pokemon in pokemonNames:
            iter=0
            url= "https://pokeapi.co/api/v2/pokemon/" + pokemon.lower() + "/"
            r=requests.get(url)
            if r.ok:
                diction=json.loads(r.text)
                movelist=[]
                for move in diction['moves']:
                    moveurl= "https://pokeapi.co/api/v2/move/" + move['move']['name'].lower() + "/"
                    moveurl= moveurl.replace(' ','-')
                    re=requests.get(moveurl)
                    moveDict=json.loads(re.text)
                    cur.execute("Select MoveName from Moves")
                    if moveDict['power']!=None and moveDict['accuracy']!=None and iter < 9: 
                        iter+=1
                        movelist.append(move['move']['name'])
                    elif iter >= 9:
                        break
                returnedPokemonMoveDiction[pokemon]=movelist
                
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
                if len(moveIDs)==0:
                    continue
                cur.execute("INSERT OR IGNORE INTO Pokemon (TypeID,AbilityIDs,MoveIDs,PokemonName) VALUES (?,?,?,?)",(typeID,abilityIDs,moveIDs,name))
            except:
                continue
        conn.commit()

    #creates file ADD MORE HERE WHEN YOU ARE DONE
    # TALK ABOUT WHAT THE FUNCTION DOES HERE
    # ...............
    def pokemonTypeStrCalculator(self, cur, conn):
            cur.execute("SELECT Pokemon.MoveIDs, Type.TypeName FROM Pokemon JOIN Type ON Pokemon.TypeID = Type.TypeID")
            poke_type_move_lst = cur.fetchall()
            conn.commit()
            cur.execute("SELECT MoveID, OverallStrength FROM Moves")
            move_str_lst = cur.fetchall()
            conn.commit()
            
            move_str_dict = {}
            for tup in move_str_lst:
                move_str_dict[tup[0]] = tup[1]

            type_overallstr_dict = {}
            for tup in poke_type_move_lst:
                for item in tup:
                    if item == tup[0]:
                        total = 0
                        for num in item.split(","):
                            num = int(num)
                            num = move_str_dict[num]
                            total += num
                        if tup[1] not in type_overallstr_dict:
                            type_overallstr_dict[tup[1]] = [total/len(item.split(","))]
                        else:
                            type_overallstr_dict[tup[1]].append(total/len(item.split(",")))
                            
            return type_overallstr_dict

    def calculationsFile(self,calculation_dict):
        f = open("poke.csv", "w")
        f.write("PokeType,OverallStr" + "\n")
        for key, value in calculation_dict.items():
            f.write(key + "," + str(round(sum(value)/len(value), 2)) + "\n")
        f.close()
        
    #You must select some data from all of the tables in your database and calculate
    #something from that data (20 points). You could calculate the count of how many items
     #occur on a particular day of the week or the average of the number of items per day.
     #● You must do at least one database join to select your data (20 points).
     #● Write out the calculated data to a file as text (10 points) 

    # add documentation here too
    def powerAccuracyVisualization(self, cur, conn):
        cur.execute("SELECT Accuracy, Power FROM Moves")
        move_info_lst = cur.fetchall()
        conn.commit()
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
        move_info_lst = cur.fetchall()
        conn.commit()
        type_lst = []
        overallstr_lst = []
        for tup in move_info_lst:
            type_lst.append(tup[1])
            overallstr_lst.append(tup[0])

        color_lst = []
        for tup in move_info_lst:
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
        move_info_lst = cur.fetchall()
        conn.commit()
        combined_dict = {}
        for tup in move_info_lst:
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

        plt.title("Average Move Type to Overall Strength", pad=15, weight="bold", color='#333333')
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
    def pokemonTypeStrVisualization1(self,calculation_dict):
        pass
            #for key, value in type_overallstr_dict.items():
            # type_overallstr_dict[key] = (round(sum(value)/len(value), 2))
    

# add documentation
    def pokemonTypeStrVisualization2(self,calculation_dict):
        for key, value in calculation_dict.items():
               calculation_dict[key] = (round(sum(value)/len(value), 2))
    
        color_lst = []
        for key in calculation_dict.keys():
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

        bars = plt.bar(list(calculation_dict.keys()),list(calculation_dict.values()),edgecolor='black',color=color_lst)

        plt.title("Average Poke Type to Overall Strength", pad=15, weight="bold", color='#333333')
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
        
def main():
    conn = sqlite3.connect('PokeDatabase.db')
    cur=conn.cursor()
    server = Pokemon()
    server.createStructure(cur,conn)
    print("Create structure has finished")
    pokemonDiction= server.getPokemonNameTypes(25)
    print("Pokemon Name Types has finished")
    pokemonMoveDiction=server.getPokemonMoves(cur,conn,pokemonDiction)
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
    server.calculationsFile(server.pokemonTypeStrCalculator(cur, conn))
    print("Calculations file has finished")
    server.powerAccuracyVisualization(cur, conn)
    print("Move Power to Move Accuracy Graph has finished")
    server.moveTypeStrVisualization1(cur, conn)
    print("Move Type to Overall Strength Graph (1) has finished")
    server.moveTypeStrVisualization2(cur, conn)
    print("Move Type to Overall Strength Graph (2) has finished")
    server.pokemonTypeStrVisualization2(server.pokemonTypeStrCalculator(cur, conn))
    print("Poke Type to Overall Strength Graph (2) has finished")

    

    #server.pokemonTypeStrVisualization1(cur, conn)
    #print("Pokemon Type Overall Strength Graph (1) has finished")



main()