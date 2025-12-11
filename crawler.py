import requests
import json
import os
import sys
import datetime

modules = {}

overwrite_module_data = {
    'ExEv': [['term', 'HS']],
    'ComEng1': [['term', 'FS']],
    'ComEng2': [['term', 'HS']],
    'SEProj': [['term', 'FS'],['isMandatory', True]],
    'PF': [['isDeactivated', True]],
    'SE1': [['successormoduleShortKey', 'SEP2']],
    'SE2': [['successormoduleShortKey', 'SEP2']],
    'SEP1': [['predecessormoduleShortKey', 'SE1'],['isMandatory', True]],
    'SEP2': [['predecessormoduleShortKey', 'SE2'],['isMandatory', True]],
    'BuPro': [['successormoduleShortKey', 'WI2']],
    'WI2': [['predecessormoduleShortKey', 'BuPro']],
    'RheKI': [['successormoduleShortKey', 'RheKoI']],
    'RheKoI': [['predecessormoduleShortKey', 'RheKI']],
    'RKI': [['successormoduleShortKey', 'RheKI']],
    'RheKI': [['predecessormoduleShortKey', 'RKI']],
    'SDW': [['successormoduleShortKey', 'IBN']],
    'IBN': [['predecessormoduleShortKey', 'SDW']],
    'FunProg': [['successormoduleShortKey', 'FP']],
    'FP': [['predecessormoduleShortKey', 'FunProg']],
    'IBN': [['predecessormoduleShortKey', 'SDW']],
    'WIoT': [['successormoduleShortKey', 'WsoT']],
    'WsoT': [['predecessormoduleShortKey', 'WIoT']],
    'SecSW': [['successormoduleShortKey', 'SecSoW']],
    'SecSoW': [['predecessormoduleShortKey', 'SecSW']],
    'Inno2': [['successormoduleShortKey', 'Inno_2']],
    'Inno_2': [['predecessormoduleShortKey', 'Inno2']],
    'BAI21': [['term', 'both'],['isMandatory', True]],
    'SAI21': [['term', 'both'],['isMandatory', True]],
    'IKBH': [['successormoduleShortKey', 'IKBD']],
    'IKBD': [['predecessormoduleShortKey', 'IKBH']]
}

