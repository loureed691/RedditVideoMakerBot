import os
import shutil
from pathlib import Path
from os.path import exists


def _listdir(d):  # listdir with full path
    return [os.path.join(d, f) for f in os.listdir(d)]


def cleanup(reddit_id) -> int:
    """Deletes all temporary assets in assets/temp

    Returns:
        int: How many files were deleted
    """
    # Use absolute path from script location instead of relative path
    base_dir = Path(__file__).parent.parent
    directory = base_dir / "assets" / "temp" / reddit_id
    
    if directory.exists():
        shutil.rmtree(directory)
        return 1
    return 0
