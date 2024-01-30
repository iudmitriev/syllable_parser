import json

from src.punctuation_mark import PunctuationMark
from src.word import Word


def stress_aligned_text(parsed_aligned_text):
    with open('word_data/unstressed_words.json', 'r') as f:
        always_unstressed = json.load(f)
    with open('word_data/known_words.json', 'r') as f:
        known_words = json.load(f)
    
    stressed_words = []
    for word in parsed_aligned_text:
        if isinstance(word, PunctuationMark):
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
            if str(word).lower() not in always_unstressed:
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
