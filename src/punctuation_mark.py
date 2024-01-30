class PunctuationMark:
    def __init__(self, mark: str):
        self.mark = mark
    
    def get_raw_str(self):
        return self.mark

    def get_processed_str(self, no_stress=False):
        return self.mark
    
    def __repr__(self):
        return self.mark
    
    def __str__(self) -> str:
        return self.mark
