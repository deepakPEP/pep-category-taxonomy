import time
from common.logger import get_logger
from common.config import MAX_RETRIES, RETRY_DELAY_SECONDS

logger = get_logger("retry")

def with_retry(fn, *args, retries: int = MAX_RETRIES, delay: int = RETRY_DELAY_SECONDS, label: str = "", **kwargs):
    """
    Generic retry wrapper.
    Retries fn(*args, **kwargs) up to `retries` times with `delay` seconds between attempts.
    Raises the last exception if all retries are exhausted.
    """
    last_exception = None

    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as ex:
            last_exception = ex
            logger.warning(
                f"[{label or fn.__name__}] Attempt {attempt}/{retries} failed: {ex}"
            )
            if attempt < retries:
                logger.info(f"[{label or fn.__name__}] Retrying in {delay}s...")
                time.sleep(delay)

    logger.error(f"[{label or fn.__name__}] All {retries} attempts failed.")
    raise last_exception
