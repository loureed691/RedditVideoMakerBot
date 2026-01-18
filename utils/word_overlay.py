"""
Helper functions for adding word-by-word text overlays to videos using FFmpeg.
"""

import os
import textwrap
from typing import Dict, List

import ffmpeg


def create_word_by_word_drawtext_filter(
    text: str,
    timings: List[Dict[str, any]],
    start_time: float,
    fontfile: str,
    fontsize: int = 40,
    fontcolor: str = "white",
    x: str = "(w-text_w)/2",
    y: str = "(h-text_h)/2",
    box: bool = True,
    boxcolor: str = "black@0.5",
    boxborderw: int = 10,
) -> List[str]:
    """
    Create FFmpeg drawtext filter expressions for word-by-word text display.

    Args:
        text: The full text
        timings: List of word timing dictionaries with 'word', 'start', 'end'
        start_time: The absolute start time in the video
        fontfile: Path to the font file
        fontsize: Font size in pixels
        fontcolor: Color of the text
        x: X position expression
        y: Y position expression
        box: Whether to add a background box
        boxcolor: Background box color
        boxborderw: Background box border width

    Returns:
        List of drawtext filter strings
    """
    drawtext_filters = []

    # Build progressive text for each timing point
    for i, timing in enumerate(timings):
        # Get all words up to and including this one
        progressive_text = " ".join([t["word"] for t in timings[: i + 1]])

        # Escape special characters for FFmpeg
        progressive_text = progressive_text.replace("'", "'\\\\\\''")
        progressive_text = progressive_text.replace(":", "\\:")

        # Calculate absolute times in the video
        abs_start = start_time + timing["start"]
        if i < len(timings) - 1:
            abs_end = start_time + timings[i + 1]["start"]
        else:
            abs_end = start_time + timing["end"]

        # Build the drawtext filter
        filter_parts = [
            f"text='{progressive_text}'",
            f"fontfile={fontfile}",
            f"fontsize={fontsize}",
            f"fontcolor={fontcolor}",
            f"x={x}",
            f"y={y}",
            f"enable='between(t,{abs_start:.3f},{abs_end:.3f})'",
        ]

        if box:
            filter_parts.extend([f"box=1", f"boxcolor={boxcolor}", f"boxborderw={boxborderw}"])

        drawtext_filters.append(":".join(filter_parts))

    return drawtext_filters


def apply_word_by_word_overlay(
    video_clip,
    text: str,
    timings: List[Dict[str, any]],
    start_time: float,
    fontfile: str = None,
    fontsize: int = 40,
    fontcolor: str = "white",
    position: str = "bottom",
):
    """
    Apply word-by-word text overlay to a video clip.

    Args:
        video_clip: FFmpeg video stream
        text: The text to display
        timings: Word timing information
        start_time: Start time in the video
        fontfile: Path to font file (default: Roboto-Bold)
        fontsize: Font size
        fontcolor: Text color
        position: Text position ('top', 'center', 'bottom')

    Returns:
        Video clip with text overlay
    """
    if fontfile is None:
        fontfile = os.path.join("fonts", "Roboto-Bold.ttf")

    # Determine Y position based on position parameter
    if position == "top":
        y = "h*0.1"
    elif position == "center":
        y = "(h-text_h)/2"
    else:  # bottom
        y = "h*0.7"

    # Get drawtext filters
    drawtext_filters = create_word_by_word_drawtext_filter(
        text=text,
        timings=timings,
        start_time=start_time,
        fontfile=fontfile,
        fontsize=fontsize,
        fontcolor=fontcolor,
        x="(w-text_w)/2",
        y=y,
        box=True,
        boxcolor="black@0.7",
        boxborderw=10,
    )

    # Apply all drawtext filters sequentially
    result = video_clip
    for filter_str in drawtext_filters:
        result = result.filter("drawtext", filter_str)

    return result
