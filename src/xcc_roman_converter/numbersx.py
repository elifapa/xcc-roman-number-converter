from dataclasses import dataclass

@dataclass 
class RomanNumber:
    number: str 

    def __post_init__(self):
        self.number = self.number.upper()

        if not self.is_valid_roman(self.number):
            raise ValueError(f"Invalid Roman numeral: {self.number}")

    @staticmethod
    def is_valid_roman(roman: str) -> bool:
        """
        Validates if the given string is a valid Roman numeral.
        """
        import re
        roman_pattern = (
            r"^M{0,3}"  # Thousands - 0 to 3000
            r"(CM|CD|D?C{0,3})"  # Hundreds - 900 (CM), 400 (CD), 0-300 (C, CC, CCC), or 500-800 (D, DC, DCC, DCCC)
            r"(XC|XL|L?X{0,3})"  # Tens - 90 (XC), 40 (XL), 0-30 (X, XX, XXX), or 50-80 (L, LX, LXX, LXXX)
            r"(IX|IV|V?I{0,3})$"  # Units - 9 (IX), 4 (IV), 0-3 (I, II, III), or 5-8 (V, VI, VII, VIII)
        )
        return bool(re.match(roman_pattern, roman))
    
    def __str__(self):
        return vars(self)


@dataclass 
class ArabicNumber:
    number: int 
    
    def __post_init__(self):
        self.number = int(self.number)  # Ensure the number is stored as an int
        if not isinstance(self.number, int):
            raise ValueError("ArabicNumber must be initialized with an integer.")
        if self.number < 1:
            raise ValueError("ArabicNumber must be a positive integer.")
        if self.number > 3999:
            raise ValueError("Currently only Arabic numbers up to 3999 are supported.")