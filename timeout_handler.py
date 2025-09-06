"""
Timeout handler for database operations to prevent health check timeouts.
"""
import signal
import functools
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def timeout_handler(signum, frame):
    """Handler for timeout signals."""
    raise TimeoutError("Database operation timed out")

@contextmanager
def database_timeout(seconds=10):
    """Context manager for database operations with timeout."""
    # Set up the timeout handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    except TimeoutError:
        logger.error(f"Database operation timed out after {seconds} seconds")
        raise
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def with_timeout(seconds=10):
    """Decorator for database operations with timeout."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                with database_timeout(seconds):
                    return func(*args, **kwargs)
            except TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds} seconds")
                return None
        return wrapper
    return decorator