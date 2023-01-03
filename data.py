import re
import hashlib
from pathlib import Path
import requests
import json
from opencc import OpenCC

ARKNIGHTS_GAMEDATA_JSON_NAME = 'arknights_gamedata.json'
ARKNIGHTS_GAMEDATA_JSON_VERSION = '1.0.2'

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
FIXED_NAME_TABLE        = {
    'operators': {
        'char_199_yak': '角峰',
        'char_128_plosis': '白面鴞',
        'char_4043_erato': '埃拉托',
    },
    'materials': {
        '30011': '源岩',
        '30012': '固源岩',
        '30013': '固源岩组',
        '30014': '提纯源岩',
    },
}

data_generated = False
materials = {}
operators = {}

# 圖片連結的文字轉換(名稱中文轉md5)
def convert_to_image_link(name):
    if not re.match(r'\.png$', name):
        name = f'{name}.png'
    md5_name = hashlib.md5(name.encode('utf-8')).hexdigest()

    return str(Path(IMAGE_URL_PREFIX, md5_name[0], md5_name[:2], name))

# 載入JSON資料
def generate_data():
    commits_res = requests.get(GITHUB_COMMITS_URL)
    latest_sha = commits_res.json().get('sha', '')

    # 讀取遊戲資料JSON
    if Path('./private', ARKNIGHTS_GAMEDATA_JSON_NAME).is_file():
        with open(Path('./private', ARKNIGHTS_GAMEDATA_JSON_NAME), 'r', encoding='utf-8') as f:
            data = json.loads(f.read())

        # 檢查資料版本
        if data.get('sha') == latest_sha and data.get('version') == ARKNIGHTS_GAMEDATA_JSON_VERSION:
            return (data['operators'], data['materials'])

    # 中文簡轉繁
    cc = OpenCC('s2t')

    # 物品資料
    item_res = requests.get(ITEM_TABLE_URL)
    item_data = item_res.json().get('items', {})

    # 模組資料
    mod_res = requests.get(UNIEQUIP_TABLE_URL)
    mod_data = mod_res.json().get('equipDict', {})

    # 技能資料
    skill_res = requests.get(SKILL_TABLE_URL)
    skill_data = skill_res.json()

    # 基建資料
    building_res = requests.get(BUILDING_DATA_URL)
    building_data = building_res.json()

    # 幹員資料
    operators_res = requests.get(OPERATOR_TABLE_URL)
    unfiltered_operators = operators_res.json()

    operator_dict = {}
    item_set = {
        'mod_unlock_token',     # 模组數據塊
        'mod_update_token_1',   # 數據增補條
        'mod_update_token_2',   # 數據增補儀
    }

    # id:char_[num]_[code]
    # Lancet-2:char_285_medic2

    # 幹員資料整理
    for operator_id, operator_data in {k: v for k, v in unfiltered_operators.items() if re.match(r'^char_', k)}.items():
        operator_dict[operator_id] = (operator := {
            'id': operator_id,
            'name': FIXED_NAME_TABLE['operators'].get(operator_id, cc.convert(operator_data['name'])),  # 幹員名稱
            'art': convert_to_image_link(f"{AVATAR_IMAGE_PREFIX}{operator_data['name']}"),              # 幹員頭像
            'phases': [],                                                                               # 幹員數值
            'skills': [],                                                                               # 幹員技能
            'uniequips': [],                                                                            # 幹員模組
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

    new_item_set = item_data.copy()
    while True:
        check_item_set = new_item_set.copy()
        new_item_set = set()
        if len(check_item_set) == 0:
            break

        for item_id in check_item_set:
            for formula in item_data[item_id]['buildingProductList']:
                if formula['roomType'] != 'WORKSHOP':
                    continue
                formula_id = formula['formulaId']
                formula_data = building_data['workshopFormulas'][formula_id]
                for cost in formula_data['costs']:
                    if cost['id'] not in item_set:
                        new_item_set.add(cost['id'])
                        item_set.add(cost['id'])

    # 素材資料整理
    material_dict = {
        d['itemId']: {
            'id': d['itemId'],
            'name': FIXED_NAME_TABLE['materials'].get(d['itemId'], cc.convert(d['name'])) ,
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

    # 資料紀錄
    with open(Path('./private', ARKNIGHTS_GAMEDATA_JSON_NAME), 'w', encoding='utf-8') as f:
        f.write(json.dumps({
            'sha': latest_sha,
            'version': ARKNIGHTS_GAMEDATA_JSON_VERSION,
            'operators': operator_dict,
            'materials': material_dict,
        }, ensure_ascii=False, separators=[',', ':']))

    return (operator_dict, material_dict)

# 幹員基本資料(名稱、圖片)
def operators_info_data(operators, input):
    data = {}
    op_data = {id:op for id, op in operators.items() if re.match(r'^char_', id)}# 幹員資料

    for op_data_value in op_data.values():
        if re.match(f'.*{input}.*',op_data_value['name']):
            data['name'] = op_data_value['name']
            data['art'] = op_data_value['art']

    return json.dumps(data, ensure_ascii=False, separators=[',', ':'])

# 幹員晉升資料(精英化I、II)
def operators_evol_data(operators, materials, input):
    data = {}
    mat_name = [mat['name'] for mat in materials.values()]# 素材名稱
    op_data = {id:op for id, op in operators.items() if re.match(r'^char_', id)}# 幹員資料

    for op_data_value in op_data.values():
        if re.match(f'.*{input}.*',op_data_value['name']):
            i = 1
            for phase_data in op_data_value['phases']:
                if phase_data['evolveCost'] is not None:
                    j = 1
                    value = {}
                    for evolveCost in phase_data['evolveCost']:
                        title = f'evol_{i}_{j}'
                        mat_name = materials[evolveCost['id']]['name']
                        mat_count = evolveCost['count']
                        mat_art = materials[evolveCost['id']]['art']
                        mat_values = f'{mat_name},{mat_count},{mat_art}'
                        value[title] = mat_values
                        j+=1
                    data[f'evol_{i}'] = value
                    i+=1

    return json.dumps(data, ensure_ascii=False, separators=[',', ':'])

# 幹員技能資料(專精I、II、III)
def operators_skill_data(operators, materials, input):
    data = {}
    value = {}
    mat_name = [mat['name'] for mat in materials.values()]# 素材名稱
    op_data = {id:op for id, op in operators.items() if re.match(r'^char_', id)}# 幹員資料

    for op_data_value in op_data.values():
        if re.match(f'.*{input}.*',op_data_value['name']):
            k = 1
            for phase_data in op_data_value['skills']:
                info = {}
                info[f'skill_{k}_name'] = phase_data['skillName']
                info[f'skill_{k}_art'] = phase_data['art']
                if len(phase_data['levelUpCosts']) != 0:
                    i = 1
                    for skillItems in phase_data['levelUpCosts']:
                        j = 1
                        for skillItemCost in skillItems:
                            title = f'skill_{i}_{j}'
                            mat_name = materials[skillItemCost['id']]['name']
                            mat_count = skillItemCost['count']
                            mat_art = materials[skillItemCost['id']]['art']
                            mat_values = f'{mat_name},{mat_count},{mat_art}'
                            value[title] = mat_values
                            j+=1
                        i+=1
                    info[f'skill_{k}_values'] = value
                else:
                    info[f'skill_{k}_values'] = "該技能無專精資訊"
                data[f'skill_{k}'] = info
                k+=1
                
    
    return json.dumps(data, ensure_ascii=False, separators=[',', ':'])

# 幹員模組資料
def operators_uniequip_data(operators, materials, input):
    data = {}
    value = {}
    mat_name = [mat['name'] for mat in materials.values()]# 素材名稱
    op_data = {id:op for id, op in operators.items() if re.match(r'^char_', id)}# 幹員資料

    itemCost:Dict[str,any]
    for op_data_value in op_data.values():
        if re.match(f'.*{input}.*',op_data_value['name']):
            for phase_data in op_data_value['uniequips']:
                if phase_data['art'] is not None:
                    data['name'] = phase_data['uniEquipName']
                    data['art'] = phase_data['art']
                    itemCost = phase_data['itemCost']
                    for id, v in itemCost.items():
                        i = 1

                        for modItems in v:
                            if modItems['id'] != '4001':
                                title = f'mod_{id}_{i}'
                                mat_name = materials[modItems['id']]['name']
                                mat_count = modItems['count']
                                mat_art = materials[modItems['id']]['art']
                                mat_values = f'{mat_name},{mat_count},{mat_art}'
                                value[title] = mat_values
                            i+=1
                    data[f'values'] = value

    return json.dumps(data, ensure_ascii=False, separators=[',', ':'])

# 若private資料夾不存在，即新建
if not Path('./private').is_dir():
    Path('./private').mkdir()

# 若遊戲資料JSON尚未建立，即新建
if not data_generated:
    operators, materials = generate_data()
    data_generated = True