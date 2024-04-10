from g2p_en import G2p

import re
import json

from src.punctuation_mark import PunctuationMark

def read_text(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines]


def parse_text(text):
    with open('word_data/replacer.json', 'r') as f:
        replace_dict = json.load(f)

    with open('word_data/symbol_mapper.json', 'r') as f:
        symbol_mapper = json.load(f)
    parsed = []
    for line in text:
        for symbol, replacer in symbol_mapper.items():
            line = line.replace(symbol, replacer)

        line = re.sub(r'[^\x00-\x7f]',r'', line)

        for to_replace, replacer in replace_dict.items():
            line = line.replace(to_replace, replacer)

        raw_punctuation_marks = [r"\n", r" ", r",", r";", r"!", r"\?", r"-", 
                                 r"\(", r"\)", r":", r'"', r"/", r"\\", r"=", r"+",
                                 r"@", r"#", r"№", r"$", r"%", r"^", r"&", r"`", 
                                 r"~", r"<", r">", r"[", r"]", r"{", r"}", r"_"]
        punctuation_marks = ["\n", " ", ",", ";", "!", "?", "-", 
                             "(", ")", ":", '"', "/", "\\", "=", "+",
                             "@", "#", "№", "$", "%", "^", "&", "`", 
                             "~", "<", ">", "[", "]", "{", "}", "_"]
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