def write_json(data, filename):
    # Taken from https://stackoverflow.com/a/22281062
    def set_default(obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        raise TypeError

    with open(filename, 'w') as output:
        json.dump(data, output, indent=2, ensure_ascii=False, default=set_default)
        output.write('\n')

def getShortNameForModule(kuerzel):
    return kuerzel.removeprefix('M_').replace('_p', 'p')

def getIdForCategory(kuerzel):
    return kuerzel.removeprefix('I-').removeprefix('I_').removeprefix('Kat_').replace('IKTS-help', 'GWRIKTS')

def create_module(content):
    return {
        'id': content['id'],
        'shortKey': getShortNameForModule(content['kuerzel']),
        'name': content['bezeichnung'].strip(),
        'url': content['url'],
        'focuses': [],
        'categories': set(),
        'ects': 0,
        'isDeactivated': False,
        'term': '',
        'recommendedmodules': [],
        'recommendedmoduleIds': set(),
        'recommendedmoduleShortKeys': set(),
        'dependentmodules': [],
        'dependentmoduleIds': set(),
        'dependentmoduleShortKeys': set(),
        'successormoduleShortKey': None,
        'predecessormoduleShortKey': None
    }

def set_term_for_module(module, moduleContent):
    if 'durchfuehrungen' in moduleContent:
        if 'endSemester' in moduleContent['durchfuehrungen']:
            beginSemester = moduleContent['durchfuehrungen']['beginSemester']
            endSemester = moduleContent['durchfuehrungen']['endSemester']

            if endSemester != 'HS' and endSemester != 'FS':
                print(f'Module {module["id"]} has no valid term')
            elif beginSemester != 'HS' and beginSemester != 'FS':
                module['term'] = endSemester
            elif beginSemester != endSemester:
                module['term'] = 'both'
            else:
                module['term'] = endSemester
    else:
        print(f'Module {module["shortKey"]} {module["id"]} has no term')

def set_successor_and_predecessor_for_module(module, moduleContent, modules):
    if 'nachfolger' in moduleContent and moduleContent['nachfolger']['kuerzel'] != moduleContent['kuerzel']:
        successormoduleShortKey = getShortNameForModule(moduleContent['nachfolger']['kuerzel'])
        module['successormoduleShortKey'] = successormoduleShortKey
        if successormoduleShortKey in modules and modules[successormoduleShortKey]['predecessormoduleShortKey'] == "":
            modules[successormoduleShortKey]['predecessormoduleShortKey'] = module['shortKey']
    if 'vorgaenger' in moduleContent and moduleContent['vorgaenger']['kuerzel'] != moduleContent['kuerzel']:
        predecessormoduleShortKey = getShortNameForModule(moduleContent['vorgaenger']['kuerzel'])
        module['predecessormoduleShortKey'] = predecessormoduleShortKey
        if predecessormoduleShortKey in modules and modules[predecessormoduleShortKey]['successormoduleShortKey'] == "":
            modules[predecessormoduleShortKey]['successormoduleShortKey'] = module['shortKey']

def set_recommended_modules_for_module(module, moduleContent):
    if 'empfehlungen' in moduleContent:
        # print(f"Empfehlungen für {module['id']} - {module['shortKey']}")
        for empfehlung in moduleContent['empfehlungen']:
            # print(empfehlung['id'],empfehlung['kuerzel'])
            recommendedmoduleShortKey = getShortNameForModule(empfehlung['kuerzel'])

            recommendedModule = {empfehlung['id']:recommendedmoduleShortKey}

            if recommendedModule not in module['recommendedmodules']:
                module['recommendedmodules'].append(recommendedModule)
            module['recommendedmoduleIds'].add(empfehlung['id'])
            module['recommendedmoduleShortKeys'].add(recommendedmoduleShortKey)
            # if recommendedmoduleShortKey in modules:
                # modules not for "Studiengang Informatik" can be recommended, such as AN1aE, which we do not care about
    if 'voraussetzungen' in moduleContent:
        for voraussetzung in moduleContent['voraussetzungen']:
            recommendedmoduleShortKey = getShortNameForModule(voraussetzung['kuerzel'])
            module['recommendedmoduleIds'].add(voraussetzung['id'])
            module['recommendedmoduleShortKeys'].add(getShortNameForModule(voraussetzung['kuerzel']))
            
            recommendedModule = {voraussetzung['id']:recommendedmoduleShortKey}

            if recommendedModule not in module['recommendedmodules']:
                module['recommendedmodules'].append(recommendedModule)

def set_deactivated_for_module(module, moduleContent): 
    # assumption: module is deactivated, if 'zustand' is 'deaktiviert' and either (1) 'endJahr' of 'durchfuehrungen' was last year or earlier or (2) no 'durchfuehrungen' is defined
    if 'zustand' in moduleContent and moduleContent['zustand'] == 'deaktiviert':
        if 'durchfuehrungen' not in moduleContent:
            module['isDeactivated'] = True
        if 'durchfuehrungen' in moduleContent and 'endJahr' in moduleContent['durchfuehrungen']:
            currentYear = datetime.datetime.today().year
            if moduleContent['durchfuehrungen']['endJahr'] < currentYear:
                module['isDeactivated'] = True

def overwrite_module_with_data(module):
    # assumption: module is not Mandatory, unless defined otherwise in overwrite_module_data
    module['isMandatory'] = False

    if module['shortKey'] not in overwrite_module_data:
        return
    overwrite_data = overwrite_module_data[module['shortKey']]
    for data in overwrite_data:
        module[data[0]] = data[1]


def fetch_data_for_studienordnung(url, output_directory, additional_module_urls=[]):
    global modules

    content = requests.get(f'{BASE_URL}{url}').content
    jsonContent = json.loads(content)

    categories = {}
    focuses = []

    def enrich_module_from_json(module, moduleContent):
        # needed for modules, whose credits do not count towards "Studiengang Informatik"
        if 'kreditpunkte' in moduleContent and module['ects'] == 0:
            module['ects'] = moduleContent['kreditpunkte']

        set_term_for_module(module, moduleContent)

        set_successor_and_predecessor_for_module(module, moduleContent, modules)

        set_recommended_modules_for_module(module,moduleContent)

        set_deactivated_for_module(module, moduleContent)

        overwrite_module_with_data(module)

        if 'categories' in module:
            for cat in module['categories']:
                if cat['shortKey'] in categories:
                    categories[cat['shortKey']]['modules'].append(
                        {'id': module['id'], 'shortKey': module['shortKey'], 'name': module['name'], 'url': module['url']})
                elif cat['shortKey'] == 'GWRIKTS':
                    categories['gwr']['modules'].append(
                        {'id': module['id'], 'shortKey': module['shortKey'], 'name': module['name'], 'url': module['url']})

    # 'kredits' contains categories
    kredits = jsonContent['kredits']
    for kredit in kredits:
        category = kredit['kategorien'][0]

        if category['kuerzel'] == 'IKTS-help':
            continue

        catShortName = getIdForCategory(category['kuerzel'])
        categories[catShortName] = {
            'id': category['id'],
            'shortKey': catShortName,
            'required_ects': kredit['minKredits'],
            'name': category['bezeichnung'],
            'modules': [],
        }

    # 'zuordnungen' contains modules
    zuordnungen = jsonContent['zuordnungen']
    for zuordnung in zuordnungen:
        module = create_module(zuordnung)

        # For some reason each category is also present as a module.
        if module['shortKey'].startswith('Kat'):
            continue

        if 'kategorien' in zuordnung:
            module['categories'] = [{'shortKey': getIdForCategory(z['kuerzel']), 'name': z['bezeichnung'], 'ects': z['kreditpunkte']} for z in zuordnung['kategorien']]
            module['ects'] = zuordnung['kategorien'][0]['kreditpunkte']

        # IKTS modules are often split into two separate modules, one of them being a "Projektarbeit".
        # This ensures that they can be differentiated in the UI.
        if zuordnung['kuerzel'].endswith('_p'):
            module['name'] += ' (Projektarbeit)'

        modules[module['id']] = module

    for additional_module_url in additional_module_urls:
        moduleContent = json.loads(requests.get(f'{BASE_URL}{additional_module_url}').content)
        moduleContent['url'] = additional_module_url
        module = create_module(moduleContent)
        categoriesForStudienordnung = [z['kategorien'] for z in moduleContent['zuordnungen'] if z['url'] == url][0]
        module['categories'] = [{'shortKey': getIdForCategory(c['kuerzel']), 'name': c['bezeichnung'], 'ects': c['kreditpunkte']} for c in categoriesForStudienordnung]
        module['ects'] = moduleContent['kreditpunkte']
        modules[module['id']] = module

    for module in modules.values():
        try:
            moduleContent = json.loads(requests.get(f'{BASE_URL}{module["url"]}').content)
        except:
            print(f'Could not get data for {module["id"]} with {BASE_URL}{module["url"]}')
            continue
        enrich_module_from_json(module, moduleContent)


    for module in modules.values():
        for recommendedmoduleId in module['recommendedmoduleIds']:
            if recommendedmoduleId in modules:
                
                dependentModule = {module['id']:module['shortKey']}

                if dependentModule not in modules[recommendedmoduleId]['dependentmodules']:
                    modules[recommendedmoduleId]['dependentmodules'].append(dependentModule)
                    
                modules[recommendedmoduleId]['dependentmoduleShortKeys'].add(module['shortKey'])
                modules[recommendedmoduleId]['dependentmoduleIds'].add(module['id'])
                if modules[recommendedmoduleId]['isDeactivated'] == False:
                    continue

    # 'spezialisierungen' contains focuses
    spezialisierungen = jsonContent['spezialisierungen']
    for spez in spezialisierungen:
        focus = {
            'id': spez['id'],
            'shortKey': spez['kuerzel'],
            'url': spez['url'],
            'name': spez['bezeichnung'],
            'modules': []
        }
        focusContent = json.loads(requests.get(f'{BASE_URL}{spez["url"]}').content)
        for zuordnung in focusContent['zuordnungen']:
            moduleId = zuordnung['id']
            moduleShortKey = getShortNameForModule(zuordnung['kuerzel'])

            if moduleShortKey == 'WIoT':
                moduleShortKey = 'WsoT'

            if moduleId in modules:
                focus['modules'].append({
                    'id': moduleId,
                    'shortKey': moduleShortKey,
                    'name': modules[moduleId]['name'],
                    'url': modules[moduleId]['url']})

                modules[moduleId]['focuses'].append({'shortKey': focus['shortKey'], 'name': focus['name'], 'url': focus['url']})

        focus['modules'].sort(key = lambda x: x['id'])
        focus['modules'] = list({m['id']: m for m in focus['modules']}.values())
        focuses.append(focus)

    # id should be unique for each module
    idsSet = set([m['id'] for m in modules.values()])
    if len(idsSet) != len(modules):
        sys.exit(1)

    categories = list(categories.values())

    for category in categories:
        category['modules'].sort(key = lambda x: x['id'])

    categories.sort(key = lambda x: x['id'])
    focuses.sort(key = lambda x: x['id'])

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    write_json(categories, f'{output_directory}/categories.json')
    write_json(focuses, f'{output_directory}/focuses.json')


BASE_URL = 'https://studien.ost.ch/'

fetch_data_for_studienordnung('allStudies/10246_I.json', 'data23', ['allModules/28254_M_MGE.json', 'allModules/44037_M_IKBH.json', 'allModules/55066_M_IKBD.json'])
fetch_data_for_studienordnung('allStudies/10191_I.json', 'data21', ['allModules/28254_M_MGE.json'])

for module in modules.values():
    module['categoriesForColoring'] = sorted([category['shortKey'] for category in module['categories']])
    del module['focuses']
    del module['categories']

output_directory = 'data'

if not os.path.exists(output_directory):
    os.mkdir(output_directory)

modules = list(modules.values())
modules.sort(key = lambda x: x['id'])
write_json(modules, f'{output_directory}/modules.json')
