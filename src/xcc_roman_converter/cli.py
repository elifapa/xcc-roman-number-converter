from xcc_roman_converter.cache import cache
from xcc_roman_converter.converter import Converter
from xcc_roman_converter.numbersx import RomanNumber, ArabicNumber
import typer
# from rich import print
from xcc_roman_converter.config import configure_logging
import typer
import structlog

# Configure logging
configure_logging()
logger = structlog.get_logger()

app = typer.Typer()

@app.callback()
def global_options(debug: bool = typer.Option(False, help="Enable debug logging")):
    """
    Global options for the CLI. Use --debug to enable debug logging.
    """
    if debug:
        # Set logging level to DEBUG
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

@app.command("cache-status")
def cache_status():
    """
    Check the status of the cache connection and retrieve cache info."
    """
    if cache.is_connected():
        logger.info("Cache is connected and operational 🟢")
        try:
            info = cache.client.info()
            logger.debug("Cache info", info=info)
        except Exception as e:
            logger.error("Failed to retrieve cache info", error=str(e))
    else:
        logger.warning("Cache is not connected or operational ❌")

@app.command("cache-clear")
def cache_clear():
    """
    Clears all cached conversion results.
    """
    cache.clear()

@app.command("cache-keys")
def cache_keys():
    """
    Retrieve roral number of cache keys along with first 10 key values.
    """
    if not cache.is_connected():
        logger.error("Cache is not connected or operational ❌")

    try:
        keys = cache.client.keys("easyconvert:*")
        logger.info("Total number of cache keys", count=len(keys))
        if keys:

            logger.info("First 10 cache keys:")
            for key in keys[:10]:
                value = cache.get(key, suppress_log=True)
                key_parts = key.split(":")
                input_type = key_parts[1]
                input = key_parts[2]
                logger.info(f"{input_type}:{input} --> {value}")
                #print(f"{input_type}:{input} --> {value}")

    except Exception as e:
        logger.error("Failed to retrieve cache stats ❌", error=str(e))

@app.command("arabic")
def convert_arabic(number: int = typer.Argument(..., 
                                                help="Arabic number to convert to Roman"
                                                )):
    """
    Converts an Arabic number to a Roman numeral.
    """
    logger.debug("Converting Arabic to Roman", input_number=number)
    try:
        class_input = ArabicNumber(number=number)
        converter = Converter(input=class_input)
        output = converter.output 
        duration = converter.duration
        logger.info("Conversion successful", duration_ms = duration, input_number = number, output = output)
        logger.info(f"💥 The Roman numeral equivalent of {class_input.number} is {output}. 💥")

    except ValueError as e:
        # typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        # print(f":rotating_light: [bold red]Error:[/bold red] {e}")
        logger.error("Conversion failed", input_number=number, error=e)


@app.command("roman")
def convert_roman(number: str = typer.Argument(..., #MMMDCCXXIV
                                               help="Roman numeral to convert to Arabic"
                                               )):
    """
    Converts a Roman numeral to an Arabic number.
    """
    logger.debug("Converting Roman to Arabic", input_number=number)
    try:
        class_input = RomanNumber(number=number)
        logger.debug("Roman number", class_input=class_input)

        converter = Converter(input=class_input)
        output = converter.output 
        duration = converter.duration
        logger.info("Conversion successful", duration_ms = duration, input_number = number, output = output)
        logger.info(f"💥 The Arabic numeral equivalent of {class_input.number} is {output}. 💥")
    except ValueError as e:
        logger.error("Conversion failed", input_number=number, error=e)


def main() -> None:
    app()



