from g2p_en import G2p

import subprocess
import os

from src.punctuation_mark import PunctuationMark
from src.word import Word


def phonemize(words):
    g2p = G2p()
    result = []
    for word in words:
        if isinstance(word, PunctuationMark):
            result.append(word)
            continue

        word_phonemed = g2p(word)
        result.append({
            'grapheme': word,
            'phoneme': word_phonemed
        })
    return result


def align(words_with_phonemes):
    request = ''
    for word in words_with_phonemes:
        if isinstance(word, PunctuationMark):
            continue

        request += ' '.join(list(word['grapheme']))
        request += '\t'
        request += ' '.join(list(word['phoneme']))
        request += '\n'
    
    tmp_filename = 'phonemes_to_align'

    with open(tmp_filename, 'w') as f:
        f.write(request)
    args = f"./m2m-aligner/m2m-aligner --errorInFile -i {tmp_filename}".split()
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()

    os.remove(tmp_filename)
    align_file = f'{tmp_filename}.m-mAlign.2-2.1-best.conYX.errorInFile.align'

    with open(align_file, 'r') as f:
        aligned_words = f.readlines()

    os.remove(align_file)
    os.remove(f'{tmp_filename}.m-mAlign.2-2.1-best.conYX.errorInFile.align.err')
    os.remove(f'{tmp_filename}.m-mAlign.2-2.1-best.conYX.errorInFile.align.model')

    return aligned_words


def parse_aligned_words(words, aligned_words):
    parsed = []
    current_word_index = 0
    for word in words:
        if isinstance(word, PunctuationMark):
            parsed.append(word)
            continue
    
        aligned_word = aligned_words[current_word_index].strip()
        current_word_index += 1

        if aligned_word == 'NO ALIGNMENT':
            parsed.append(word)
            continue
        
        grapheme, phoneme = aligned_word.strip().split('\t')
        grapheme_symbols = grapheme.strip('|').split('|')
        phoneme_symbols = phoneme.strip('|').split('|')

        parsed.append(Word(grapheme_symbols, phoneme_symbols))
    return parsed
