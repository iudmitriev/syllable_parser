import json


def get_rythm(rythm):
    if rythm == 'prose':
        return None
    
    try:
        with open(f'rythms/{rythm}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print('Something went wrong: unknown rythm')
        return None