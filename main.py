from src.file_parser import parse_text, read_text
from src.phonemizer import phonemize, align, parse_aligned_words
from src.marker import stress_aligned_text, parse_rythmic_words
from src.rythm_parser import get_rythm

import argparse

def mark_rythmic_text(filename, rythm):
    parsed_text = parse_text(filename)
    phonemized_text = phonemize(parsed_text)
    aligned_phonemes = align(phonemized_text)
    parsed_aligned_text = parse_aligned_words(parsed_text, aligned_phonemes)

    rythm_suggestion = get_rythm(rythm)
    stressed_text = stress_aligned_text(
        parsed_aligned_text, 
        rythm_suggestion=rythm_suggestion
    )
    result = parse_rythmic_words(stressed_text)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rythm',
        choices=['prose', 'iamb', 'trochee', 'dactyl', 'amphibrach', 'anapaest'],
        default='prose', help='Rythm suggestion for text'
    )
 
    args = parser.parse_args()
    rythm = args.rythm
    
    text = read_text('text.txt')
    result = mark_rythmic_text(text, rythm)
    with open('result.txt', 'w') as f:
        f.write(result)
