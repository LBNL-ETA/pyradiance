"""
Auxiliary functions.
"""

from pathlib import Path
from functools import wraps
from subprocess import CalledProcessError

BINPATH = Path(__file__).parent / "bin"

def handle_called_process_error(func):
    """
    Decorator to handle subprocess.CalledProcessError.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except CalledProcessError as e:
            raise RuntimeError(f"An error occurred with exit code {e.returncode}: {e.stderr.decode('utf-8')}")
        else:
            return result
    return wrapper
