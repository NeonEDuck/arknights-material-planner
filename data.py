import re
import hashlib
from pathlib import Path
import requests
import json
from opencc import OpenCC

ARKNIGHTS_GAMEDATA_JSON_NAME = 'arknights_gamedata.json'
ARKNIGHTS_GAMEDATA_JSON_VERSION = '1.0.0'

GITHUB_COMMITS_URL      = 'https://api.github.com/repos/Kengxxiao/ArknightsGameData/commits/master'
OPERATOR_TABLE_URL      = 'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/character_table.json'
ITEM_TABLE_URL          = 'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/item_table.json'
SKILL_TABLE_URL         = 'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/skill_table.json'
UNIEQUIP_TABLE_URL      = 'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/uniequip_table.json'
BUILDING_DATA_URL       = 'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/building_data.json'
IMAGE_URL_PREFIX        = 'https://prts.wiki/images/'
AVATAR_IMAGE_PREFIX     = '头像_'
ITEM_IMAGE_PREFIX       = '道具_带框_'
SKILL_IMAGE_PREFIX      = '技能_'
UNIEQUIP_IMAGE_PREFIX   = '模组_'

data_generated = False
materials = {}
operators = {}

def convert_to_image_link(name):
    if not re.match(r'\.png$', name):
        name = f'{name}.png'
    md5_name = hashlib.md5(name.encode('utf-8')).hexdigest()

    return str(Path(IMAGE_URL_PREFIX, md5_name[0], md5_name[:2], name))

def generate_data():
    commits_res = requests.get(GITHUB_COMMITS_URL)
    latest_sha = commits_res.json().get('sha', '')

    if Path('./private', ARKNIGHTS_GAMEDATA_JSON_NAME).is_file():
        with open(Path('./private', ARKNIGHTS_GAMEDATA_JSON_NAME), 'r', encoding='utf-8') as f:
            data = json.loads(f.read())

        if data.get('sha') == latest_sha and data.get('version') == ARKNIGHTS_GAMEDATA_JSON_VERSION:
            return (data['operators'], data['materials'])

    cc = OpenCC('s2t')

    item_res = requests.get(ITEM_TABLE_URL)
    item_data = item_res.json().get('items', {})

    mod_res = requests.get(UNIEQUIP_TABLE_URL)
    mod_data = mod_res.json().get('equipDict', {})

    skill_res = requests.get(SKILL_TABLE_URL)
    skill_data = skill_res.json()

    building_res = requests.get(BUILDING_DATA_URL)
    building_data = building_res.json()

    operators_res = requests.get(OPERATOR_TABLE_URL)
    unfiltered_operators = operators_res.json()

    operator_dict = {}
    item_set = {
        '3301',                 # 技巧概要·卷1
        '3302',                 # 技巧概要·卷2
        '3303',                 # 技巧概要·卷3
        'mod_unlock_token',     # 模组數據塊
        'mod_update_token_1',   # 數據增補條
        'mod_update_token_2',   # 數據增補儀
    }

    for operator_id, operator_data in {k: v for k, v in unfiltered_operators.items() if re.match(r'^char_', k)}.items():
        operator_dict[operator_id] = (operator := {
            'name': cc.convert(operator_data['name']),
            'art': convert_to_image_link(f"{AVATAR_IMAGE_PREFIX}{operator_data['name']}"),
            'phases': [],
            'skills': [],
            'uniequips': [],
        })

        for phase in operator_data.get('phases', []):
            for item in phase.get('evolveCost', None) or []:
                item_set.add(item['id'])
            operator['phases'].append({
                'maxLevel': phase.get('maxLevel'),
                'evolveCost': phase.get('evolveCost')
            })

        for skill in operator_data.get('skills', []):
            skill['skillName'] = skill_data[skill['skillId']]['levels'][0]['name']

            for cond in skill.get('levelUpCostCond', []):
                for item in cond.get('levelUpCost') or []:
                    item_set.add(item['id'])

            operator['skills'].append({
                'skillId': skill['skillId'],
                'skillName': cc.convert(skill['skillName']),
                'art': convert_to_image_link(f"{SKILL_IMAGE_PREFIX}{skill['skillName']}"),
                'levelUpCosts': [x.get('levelUpCost', {}) for x in skill.get('levelUpCostCond', [])]
            })

        operator['uniequips'] = [
            {
                'uniEquipId': x['uniEquipId'],
                'uniEquipName': cc.convert(x['uniEquipName']),
                'art': convert_to_image_link(f"{UNIEQUIP_IMAGE_PREFIX}{x['uniEquipName']}") if i > 0 else None,
                'typeIcon': x['typeIcon'],
                'itemCost': x['itemCost'],
            } for i, x in enumerate(sorted(
                filter(
                    lambda x: (x['charId'] == operator_id),
                    [v for v in mod_data.values()]
                ),
                key=lambda x: x['uniEquipId']
            ))
        ]

    material_dict = {
        d['itemId']: {
            'id': d['itemId'],
            'name': cc.convert(d['name']),
            'art': convert_to_image_link(f"{ITEM_IMAGE_PREFIX}{d['name']}"),
            'formulas': [
                {
                    'formulaId': f['formulaId'],
                    'count': f['count'],
                    'goldCost': f['goldCost'],
                    'costs': f['costs'],
                }
                for _, f in filter(lambda x: x[1]['formulaId'] in (y['formulaId'] for y in d['buildingProductList']), building_data['workshopFormulas'].items())
            ]
        } for d in sorted(
            sorted(
                [
                    item_data[x] for x in item_set
                ],
                key=lambda x: x['sortId'], reverse=True
            ),
            key=lambda x: x['rarity']
        )
    }

    with open(Path('./private', ARKNIGHTS_GAMEDATA_JSON_NAME), 'w', encoding='utf-8') as f:
        f.write(json.dumps({
            'sha': latest_sha,
            'version': ARKNIGHTS_GAMEDATA_JSON_VERSION,
            'operators': operator_dict,
            'materials': material_dict,
        }, ensure_ascii=False, separators=[',', ':']))

    return (operator_dict, material_dict)


if not Path('./private').is_dir():
    Path('./private').mkdir()

if not data_generated:
    operators, materials = generate_data()
    data_generated = True