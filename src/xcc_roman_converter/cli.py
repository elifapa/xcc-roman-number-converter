from xcc_roman_converter.cache import cache #, create_redis_cache, create_noop_cache
from xcc_roman_converter.converter import Converter
from xcc_roman_converter.numbersx import RomanNumber, ArabicNumber
import typer
from xcc_roman_converter.config import configure_logging
import structlog
import os

# Configure logging
configure_logging()
logger = structlog.get_logger()

app = typer.Typer()

# Global cache state
_global_cache_enabled = os.getenv("CACHE_ENABLED", "False").lower() in ("true", "1", "yes")
_current_cache = cache

@app.callback()
def global_options(
    debug: bool = typer.Option(False, help="Enable debug logging"),
    no_cache: bool = typer.Option(True, "--no-cache", help="Disable caching globally for all commands")
):
    """
    Global options for the CLI. Use --debug to enable debug logging, --no-cache to disable caching globally.
    """
    global _global_cache_enabled, _current_cache
    
    if debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    if no_cache:
        _global_cache_enabled = False
        _current_cache = None
        logger.debug("Caching disabled globally ⚪")
    if not no_cache:
        _global_cache_enabled = True
        _current_cache = cache

@app.command("cache-status")
def cache_status():
    """
    Check the status of the cache connection and retrieve cache info.
    """
    print("_global_cache_enabled:", _global_cache_enabled)
    if not _global_cache_enabled:
        logger.info("Cache is disabled globally ⚪")
        return
    
    if _current_cache.is_connected():
        logger.info("Cache is enabled and operational 🟢")
        try:
            if hasattr(_current_cache, 'client') and _current_cache.client:
                info = _current_cache.get_info()
                redis_version = info.get('redis_version', 'Unknown')
                key_count = _current_cache.get_key_count()
                logger.info(f"Redis version: {redis_version}")
                logger.info(f"Database keys: {key_count}")
        except Exception as e:
            logger.error("Failed to retrieve cache info", error=str(e))
    else:
        logger.warning("Cache is enabled but Redis is not available ❌")

@app.command("cache-clear")
def cache_clear():
    """
    Clears all cached conversion results.
    """
    if not _global_cache_enabled:
        logger.warning("Cache is disabled globally - nothing to clear")
        return
    
    if not _current_cache.is_connected():
        logger.warning("Cache is not available - nothing to clear")
        return
    
    if _current_cache.clear():
        logger.info("Cache cleared successfully ✅")
    else:
        logger.error("Failed to clear cache ❌")

@app.command("cache-keys")
def cache_keys():
    """
    Retrieve total number of cache keys along with first 10 key values.
    """
    if not _global_cache_enabled:
        logger.info("Cache is disabled globally - no keys to display ⚪")
        return

    if not _current_cache.is_connected():
        logger.error("Cache is not available ❌")
        return

    try:
        keys = _current_cache.get_keys("easyconvert:*")
        logger.info("Total cached conversions", count=len(keys))
        
        if keys:
            logger.info("📋 Recent cached conversions:")
            for key in keys[:10]:
                value = _current_cache.get(key, suppress_log=True)
                key_parts = key.split(":")
                if len(key_parts) >= 3:
                    input_type = key_parts[1]
                    input_value = key_parts[2]
                    logger.info(f"  {input_type}:{input_value} → {value}")
            
            if len(keys) > 10:
                logger.info(f"  ... and {len(keys) - 10} more")
        else:
            logger.info("No cached conversions found")

    except Exception as e:
        logger.error("Failed to retrieve cache stats ❌", error=str(e))

@app.command("arabic")
def convert_arabic(
    number: int = typer.Argument(..., help="Arabic number to convert to Roman"),
    # cache: bool = typer.Option(True, "--cache/--no-cache", help="Enable/disable cache for this conversion")
):
    """
    Converts an Arabic number to a Roman numeral.
    
    Examples:
      easyconvert arabic 42                    # Use cache (default)

    """
    logger.debug("Converting Arabic to Roman", input_number=number, cache_enabled=cache)
    
    try:
        class_input = ArabicNumber(number=number)
        
        converter = Converter(input=class_input)
        output = converter.output 
        duration = converter.duration
        
        # Determine cache status for display
        cache_used = _global_cache_enabled and cache and cache.is_connected()
        cache_status = "✅ Cached" if cache_used else "⚪ Not cached"
        
        logger.info("Conversion successful", 
                   duration_ms=duration, 
                   input_number=number, 
                   output=output,
                   cache_status=cache_status)
        logger.info(f"💥 The Roman numeral equivalent of {class_input.number} is {output}. 💥")
        return output
    except ValueError as e:
        logger.error("Conversion failed", input_number=number, error=e)

@app.command("roman")
def convert_roman(
    number: str = typer.Argument(..., help="Roman numeral to convert to Arabic"),
):
    """
    Converts a Roman numeral to an Arabic number.
    
    Examples:
      easyconvert roman "XLII"                 # Use cache (default)
      easyconvert roman "XLII" --no-cache     # Skip cache for this conversion
      easyconvert --no-cache roman "XLII"     # Global no-cache flag
    """
    logger.debug("Converting Roman to Arabic", input_number=number, cache_enabled=cache)
    
    try:
        class_input = RomanNumber(number=number)
        logger.debug("Roman number", class_input=class_input)

        
        converter = Converter(input=class_input)
        output = converter.output 
        duration = converter.duration
        
        # Determine cache status for display
        cache_used = _global_cache_enabled and cache and cache.is_connected()
        cache_status = "✅ Cached" if cache_used else "⚪ Not cached"
        
        logger.info("Conversion successful", 
                   duration_ms=duration, 
                   input_number=number, 
                   output=output,
                   cache_status=cache_status)
        logger.info(f"💥 The Arabic numeral equivalent of {class_input.number} is {output}. 💥")
        return output
        
    except ValueError as e:
        logger.error("Conversion failed", input_number=number, error=e)

def main() -> None:
    app()