from src.letters_info import *

class Word:
    def __init__(self, grapheme_symbols, phoneme_symbols):
        assert len(grapheme_symbols) == len(phoneme_symbols)

        grapheme_symbols = [
            symbol.split(':') for symbol in grapheme_symbols
        ]
        phoneme_symbols = [
            symbol.split(':') for symbol in phoneme_symbols
        ]
        self.stress_info = []
        self.num_vowels = 0
        for i in range(len(grapheme_symbols)):
            stress_info = -1
            for phoneme in phoneme_symbols[i]:
                if self.is_phoneme_vowel(phoneme):
                    stress_info = max(stress_info, int(phoneme[-1]))
                    self.num_vowels += 1
            
            self.stress_info.append(stress_info)
        

        for i in range(len(grapheme_symbols)):
            stress_info = self.stress_info[i]
            if stress_info == -1:
                banned_grapheme_list = VOWELS
            else:
                banned_grapheme_list = STRICT_CONSONANTS
            graphemes = grapheme_symbols[i]


            if i != len(grapheme_symbols) - 1:
                next_is_different = (self.stress_info[i] == -1) + (self.stress_info[i+1] == -1) == 1
                while next_is_different and len(graphemes) >= 1 and graphemes[-1].lower() in banned_grapheme_list:
                        grapheme_symbols[i + 1] = [graphemes[-1]] + grapheme_symbols[i + 1]
                        graphemes.pop()
            if i != 0:
                prev_is_different = (self.stress_info[i-1] == -1) + (self.stress_info[i] == -1) == 1
                while prev_is_different and len(graphemes) >= 1 and graphemes[0].lower() in banned_grapheme_list:
                        grapheme_symbols[i - 1] = grapheme_symbols[i - 1] + [graphemes[0]]
                        graphemes.pop(0)
            
        self.grapheme_symbols = grapheme_symbols
        self.phoneme_symbols = phoneme_symbols
        self.word_stress = max(self.stress_info)
    

    def get_processed_str(self, no_stress=False):
        word = ''
        for i in range(len(self.grapheme_symbols)):
            grapheme = self.grapheme_symbols[i]
            if self.stress_info[i] > -1:
                current_index = 0
                while (current_index < len(grapheme) and 
                       grapheme[current_index].lower() in STRICT_CONSONANTS):
                    word += grapheme[current_index]
                    current_index += 1
                
                group_vowels = []
                while (current_index < len(grapheme) and 
                       grapheme[current_index].lower() in VOWELS):
                    group_vowels.append(grapheme[current_index])
                    current_index += 1
                
                if len(group_vowels) > 1:
                    word += '[' + ''.join(group_vowels) + ']'
                elif len(group_vowels) == 1:
                    word += ''.join(group_vowels)
                else:
                    word += PHANTOM_VOWEL

                if (self.stress_info[i] == self.word_stress and
                    not no_stress):
                    word += '<'
                
                while current_index < len(grapheme):
                    word += grapheme[current_index]
                    current_index += 1
            else:
                for letter in grapheme:
                    if letter in STRICT_VOWELS:
                        if word[-1] == PHANTOM_VOWEL:
                            word = word[:-1]
                            word += letter
                        else:
                            word += MUTE_SYMBOL
                    else:
                        word += letter
        return word

    def __str__(self):
        return ''.join([''.join(grapheme) for grapheme in self.grapheme_symbols])

    def __repr__(self) -> str:
        grapheme = '|'.join([''.join(grapheme) for grapheme in self.grapheme_symbols])
        phoneme = '|'.join(['.'.join(phoneme) for phoneme in self.phoneme_symbols])
        return f'[{grapheme}/{phoneme}]'

    def __len__(self):
        return len(self.grapheme_symbols)

    @staticmethod
    def is_phoneme_vowel(phoneme):            
        return phoneme[-1] in ['0', '1', '2']

    @staticmethod
    def is_phoneme_consonant(phoneme):            
        return not Word.is_phoneme_vowel(phoneme)
