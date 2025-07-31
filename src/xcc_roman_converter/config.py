import logging
import structlog

# Mapping of Roman numerals to their corresponding Arabic values
ROMAN_TO_ARABIC = {
    'I': 1,
    'V': 5,
    'X': 10,
    'L': 50,
    'C': 100,
    'D': 500,
    'M': 1000,
    '_V': 5000,
    '_X': 10000,
    '_L': 50000,
    '_C': 100000, 
    '_D': 500000,
    '_M': 1000000,
}

ARABIC_TO_ROMAN = {
    1: "I", 
    4: "IV", 
    5: "V", 
    9: "IX",
    10: "X", 
    40: "XL", 
    50: "L",
    90: "XC",
    100: "C", 
    400: "CD", 
    500: "D",
    900: "CM", 
    1000: "M"
}

## Logging configuration
def configure_logging():
    """
    Configures structlog for structured logging.
    """
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # structlog.processors.JSONRenderer(),
            structlog.dev.ConsoleRenderer(colors=True),  # Prettify logs with colors
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )