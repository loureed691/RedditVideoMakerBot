import os
import shutil
from pathlib import Path
from typing import List


def _listdir(d: str) -> List[str]:
    """List directory with full paths.
    
    Args:
        d: Directory path
        
    Returns:
        List of full paths to files in the directory
    """
    return [os.path.join(d, f) for f in os.listdir(d)]


def cleanup(reddit_id: str) -> int:
    """Deletes all temporary assets in assets/temp

    Args:
        reddit_id: The Reddit post ID to clean up
    
    Returns:
        int: How many directories were deleted (0 or 1)
    """
    # Use absolute path from script location instead of relative path
    base_dir = Path(__file__).parent.parent
    directory = base_dir / "assets" / "temp" / reddit_id
    
    if directory.exists():
        shutil.rmtree(directory)
        return 1
    return 0
