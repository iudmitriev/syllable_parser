from g2p_en import G2p

import re
import json

from src.punctuation_mark import PunctuationMark


def read_text(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.strip().split() for line in lines]


def parse_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    with open('word_data/replacer.json', 'r') as f:
        replace_dict = json.load(f)
    parsed = []
    for line in lines:
        for to_replace, replacer in replace_dict.items():
            line = line.replace(to_replace, replacer)

        raw_punctuation_marks = [r"\n", r" ", r",", r";", r"!", r"\?", r"-", r"—", r"―", r"\(", r"\)", ":", "“", "”"]
        punctuation_marks = ["\n", " ", ",", ";", "!", "?", "-", "—", "―", "(", ")", ":", "“", "”"]
        re_expression = r"(" + r"|".join(raw_punctuation_marks) + r")"

        line_splited = re.split(re_expression, line.strip())
        for word in line_splited:
            if word == '':
                continue
            if word in punctuation_marks:
                parsed.append(PunctuationMark(word))
            else:
                parsed.append(word)
        parsed.append(PunctuationMark('\n'))
    return parsed
