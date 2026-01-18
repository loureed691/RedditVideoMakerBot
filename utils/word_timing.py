"""
Utility module for generating word-level timing information for text-to-speech.
This module estimates word timings based on audio duration and word count.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def estimate_word_timings(text: str, audio_duration: float) -> List[Dict[str, Any]]:
    """
    Estimate word-level timing based on text and audio duration.

    Args:
        text: The text that was spoken
        audio_duration: Duration of the audio in seconds

    Returns:
        List of dictionaries with 'word', 'start', and 'end' times

    Raises:
        ValueError: If audio_duration is not positive
    """
    # Split text into words (removing extra whitespace and punctuation for timing)
    words = [word.strip() for word in text.split() if word.strip()]

    if not words:
        return []

    if audio_duration <= 0:
        raise ValueError(f"audio_duration must be positive, got {audio_duration}")

    # Calculate average time per word
    time_per_word = audio_duration / len(words)

    timings = []
    current_time = 0.0

    for word in words:
        timings.append({"word": word, "start": current_time, "end": current_time + time_per_word})
        current_time += time_per_word

    return timings


def save_word_timings(timings: List[Dict[str, Any]], filepath: str):
    """
    Save word timings to a JSON file.

    Args:
        timings: List of word timing dictionaries
        filepath: Path to save the JSON file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(timings, f, indent=2, ensure_ascii=False)


def load_word_timings(filepath: str) -> List[Dict[str, Any]]:
    """
    Load word timings from a JSON file.

    Note: This function is part of the public utility API and may be used by external
    callers (e.g., UI layers, testing code) to load previously saved timing information.

    Args:
        filepath: Path to the JSON file

    Returns:
        List of word timing dictionaries

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_progressive_text_at_time(timings: List[Dict[str, Any]], time: float) -> str:
    """
    Compute the progressive text that should be visible at a given playback time.

    This helper is intended as part of the public utility API of this module and may be
    used by external callers (e.g., UI layers, animation code, or tests) to reconstruct
    the text that should be displayed word-by-word based on timing information.

    All words whose `start` time is less than or equal to the given time are included,
    in their original order, and joined into a single string.

    Args:
        timings: List of word timing dictionaries, each containing at least
            ``"word"`` (str) and ``"start"`` (float) keys.
        time: Current time in seconds.

    Returns:
        A string containing all words that should be visible at the given time.
    """
    visible_words = [timing["word"] for timing in timings if timing["start"] <= time]
    return " ".join(visible_words)
