from xcc_roman_converter.numbersx import RomanNumber, ArabicNumber
from xcc_roman_converter.config import ROMAN_TO_ARABIC, ARABIC_TO_ROMAN
from xcc_roman_converter.cache import cache
from xcc_roman_converter.config import configure_logging
import structlog
import time

# Configure logging
configure_logging()
logger = structlog.get_logger()

class Converter:
    def __init__(self, input: RomanNumber | ArabicNumber):
        self.roman_to_arabic = ROMAN_TO_ARABIC
        # self.arabic_to_roman = {v: k for k, v in ROMAN_TO_ARABIC.items()} 
        self.arabic_to_roman = ARABIC_TO_ROMAN
        self.input = input
        self.output = None
        self.duration = 0

        # Try to retrieve from cache
        cache_key = self._generate_redis_cache_key()
        cached_value = cache.get(cache_key)
        if cached_value:
            self.output = cached_value
            return

        # If not in cache, perform conversion and set it to cache
        if isinstance(input, RomanNumber):
            self.output, self.duration = self.convert_to_arabic()
        elif isinstance(input, ArabicNumber):
            self.output, self.duration = self.convert_to_roman()

        cache.set(cache_key, self.output)

    def _generate_redis_cache_key(self) -> str:
        """
        Generates unique cache key for Redis. 
        """
        input_type = type(self.input).__name__.lower()
        input_value = str(self.input.number)
        return f"easyconvert:{input_type}:{input_value}"
    
    def _convert(self):
        """
        Converts the input number based on its type, using Redis cache if available.
        """
        # Try to retrieve from cache
        cache_key = self._generate_redis_cache_key()
        cached_value = cache.get(cache_key)
        if cached_value:
            self.output = cached_value
            return

        # If not in cache, perform conversion and set it to cache
        if isinstance(input, RomanNumber):
            self.output = self.convert_to_arabic()
        elif isinstance(input, ArabicNumber):
            self.output = self.convert_to_roman()

        cache.set(cache_key, self.output)


    def convert_to_arabic(self) -> tuple[int, float]:
        """
        Converts a Roman numeral string to its Arabic numeral equivalent.
        
        Example: MMMDCCXXIV (Roman) -> 3724 (Arabic)
        reversed: VIXXCCDMMM 
        """

        input_number = self.input.number
        logger.info("Performing Roman to Arabic conversion...", input=input_number)
        start = time.perf_counter()
        output = 0
        prev_value = 0

        for char in reversed(input_number):
            value = self.roman_to_arabic.get(char, 0)
            if value < prev_value:
                output -= value
            else:
                output += value
            prev_value = value

        end = time.perf_counter()
        duration = round((end - start) * 1000, 5)

        return output, duration

    def convert_to_roman(self) -> tuple[str, float]:
        """
        Converts an Arabic numeral to its Roman numeral equivalent.
        """
        input_number = self.input.number
        logger.info("Performing Arabic to Roman conversion...", input=input_number)
        
        start = time.perf_counter()

        roman_numerals = []
        for value, numeral in sorted(self.arabic_to_roman.items(), key=lambda x: x[0], reverse=True):
            while input_number >= value:
                roman_numerals.append(numeral)
                input_number -= value

        end = time.perf_counter()
        duration = round((end - start) * 1000, 5)

        return ''.join(roman_numerals), duration
    