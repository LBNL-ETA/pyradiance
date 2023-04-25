"""
Auxiliary functions.
"""

from pathlib import Path
from functools import wraps
from subprocess import CalledProcessError

BINPATH = Path(__file__).parent / "bin"

def handle_called_process_error(func):
    """
    Decorator to handle CalledProcessError.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except CalledProcessError as e:
            err = ""
            if e.stderr is not None:
                err = e.stderr.decode()
            raise RuntimeError(f"An error occurred with exit code {e.returncode}: {err}")
        else:
            return result
    return wrapper
