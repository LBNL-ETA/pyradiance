"""
Auxiliary functions.
"""

from pathlib import Path
from functools import wraps
from subprocess import CalledProcessError
import os

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
            errmsg = e.stderr or b""
            raise RuntimeError(
                f"An error occurred with exit code {e.returncode}: {errmsg.decode()}"
            )
        else:
            return result

    return wrapper


def write(
    file_path: str | Path, data: str | bytes, overwrite: bool = True, mode: str = "wb"
) -> str:
    """Write data to a file.

    Args:
        file_path: path to file
        data: data to write
        overwrite: if True, overwrite the file if it already exists
        mode: 'w' for text, 'wb' for binary

    Returns:
        str: path to file
    """
    if not overwrite and os.path.exists(file_path):
        raise Exception(
            f"The path {file_path} already exists and "
            f'"overwrite" has been set to False.'
        )
    else:
        with open(file_path, mode=mode) as write_data:
            write_data.write(data)
    return str(file_path)
