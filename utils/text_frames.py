"""
Generate image sequences for word-by-word text display.
This module creates transparent PNG overlays with progressive text.
"""

import os
import textwrap
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw, ImageFont


def wrap_text_to_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    Wrap text to fit within a maximum width.

    Args:
        text: Text to wrap
        font: Font to use for measurement
        max_width: Maximum width in pixels

    Returns:
        List of text lines
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def create_text_overlay_image(
    text: str,
    width: int,
    height: int,
    fontfile: str,
    fontsize: int = 50,
    fontcolor: tuple = (255, 255, 255, 255),
    bgcolor: tuple = (0, 0, 0, 180),
    padding: int = 20,
    position: str = "bottom",
) -> Image.Image:
    """
    Create a transparent image with text overlay.

    Args:
        text: Text to render
        width: Image width
        height: Image height
        fontfile: Path to font file
        fontsize: Font size
        fontcolor: Text color as RGBA tuple
        bgcolor: Background color as RGBA tuple (with alpha for transparency)
        padding: Padding around text
        position: Text position ('top', 'center', 'bottom')

    Returns:
        PIL Image with text overlay
    """
    # Create transparent image
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Load font
    try:
        font = ImageFont.truetype(fontfile, fontsize)
    except:
        font = ImageFont.load_default()

    # Wrap text to fit width
    max_text_width = width - 2 * padding
    lines = wrap_text_to_lines(text, font, max_text_width)

    # Calculate text dimensions
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = font.getbbox(line)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    total_text_height = sum(line_heights) + (len(lines) - 1) * padding // 2
    max_line_width = max(line_widths) if line_widths else 0

    # Determine Y position
    if position == "top":
        y_start = padding
    elif position == "center":
        y_start = (height - total_text_height) // 2
    else:  # bottom
        y_start = int(height * 0.65)

    # Draw background box
    box_height = total_text_height + padding * 2
    box_x1 = (width - max_line_width - padding * 2) // 2
    box_y1 = y_start - padding
    box_x2 = box_x1 + max_line_width + padding * 2
    box_y2 = box_y1 + box_height

    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=bgcolor)

    # Draw text lines
    y = y_start
    for line, line_width in zip(lines, line_widths):
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill=fontcolor)
        y += line_heights[lines.index(line)] + padding // 2

    return image


def generate_word_by_word_frames(
    timings: List[Dict[str, any]],
    width: int,
    height: int,
    output_dir: str,
    filename_prefix: str,
    fontfile: str,
    fontsize: int = 50,
    fontcolor: tuple = (255, 255, 255, 255),
    position: str = "bottom",
):
    """
    Generate PNG frames for word-by-word text animation.

    Args:
        timings: List of word timing dictionaries
        width: Frame width
        height: Frame height
        output_dir: Directory to save frames
        filename_prefix: Prefix for frame filenames
        fontfile: Path to font file
        fontsize: Font size
        fontcolor: Text color
        position: Text position
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate a frame for each word progression
    for i, timing in enumerate(timings):
        # Build progressive text
        progressive_text = " ".join([t["word"] for t in timings[: i + 1]])

        # Create image
        image = create_text_overlay_image(
            text=progressive_text,
            width=width,
            height=height,
            fontfile=fontfile,
            fontsize=fontsize,
            fontcolor=fontcolor,
            position=position,
        )

        # Save frame
        output_path = os.path.join(output_dir, f"{filename_prefix}_word_{i:04d}.png")
        image.save(output_path)
