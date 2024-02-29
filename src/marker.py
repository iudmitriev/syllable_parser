import json

from src.punctuation_mark import PunctuationMark
from src.word import Word


def stress_aligned_text(parsed_aligned_text, rythm_suggestion=None):
    with open('word_data/unstressed_words.json', 'r') as f:
        always_unstressed = json.load(f)
    with open('word_data/metricly_dual_words.json', 'r') as f:
        metricly_dual = json.load(f)
    with open('word_data/known_words.json', 'r') as f:
        known_words = json.load(f)
    
    if rythm_suggestion is None:
        # prosaic mode
        always_unstressed += metricly_dual


    stressed_words = []
    current_rythm_pattern = rythm_suggestion
    stress_moved = False
    for word in parsed_aligned_text:
        if isinstance(word, PunctuationMark):
            if str(word) == '\n':
                current_rythm_pattern = rythm_suggestion
                stress_moved = False
            stressed_words.append(word)
        elif isinstance(word, str):
            # unaligned word
            if word.lower() in known_words:
                stressed_word = known_words[word.lower()]
                if word.lower() != word:
                    stressed_word = stressed_word.capitalize()
                stressed_words.append(stressed_word)
            else:
                stressed_words.append(f"<<<{word}>>>")
        elif isinstance(word, Word):
            if current_rythm_pattern is None:
                if str(word).lower() in always_unstressed:
                    suggested_stress = False
                else:
                    suggested_stress = True
            else:
                if len(current_rythm_pattern) >= word.num_vowels:
                    suggested_stress = any(current_rythm_pattern[:word.num_vowels])
                else:
                    suggested_stress = False
                
                if str(word).lower() in always_unstressed:
                    if suggested_stress:
                        stress_moved = True
                    suggested_stress = False
                else:
                    if stress_moved:
                        suggested_stress = True
                        stress_moved = False 
            
                current_rythm_pattern = current_rythm_pattern[word.num_vowels:]
            
            if suggested_stress:
                stressed_words.append(word.get_processed_str())
            else:
                stressed_words.append(word.get_processed_str(no_stress=True))
        else:
            raise ValueError(f'Unknown type in text: {type(word)}')
        
    return stressed_words


def parse_rythmic_words(stressed_text):
    punctuation_enders = ['.', ',', ';', '!', '?']
    result = ''
    wrote_something = False
    for word in stressed_text:
        if isinstance(word, PunctuationMark):
            if str(word) == '\n' and \
               len(result) >= 2 and not '|' in [result[-1], result[-2]]:
                result += '|'
            result += str(word)
            if str(word) in punctuation_enders and wrote_something:
                result += '|'
                wrote_something = False
        else:
            result += word
            if '<' in word:
                result += '|'
                wrote_something = False
            else:
                wrote_something = True
    return result
