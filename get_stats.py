import json
from pprint import pprint
import sqlite3
dbfile = './pysqlsimplecipher/output.db'


# Calcul les dégâts des attaques spéciales
def calc_super_attack_damage(base_attack: int, special_description: str):
    super_attack_multiplier = {
        "low": 1.3,
        # "damage": 1.7,
        "huge": 2,
        "destructive": 2,
        "extreme": 2.2,
        "mass": 2.2,
        "supreme": 2.5,
        "immense": 2.8,
        "colossal": 3,
        "mega-colossal": 3.5
    }
    total: int = 0
    for multiplier in super_attack_multiplier:
        if multiplier in special_description.split():
            total = base_attack * super_attack_multiplier[multiplier]
            print(super_attack_multiplier[multiplier])
            return round(total)
      

# Retourne l'élément et le type d'un personnage par rapport à la valeur de son élément
def get_type_class(element: int):
    elements = {
        "10": "Super AGL",
        '11': "Super TEQ",
        "12": "Super INT",
        "13": "Super STR",
        "14": "Super PHY",
        "20": "Extreme AGL",
        "21": "Extreme TEQ",
        "22": "Extreme INT",
        "23": "Extreme STR",
        "24": "Extreme PHY"
    }
    for el in elements:
        if int(el) == element:
            return elements[el]


# Extrait les infos sur les ennemies et les rounds depuis les info du jeu
def extract_enemies_info(input_file, output_file):
    with open(input_file + '.json') as json_data:
        d = json.load(json_data)
        json_data.close()
        i = 0
        informations = {
        
        }
        while(i < 15):
            if str(i) in d['sugoroku']['events']:
                if 'content' in d['sugoroku']['events'][str(i)]:
                    if 'enemies' in d['sugoroku']['events'][str(i)]['content']:
                        battles_infos = d['sugoroku']['events'][str(i)]['content']['battle_info']
                        enemies_infos = d['sugoroku']['events'][str(i)]['content']['enemies']
                        informations.update({
                                str(i): {
                                    "battles_infos": battles_infos,
                                    "enemies_infos": enemies_infos
                                }
                            }) 
            i += 1
    with open(f'{output_file}.json', 'w') as f:
        f.write(json.dumps(informations, indent=2))
       

# Après avoir extrait les infos, crée un fichier JSON avec toutes les informations nécéssaires sur le niveau donné
def get_enemies_info(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)  
        informations = {}
        fight_number = 1
    i = 1
    while(i < 15):
        if str(i) in data:
            round_number = len(data[str(i)]['battles_infos'])
   
            for info in data[str(i)]['enemies_infos']:
                
                con = sqlite3.connect(dbfile)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                char_and_special_info = "SELECT cards.name AS 'Nom', cards.lv_max AS 'Niveau Max', cards.element AS 'Type et Classe', special_sets.name AS 'Nom', special_sets.description as 'Description' FROM card_specials JOIN special_sets ON card_specials.special_set_id = special_sets.id JOIN cards ON card_specials.card_id = cards.id WHERE cards.id = ?"
                param = (info[0]['card_id'],)  
                cur.execute(char_and_special_info, param)
                special_description = ''
                boss_name = ''
                elements = ''
                cooldown = None
                special_attack_chance = None
                max_special_per_turn = None
                row = cur.fetchone()
                if row:
                    special_description = row['Description']
                    boss_name = row['Nom']
                    elements = get_type_class(row['Type et Classe'])
                else:
                    special_description = None
                
                ai_infos = "SELECT * FROM enemy_ai_conditions WHERE ai_type = ? ORDER BY id desc LIMIT 1"
                param = (info[0]['ai_type'],) 
                cur.execute(ai_infos, param)
                row = cur.fetchone()
                if row:
                    cooldown = row['min_interval']
                    special_attack_chance = row['weight']
                    max_special_per_turn = row['max_num_per_turn']
                skills = []
                for id in info[0]['enemy_skill_ids']:
                    skills_info = "SELECT description, eff_value1 FROM enemy_skills WHERE id = ?"
                    param = (id,)
                    cur.execute(skills_info, param)
                    row = cur.fetchone()
                    if row:
                        skills.append({
                            "description": row['description'],
                            "effect": row['eff_value1']
                        })

                con.close()
                key = f'fight_{str(fight_number)}'
                if key not in informations:
                    informations[key] = {'nb_of_round': round_number,'enemies': []}  # Initialisation de la structure
                informations[key]['enemies'].append({
                        'card_id': info[0]['card_id'],
                        'name': boss_name,
                        'type_and_class': elements,
                        'special_description': special_description,
                        "super_attack_damage": calc_super_attack_damage(info[0]['attack'], special_description),
                        'hp': info[0]['hp'],
                        'attack': info[0]['attack'],
                        'defence': info[0]['defence'],
                        'enemy_skills': skills,
                        'attack per turn': info[0]["multi_atk_num"],
                        'special_cooldown': cooldown,
                        'special_attack_chance': f"{special_attack_chance}%",
                        'max_special_per_turn': max_special_per_turn
                        }
                    )
            fight_number += 1
            with open(output_file, 'w') as output:
                json.dump(informations, output, indent = 2)
       
        i +=1

# extract_enemies_info('./raw/enn_surp_lvl_8', 'enn_surp_lvl_8_extracted')

get_enemies_info('enn_surp_lvl_8_extracted.json', './enemies_info/enn_surp_lvl_8.json')


