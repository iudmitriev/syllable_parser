from src.parser import parse_file
from src.phonemizer import phonemize, align, parse_aligned_words
from src.marker import stress_aligned_text, parse_rythmic_words

if __name__ == '__main__':

    parsed_text = parse_file('text.txt')
    phonemized_text = phonemize(parsed_text)
    aligned_phonemes = align(phonemized_text)
    parsed_aligned_text = parse_aligned_words(parsed_text, aligned_phonemes)

    stressed_text = stress_aligned_text(parsed_aligned_text)
    result = parse_rythmic_words(stressed_text)
    with open('result.txt', 'w') as f:
        f.write(result)
